import io
import pandas as pd
import pyarrow.feather as feather
from typing import Dict, Literal, Optional, Union

from .fileformat_base import FileformatBase
from .echoss_logger import get_logger, set_logger_level

logger = get_logger('echoss_fileformat')


class FeatherHandler(FileformatBase):
    """Feather file handler

    이미 처리된 결과를 읽고 쓰기 위해서 사용.
    parquet 포맷과 유사하게 사용 
    
    processing_type 'array'는 내부 목록에 dataframe 추가 후 to_pandas 로 최종 dataframe 획득 
    'object' 는 바로 dataframe 객체 리턴
    
    """
    format = "feather"

    def __init__(self, processing_type: str = 'object',
                 encoding='utf-8', error_log='error.log'):
        """Initialize feather file format

        Args:
            processing_type (): Literal['array', 'multiline', 'object']
        """
        super().__init__(processing_type = processing_type, encoding=encoding, error_log=error_log)

    def load(self, file_or_filename: Union[io.TextIOWrapper, io.BytesIO, str], **kwargs) -> Optional[pd.DataFrame]:
        """파일 객체나 파일명에서 feather 데이터 읽기

        Args:
            file_or_filename (): file-like object which has read() method or filename string
        Returns:
            dictionary object if processing_type is 'object', else None

        """
        read_df = None
        open_mode = self._decide_rw_open_mode('load')
        # file_or_filename 클래스 유형에 따라서 처리 방법이 다름
        fp, binary_mode, opened = self._get_file_obj(file_or_filename, open_mode)

        try:
            read_df = feather.read_feather(fp, **kwargs)
        except Exception as e:
            self.fail_list.append(str(fp))
            logger.error(f"{fp=}, {binary_mode=}, {opened=}, {self.processing_type=} load raise: {e}")

        # close opened file if filename
        self._safe_close(fp, opened)

        if self.processing_type == FileformatBase.TYPE_OBJECT:
            return read_df
        else:
            self.pass_list.append(read_df)

    def loads(self, str_or_bytes: Union[str, bytes]) -> Optional[pd.DataFrame]:
        """문자열이나 bytes 에서 feather 객체 읽기

        데이터 처리 결과는 객체 내부에 성공 목록과 실패 목록으로 저장됨

        Args:
            str_or_bytes (str, bytes): text 모드 string 또는 binary 모드 bytes

        Returns:
            dictionary object if processing_type is 'object', else None
        """
        read_df = None
        try:
            if isinstance(str_or_bytes, str):
                file_obj = io.StringIO(str_or_bytes)
                read_df = self.load(file_obj )
            elif isinstance(str_or_bytes, bytes):
                file_obj = io.BytesIO(str_or_bytes)
                read_df = self.load(file_obj )
        except Exception as e:
            self.fail_list.append(str_or_bytes)
            logger.error(f"'{str_or_bytes}' loads raise {e}")
        finally:
            if self.processing_type == FileformatBase.TYPE_OBJECT:
                return read_df

    def to_pandas(self) -> pd.DataFrame:
        """클래스 내부메쏘드 feather 파일 처리 결과를 pd.DataFrame 형태로 받음

        내부적으로 추가할 데이터(pass_list)가 있으면 추가하여 새로운 pd.DataFrame 생성
        실패 목록(fail_list)가 있으면 파일로 저장
        (검토 중) 학습을 위한 dataframe 이기 떄문에 dot('.') 문자로 normalize 된 flatten 컬럼과 값을 가진다.

        Returns: pandas DataFrame
        """
        if self.processing_type == FileformatBase.TYPE_OBJECT:
            logger.error(f"{self.processing_type} not support to_pandas() method")
            return None

        if len(self.pass_list) > 0:
            try:
                # 검토 중. flatten 할 것인가 말 것인가?
                append_df = pd.DataFrame(self.pass_list)
                # append_df = pd.feather_normalize(self.pass_list)
                merge_df = pd.concat([self.data_df, append_df], ignore_index=True)
                self.data_df = merge_df
            except Exception as e:
                logger.error(f"pass_list[{len(self.pass_list)}] to_pandas raise {e}")
                self.fail_list.extend(self.pass_list)
            finally:
                self.pass_list.clear()
        if len(self.fail_list) > 0:
            error_fp = None
            try:
                error_fp = open(self.error_log, mode='ab')
            except Exception as e:
                logger.error(f"fail_list[{len(self.fail_list)}] error log append raise {e}")

            if error_fp:
                for fail in self.fail_list:
                    try:
                        fail_str = None
                        if isinstance(fail, dict):
                            fail_str = feather.dumps(fail, ensure_ascii=False, separators=(',', ':'))
                        elif isinstance(fail, list):
                            fail_str = str(fail)
                        elif not isinstance(fail, str):
                            fail_str = str(fail)

                        if fail_str:
                            fail_bytes = fail_str.encode(self.encoding)
                            error_fp.write(fail_bytes)
                            error_fp.write(b'\n')
                    except Exception as e:
                        logger.exception(e)
                error_fp.close()
                self.fail_list.clear()
        return self.data_df

    def dump(self, file_or_filename: Union[io.TextIOWrapper, io.BytesIO, str], data=None, **kwargs) -> None:
        """데이터를 feather 파일로 쓰기

        파일은 text, binary 모드 파일객체이거나 파일명 문자열
        Args:
            file_or_filename (file, str): 파일객체 또는 파일명, text 모드는 TextIOWrapper, binary 모드는 BytesIO 사용
            data: use this data instead of self.data_df if provide 기능 확장성과 호환성을 위해서 남김
            kwargs : if empty use whole file, else use only key value. for example 'data'

        """
        if self.processing_type == FileformatBase.TYPE_OBJECT:
            if data is None:
                raise TypeError(f"dump() method must have data parameter in {self.processing_type=}")

        fp = None
        mode = ''
        opened = False
        try:
            open_mode = self._decide_rw_open_mode('dump')
            # file_or_filename 클래스 유형에 따라서 처리 방법이 다름
            fp, binary_mode, opened = self._get_file_obj(file_or_filename, open_mode)
            if data is None:
                # dataframe 에 추가할 것 있으면 concat
                data = self.to_pandas()
        except Exception as e:
            self.fail_list.append(data)
            logger.error(f"{fp=}, {binary_mode=}, {opened=}, '{self.processing_type}' dump raise: {e}")

        # 파일로 저장
        try:
            feather.write_feather(data, fp)
        except Exception as e:
            self.fail_list.append(data)
            logger.error(f"{fp=}, {binary_mode=}, {opened=}, '{self.processing_type}' dump raise: {e}")

        self._safe_close(fp, opened)

    def dumps(self, data=None ) -> str:
        """feather 데이터를 문자열 또는 바이너리 형태로 출력

        파일은 text, binary 모드 파일객체이거나 파일명 문자열

        Args:
            data (): 출력할 데이터, 생략되면 self.data_df 사용
            data_key (str): 출력을 feather object 로 한번 더 감쌀 경우에 사용

        Returns:
            데이터를 문자열로 출력
        """
        if self.processing_type == FileformatBase.TYPE_OBJECT:
            if data is None:
                raise TypeError(f"dumps() method must have data parameter if {self.processing_type=}")
        try:
            file_obj = io.BytesIO()
            if file_obj:
                self.dump(file_obj, data=data )
                feather_bytes = file_obj.getvalue()
                return feather_bytes.decode(encoding=self.encoding)
        except Exception as e:
            logger.error(f"{str(self)}  dumps raise: {e}")
        return ""

    """
    클래스 내부 메쏘드 
    """


    def _decide_rw_open_mode(self, method_name) -> str:
        """내부메쏘드 feather_type 과 method_name 에 따라서 파일 일기/쓰기 오픈 모드 결정
        메쏘드에 입력된 매개변수가 filename 이라서 open() 호출 시에 mode 문자열을 결정하기위해서 사용

        Args:
            method_name: 'load' or 'dump'

        Returns: Literal['r', 'w', 'rb', 'wb']
        """
        if 'dump' == method_name:
            return 'wb'
        elif 'load' == method_name:
            return 'rb'
        else:
            raise TypeError(f"method_name='{method_name}'] not supported yet.")
