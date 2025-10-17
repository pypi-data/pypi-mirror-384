import asyncio
import random

import numpy as np
import pandas as pd
from io import StringIO
from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError
from utils_hj3415 import setup_logger, tools
from . import helper
from db2_hj3415.nfs import C101, C103, C104, C106, C108, 항목값y, 항목값q, 기업데이터
from datetime import datetime, timezone

mylogger = setup_logger(__name__, 'WARNING')


async def parse_c101(code: str, page: Page) -> C101 | None:
    url = f"https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={code}"

    page.set_default_timeout(3000)
    print(f"Fetching c101 / {code} from {url}")
    await page.goto(url, timeout=10000)
    mylogger.debug(f"페이지 제목: {await page.title()}")
    await asyncio.sleep(2)

    try:
        raw_date_str = await page.get_by_text("[기준:").first.text_content()
        날짜 = raw_date_str.replace("[기준:", "").replace("]", "")
        mylogger.debug(f"날짜:{날짜}")
    except:
        mylogger.error(f'Page not found for {code}')
        return None

    # 1. 재무정보 (1st table)
    e_1st_table = page.locator("#pArea > div.wrapper-table > div > table > tbody")
    await helper.wait_with_retry(e_1st_table)

    종목명 = (await e_1st_table.locator("tr:nth-child(1) > td > dl > dt:nth-child(1) > span").text_content()).strip()
    코드 = (await e_1st_table.locator("tr:nth-child(1) > td > dl > dt:nth-child(1) > b").text_content()).strip()
    업종 = (await e_1st_table.locator("tr:nth-child(1) > td > dl > dt:nth-child(4)").text_content()).split(":")[1].strip()

    eps = tools.to_int(await e_1st_table.locator("tr:nth-child(3) > td > dl > dt:nth-child(1) > b").text_content())
    bps = tools.to_int(await e_1st_table.locator("tr:nth-child(3) > td > dl > dt:nth-child(2) > b").text_content())
    per = tools.to_float(await e_1st_table.locator("tr:nth-child(3) > td > dl > dt:nth-child(3) > b").text_content())
    업종per = tools.to_float(await e_1st_table.locator("tr:nth-child(3) > td > dl > dt:nth-child(4) > b").text_content())
    pbr = tools.to_float(await e_1st_table.locator("tr:nth-child(3) > td > dl > dt:nth-child(5) > b").text_content())
    배당수익률 = tools.to_float(await e_1st_table.locator("tr:nth-child(3) > td > dl > dt:nth-child(6) > b").text_content())

    # 2. 주가 정보 (2nd table)
    e_2nd_table = page.locator("#cTB11 > tbody")
    await helper.wait_with_retry(e_2nd_table)

    주가 = tools.to_int(await e_2nd_table.locator("tr:nth-child(1) > td > strong").text_content())
    전일대비 = tools.to_int((await e_2nd_table.locator("tr:nth-child(1) > td > span:nth-child(2)").text_content()).replace("원", ""))
    수익률 = tools.to_float((await e_2nd_table.locator("tr:nth-child(1) > td > span:nth-child(3)").text_content()).replace("%", ""))

    최고최저52 = await e_2nd_table.locator("tr:nth-child(2) > td").text_content()
    최고52, 최저52 = (tools.to_int(x.strip().replace("원", "")) for x in 최고최저52.split("/"))

    거래량거래대금 = await e_2nd_table.locator("tr:nth-child(4) > td").text_content()
    거래량_str, 거래대금_str = (x.strip() for x in 거래량거래대금.split("/"))
    거래량 = tools.to_int(거래량_str.replace("주", ""))
    거래대금 = tools.parse_won(거래대금_str)

    시가총액 = tools.parse_won(await e_2nd_table.locator("tr:nth-child(5) > td").text_content())
    베타52주 = tools.to_float(await e_2nd_table.locator("tr:nth-child(6) > td").text_content())

    발행주식유동비율 = await e_2nd_table.locator("tr:nth-child(7) > td").text_content()
    발행주식_str, 유동비율_str = (x.strip() for x in 발행주식유동비율.split("/"))
    발행주식 = tools.to_int(발행주식_str.replace("주", ""))
    유동비율 = tools.to_float(유동비율_str.replace("%", ""))

    외국인지분율 = tools.to_float((await e_2nd_table.locator("tr:nth-child(8) > td").text_content()).replace("%", ""))

    수익률1M3M6M1Y = await e_2nd_table.locator("tr:nth-child(9) > td").text_content()
    수익률1M, 수익률3M, 수익률6M, 수익률1Y = (tools.to_float(x.strip().replace("%", "")) for x in 수익률1M3M6M1Y.split("/"))

    # 3. 개요
    개요_ul = page.locator("#wrapper > div:nth-child(6) > div.cmp_comment > ul")
    await helper.wait_with_retry(개요_ul)
    li_elements = await 개요_ul.locator("li").all()
    개요_list = [(await li.text_content()).strip() for li in li_elements]
    개요 = "".join(개요_list)

    data = {
        "종목명": 종목명,
        "코드": 코드,
        "날짜": 날짜,
        "업종": 업종,
        "eps": eps,
        "bps": bps,
        "per": per,
        "업종per": 업종per,
        "pbr": pbr,
        "배당수익률": 배당수익률,
        "주가": 주가,
        "전일대비": 전일대비,
        "수익률": 수익률,
        "최고52": 최고52,
        "최저52": 최저52,
        "거래량": 거래량,
        "거래대금": 거래대금,
        "시가총액": 시가총액,
        "베타52주": 베타52주,
        "발행주식": 발행주식,
        "유동비율": 유동비율,
        "외국인지분율": 외국인지분율,
        "수익률1M": 수익률1M,
        "수익률3M": 수익률3M,
        "수익률6M": 수익률6M,
        "수익률1Y": 수익률1Y,
        "개요": 개요,
    }

    mylogger.debug(data)

    return C101(**data)

