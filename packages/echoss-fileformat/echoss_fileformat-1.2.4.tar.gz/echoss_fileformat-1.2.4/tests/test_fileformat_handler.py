import io
import unittest
import logging
import os
import time
from echoss_fileformat import FileformatBase
from echoss_fileformat import get_logger, to_table

logger = get_logger("test_fileformat_nandler")


class FileformatHandlerTestCase(unittest.TestCase):
    """
        테스트 설정
    """
    def setUp(self):
        ids = self.id().split('.')
        self.str_id = f"{ids[-2]}: {ids[-1]}"
        self.start_time = time.perf_counter()
        logger.info(f"setting up test [{self.str_id}] ")

    def tearDown(self):
        self.end_time = time.perf_counter()
        logger.info(f" tear down test [{self.str_id}] elapsed time {(self.end_time-self.start_time)*1000: .3f}ms \n")

    """
    유닛 테스트 
    """
    def test_get_file_obj_not_exist(self):
        handler = FileformatBase()

        # not exist Directory and 'r'
        filename = 'test_data_wrong/complex_one.json'
        open_mode = 'r'
        with self.assertRaises(FileNotFoundError) as context:
            fp, binary_mode, opened = handler._get_file_obj(filename, open_mode)
            handler._safe_close(fp, opened)
        self.assertTrue(filename in str(context.exception))

        # not exist Directory and 'w'
        filename = 'test_data_wrong/complex_one.json'
        open_mode = 'w'
        with self.assertRaises(FileNotFoundError) as context:
            fp, binary_mode, opened = handler._get_file_obj(filename, open_mode)
            handler._safe_close(fp, opened)
        self.assertTrue(filename in str(context.exception))

        # exist Directory and 'r
        filename = 'test_data/complex_one_not_exist.json'
        open_mode = 'r'
        with self.assertRaises(FileNotFoundError) as context:
            fp, mode, opened = handler._get_file_obj(filename, open_mode)
            handler._safe_close(fp, opened)
        self.assertTrue(filename in str(context.exception))

        # exist Directory and 'w'
        filename = 'test_data/complex_one_not_exist_to_delete.json'
        open_mode = 'w'
        try:
            fp, mode, opened = handler._get_file_obj(filename, open_mode)
            if opened:
                handler._safe_close(fp, opened)
                # 임시 파일 삭제
                os.remove(filename)
        except Exception as e:
            self.assertTrue(filename in str(e))

    def test_get_file_obj_open_mode_filename(self):
        handler = FileformatBase()

        # not exist Directory and 'r'
        open_modes = ['r', 'w', 'rb', 'wb']
        filenames = [
            'test_data/simple_multiline_object.jsonl',
            'test_data/simple_multiline_object_to_delete.json',
            'test_data/simple_multiline_object.jsonl',
            'test_data/simple_multiline_object_to_delete.json',
        ]

        line_list = []
        for filename, open_mode in zip(filenames, open_modes):
            handler = FileformatBase()
            fp, mode, opened = handler._get_file_obj(filename, open_mode)
            # logger.info(f"{fp=} {mode=} {opened=}")

            if open_mode in ['r', 'rb']:
                try:
                    for l in fp:
                        line_list.append(l)
                except Exception as e:
                    logger.info(f"{e}")

            elif open_mode in ['w', 'wb']:
                for l in line_list:
                    fp.write(l)
                line_list.clear()

            if opened:
                handler._safe_close(fp, opened)

            if open_mode in ['r', 'rb']:
                logger.info(f"assertEqual({len(line_list)}, 15)")
                self.assertEqual(len(line_list), 15)
            elif open_mode in ['w', 'wb']:
                logger.info(f"{os.path.exists(filename)=} and {(os.path.getsize(filename) > 0)=} are all True ")
                self.assertTrue(os.path.exists(filename))
                self.assertTrue(os.path.getsize(filename) > 0)
                if '_to_delete' in filename:
                    os.remove(filename)
        pass

    def test_get_file_obj_open_mode_file_obj(self):
        handler = FileformatBase()

        # not exist Directory and 'r'
        open_modes = ['r', 'w', 'rb', 'wb']
        filenames = [
            'test_data/simple_multiline_object.jsonl',
            'test_data/simple_multiline_object_to_delete.json',
            'test_data/simple_multiline_object.jsonl',
            'test_data/simple_multiline_object_to_delete.json',
        ]
        expect_instances = [
            io.TextIOWrapper,
            io.TextIOWrapper,
            io.BufferedIOBase,
            io.BufferedIOBase
        ]

        line_list = []
        for filename, open_mode, expect_instance in zip(filenames, open_modes, expect_instances):
            handler = FileformatBase()

            if 'b' in open_mode:
                fp = open(filename, open_mode)
            else:
                fp = open(filename, open_mode, encoding='utf-8')

            result_fp, binary_mode, opened = handler._get_file_obj(fp, open_mode)

            # logger.info(f"{result_fp=}. {binary_mode=}, {opened=}")
            logger.info(f"assertTrue {isinstance(fp, expect_instance)=}")
            self.assertTrue(isinstance(fp, expect_instance))

            if opened:
                handler._safe_close(fp, opened)
                if '_to_delete' in filename:
                    os.remove(filename)
        pass


if __name__ == '__main__':
    unittest.main(verbosity=2)
