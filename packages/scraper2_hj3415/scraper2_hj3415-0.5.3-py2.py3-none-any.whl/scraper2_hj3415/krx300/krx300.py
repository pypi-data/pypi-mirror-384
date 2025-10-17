import os
import time
import shutil
import pandas as pd
import sqlite3
import random
import requests
from datetime import datetime, timedelta

from db2_hj3415.nfs import get_all_codes, delete_code_from_all_collections
from utils_hj3415 import setup_logger

mylogger = setup_logger(__name__,'WARNING')

table_name = 'krx300'

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, 'temp')
SQLITE_PATH = os.path.join(BASE_DIR, 'krx.db')

def find_valid_url(max_days: int = 15) -> str:
    delta = 1
    while delta <= max_days:
        date = datetime.now() - timedelta(days=delta)
        date_str = date.strftime('%Y%m%d')
        url = f'https://www.samsungfund.com/excel_pdf.do?fId=2ETFA4&gijunYMD={date_str}'

        try:
            response = requests.get(url, timeout=5)
            time.sleep(random.uniform(2.5, 4.0))  # 일정하지 않게 랜덤 지연

            if response.headers.get('Content-Length', '0') != '0':
                print('삼성자산운용 krx300 엑셀다운 url :', url)
                return url
            else:
                mylogger.warning(f"{url} - Content-Length=0, 파일 없음")
        except Exception as e:
            mylogger.error(f"{url} 요청 실패: {e}")

        delta += 1

    raise RuntimeError("유효한 KRX300 엑셀 파일을 찾지 못했습니다.")

def download_excel() -> str | None:
    # 임시폴더 정리
    shutil.rmtree(TEMP_DIR, ignore_errors=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    mylogger.info(f"임시폴더 초기화 완료: {TEMP_DIR}")

    try:
        url = find_valid_url()
        response = requests.get(url, timeout=10)

        filename = f"{url[-12:]}.xls"  # 예: '20240611.xls'
        SAVE_PATH = os.path.join(TEMP_DIR, filename)

        if response.status_code == 200:
            with open(SAVE_PATH, 'wb') as f:
                f.write(response.content)
            print(f"엑셀 파일 다운로드 완료: {SAVE_PATH}")
            return SAVE_PATH
        else:
            mylogger.error(f"다운로드 실패: 상태코드 {response.status_code}")
            return None

    except Exception as e:
        mylogger.error(f"엑셀 다운로드 중 오류 발생: {e}")
        return None

def make_db(excel_path: str):
    # 1. 엑셀 파일 읽기
    try:
        df: pd.DataFrame = pd.read_excel(excel_path, usecols='B:I', skiprows=2)  # type: ignore
        mylogger.info(f"엑셀 파일 읽기 성공: {excel_path}")
    except Exception as e:
        mylogger.error(f"엑셀 파일 읽기 실패: {e}")
        return

    # 2. SQLite 데이터베이스 연결
    try:
        conn = sqlite3.connect(SQLITE_PATH)
        mylogger.info(f"SQLite 연결 성공: {SQLITE_PATH}")
    except Exception as e:
        mylogger.error(f"SQLite 연결 실패: {e}")
        return

    try:
        # 3. 데이터 삽입
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"엑셀 데이터를 테이블 '{table_name}'에 성공적으로 삽입됨.")

        # 4. 원화예금 항목 삭제
        sql = f'DELETE FROM "{table_name}" WHERE "종목명" = ?'
        conn.execute(sql, ('원화예금',))
        conn.commit()
        mylogger.info("원화예금 항목 삭제 완료.")

    except Exception as e:
        mylogger.error(f"DB 작업 중 오류 발생: {e}")

    finally:
        conn.close()
        mylogger.info("SQLite 연결 종료.")

def get_codes() -> list[str]:
    """
    Retrieve a list of stock codes from the krx300 SQLite table.
    If the database does not exist, it downloads the Excel and creates it.
    """
    if not os.path.exists(SQLITE_PATH):
        mylogger.warning(f"{SQLITE_PATH} 파일이 존재하지 않아 새로 생성합니다.")
        excel_path = download_excel()
        if not excel_path:
            mylogger.error("엑셀 파일 다운로드 실패 - 코드 추출 중단")
            return []
        make_db(excel_path)

    try:
        with sqlite3.connect(SQLITE_PATH) as conn:
            query = f'SELECT 종목코드 FROM "{table_name}" WHERE 종목코드 LIKE "______"'   # 6자리 종목코드만
            codes = pd.read_sql(query, conn)['종목코드'].tolist()
            mylogger.info(f"총 {len(codes)}개의 종목코드 불러옴")
            return codes
    except Exception as e:
        mylogger.error(f"종목코드 불러오기 실패: {e}")
        return []