async def parse_c101_many(codes: list[str], page:Page) -> list[C101|None]:
    results: list[C101|None] = []

    for code in codes:
        print(f"Parsing.. {code} / c101")
        try:
            result = await parse_c101(code, page)
            results.append(result)
        except Exception as e:
            mylogger.error(f"Error while parsing {code}: {e}")
            results.append(None)
        finally:
            await asyncio.sleep(random.uniform(1.0, 2.0))
    return results

async def click_buttons(page: Page, buttons: list[tuple[str, str]]) -> bool:
    """
    Playwright에서 버튼 클릭을 처리하는 비동기 함수
    :param page: Playwright의 Page 객체
    :param buttons: (버튼 이름, XPath) 리스트
    :return: 모든 클릭이 성공하면 True, 아니면 False
    """
    mylogger.debug('*** Setting page by clicking buttons ***')
    mylogger.debug(buttons)

    for name, xpath in buttons:
        mylogger.debug(f'- Click the {name} / {xpath} button')
        try:
            # 요소가 나타날 때까지 대기 후 클릭
            await page.wait_for_selector(f'xpath={xpath}')
            await page.locator(f'xpath={xpath}').click()
        except PlaywrightTimeoutError:
            mylogger.warning(f"{name} 엘리먼트를 찾지 못했습니다.")
            return False

        await asyncio.sleep(random.uniform(1, 3))

    mylogger.debug('*** Buttons click done ***')
    return True

T_C1034 = list[항목값y] | list [항목값q]

def df_to_c1034_model(data: dict[str, pd.DataFrame]) -> dict[str, T_C1034]:
    cleaned_data: dict[str, T_C1034] = {}

    for page, df in data.items():
        if not isinstance(df, pd.DataFrame):
            continue

        records = df.replace({np.nan: None}).to_dict(orient="records")

        if page.endswith("q"):
            cleaned_data[page] = [항목값q(**item) for item in records]
        elif page.endswith("y"):
            cleaned_data[page] = [항목값y(**item) for item in records]
        else:
            raise ValueError(f"알 수 없는 페이지 키 형식: {page}")

    return cleaned_data

