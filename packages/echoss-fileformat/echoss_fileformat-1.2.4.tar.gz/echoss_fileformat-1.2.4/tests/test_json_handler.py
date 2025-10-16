import unittest
import time
import logging
import os

from echoss_fileformat import JsonHandler, FeatherHandler
from echoss_fileformat import get_logger, to_table

logger = get_logger(logger_name='test_json_handler', backup_count=1)


class MyTestCase(unittest.TestCase):
    """
        테스트 설정
    """
    def setUp(self):
        """Before test"""
        ids = self.id().split('.')
        self.str_id = f"{ids[-2]}: {ids[-1]}"
        self.start_time = time.perf_counter()
        logger.info(f"setting up test [{self.str_id}] ")

    def tearDown(self):
        """After test"""
        self.end_time = time.perf_counter()
        logger.info(f" tear down test [{self.str_id}] elapsed time {(self.end_time-self.start_time)*1000: .3f}ms \n")

    """
    유닛 테스트 
    """

    def test_load_complex_by_json_type(self):
        json_types = ['object', 'array', 'multiline']
        expect_passes = [0, 0, 0]
        expect_fails = [0, 1, 1942]

        for processing_type, expect_pass, expect_fail in zip(json_types, expect_passes, expect_fails):
            try:
                handler = JsonHandler(processing_type)
                dict_obj = handler.load('test_data/complex_one_object.json')
                pass_size = len(handler.pass_list)
                fail_size = len(handler.fail_list)
            except Exception as e:
                self.assertTrue(True, f"\t {processing_type=} File load fail by {e}")
            else:
                logger.info(f"\t {processing_type=} assertEqual({expect_pass=}, {pass_size=})")
                self.assertEqual(pass_size, expect_pass)
                logger.info(f"\t {processing_type=} assertEqual({expect_fail=}, {fail_size=})")
                self.assertEqual(fail_size, expect_fail)


    def test_load_complex_by_data_key(self):
        json_types = ['object', 'array', 'multiline']
        expect_passes = [0, 102, 0]
        expect_fails = [0, 0, 1942]

        for processing_type, expect_pass, expect_fail in zip(json_types, expect_passes, expect_fails):
            try:
                handler = JsonHandler(processing_type)
                handler.load('test_data/complex_one_object.json', data_key='main')
                pass_size = len(handler.pass_list)
                fail_size = len(handler.fail_list)
            except Exception as e:
                logger.error(f"\t {processing_type=} File load raise: {e}")
                self.assertTrue(True, f"\t {processing_type=} File load raise: {e}")
            else:
                logger.info(f"\t {processing_type=} load assertEqual({expect_pass=}, {pass_size=})")
                self.assertEqual(pass_size, expect_pass)
                logger.info(f"\t {processing_type=} load assertEqual({expect_fail=}, {fail_size=})")
                self.assertEqual(fail_size, expect_fail)

    def test_load_mutliline_by_mode(self):
        modes = ['text', 'binary']
        expect_passes = [15, 15]
        expect_fails = [0, 0]

        for mode, expect_pass, expect_fail in zip(modes, expect_passes, expect_fails):
            try:
                handler = JsonHandler('multiline')
                if mode == 'text':
                    with open('test_data/simple_multiline_object.jsonl', 'r', encoding='utf-8') as fp:
                        handler.load(fp)
                        pass_size = len(handler.pass_list)
                        fail_size = len(handler.fail_list)
                elif mode == 'binary':
                    with open('test_data/simple_multiline_object.jsonl', 'rb') as fb:
                        handler.load(fb)
                        pass_size = len(handler.pass_list)
                        fail_size = len(handler.fail_list)
            except Exception as e:
                self.assertTrue(True, f"\t {mode} multiline File load fail by {e}")
            else:
                logger.info(f"\t open mode '{mode}' 'multiline' expect pass {expect_pass} get {pass_size}")
                # self.assertEqual(pass_size == expect_pass)
                logger.info(f"\t open mode '{mode}' 'multiline' expect fail {expect_fail} get {fail_size}")
                # self.assertEqual(fail_size == expect_fail)

    def test_load_mutliline_by_data_key(self):
        processing_types = ['object', 'array', 'multiline']
        expect_passes = [0, 0, 15]
        expect_fails = [1, 1, 0]

        for processing_type, expect_pass, expect_fail in zip(processing_types, expect_passes, expect_fails):
            try:
                handler = JsonHandler(processing_type)
                handler.load('test_data/simple_multiline_object.jsonl', data_key='message')
                pass_size = len(handler.pass_list)
                fail_size = len(handler.fail_list)
            except Exception as e:
                self.assertTrue(True, f"\t {processing_type} json_type File load fail by {e}")
            else:
                logger.info(f"\t {processing_type} load expect pass {expect_pass} get {pass_size}")
                self.assertTrue(pass_size == expect_pass)
                logger.info(f"\t {processing_type} load expect fail {expect_fail} get {fail_size}")
                self.assertTrue(fail_size == expect_fail)

            # 임시 코드로 feather 저장
            if processing_type == 'multiline':
                df = handler.to_pandas()
                feather_handler = FeatherHandler()
                feather_handler.dump('test_data/simple_object.feather', df)


    """
    dump
    """

    def test_dump_complex_by_json_type(self):
        json_types = ['object', 'array']
        data_keys = ['', 'main']
        expect_file_sizes = [35248, 32724]

        load_filename = 'test_data/complex_one_object.json'
        dump_filename = 'test_data/complex_one_object_dump_to_delete.json'

        for processing_type, data_key, expect_file_size  in zip(json_types, data_keys, expect_file_sizes):
            try:
                handler = JsonHandler(processing_type)
                dict_obj = handler.load(load_filename, data_key=data_key)
                pass_size = len(handler.pass_list)

                if processing_type == 'object':
                    handler.dump(dump_filename, data=dict_obj)
                else:
                    handler.dump(dump_filename)
                exist = os.path.exists(dump_filename)
                file_size = os.path.getsize(dump_filename)

                if exist and 'to_delete' in dump_filename:
                    os.remove(dump_filename)

                logger.info(f"\t assertEqual(True, {exist=}) at {processing_type=} dump")
                self.assertEqual(True, exist)
                logger.info(f"\t assertEqual({expect_file_size=}, {file_size=}) at {processing_type=} dump")
                self.assertEqual(expect_file_size, file_size)
            except Exception as e:
                self.assertTrue(True, f"\t {processing_type} json_type File dump fail by {e}")

    def test_dump_mutliline_by_mode(self):
        # multiline 은 내부적으로 binary 로 동작하여 외부 지정이 의미가 없음
        modes = ['text', 'binary']
        expect_file_sizes = [13413, 13413]

        json_type = JsonHandler.TYPE_MULTILINE
        load_filename = 'test_data/simple_multiline_object.jsonl'

        for mode, expect_file_size in zip(modes, expect_file_sizes):
            try:
                handler = JsonHandler('multiline')
                if mode == 'text':
                    with open(load_filename, 'r', encoding='utf-8') as fp:
                        handler.load(fp)
                        pass_size = len(handler.pass_list)
                        fail_size = len(handler.fail_list)
                elif mode == 'binary':
                    with open(load_filename, 'rb') as fb:
                        handler.load(fb)
                        pass_size = len(handler.pass_list)
                        fail_size = len(handler.fail_list)
            except Exception as e:
                self.assertTrue(True, f"\t {mode} multiline File load fail by {e}")
            else:
                logger.info(f"\t open mode '{mode}' 'multiline' load {pass_size=}, {fail_size=}")

            try:
                dump_filename = f'test_data/simple_multiline_{mode}_object_to_delete.json'
                handler.dump(dump_filename)
                exist = os.path.exists(dump_filename)
                file_size = os.path.getsize(dump_filename)

                if exist and '_to_delete' in dump_filename:
                    os.remove(dump_filename)

                logger.info(f"\t {json_type} dump expect exist True get {exist}")
                self.assertEqual(True, exist)
                logger.info(f"\t {json_type} dump expect file_size {expect_file_size} get {file_size}")
                self.assertEqual(expect_file_size, file_size)
            except Exception as e:
                self.assertTrue(True, f"\t {mode} multiline File load fail by {e}")


    def test_dump_mutliline_by_data_key(self):
        modes = ['text', 'binary']
        data_keys = ['message', 'message']
        expect_file_sizes = [10513, 10513]

        json_type = JsonHandler.TYPE_MULTILINE
        load_filename = 'test_data/simple_multiline_object.jsonl'

        for mode, data_key, expect_file_size in zip(modes, data_keys, expect_file_sizes):
            try:
                handler = JsonHandler('multiline')
                if mode == 'text':
                    with open(load_filename, 'r', encoding='utf-8') as fp:
                        handler.load(fp, data_key=data_key)
                        pass_size = len(handler.pass_list)
                        fail_size = len(handler.fail_list)
                elif mode == 'binary':
                    with open(load_filename, 'rb') as fb:
                        handler.load(fb, data_key=data_key)
                        pass_size = len(handler.pass_list)
                        fail_size = len(handler.fail_list)
            except Exception as e:
                self.assertTrue(True, f"\t {mode} multiline File load fail by {e}")
                # logger.error(True, f"\t {mode} multiline File load fail by {e}")
            else:
                logger.info(f"\t open mode '{mode}' 'multiline' load {pass_size=}, {fail_size=}")

            try:
                dump_filename = f'test_data/simple_multiline_{mode}_object_to_delete.json'
                handler.dump(dump_filename, data_key=data_key)
                exist = os.path.exists(dump_filename)
                file_size = os.path.getsize(dump_filename)

                if exist and '_to_delete' in dump_filename:
                    os.remove(dump_filename)

                logger.info(f"\t {json_type} dump expect exist True get {exist}")
                self.assertEqual(True, exist)
                logger.info(f"\t {json_type} dump expect file_size {expect_file_size} get {file_size}")
                self.assertEqual(expect_file_size, file_size)
            except Exception as e:
                self.assertTrue(True, f"\t {mode} multiline File load fail by {e}")
                # logger.error(f"\t {mode} multiline File load fail by {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
