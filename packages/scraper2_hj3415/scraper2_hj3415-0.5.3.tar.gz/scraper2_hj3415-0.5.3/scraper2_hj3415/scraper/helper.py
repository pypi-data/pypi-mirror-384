import random
import subprocess
import asyncio
import pandas as pd
from io import StringIO
from pathlib import Path

from playwright.async_api import Locator
from utils_hj3415 import setup_logger


mylogger = setup_logger(__name__, 'WARNING')


def ensure_playwright_installed():
    # 사용자 홈 디렉토리 기준으로 설치 경로 확인
    cache_dir = Path.home() / ".cache" / "ms-playwright"

    if not cache_dir.exists():
        print("Playwright driver installing...")
        subprocess.run(["playwright", "install"], check=True)


async def get_df_from_table(table_locator: Locator, header=0) -> pd.DataFrame:
    """
    Playwright에서 받은 table locator로부터 HTML을 추출해 pandas DataFrame으로 변환

    - table_locator: Playwright의 table 요소 Locator 객체
    - header: 테이블의 헤더구조 - 기본형 : 0 아니면 [0,1,...]
    - return: pandas.DataFrame
    """
    # HTML 추출
    html = await table_locator.evaluate("el => el.outerHTML")  # <table> 태그까지 포함

    try:
        df = pd.read_html(StringIO(html), header=header)[0]
        mylogger.debug(df)
    except ValueError as e:
        raise ValueError("pandas.read_html()에서 테이블을 찾지 못했습니다") from e

    if header == 0: # 일반적인 헤더의 경우만
        # '항목' 열 정리 (있는 경우)
        if '항목' in df.columns:
            df['항목'] = df['항목'].str.replace('펼치기', '').str.strip()

        # 열 이름 정리
        df.columns = (df.columns
                      .str.replace('연간컨센서스보기', '', regex=False)
                      .str.replace('연간컨센서스닫기', '', regex=False)
                      .str.replace('(IFRS연결)', '', regex=False)
                      .str.replace('(IFRS별도)', '', regex=False)
                      .str.replace('(GAAP개별)', '', regex=False)
                      .str.replace('(YoY)', '', regex=False)
                      .str.replace('(QoQ)', '', regex=False)
                      .str.replace('(E)', '', regex=False)
                      .str.replace('.', '', regex=False)
                      .str.strip())

    return df


async def wait_with_retry(locator, retries=3, delay=3):
    for i in range(retries):
        try:
            await locator.wait_for(state="attached", timeout=10000)
            return True
        except Exception:
            if i < retries - 1:
                await asyncio.sleep(delay)
            else:
                raise


def is_ymd_format(date_str: str) -> bool:
    try:
        from datetime import datetime
        datetime.strptime(date_str, "%Y%m%d")
        return True
    except ValueError:
        return False