async def parse_c103(code: str, page: Page) -> C103:
    '''
    # XPATH 상수
    손익계산서 = '//*[@id="rpt_tab1"]'
    재무상태표 = '//*[@id="rpt_tab2"]'
    현금흐름표 = '//*[@id="rpt_tab3"]'
    연간 = '//*[@id="frqTyp0"]'
    분기 = '//*[@id="frqTyp1"]'
    검색 = '//*[@id="hfinGubun"]'
    '''

    btns = {
        "손익계산서y": [
            ('손익계산서', '//*[@id="rpt_tab1"]'),
            ('연간', '//*[@id="frqTyp0"]'),
            ('검색', '//*[@id="hfinGubun"]'),
        ],
        "재무상태표y": [
            ('재무상태표', '//*[@id="rpt_tab2"]'),
            ('연간', '//*[@id="frqTyp0"]'),
            ('검색', '//*[@id="hfinGubun"]'),
        ],
        "현금흐름표y": [
            ('현금흐름표', '//*[@id="rpt_tab3"]'),
            ('연간', '//*[@id="frqTyp0"]'),
            ('검색', '//*[@id="hfinGubun"]'),
        ],
        "손익계산서q": [
            ('손익계산서', '//*[@id="rpt_tab1"]'),
            ('분기', '//*[@id="frqTyp1"]'),
            ('검색', '//*[@id="hfinGubun"]'),
        ],
        "재무상태표q": [
            ('재무상태표', '//*[@id="rpt_tab2"]'),
            ('분기', '//*[@id="frqTyp1"]'),
            ('검색', '//*[@id="hfinGubun"]'),
        ],
        "현금흐름표q": [
            ('현금흐름표', '//*[@id="rpt_tab3"]'),
            ('분기', '//*[@id="frqTyp1"]'),
            ('검색', '//*[@id="hfinGubun"]'),
        ],
    }

    url = f"https://navercomp.wisereport.co.kr/v2/company/c1030001.aspx?cn=&cmp_cd={code}"

    page.set_default_timeout(10000)
    print(f"Fetching c103 / {code} from {url}")
    await page.goto(url, timeout=10000)
    mylogger.debug(f"페이지 제목: {await page.title()}")
    await asyncio.sleep(2)

    data = {'코드':code, '날짜':datetime.now(timezone.utc)}

    dfs:dict[str, pd.DataFrame] = {}

    for title, btn_list in btns.items():
        print(f"Clicking for {title}...")
        await click_buttons(page, btn_list)
        selector = 'div#wrapper div table'
        await page.wait_for_selector(selector, state="attached")
        table_locator = page.locator(selector).nth(2)
        mylogger.debug((await table_locator.inner_html())[:100])
        try:
            dfs[title] = await helper.get_df_from_table(table_locator)
        except Exception as e:
            mylogger.error(f"{title} 테이블 파싱 실패: {e}")
            dfs[title] = pd.DataFrame()

    data.update(df_to_c1034_model(dfs))
    return C103(**data)

async def parse_c103_many(codes: list[str], page:Page) -> dict[str, C103 | None]:
    results: dict[str, C103 | None] = {}

    for code in codes:
        print(f"Parsing.. {code} / c103")
        try:
            result = await parse_c103(code, page)
            results[code] = result
        except Exception as e:
            mylogger.error(f"Error while parsing {code}: {e}")
            results[code] = None
        finally:
            await asyncio.sleep(random.uniform(1.0, 2.0))
    return results


