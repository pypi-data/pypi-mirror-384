import os
import sys

# 소스 디렉토리 경로 설정
SOURCE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "echoss_fileformat"))

# 소스 디렉토리가 존재하면 sys.path에 추가
if os.path.exists(SOURCE_DIR):
    sys.path.insert(0, SOURCE_DIR)
    print(f"[tests] tests with source in source directory : {SOURCE_DIR}")
else:
    print("[tests] tests with installed package.")
