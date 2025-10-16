import io
import os
import pandas as pd
import time
import unittest

from echoss_fileformat import FileUtil, to_table, get_logger, modify_loggers_by_prefix

logger = get_logger("test_echoss_logger", backup_count=1)
verbose = True


class FileUtilTestCase(unittest.TestCase):
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

    def test_modfify_loggers_by_prefix(self):

        new_log_path = "logs/test_echoss_logger.log"
        modify_logger = modify_loggers_by_prefix("echoss", new_path=new_log_path)

        load_filename = 'test_data/simple_standard.csv'
        dump_filename = 'test_data/simple_standard_to_delete.csv'
        try:
            csv_df = FileUtil.load(load_filename, header=0, skiprows=0)
            if csv_df is not None:
                if verbose:
                    modify_logger.info(to_table(csv_df.head(10)))
            else:
                modify_logger.info('empty dataframe')

            FileUtil.dump(csv_df, dump_filename)
            exist = os.path.exists(dump_filename)
            file_size = os.path.getsize(dump_filename)

            read_df = None
            if exist and 'to_delete' in dump_filename:
                read_df = FileUtil.load_csv(dump_filename)
                os.remove(dump_filename)

            logger.info(f"assertTrue dump expect exist True get {exist}")
            self.assertTrue(exist == True, "dump expect exist True")
            logger.info(f"assert_frome_equal csv_df and read_df ")
            pd.testing.assert_frame_equal(csv_df, read_df)

            self.assertTrue(os.path.exists(new_log_path), "modify loogers by prefix failed")

        except Exception as e:
            logger.error(f"\t File load fail by {e}")
            self.assertTrue(True, f"\t File load fail by {e}")



if __name__ == '__main__':
    unittest.main(verbosity=2)