async def parse_c104(code: str, page: Page) -> C104:
    '''
    # XPATH 상수
    수익성 = '//*[ @id="val_tab1"]'
    성장성 = '//*[ @id="val_tab2"]'
    안정성 = '//*[ @id="val_tab3"]'
    활동성 = '//*[ @id="val_tab4"]'

    연간 = '//*[@id="frqTyp0"]'
    분기 = '//*[@id="frqTyp1"]'
    검색 = '//*[@id="hfinGubun"]'

    가치분석연간 = '//*[@id="frqTyp0_2"]'
    가치분석분기 = '//*[@id="frqTyp1_2"]'
    가치분석검색 = '//*[@id="hfinGubun2"]'
    '''

    btns = {
        '수익성y': [
            ('수익성', '//*[ @id="val_tab1"]'),
            ('연간', '//*[@id="frqTyp0"]'),
            ('검색', '//*[@id="hfinGubun"]'),
        ],
        '성장성y': [
            ('성장성', '//*[ @id="val_tab2"]'),
            ('연간', '//*[@id="frqTyp0"]'),
            ('검색', '//*[@id="hfinGubun"]'),
        ],
        '안정성y': [
            ('안정성', '//*[ @id="val_tab3"]'),
            ('연간', '//*[@id="frqTyp0"]'),
            ('검색', '//*[@id="hfinGubun"]'),
        ],
        '활동성y': [
            ('활동성', '//*[ @id="val_tab4"]'),
            ('연간', '//*[@id="frqTyp0"]'),
            ('검색', '//*[@id="hfinGubun"]'),
        ],
        '가치분석y': [
            ('가치분석연간', '//*[@id="frqTyp0_2"]'),
            ('가치분석검색', '//*[@id="hfinGubun2"]'),
        ],
        '수익성q': [
            ('수익성', '//*[ @id="val_tab1"]'),
            ('분기', '//*[@id="frqTyp1"]'),
            ('검색', '//*[@id="hfinGubun"]'),
        ],
        '성장성q': [
            ('성장성', '//*[ @id="val_tab2"]'),
            ('분기', '//*[@id="frqTyp1"]'),
            ('검색', '//*[@id="hfinGubun"]'),
        ],
        '안정성q': [
            ('안정성', '//*[ @id="val_tab3"]'),
            ('분기', '//*[@id="frqTyp1"]'),
            ('검색', '//*[@id="hfinGubun"]'),
        ],
        '활동성q': [
            ('활동성', '//*[ @id="val_tab4"]'),
            ('분기', '//*[@id="frqTyp1"]'),
            ('검색', '//*[@id="hfinGubun"]'),
        ],
        '가치분석q': [
            ('가치분석분기', '//*[@id="frqTyp1_2"]'),
            ('가치분석검색', '//*[@id="hfinGubun2"]'),
        ],
    }

    url = f"https://navercomp.wisereport.co.kr/v2/company/c1040001.aspx?cn=&cmp_cd={code}"

    page.set_default_timeout(10000)
    print(f"Fetching c104 / {code} from {url}")
    await page.goto(url, timeout=10000)
    mylogger.debug(f"페이지 제목: {await page.title()}")
    await asyncio.sleep(2)

    data = {'코드':code, '날짜':datetime.now(timezone.utc)}

    dfs: dict[str, pd.DataFrame] = {}

    for title, btn_list in btns.items():
        print(f"Clicking for {title}...")
        await click_buttons(page, btn_list)
        selector = 'xpath=//table[@class="gHead01 all-width data-list"]'
        await page.wait_for_selector(selector, state="attached")

        if title.startswith("가치분석"):
            table_locator = page.locator(selector).nth(1)
        else:
            table_locator = page.locator(selector).nth(0)

        try:
            dfs[title] = await helper.get_df_from_table(table_locator)
        except Exception as e:
            mylogger.error(f"{title} 테이블 파싱 실패: {e}")
            dfs[title] = pd.DataFrame()

    data.update(df_to_c1034_model(dfs))
    return C104(**data)

async def parse_c104_many(codes: list[str], page:Page) -> dict[str, C104 | None]:
    results: dict[str, C104 | None] = {}

    for code in codes:
        print(f"Parsing.. {code} / c104")
        try:
            result = await parse_c104(code, page)
            results[code] = result
        except Exception as e:
            mylogger.error(f"Error while parsing {code}: {e}")
            results[code] = None
        finally:
            await asyncio.sleep(random.uniform(1.0, 2.0))
    return results


