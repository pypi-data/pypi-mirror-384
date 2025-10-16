# echoss_fileformat v1.2.1

# File Format Handlers

This project provides file format handler packages for JSON, CSV, XML, and Excel files. The packages provide an abstraction layer to load and save data in these file formats using a unified API.

## Version History
- v1.0 : Object method
- v1.1 : static method
- v1.2 : stable updated 

## Installation

To install the package, use pip:
pip install echoss_fileformat

To upgrade the installed package, use pip:
pip install echoss_fileformat -U

## Usage

1. static call 

```python
from echoss_fileformat import FileUtil, to_table, get_logger, set_logger_level

# FileUtil Load test_data from a file
csv_df = FileUtil.load('test_data.csv')
excel_df = FileUtil.load('weather_data.xls')
json_df = FileUtil.load('test_data.json', data_key = 'data')
jsonl_df = FileUtil.load('test_multiline_json.jsonl', data_key = 'data')

# FileUtil Save DataFrame to a file
FileUtil.dump(excel_df, 'save/test_data_1.csv')
FileUtil.dump(csv_df, 'weather_data.xlsx')
FileUtil.dump(json_df, 'test_data_2.jsonl')

# read/write config file
app_config = FileUtil.dict_load('config/application.yaml')
db_config = FileUtil.dict_load('jdbc.properties')
FileUtil.dict_dump(app_config, 'new_config.xml')

# DataFrame to table-like string
logger = get_logger("echoss_fileformat_test")
set_logger_level("DEBUG")
logger.debug(to_table(json_df))
```

파일 포맷 읽기 :
- FileUtil.load(file_path: str, file_format=None, **kwargs) : 파일 확장자 기준으로 매칭되는 파일포맷으로 읽음
  * 확장자 .csv : 기본csv 파일 포맷으로 읽기. 컬럼 구분자는 콤마(,) 사용.
  * 확장자 .tsv : 컬럼 구분자 탭(\t)인 csv 파일 포맷으로 읽기.
  * 확장자 .xls .xlsx : excel 파일 포맷으로 읽기
  * 확장자 .json : 파일 전체가 1개의 json 객체인 파일포맷으로읽기 (전체가 JSON array 인경우는 객체로 감싸야함)
  * 확자자 .jsonl : 라인 하나가 json  객체인 multi line json 파일 형태
  * 확장자 .xml : xml 파일포맷으로 읽기
  * 확장자 .parquet : parquet 파일포맷으로 읽기
  * 확장자 .feather : feather 파일포맷으로 읽기
- FileUtil.load(filename_or_file, file_format='csv') :  csv 파일 포맷으로 파일명  또는 file-like object 로 읽음
- FileUtil.load(filename_or_file, file_format='xlsx') :  excel 파일 포맷으로 파일명  또는 file-like object 로 읽음
- FileUtil.load(filename_or_file, file_format='json') :  json 파일 포맷으로 파일명  또는 file-like object 로 읽음

파일 포맷 쓰기 :
- FileUtil.dump(df: pd.DataFrame, file_path: str, file_format=None, force_write=False, **kwargs) : 파일 확장자 기준으로 매칭되는 파일포맷으로 쓰기
  * 확장자 .csv : 기본csv 파일 포맷으로 쓰기. 컬럼 구분자는 콤마(,) 사용.
  * 확장자 .tsv : 컬럼 구분자 탭(\t)인 csv 파일 포맷으로 쓰기.
  * 확장자 .xls .xlsx : excel 파일 포맷으로 쓰기
  * 확장자 .json : 파일 전체가 1개의 json 객체인 파일포맷으로쓰기 (전체가 JSON array 인경우는 객체로 감싸야함)
  * 확자자 .jsonl : 라인 하나가 json  객체인 multi line json 파일 형태
  * 확장자 .xml : xml 파일포맷으로 쓰기
  * 확장자 .parquet : parquet 파일포맷으로 쓰기
  * 확장자 .feather : feather 파일포맷으로 쓰기
