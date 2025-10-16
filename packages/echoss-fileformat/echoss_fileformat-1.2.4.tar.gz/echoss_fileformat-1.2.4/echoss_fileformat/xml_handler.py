import io
import json
import pandas as pd
from typing import Dict, Literal, Optional, Union, List
from lxml import etree as et

from .fileformat_base import FileformatBase
from .echoss_logger import get_logger, set_logger_level

logger = get_logger('echoss_fileformat')


class XmlHandler(FileformatBase):
    """XML file handler

    XML 은 json_type 과 같은 구분이 없이 전체 파일을 하나의 tree로 처리함
    ('multiline' 형태는 지원하지 않음)

    'array' 유형은 전체 XML 읽기 후 트리구조를 따라가면서 dictionary 로 만들어서 처리함
    특정 키만 학습데이터로 사용할 경우에는 data_key 로 키를 지정하여 처리되는 값을 지정

    'object' 는 학습 데이터가 아니라 메타 정보를 읽기 위해서 사용. dataframe 으로 바꾸지 않고 그대로 사욤
    """
    format = "xml"

    def __init__(self, processing_type: str = 'array',
                 encoding='utf-8', error_log='error.log'):
        """Initialize XML file format

        Args:
            processing_type (): Literal['array', 'object'] XML 은 'multiline' 지원 안함
        """
        super().__init__(processing_type=processing_type, encoding=encoding, error_log=error_log)

        # load 시에 root 기억
        self.root = None

        # root 노드의 tag 는 필수 이므로 기본값을 'data' 로 설정. top level 노드의 tag 값도 필수 'row' 기본값
        self.root_tag = 'data'
        self.child_tag = 'row'

    def load(self, file_or_filename: Union[io.TextIOWrapper, io.BytesIO, io.BufferedIOBase, str],
             data_key: str = None, usecols: list = None):
        """파일 객체나 파일명에서 JSON 데이터 읽기

        Args:
            file_or_filename (file-like object): file or s3 stream object which support .read() function
            data_key (str): if empty use whole file, else use only key value. for example 'data'
            usecols (list]): 전체 키 사용시 None, 이름의 리스트 ['foo', 'bar', 'baz'] 처럼 사용

        Returns:
            list of json object, which passing load json processing till now
        """
        fp = None,
        opened = False
        try:
            open_mode = self._decide_rw_open_mode('load')

            # file_or_filename 클래스 유형에 따라서 처리 방법이 다른 것을 일원화
            fp, binary_mode, opened = self._get_file_obj(file_or_filename, open_mode)

            # 전체 파일을 일고 나머지 처리
            tree = et.parse(fp)
            root = tree.getroot()

            # # root 노드의 namespace 처리 -> lxml 에서는 라이브러리가 처리해줌
            # tag_splits = root.tag.split('}')
            # if len(tag_splits) >= 1:
            #     namespace = tag_splits[0][1:]
            #     # generate namespace mapping
            #     ns_map = {prefix: uri for prefix, uri in root.nsmap.items() if prefix is not None}
            #     # Add default namespace to the mapping
            #     ns_map[''] = namespace
            #
            # # Register the namespace mapping
            # for prefix, uri in ns_map.items():
            #     ET.register_namespace(prefix, uri)
            # tree.ET.parse(fp)
            # root = tree.getroot()

            # root 기억
            self.root = root
            self.root_tag = root.tag
        except Exception as e:
            self.fail_list.append(str(file_or_filename))
            logger.error(f"'{file_or_filename}' load raise: {e}")
            raise e
        finally:
            self._safe_close(fp, opened)

        # 'array' 처리 유형의 파일 처리
        # 'array' 모드에서는 tag 의 attrib 는 처리하지 않고, text 만 사용함
        # 즉, <temperature>17.6</temperature> 형태를 'temperature': 17.6 으로 처리함
        try:
            # data_key 과 usecols 확인
            if data_key is None:
                data_nodes = [root]
            else:
                # self.child_tag = data_key.split('/')[-1]
                data_nodes = tree.findall(data_key, namespaces=root.nsmap)
        except Exception as e:
            self.fail_list.append(str(file_or_filename))
            logger.error(f"'{file_or_filename}' load raise: {e}")
            raise e

        for child in data_nodes:
            try:
                node_dict = {}
                self._add_all_child_text(child, node_dict, usecols=usecols)
                self.pass_list.append(node_dict)
                self.child_tag = child.tag
            except Exception as e:
                self.fail_list.append(str(child))
                logger.error(f"'{file_or_filename}' load raise {e}")

        # 'object' 처리 유형의 파일 처리는 루트 트리를 바로 리턴
        if self.processing_type == FileformatBase.TYPE_OBJECT:
            return data_nodes
        else:
            return None


    def loads(self, str_or_bytes: Union[str, bytes],
              data_key: str = None, usecols: list = None) -> Optional[et.Element]:
        """문자열이나 bytes 에서 XML 객체 읽기

        데이터 처리 결과는 객체 내부에 성공 목록과 실패 목록으로 저장됨

        Args:
            str_or_bytes (str, bytes): text 모드 string 또는 binary 모드 bytes
            data_key (str): if empty use whole file, else use only key value. for example 'data'
            usecols (list]): 전체 키 사용시 None, 이름의 리스트 ['foo', 'bar', 'baz'] 처럼 사용
        """
        root = None
        try:
            if isinstance(str_or_bytes, str):
                file_obj = io.StringIO(str_or_bytes)
                root = self.load(file_obj, data_key=data_key, usecols=usecols)
            elif isinstance(str_or_bytes, bytes):
                file_obj = io.BytesIO(str_or_bytes)
                root = self.load(file_obj, data_key=data_key, usecols=usecols)
        except Exception as e:
            self.fail_list.append(str_or_bytes)
            logger.error(f"'{str_or_bytes}' loads raise {e}")

        # 'object' 처리 유형의 파일 처리는 루트 트리를 바로 리턴
        if self.processing_type == FileformatBase.TYPE_OBJECT:
            return root

    def to_pandas(self) -> pd.DataFrame:
        """클래스 내부메쏘드 JSON 파일 처리 결과를 pd.DataFrame 형태로 받음

        내부적으로 추가할 데이터(pass_list)가 있으면 추가하여 새로운 pd.DataFrame 생성
        실패 목록(fail_list)가 있으면 파일로 저장
        학습을 위한 dataframe 이기 떄문에 dot('.') 문자로 normalize 된 flatten 컬럼과 값을 가진다.

        Returns: pandas DataFrame
        """
        if self.processing_type == FileformatBase.TYPE_OBJECT:
            logger.error(f"{self.processing_type} not support to_pandas() method")
            raise TypeError(f"processing_type '{self.processing_type}' support to_pandas() method")

        if len(self.pass_list) > 0:
            try:
                append_df = pd.DataFrame(self.pass_list)
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
                            fail_str = json.dumps(fail, ensure_ascii=False, separators=(',', ':'))
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

    def dump(self, file_or_filename: Union[io.TextIOWrapper, io.BytesIO, str],
             data=None, root_tag=None, child_tag=None) -> None:
        """데이터를 JSON 파일로 쓰기

        파일은 text, binary 모드 파일객체이거나 파일명 문자열
        Args:
            file_or_filename (file, str): 파일객체 또는 파일명, text 모드는 TextIOWrapper, binary 모드는 BytesIO 사용
            data: use this data instead of self.data_df if provide 기능 확장성과 호환성을 위해서 남김
            root_tag (str): XML 파일은 전체를 묶을 루트 노드가 필요. 지정하지 않으면 이전 load()에서 얻은 값이나 초기값 'data' 사용
            child_tag (str): 루트 노드 아래 자식노드도 이름 필요. 지정하지 않으면 이전 load()에서 얻은 값이나 초기값 'row' 사용
        Returns:
            없음
        """
        if self.processing_type == FileformatBase.TYPE_OBJECT:
            if data is None:
                raise TypeError(f"'{self.processing_type=}' dump() must have data parameter")
            # elif not (isinstance(data, type(ET._Element)) or (root_tag and child_tag)):
            #     raise TypeError(f"'{self.processing_type=}' dump() must have root_tag and child_tag by type(Element)")

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
            logger.error(f"{fp=}, {binary_mode=}, {opened=}, {self.processing_type=} dump raise: {e}")

        if not root_tag:
            root_tag = self.root_tag
        if not child_tag:
            child_tag = self.child_tag

        try:
            # 'object' 에서만 사용
            if isinstance(data, et._ElementTree):
                data.write(fp, encoding='utf-8', xml_declaration=True)
            # 'object' 에서만 사용
            elif isinstance(data, et._Element):
                tree = et.ElementTree(data)
                tree.write(fp, encoding='utf-8', xml_declaration=True)
            # dataframe -> xml
            elif isinstance(data, pd.DataFrame):
                df: pd.DataFrame = data
                # dataframe 에서 직접 XML 생성
                new_root = et.Element(self.root.tag, attrib=self.root.attrib, nsmap=self.root.nsmap)

                for i in range(len(df)):
                    row = et.SubElement(new_root, child_tag, nsmap=self.root.nsmap)
                    for column in df.columns:
                        col_node = et.SubElement(row, column, nsmap=self.root.nsmap)
                        value = str(df[column].iloc[i])
                        col_node.text = value

                tree = et.ElementTree(new_root)
                tree.write(fp, encoding=self.encoding, xml_declaration=True, pretty_print=True)

            # data is list -> json array
            elif isinstance(data, list) and all(isinstance(item, dict) for item in data):
                # list 에서 직접 XML 생성
                root = et.Element(root_tag, nsmap=self.root.nsmap)
                for item in data:
                    # item is a dict
                    row = et.SubElement(root, child_tag, nsmap=self.root.nsmap)
                    for key in item:
                        row.set(key, item[key])

                tree = et.ElementTree(root)
                tree.write(fp, encoding=self.encoding, xml_declaration=True)
            else:
                dict_list = []
                self.fail_list.append(data)
                logger.error(f"{fp=}, {binary_mode=}, {opened=}, {self.processing_type=} {type(data)} is not supported")
        except Exception as e:
            self.fail_list.append(data)
            logger.error(f"{fp=}, {binary_mode=}, {opened=}, {self.processing_type=} dump raise: {e}")
        finally:
            self._safe_close(fp, opened)

    def dumps(self, data=None, root_tag=None, child_tag=None) -> str:
        """XML 데이터를 형태로 출력

        파일은 text, binary 모드 파일객체이거나 파일명 문자열

        Args:
            data (): 출력할 데이터, 생략되면 self.data_df 사용

        Returns:
            XML 데이터를 문자열로 출력
        """
        try:
            file_obj = io.BytesIO()

            if file_obj:
                self.dump(file_obj, data=data, root_tag=root_tag, child_tag=child_tag)
                xml_bytes = file_obj.getvalue()
                return xml_bytes.decode(encoding=self.encoding)
        except Exception as e:
            logger.error(f"{self} dump raise: {e}")
        return ""


    """
    클래스 내부 메쏘드 
    """

    def _decide_rw_open_mode(self, method_name) -> str:
        """내부메쏘드 json_type 과 method_name 에 따라서 파일 일기/쓰기 오픈 모드 결정

        XML은 binary 로 처리 필요

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

    def _add_all_child_text(self, parent: et._Element, parent_dict: dict, usecols: list = None, parent_key=None):
        """
            element node 안의 모든 text 를 dictionary 에 추가
        """
        for child in parent:
            node_key = et.QName(child).localname
            if parent_key:
                child_key = parent_key + '.' + node_key
            else:
                child_key = node_key

            if len(child.getchildren()) > 0:
                self._add_all_child_text(child, parent_dict, usecols=usecols, parent_key=child_key)
            else:
                if usecols is None or node_key in usecols:
                    parent_dict[child_key] = self._text_to_type_object(child.text)

    def _text_to_type_object(self, text: str):
        """
            child text 의 타입을 추정하여 object 값으로 변환
        """
        if text is None:
            return None

        if text.isalpha():
            if 'true' == text.lower():
                return True
            elif 'false' == text.lower():
                return False
            else:
                return text
        # 숫자 계통일 가능성
        else:
            dot_count = 0
            for c in text:
                if c == '.':
                    dot_count += 1
                elif not c.isnumeric():
                    return text

            if dot_count == 0:
                # Check if the text value can be converted to an int
                try:
                    value = int(text)
                    return value
                except ValueError:
                    return text
            elif dot_count == 1:
                # Check if the text value can be converted to a float
                try:
                    value = float(text)
                    return value
                except ValueError:
                    return text
            else:
                return text

    def xml_to_dict(self, node: et.Element) -> dict:
        """convert an etree to dictionary