def df_to_c106_model(data: dict[str, pd.DataFrame]) -> dict[str, list[기업데이터]]:
    cleaned_data: dict[str, list[기업데이터]] = {}

    for page, df in data.items():
        if not isinstance(df, pd.DataFrame):
            continue

        records = df.replace({np.nan: None}).to_dict(orient="records")
        cleaned_data[page] = [기업데이터(**item) for item in records]

    return cleaned_data

async def parse_c106(code: str, page: Page) -> C106:
    async def get_company_names_from_header() -> list:
        selector = '#cTB611_h'
        await page.wait_for_selector(selector, state="attached")
        table_header_locator = page.locator(selector)
        mylogger.debug((await table_header_locator.inner_html())[:100])

        # 업체명들은 <th> 태그의 첫 번째 줄에 위치하므로 <thead> 안의 th에서 첫 줄만 추출
        headers = table_header_locator.locator(
            'xpath=//caption[contains(text(), "기업간비교자료")]/following-sibling::thead//th[not(@colspan)]')
        names = []
        count = await headers.count()
        for i in range(count):
            text = await headers.nth(i).inner_text()
            name = text.strip().split("\n")[0]  # 첫 번째 줄만 추출
            names.append(name)
        return names

    async def get_df_from_comparison_table(locator: Locator, company_names: list[str]) -> pd.DataFrame:
        html = await locator.evaluate("el => el.outerHTML")

        # header=None: 첫 줄을 헤더로 쓰지 않겠다는 의미
        df = pd.read_html(StringIO(html), header=None)[0]

        # 첫 번째 열은 '항목', 나머지는 주어진 회사명으로 설정
        df.columns = ["항목", '항목2'] + company_names

        # 항목1 열의 NaN은 이전 값으로 채움 (대분류)
        df['항목'] = df['항목'].ffill()

        # 첫 두 줄만 한 칸씩 오른쪽으로 밀고 '항목'을 삽입
        for i in range(2):  # 0번, 1번 row
            row = df.loc[i].tolist()  # 현재 행 전체를 리스트로 가져오기
            new_row = ['주가데이터'] + row  # 앞에 '주가데이터' 삽입
            df.loc[i] = new_row[:len(df.columns)]  # 덮어쓰기 (열 수에 맞게 자름)

        # 항목2가 NaN인 행 제거 (실 데이터가 없는 줄)
        df = df[df['항목2'].notna()].reset_index(drop=True)

        # 예: 항목2 값이 특정 값일 때 항목을 수동 지정
        df.loc[df['항목2'].isin(['투자의견', '목표주가(원)']), '항목'] = '기타지표'

        # 예: 항목2가 '재무연월'인 행을 제거 - 필요없는 행
        if '항목2' in df.columns:
            df = df[df['항목2'] != '재무연월'].reset_index(drop=True)

        # 필요시 숫자 정리
        for col in df.columns[2:]:
            df[col] = df[col].replace('-', '0')  # '-' 를 0으로
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # '항목' 열에 있는 "펼치기" 같은 문자열 제거
        df["항목"] = df["항목"].astype(str).str.replace("펼치기", "").str.strip()

        return df

    url = f"https://navercomp.wisereport.co.kr/v2/company/c1060001.aspx?cn=&cmp_cd={code}"

    page.set_default_timeout(10000)
    print(f"Fetching c106 / {code} from {url}")
    await page.goto(url, timeout=10000)
    mylogger.debug(f"페이지 제목: {await page.title()}")
    await asyncio.sleep(2)

    data = {'코드': code, '날짜': datetime.now(timezone.utc)}

    dfs: dict[str, pd.DataFrame] = {}

    company_names = await get_company_names_from_header()
    mylogger.info(f"테이블 헤더에서 추출된 종목: {company_names}")

    for period in ["Q", "Y"]:
        table_url = f"https://navercomp.wisereport.co.kr/v2/company/cF6002.aspx?cmp_cd={code}&finGubun=MAIN&sec_cd=FG000&frq={period}"
        try:
            await page.goto(table_url, timeout=10000)
            await page.wait_for_selector("#cTB611", state="attached")
            table_locator = page.locator("#cTB611")
            df = await get_df_from_comparison_table(table_locator, company_names)
            dfs[period.lower()] = df
        except Exception as e:
            mylogger.error(f"{period} 테이블 파싱 실패: {e}")
            dfs[period.lower()] = pd.DataFrame()

    data.update(df_to_c106_model(dfs))
    return C106(**data)

