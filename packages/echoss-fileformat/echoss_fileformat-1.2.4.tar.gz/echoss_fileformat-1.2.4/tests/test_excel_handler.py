import unittest
import time
import os
import sys
import pandas as pd

from echoss_fileformat import ExcelHandler
from echoss_fileformat import get_logger, to_table

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

    def test_object_type(self):
        """메타데이터의 목적으로 파일 그대로 읽어주는 'object' 방식의 기능 테스트
        """
        expect_shape = (101, 8)
        load_filename = 'test_data/multiheader_table.xlsx'
        dump_filename = 'test_data/multiheader_table_to_delete_object.xlsx'
        load_shape = None,
        dump_shape = None,
        load_columns = []
        dump_columns = []
        try:
            handler = ExcelHandler(processing_type='object')
            df = handler.load(load_filename, header=[3,4])

            # t_pandas() 사용하지 않음
            if df is not None:
                if verbose:
                    logger.info(to_table(df))
                load_columns = list(df.columns)
                load_shape = df.shape
                logger.info(f"\t expect dataframe shape={expect_shape} and get {load_shape}")
                # self.assertEqual(load_shape, expect_shape)
            else:
                logger.info('\t empty dataframe')

            handler.dump(dump_filename, sheet_name="오브젝트", data=df)
            exist = os.path.exists(dump_filename)

            if exist:
                check_handler = ExcelHandler(processing_type='object')
                check_df = check_handler.load(dump_filename, header=[0,1])
                # check_df = check_handler.to_pandas()
                dump_columns = list(check_df.columns)
                dump_shape = check_df.shape
            if exist and 'to_delete' in dump_filename:
                os.remove(dump_filename)

        except Exception as e:
            logger.error(f"\t File load fail by {e}")
            # self.assertTrue(True, f"\t File load fail by {e}")
        else:
            logger.info(f"\t assert not equal {load_shape=} and {dump_shape}")
            self.assertNotEqual(load_shape,  dump_shape)
            logger.info(f"\t assert list equal {load_columns=}, {dump_columns[1:]=}")
            self.assertListEqual(load_columns, dump_columns[1:])

    def test_basic_excel(self):
        expect_pass = 1
        expect_fail = 0
        load_filename = 'test_data/simple_table.xlsx'
        expect_len = 100
        dump_filename = 'test_data/simple_table_to_delete.xlsx'
        try:
            handler = ExcelHandler()
            handler.load(load_filename)
            pass_size = len(handler.pass_list)
            fail_size = len(handler.fail_list)
            df = handler.to_pandas()
            if df is not None:
                if verbose:
                    logger.info(to_table(df))
                load_columns = list(df.columns)
                load_len = len(df)
                logger.info(f"\t expect dataframe len={expect_len} and get {len(df)}")
                self.assertEqual(load_len, expect_len)
            else:
                logger.info('\t empty dataframe')

            handler.dump(dump_filename)
            exist = os.path.exists(dump_filename)

            if exist:
                check_handler = ExcelHandler()
                check_handler.load(dump_filename)
                check_df = check_handler.to_pandas()
                dump_columns = list(check_df.columns)
                dump_len = len(check_df)
            if exist and 'to_delete' in dump_filename:
                os.remove(dump_filename)

        except Exception as e:
            logger.error(f"\t File load fail by {e}")
            # self.assertTrue(True, f"\t File load fail by {e}")
        else:
            logger.info(f"\t load df len={load_len}, dump df len={dump_len}")
            self.assertEqual(load_len,  dump_len)
            logger.info(f"\t load columns len={len(load_columns)}, dump columns len={len(dump_columns)}")
            self.assertListEqual(load_columns, dump_columns)

    def test_with_options(self):
        expect_shape = (20, 3)

        load_filename = 'test_data/채널지수평가 샘플_v0.1.xlsx'
        dump_filename = 'test_data/채널지수평가 샘플_v0.1_to_delete.xlsx'
        try:
            handler = ExcelHandler()
            handler.load(load_filename, sheet_name='Youtube생산성', skiprows=1, header=0, nrows=20, usecols='B:D')
            df = handler.to_pandas()
            if df is not None:
                if verbose:
                    print(to_table(df))
                load_columns = list(df.columns)
                load_shape = df.shape
                logger.info(f"expect dataframe shape={expect_shape} and get {load_shape}")
                self.assertEqual(expect_shape, load_shape)
            else:
                logger.error('empty dataframe')

            handler.dump(dump_filename)
            exist = os.path.exists(dump_filename)

            if exist:
                check_handler = ExcelHandler()
                check_handler.load(dump_filename)
                check_df = check_handler.to_pandas()
                dump_columns = list(check_df.columns)
                dump_shape = check_df.shape
            if exist and 'to_delete' in dump_filename:
                os.remove(dump_filename)

        except Exception as e:
            logger.error(f"\t File load fail by {e}")
            # self.assertTrue(True, f"\t File load fail by {e}")
        else:
            logger.info(f"\t assert load df {load_shape=}, dump df {dump_shape=} is same?")
            self.assertEqual(load_shape,  dump_shape)
            logger.info(f"\t assert load columns {load_columns}, dump columns {dump_columns} is same?")
            self.assertListEqual(load_columns, dump_columns)

    def test_multi_header_load_skiprows(self):
        expect_shape = (50, 8)
        test_skiprows = [0,    3,      [0, 1, 2], [0, 1, 2]]
        test_header = [[3, 4], [0, 1], [3, 4],    [0, 1]]
        expect_success = [True, True, False, True]
        expect_columns = [('수집항목', '개체번호'), ('과폭', 'cm'), ('과고', 'cm'), ('과중', 'g'), ('당도', 'Brix %'), ('산도', '0-14'), ('경도', 'kgf'), ('수분율', '%')]
        load_filename = 'test_data/multiheader_table.xlsx'
        try:
            for skiprows, header, succeed in zip(test_skiprows, test_header, expect_success):
                handler = ExcelHandler()
                logger.info(f"\ttry load sheet_name='50주차', skiprows={skiprows}, header={header}, nrows=50")
                handler.load(load_filename, sheet_name='50주차', skiprows=skiprows, header=header, nrows=50)
                df = handler.to_pandas()
                if df is not None:

                    load_columns = list(df.columns)
                    load_shape = df.shape

                    logger.debug(f"load df columns={load_columns}")
                    if verbose:
                        logger.info(to_table(df))
                    logger.debug(f"expect dataframe shape={expect_shape} and get {load_shape}")

                    is_same_df = expect_shape == load_shape and expect_columns == load_columns
                    logger.info(f"\t\tassert is_same_df={succeed} and get {is_same_df}")

                    self.assertEqual(succeed, is_same_df)
                    pass
                else:
                    logger.error('empty dataframe')

        except Exception as e:
            logger.error(f"\t File load fail : {e}")
            logger.debug(f"{skiprows=}, {header=},  {succeed=} ")
            # self.assertTrue(True, f"\t File load fail by {e}")

    def test_multi_header_3(self):
        expect_shape = (100, 8)

        load_filename = 'test_data/multiheader_table.xlsx'
        dump_filename = 'test_data/multiheader_table_to_delete.xlsx'
        try:
            handler = ExcelHandler()
            handler.load(load_filename, sheet_name='50주차', skiprows=0, header=[3, 4], nrows=100)

            df = handler.to_pandas()
            if df is not None:
                if verbose:
                    print(to_table(df))
                load_columns = list(df.columns)

                load_shape = df.shape
                logger.info(f"expect dataframe shape={expect_shape} and get {load_shape}")
                self.assertEqual(expect_shape, load_shape)
            else:
                logger.error('empty dataframe')

            handler.dump(dump_filename, sheet_name="학습데이터")
            exist = os.path.exists(dump_filename)

            if exist:
                check_handler = ExcelHandler()
                # sheet_name='50주차', skiprows=1, , nrows=100
                # 멀티 헤더 문제 때문에 빈칸이 하나더 추가되어 nrows 를 설정하면 +1을 해야함
                # check_handler.load(dump_filename, skiprows=0, header=[0, 1], nrows=101)
                check_handler.load(dump_filename, skiprows=0, header=[0, 1])
                check_df = check_handler.to_pandas()
                dump_columns = list(check_df.columns)
                dump_shape = check_df.shape
            if exist and 'to_delete' in dump_filename:
                os.remove(dump_filename)

        except Exception as e:
            logger.error(f"\t File load fail by {e}")
            # self.assertTrue(True, f"\t File load fail by {e}")
        else:
            logger.info(f"\t assert load df {load_shape=}, {dump_shape=} is equal")
            self.assertEqual(load_shape,  dump_shape)
            logger.info(f"\t assert load {load_columns=}, {dump_columns=} is list equal")
            self.assertListEqual(load_columns, dump_columns)


if __name__ == '__main__':
    unittest.main(verbosity=2)