- FileUtil.dump(filename_or_file, file_format='jsonl') :  jsonl 파일 포맷으로 파일명  또는 file-like object 로 쓰기
- FileUtil.dump_xml(filename_or_file, file_format='xml', force_write=True) :  xml 파일 포맷으로 overwrite 파일 쓰기

For config file load/dump:

dict_load() : load file format to dictionary for configuration files .yaml, .xml, .json and .properties
dict_dump() : write dictionary to file format  .yaml, .xml, .json and .properties

For print dataframe:

def to_table(df: pd.DataFrame, index=True, max_cols=16, max_rows=10, col_space=4, max_colwidth=24): 
dataframe to table-like string

exampe:
```
+--------------------------+----------------+----------------+---------------+--------------------+------------------+-----------------+-----------------+
| ('수집항목', '개체번호') | ('과폭', 'cm') | ('과고', 'cm') | ('과중', 'g') | ('당도', 'Brix %') | ('산도', '0-14') | ('경도', 'kgf') | ('수분율', '%') |
+--------------------------+----------------+----------------+---------------+--------------------+------------------+-----------------+-----------------+
| 1                        | 8.2            | 6.6            | 253           | 3.1                | 4.0              | 2.71            | 71.2            |
+--------------------------+----------------+----------------+---------------+--------------------+------------------+-----------------+-----------------+
| 2                        | 6.3            | 5.7            | 136           | 3.1                | 4.0              | 2.74            | 72.2            |
+--------------------------+----------------+----------------+---------------+--------------------+------------------+-----------------+-----------------+
| 3                        | 8.0            | 6.3            | 220           | 3.4                | 4.5              | 2.71            | 70.4            |
+--------------------------+----------------+----------------+---------------+--------------------+------------------+-----------------+-----------------+
| 4                        | 7.3            | 6.0            | 173           | 3.7                | 4.0              | 2.75            | 73.78           |
+--------------------------+----------------+----------------+---------------+--------------------+------------------+-----------------+-----------------+
| 5                        | 6.3            | 5.5            | 130           | 3.6                | 4.0              | 2.72            | 75.4            |
+--------------------------+----------------+----------------+---------------+--------------------+------------------+-----------------+-----------------+
```


2. Object 
- 학습데이터가 아닌 메타데이터 객체로 읽어들일 경우

handler = CsvHandler('object')

- 학습데이터로 읽어들이는 경우 

handler = ExcelHandler()
또는 handler = ExcelHandler('array')

- JSON 파일 중에서 각 줄이 하나의 json 객체일 경우

handler = JsonHandler('multiline')


The package provides an abstraction layer to load and save data in JSON, CSV, XML, and Excel formats. The API includes the following methods:

* `load(file_or_filename, **kwargs)`: Load data from a file.
* `loads(bytes_or_str, **kwargs)`: Load data from a string.
* `dump(file_or_filename, data = None, **kwargs)`: Save data to a file.
* `dumps(data = None, **kwargs)`: Save data to a string.

The following example demonstrates how to load data from a CSV file and save it as a JSON file:

```python
from echoss_fileformat import CsvHandler, JsonHandler

# Load test_data from a CSV file
csv_handler = CsvHandler()
data = csv_handler.load('test_data.csv', header=[0, 1])

# Save test_data as a JSON file
json_handler = JsonHandler('array')
json_handler.load( 'test_data_1.json', data_key = 'data')
json_handler.load( 'test_data_2.json', data_key = 'data')
json_handler.dump( 'test_data_all.json')
```

## Contributing
Contributions are welcome! If you find a bug or want to suggest a new feature, please open an issue on the GitHub repository.

## License
This project is licensed under the LGPL License. See the LICENSE file for more information.

## Credits
This project was created by 12cm. Special thanks to 12cm R&D for their contributions to the project.
