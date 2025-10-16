import io
import pandas as pd
from typing import Union, Literal, Optional

from .fileformat_base import FileformatBase
from .echoss_logger import get_logger, set_logger_level

logger = get_logger('echoss_fileformat')


class CsvHandler(FileformatBase):
    """CSV file handler

    학습데이터로 CSV 파일은 전체 읽기를 기본으로 해서
    해더와 사용 컬럼 지정을 제공한다
    """
    format = "csv"

    def __init__(self, processing_type='array', encoding='utf-8', error_log='error.log',
                 delimiter=',', quotechar='"', quoting=0, escapechar='\\'):
        """CSV 파일 핸들러 초기화 메쏘드

        학습데이터는 processing_type='array' 사용. 누적 후 to_pandas()로 최종 dataframe 획득

        'object' 는 전체를 읽어서 바로 dataframe 으로 리턴하는 방식

        Args:
            processing_type (): Literal['array', 'object']
            encoding: 파일 인코팅
            error_log: 파일 처리 실패 시 에러 저장 파일명
            delimiter: 컬럼 구분자 (실제 구현 함수에서는 sep 으로 변경. 추후 변경 가능성)
            quotechar: 인용 문자
            quoting (int): 인용문자 사용빈도에 정책,  0: QUOTE_MINIMAL, 1: QUOTE_ALL, 2: QUOTE_NONNUMERIC, 3: QUOTE_NONE
            escapechar: 예외처리 문자
        """
        super().__init__(processing_type=processing_type, encoding=encoding, error_log=error_log)
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.quoting = quoting
        self.escapechar = escapechar

    def load(self, file_or_filename: Union[io.TextIOWrapper, io.BytesIO, io.BufferedIOBase, str],
             header: Union[int, list] = 0, skiprows: int = 0, nrows: int = None, usecols=None, **kwargs) -> Optional[pd.DataFrame]:
        """CSV 파일 읽기

            CSV 파일을 읽고 dataframe 으로 처리함

        Args:
            file_or_filename (file-like object): file object or file name
            header (Union[int, list]): 헤더로 사용될 row index, 멀티헤더인 경우에는 [1, 2, 3] 형태로 사용
            skiprows (int) : 데이터를 읽기 위해서 스킵할 row 숫자 지정. (header 로 부터 스킵 숫자)
            nrows (int): skiprows 부터 N개의 데이터 row 건수만 읽을 경우 지정
            usecols (Union[int, list]): 전체 컬럼 사용시 None, 컬럼 번호나 이름의 리스트 [0, 1, 2] or ['foo', 'bar', 'baz']
            **kwargs : 추가 키워드 옵션
        """
        fp = None
        opened = None
        try:
            # file_or_filename 객체가 지원되는 file-like object 또는 filename string 인지 검사
            open_mode = self._decide_rw_open_mode('load')
            fp, binary_mode, opened = self._get_file_obj(file_or_filename, open_mode)

            # kwargs pop ?
            kw_encoding = kwargs.pop('encoding', self.encoding)
            kw_sep = kwargs.pop('sep', self.delimiter)
            kw_quotechar = kwargs.pop('quotechar', self.quotechar)
            kw_escapechar = kwargs.pop('escapechar', self.escapechar)
            kw_infer_datetime_format = kwargs.pop('infer_datetime_format', True)
            kw_on_bad_lines = kwargs.pop('on_bad_lines', 'warn')

            # noinspection PyTypeChecker
            df = pd.read_csv(
                fp,
                encoding=kw_encoding,
                sep=kw_sep,
                quotechar=kw_quotechar,
                escapechar=kw_escapechar,
                header=header,
                skiprows=skiprows,
                nrows=nrows,
                usecols=usecols,
                on_bad_lines=kw_on_bad_lines,
                **kwargs
            )

            if self.processing_type == FileformatBase.TYPE_OBJECT:
                return df
            else:
                self.pass_list.append(df)
        except Exception as e:
            self.fail_list.append(str(file_or_filename))
            logger.error(f"{file_or_filename} load raise: {e}")
        finally:
            self._safe_close(fp, opened)


    def loads(self, str_or_bytes: Union[str, bytes],
              header=0, skiprows=0, nrows=None, usecols=None) -> pd.DataFrame:
        """문자열이나 bytes 에서 CSV 읽기

        Args:
            str_or_bytes (str, bytes): text 모드 string 또는 binary 모드 bytes
            header (Union[int, list]): 헤더로 사용될 1부터 시작되는 row index, 멀티헤더인 경우에는 [1, 2, 3] 형태로 사용
            skiprows (int) : 데이터가 시작되는 row index 지정
            nrows (int): skiprows 부터 N개의 데이터 row 만 읽을 경우 숮자 지정
            usecols (Union[int, list]): 전체 컬럼 사용시 None, 컬럼 번호나 이름의 리스트 [0, 1, 2] or ['foo', 'bar', 'baz']
        """
        file_obj = None
        try:
            if isinstance(str_or_bytes, str):
                file_obj = io.StringIO(str_or_bytes)
            elif isinstance(str_or_bytes, bytes):
                file_obj = io.BytesIO(str_or_bytes)

            if file_obj:
                df = self.load(file_obj, header=header, skiprows=skiprows, nrows=nrows, usecols=usecols)
                if self.processing_type == FileformatBase.TYPE_OBJECT:
                    return df
        except Exception as e:
            self.fail_list.append(str_or_bytes)
            logger.error(f"'{str_or_bytes}' loads raise {e}")

    def to_pandas(self) -> pd.DataFrame:
        """클래스 내부메쏘드 CSV 파일 처리 결과를 pd.DataFrame 형태로 pass_list 에 저장

        내부적으로 추가할 데이터(pass_list)가 있으면 모두 통합하여 새로운 dataframe 을 생성함
        실패 목록(fail_list)가 있으면 파일로 저장
        학습을 위한 dataframe 이기 떄문에 dot('.') 문자로 normalize 된 flatten 컬럼과 값을 가진다.

        Returns: pandas DataFrame
        """
        if self.processing_type == CsvHandler.TYPE_OBJECT:
            logger.error(f"{self.processing_type} not support to_pandas() method")
            raise TypeError(f"processing_type '{self.processing_type}' support to_pandas() method")

        if len(self.pass_list) > 0:
            try:
                if len(self.data_df) > 0:
                    df_list = [self.data_df].extend(self.pass_list)
                else:
                    df_list = self.pass_list
                merge_df = pd.concat(df_list, ignore_index=True)
                self.data_df = merge_df
            except Exception as e:
                logger.error(f"pass_list[{len(self.pass_list)}] to_pandas raise: {e}")
                self.fail_list.extend(self.pass_list)
            finally:
                self.pass_list.clear()

        if len(self.fail_list) > 0:
            error_fp = None
            try:
                error_fp = open(self.error_log, mode='ab')
            except Exception as e:
                logger.error(f"fail_list[{len(self.fail_list)}] error log append raise: {e}")

            if error_fp:
                for fail in self.fail_list:
                    try:
                        if not isinstance(fail, str):
                            fail_str = str(fail)
                        else:
                            fail_str = fail
                        fail_bytes = fail_str.encode(self.encoding)
                        error_fp.write(fail_bytes)
                        error_fp.write(b'\n')
                    except Exception as e:
                        logger.exception(e)
                error_fp.close()
                self.fail_list.clear()
        return self.data_df

    def dump(self, file_or_filename, data: pd.DataFrame = None, **kwargs):
        """데이터를 CSV 파일로 쓰기

        파일은 text, binary 모드 파일객체이거나 파일명 문자열
        Args:
            file_or_filename (file, str): 파일객체 또는 파일명
            data: dataframe 으로 설정시 사용. 기존 유틸리티의 호환성을 위해서 남김
            kwargs : optional key value args
        """
        open_mode = self._decide_rw_open_mode('dump')
        fp, binary_mode, opened = self._get_file_obj(file_or_filename, open_mode)

        try:
            if data is None:
                df = self.to_pandas()
            else:
                df = data

                # kwargs pop ?
            kw_encoding = kwargs.pop('encoding', self.encoding)
            kw_sep = kwargs.pop('sep', self.delimiter)
            kw_quotechar = kwargs.pop('quotechar', self.quotechar)
            kw_escapechar = kwargs.pop('escapechar', self.escapechar)
            kw_quoting = kwargs.pop('quoting', self.quoting)
            kw_index = kwargs.pop('index', False)
            df.to_csv(
                fp,
                encoding=kw_encoding,
                sep=kw_sep,
                quotechar=kw_quotechar,
                escapechar=kw_escapechar,
                quoting=kw_quoting,
                index=kw_index
            )
        except Exception as e:
            self.fail_list.append(str(file_or_filename))
            logger.error(f"{file_or_filename} load raise: {e}")
        finally:
            self._safe_close(fp, opened)

    def dumps(self, data: pd.DataFrame = None) -> str:
        """데이터를 CSV 파일로 쓰기

        파일은 text, binary 모드 파일객체이거나 파일명 문자열
        Args:
            data: 내장 dataframe 대신 사용할 data. 기능 확장성과 호환성을 위해서 남김
        Returns:
            없음
        """
        file_obj = io.StringIO()

        try:
            self.dump(file_obj, data=data)
        except Exception as e:
            logger.error(f"{self.processing_type=} dumps raise {e}")
        return file_obj.getvalue()

    """
    클래스 내부 메쏘드   
    """

    def _check_file_or_filename(self, file_or_filename):
        """파일 변수의 유형 체크
        Args:
            file_or_filename: file object or file name

        Returns: (fp, mode)
            fp : file obj if exist, or None
            mode : Union['binary', 'text', 'str']
        """
        if isinstance(file_or_filename, io.TextIOWrapper):
            mode = 'text'
        # AWS s3 use io.BytesIO
        elif isinstance(file_or_filename, io.BytesIO):
            mode = 'binary'
        # open 'rb' use io.BufferedIOBase (BufferedReader or BufferedWriter)
        elif isinstance(file_or_filename, (io.BufferedReader, io.BufferedWriter)):
            if isinstance(file_or_filename, io.BufferedReader):
                fp: io.BufferedReader = file_or_filename
            else:
                fp: io.BufferedWriter = file_or_filename
            if 'b' in fp.mode:
                mode = 'binary'
            else:
                mode = 'text'
        elif isinstance(file_or_filename, str):
            mode = 'str'
        # elif isinstance(file_or_filename, Path)  # 향후 pathlib.Path 객체 사용 검토
        else:
            raise TypeError(f"'{self.processing_type}' {file_or_filename} is not file-like obj")
        return mode