async def parse_c106_many(codes: list[str], page:Page) -> dict[str, C106 | None]:
    results: dict[str, C106 | None] = {}

    for code in codes:
        print(f"Parsing.. {code} / c106")
        try:
            result = await parse_c106(code, page)
            results[code] = result
        except Exception as e:
            mylogger.error(f"Error while parsing {code}: {e}")
            results[code] = None
        finally:
            await asyncio.sleep(random.uniform(1.0, 2.0))
    return results

async def parse_c108(code: str, page: Page) -> list[C108]:
    def extract_bullets(text: str | None) -> list[str]:
        if not text:
            return []
        return [
            line.replace("▶", "").strip()
            for line in text.splitlines()
            if line.strip().startswith("▶")
        ]

    url = f"https://navercomp.wisereport.co.kr/v2/company/c1080001.aspx?cn=&cmp_cd={code}"

    page.set_default_timeout(10000)
    print(f"Fetching c108 / {code} from {url}")
    await page.goto(url, timeout=10000)
    mylogger.debug(f"페이지 제목: {await page.title()}")
    await asyncio.sleep(2)

    # 제목 검사로 페이지 비정상 여부 판단
    title = await page.title()
    if '접속장애' in title:
        mylogger.warning(f"c108 스크랩 에러 - {title}")
        return []

    table_locator = page.locator("#tableCmpDetail")
    mylogger.debug((await table_locator.inner_html())[:100])

    """# 모든 행과 열, 넓은 컬럼 출력 허용
    pd.set_option('display.max_rows', None)  # 행 전체 보기
    pd.set_option('display.max_columns', None)  # 열 전체 보기
    pd.set_option('display.width', None)  # 한 줄에 다 출력
    pd.set_option('display.max_colwidth', None)  # 각 셀의 내용 전체 보기"""

    try:
        df = await helper.get_df_from_table(table_locator)
        df.rename(columns={'일자': '날짜'}, inplace=True)
        df['날짜'] = pd.to_datetime(df['날짜'], format="%y/%m/%d")
        df['날짜'] = df['날짜'].dt.strftime("%Y.%m.%d")
        mylogger.debug(df)
    except Exception as e:
        mylogger.error(f"테이블 파싱 실패: {e}")
        return []

    row_count = df.shape[0]
    mylogger.debug(f"행의 개수: {row_count}")

    contents = []
    for i in range(row_count):
        try:
            # 각 행의 제목을 클릭
            await page.locator(f"#a{i}").click()

            # 내용이 나타나길 기다렸다가 텍스트를 스크랩함.
            await page.wait_for_selector(f"#c{i} > div > div.comment-body", state="attached")
            text = await page.locator(f"#c{i} > div > div.comment-body").inner_text()
            mylogger.debug(f"raw content: {text}")

            # 내용 항목을 정리하고 리스트로 저장함.
            content_one = extract_bullets(text)
            mylogger.debug(f"content: {content_one}")
        except Exception as e:
            mylogger.warning(f"내용 추출 실패 (index {i}): {e}")
            content_one = []
        contents.append(content_one)

    df['내용'] = contents
    mylogger.debug(df)

    records = df.replace({np.nan: None}).to_dict(orient="records")
    for record in records:
        record['코드'] = code
    return [C108(**item) for item in records]

async def parse_c108_many(codes: list[str], page:Page) -> list[C108 | None]:
    results: list[C108|None] = []

    for code in codes:
        print(f"Parsing.. {code} / c108")
        try:
            result = await parse_c108(code, page)
            results.extend(result)
        except Exception as e:
            mylogger.error(f"Error while parsing {code}: {e}")
            results.append(None)
        finally:
            await asyncio.sleep(random.uniform(1.0, 2.0))
    return results
