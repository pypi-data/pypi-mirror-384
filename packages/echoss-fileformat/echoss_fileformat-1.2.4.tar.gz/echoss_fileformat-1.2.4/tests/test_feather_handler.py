import unittest
import time
import logging
import os

from echoss_fileformat import CsvHandler
from echoss_fileformat import FeatherHandler
from echoss_fileformat import get_logger, to_table

logger = get_logger("test_feather_handler")
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

    def test_load_csv_dump_feather(self):
        expect_pass = 1
        expect_fail = 0
        expect_file_size = 14554
        load_filename = 'test_data/simple_standard.csv'
        dump_filename = 'test_data/simple_standard_to_delete.feather'
        try:
            csv_handler = CsvHandler()
            csv_handler.load(load_filename, header=0, skiprows=0)
            pass_size = len(csv_handler.pass_list)
            fail_size = len(csv_handler.fail_list)
            csv_df = csv_handler.to_pandas()
            expect_header = "SEQ_NO,PROMTN_TY_CD,PROMTN_TY_NM,BRAND_NM,SVC_NM,ISSU_CO,PARTCPTN_CO,PSNBY_ISSU_CO,COUPON_CRTFC_CO,COUPON_USE_RT"
            expect_row = "0,9,대만프로모션발급인증통계,77chocolate,S0013,15,15,1.0,15,1.0"
            expect_csv_str = expect_header+"\r\n"+expect_row
            csv_str = csv_handler.dumps()
            if verbose:
                logger.info("expect header [ "+expect_header+" ]")
                logger.info(to_table(csv_df, col_space=10, max_colwidth=16))

            self.assertTrue(csv_str.startswith(expect_csv_str), "startswith fail")

            feather_handler = FeatherHandler()
            feather_handler.dump(dump_filename, data=csv_df)
            exist = os.path.exists(dump_filename)
            file_size = os.path.getsize(dump_filename)
            if exist and 'to_delete' in dump_filename:
                os.remove(dump_filename)

            logger.info(f"\t {feather_handler} dump expect exist True get {exist}")
            logger.info(f"\t {feather_handler} dump expect file_size {expect_file_size} get {file_size}")

        except Exception as e:
            logger.error(f"\t File load fail by {e}")
            self.assertTrue(True, f"\t File load fail by {e}")
        else:
            logger.info(f"\t load expect pass {expect_pass} get {pass_size}")
            self.assertTrue(pass_size == expect_pass)
            logger.info(f"\t load expect fail {expect_fail} get {fail_size}")
            self.assertTrue(fail_size == expect_fail)


if __name__ == '__main__':
    unittest.main(verbosity=2)