def get_code_names() -> list[list[str]]:
    if not os.path.exists(SQLITE_PATH):
        mylogger.warning(f"{SQLITE_PATH} 파일이 존재하지 않아 새로 생성합니다.")
        excel_path = download_excel()
        if not excel_path:
            mylogger.error("엑셀 파일 다운로드 실패 - 코드/이름 추출 중단")
            return []
        make_db(excel_path)

    try:
        with sqlite3.connect(SQLITE_PATH) as conn:
            query = f'SELECT 종목코드, 종목명 FROM "{table_name}" WHERE 종목코드 LIKE "______"'
            df = pd.read_sql(query, conn)
            return df.values.tolist()
    except Exception as e:
        mylogger.error(f"코드/종목명 조회 실패: {e}")
        return []

def get_name(code: str) -> str | None:
    if not os.path.exists(SQLITE_PATH):
        mylogger.warning(f"{SQLITE_PATH} 파일이 존재하지 않아 새로 생성합니다.")
        excel_path = download_excel()
        if not excel_path:
            return None
        make_db(excel_path)

    try:
        with sqlite3.connect(SQLITE_PATH) as conn:
            query = f'SELECT 종목명 FROM "{table_name}" WHERE 종목코드 = ?'
            result = conn.execute(query, (code,)).fetchone()
            return result[0] if result else None
    except Exception as e:
        mylogger.error(f"종목명 조회 실패: {e}")
        return None

async def sync_with_mongo() -> bool:

    # krx300 sqlite3 리프레시
    excel_path = download_excel()
    if not excel_path:
        mylogger.error("엑셀 다운로드 실패 - MongoDB 동기화 중단")
        return False
    make_db(excel_path)

    in_mongo_codes = await get_all_codes()
    in_sqlite_codes = get_codes()
    print(f"In mongodb: {len(in_mongo_codes)} - {in_mongo_codes[:5]}{' ...' if len(in_mongo_codes) > 5 else ''}")
    print(f"In sqlite3: {len(in_sqlite_codes)} - {in_sqlite_codes[:5]}{' ...' if len(in_sqlite_codes) > 5 else ''}")

    sqlite_set = set(in_sqlite_codes)
    mongo_set = set(in_mongo_codes)

    to_delete = list(mongo_set - sqlite_set)
    to_add = list(sqlite_set - mongo_set)

    if len(to_add) == 0 and len(to_delete) == 0:
        print(f"mongodb와 krx300의 sync는 일치합니다.(총 {len(in_mongo_codes)} 종목)")
    else:
        print(f"mongodb에서 삭제될 코드: {len(to_delete)}개 - {to_delete[:5]}{' ...' if len(to_delete) > 5 else ''}")
        print(f"mongodb에 추가될 코드: {len(to_add)}개 - {to_add[:5]}{' ...' if len(to_add) > 5 else ''}")

        # 몽고디비에서 불필요한 종목 삭제하고 서버에 기록.
        for code in to_delete:
            try:
                await delete_code_from_all_collections(code)
            except Exception as e:
                mylogger.error(f"{code} 삭제 실패: {e}")

        # 몽고디비에 새로운 종목 추가하고 서버에 기록. 중간 에러시 스크랩한 데이터손실을 최소화하기위해 batch_size 종목단위로 저장
        async def batch_process(col: str, codes: list[str], batch_size: int = 5):
            for i in range(0, len(codes), batch_size):
                batch = codes[i:i + batch_size]
                print(f"종목 : {batch} 을 저장합니다.")
                try:
                    # 상호참조 문제로 이곳에서 임포트 한다.
                    from scraper2_hj3415.cli.nfs import parse_many_data, save_many_data
                    many_data = await parse_many_data(col, batch)
                    await save_many_data(col, many_data)
                    mylogger.info(f"[{col}] 저장 완료: {len(batch)}개 종목")
                except Exception as e:
                    mylogger.warning(f"[{col}] 배치 실패 (종목들: {batch}): {e}")

        try:
            for col in ['c101', 'c103', 'c104', 'c106', 'c108']:
                await batch_process(col, to_add, batch_size=5)
        except Exception as e:
            mylogger.error(f"nfs 전체 크롤링 실패: {e}")
            return False
    return True

