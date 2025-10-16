import unittest
import time
import os
import pandas as pd

from echoss_fileformat import CsvHandler
from echoss_fileformat import echoss_logger, to_table, LOG_FORMAT_DETAIL

logger = echoss_logger.get_logger("test_csv_handler", backup_count=1, logger_format=LOG_FORMAT_DETAIL)
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

    def test_load_simple_standard_csv(self):
        expect_pass = 1
        expect_fail = 0
        load_filename = 'test_data/simple_standard.csv'
        dump_filename = 'test_data/simple_standard_to_delete.csv'
        try:
            handler = CsvHandler()
            handler.load(load_filename, header=0, skiprows=0)
            pass_size = len(handler.pass_list)
            fail_size = len(handler.fail_list)
            csv_df = handler.to_pandas()
            if csv_df is not None:
                if verbose:
                    logger.info(to_table(csv_df))
            else:
                logger.info('empty dataframe')
            expect_csv_str = "SEQ_NO,PROMTN_TY_CD,PROMTN_TY_NM,BRAND_NM,SVC_NM,ISSU_CO,PARTCPTN_CO,PSNBY_ISSU_CO,COUPON_CRTFC_CO,COUPON_USE_RT\r\n"+"0,9,대만프로모션발급인증통계,77chocolate,S0013,15,15,1.0,15,1.0"
            csv_str = handler.dumps()
            # logger.info("[\n"+csv_str+"]")
            expect_file_size = 17827
            self.assertTrue(csv_str.startswith(expect_csv_str), "startswith fail")

            handler.dump(dump_filename)
            exist = os.path.exists(dump_filename)
            file_size = os.path.getsize(dump_filename)
            if exist and 'to_delete' in dump_filename:
                os.remove(dump_filename)

            logger.info(f"\t {handler} dump expect exist True get {exist}")
            logger.info(f"\t {handler} dump expect file_size {expect_file_size} get {file_size}")

        except Exception as e:
            logger.error(f"\t File load fail by {e}")
            self.assertTrue(True, f"\t File load fail by {e}")
        else:
            logger.info(f"\t load expect pass {expect_pass} get {pass_size}")
            self.assertTrue(pass_size == expect_pass)
            logger.info(f"\t load expect fail {expect_fail} get {fail_size}")
            self.assertTrue(fail_size == expect_fail)

    def test_load_simple_standard_csv_by_mode(self):
        modes = ['text', 'binary']
        expect_shape = (212, 10)

        load_filename = 'test_data/simple_standard.csv'
        dump_filename = 'test_data/simple_standard_to_delete.csv'
        file_obj = None
        handler = CsvHandler()

        for given_mode in modes:
            expect_pass = 1
            expect_fail = 0
            try:
                if 'text' == given_mode:
                    file_obj = open(load_filename, 'r', encoding='utf-8')
                else:
                    file_obj = open(load_filename, 'rb')
                handler.load(file_obj, header=0, skiprows=0)

                csv_df = handler.to_pandas()
                if csv_df is not None and len(csv_df) > 0:
                    df_shape = csv_df.shape
                    if expect_shape == df_shape:
                        logger.info(f"load mode={given_mode}, shape={csv_df.shape} are equal")
                    else:
                        logger.error(f"load mode={expect_shape}, and get shape={csv_df.shape}")
                else:
                    logger.error('empty dataframe')
            except Exception as e:
                logger.error(f"\t File load fail by {e}")
                self.assertTrue(True, f"\t File load fail by {e}")
            finally:
                if file_obj:
                    file_obj.close()
                    file_obj = None

            try:
                if 'text' == given_mode:
                    file_obj = open(dump_filename, 'w', encoding='utf-8')
                else:
                    file_obj = open(dump_filename, 'wb')
                handler.dump(file_obj, quoting=0)
                if file_obj:
                    file_obj.close()
                    file_obj = None

                check_csv = CsvHandler()
                check_csv.load(dump_filename)

                check_df = check_csv.to_pandas()
                if check_df is not None and len(check_df) > 0:
                    df_shape = check_df.shape
                    if expect_shape == df_shape:
                        logger.info(f"dump mode={given_mode}, shape={check_df.shape} are equal")
                    else:
                        logger.error(f"dump mode={given_mode}, {expect_shape=} and get shape={check_df.shape}")
                else:
                    logger.error('dump and load make empty dataframe')

                if 'to_delete' in dump_filename:
                    os.remove(dump_filename)

            except Exception as e:
                logger.error(f"\t File dump open mode={given_mode} fail by {e}")
                self.assertTrue(True, f"\t File dump fail by {e}")
            finally:
                if file_obj:
                    file_obj.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
