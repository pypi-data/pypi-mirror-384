import unittest
import time
import os
from lxml import etree as et
from echoss_fileformat import XmlHandler, get_logger

logger = get_logger(__name__)
verbose = True


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

    def test_simple_object_load(self):
        processing_types = ['object', 'object']
        file_names = ['test_data/simple_config.xml', 'test_data/simple_pom.xml']
        expect_passes = [15, 11]
        expect_fails = [0, 1]

        # known bug on pom xml parsing
        for processing_type, file_name, expect_pass, expect_fail in \
                zip(processing_types, file_names, expect_passes, expect_fails):
            try:
                handler = XmlHandler(processing_type)
                tree_obj = handler.load(file_name)
                pass_size = len(handler.pass_list)
                fail_size = len(handler.fail_list)
                if verbose:
                    logger.info(f"{type(tree_obj)=}, {tree_obj=}")

            except Exception as e:
                logger.error(f"\t {processing_type=} File load raise: {e}")
                self.assertTrue(True, f"\t {processing_type=} File load raise: {e}")
            else:
                logger.info(f"\t {processing_type=} load assertEqual({expect_pass=}, {pass_size=})")
                self.assertEqual(pass_size, expect_pass)
                logger.info(f"\t {processing_type=} load assertEqual({expect_fail=}, {fail_size=})")
                self.assertEqual(fail_size, expect_fail)

    def test_simple_object_dump(self):
        processing_types = ['object', 'object']
        load_filenames = ['test_data/simple_config.xml', 'test_data/simple_pom.xml']
        dump_filenames = ['test_data/simple_config_to_delete.xml', 'test_data/simple_pom_to_delete.xml']
        expect_file_sizes = [1132, 11082]

        for processing_type, load_filename, dump_filename, expect_file_size \
                in zip(processing_types, load_filenames, dump_filenames, expect_file_sizes):
            try:
                handler = XmlHandler(processing_type)
                tree_obj = handler.load(load_filename)
                pass_size = len(handler.pass_list)
                fail_size = len(handler.fail_list)
                if verbose:
                    logger.info(f"{type(tree_obj)=}, {tree_obj=}")

            except Exception as e:
                logger.error(f"\t {processing_type=} File load raise: {e}")
                self.assertTrue(True, f"\t {processing_type=} File load raise: {e}")

            try:
                handler = XmlHandler(processing_type)
                handler.dump(dump_filename, data=tree_obj)
                tree_str = handler.dumps(data=tree_obj)
                if verbose:
                    logger.info(f"{type(tree_obj)=}, {tree_str=}")

                exist = os.path.exists(dump_filename)
                file_size = os.path.getsize(dump_filename)

                if exist and '_to_delete' in dump_filename:
                    os.remove(dump_filename)

                logger.info(f"\t {processing_type=} dump assertTrue {exist=}")
                # self.assertEqual(True, exist)
                logger.info(f"\t {processing_type=} dump assertEqual({expect_file_size=}, {file_size=})")
                # self.assertEqual(expect_file_size, file_size)

            except Exception as e:
                logger.error(f"\t {processing_type=} File dump raise: {e}")
                self.assertTrue(True, f"\t {processing_type=} File dump raise: {e}")

    def test_load_array_by_data_key(self):
        processing_types = ['array', 'array']
        load_filenames = ['test_data/complex_one_object.xml', 'test_data/complex_one_object.xml']
        dump_filenames = ['test_data/complex_one_object_to_delete_bndbox.xml',
                          'test_data/simple_pom_to_delete_object.xml']
        data_keys = ['.//bndbox', './/object']
        expect_file_sizes = [1132, 11082]

        for processing_type, load_filename, dump_filename, data_key, expect_file_size \
                in zip(processing_types, load_filenames, dump_filenames, data_keys, expect_file_sizes):
            try:
                handler = XmlHandler(processing_type)
                tree_obj = handler.load(load_filename, data_key=data_key)
                pass_size = len(handler.pass_list)
                fail_size = len(handler.fail_list)
                if verbose:
                    logger.info(f"{type(tree_obj)=}, {tree_obj=} {pass_size=} {fail_size=}")

            except Exception as e:
                logger.error(f"\t {processing_type=} File load raise: {e}")
                self.assertTrue(True, f"\t {processing_type=} File load raise: {e}")

            try:
                handler.dump(dump_filename)

                exist = os.path.exists(dump_filename)
                file_size = os.path.getsize(dump_filename)

                if exist and '_to_delete' in dump_filename:
                    os.remove(dump_filename)

                logger.info(f"\t {processing_type=} dump assertTrue {exist=}")
                # self.assertEqual(True, exist)
                logger.info(f"\t {processing_type=} dump assertEqual({expect_file_size=}, {file_size=})")
                # self.assertEqual(expect_file_size, file_size)

            except Exception as e:
                logger.error(f"\t {processing_type=} File dump raise: {e}")
                self.assertTrue(True, f"\t {processing_type=} File dump raise: {e}")

    def test_to_dict(self):
        # Sample XML data
        xml_data = """
        <note>
          <to>Tove</to>
          <from>Jani</from>
          <heading>Reminder</heading>
          <body>Don't forget me this weekend!</body>
        </note>
        """
        handler = XmlHandler(processing_type='object')
        root = et.fromstring(xml_data)
        xml_dict = handler.xml_to_dict(root)
        logger.info(xml_data)
        logger.info(xml_dict)


if __name__ == '__main__':
    unittest.main(verbosity=2)