\
        Returns: dict
        """
        d = {node.tag: {} if node.attrib else None}
        children = list(node)
        if children:
            dd = {}
            for dc in map(self.xml_to_dict, children):
                for k, v in dc.items():
                    if k in dd:
                        if not isinstance(dd[k], list):
                            dd[k] = [dd[k]]
                        dd[k].append(v)
                    else:
                        dd[k] = v
            d = {node.tag: dd}
        if node.attrib:
            d[node.tag].update((k, v) for k, v in node.attrib.items())
        if node.text:
            text = node.text.strip()
            if children or node.attrib:
                if text:
                    d[node.tag]['text'] = text
            else:
                d[node.tag] = text
        return d

    def dict_to_xml(self, tag, d):
        """
        Turn a simple dict of key/value pairs into XML
        """
        elem = et.Element(tag)
        for key, val in d.items():
            if isinstance(val, dict):
                child = self.dict_to_xml(key, val)
                elem.append(child)
            elif isinstance(val, list):
                for sub_dict in val:
                    child = self.dict_to_xml(key, sub_dict)
                    elem.append(child)
            else:
                child = et.SubElement(elem, key)
                child.text = str(val)
                elem.append(child)
        return elem

    def dict_dump(self, config: dict, tag: str, file_path: str):
        """config dictionary write to file path with wrapping root tag
        Args:
            config (dict): config dictionary
            tag (str): wrapping root tag
            file_path (str): file path to write

        """
        if len(config) == 1 and tag is None:
            for k, v in config.items():
                root_node = self.dict_to_xml(k, v)
        else:
            root_node = self.dict_to_xml(tag, config)
        tree = et.ElementTree(root_node)
        with open(file_path, 'wb') as f:
            tree.write(f, pretty_print=True, xml_declaration=True, encoding=self.encoding)
