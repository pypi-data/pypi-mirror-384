import asyncio
import pandas as pd
from playwright.async_api import Page

from utils_hj3415 import setup_logger
from . import helper


mylogger = setup_logger(__name__, 'WARNING')


async def parse_sp500(page: Page, years=1) -> pd.DataFrame:
    last_page = int(27 * years)
    url = 'https://finance.naver.com/world/sise.nhn?symbol=SPI@SPX'

    page.set_default_timeout(3000)
    print(f"Fetching sp500 from {url} - {last_page} pages")
    await page.goto(url, timeout=10000, wait_until="domcontentloaded")
    mylogger.debug(f"페이지 제목: {await page.title()}")
    await asyncio.sleep(2)

    paging_locator = page.locator("#dayPaging")
    await helper.wait_with_retry(paging_locator)
    paging_html = await paging_locator.inner_html()
    mylogger.debug(paging_html[:50])

    df_list = []

    i = 1
    while i <= last_page:
        link_id = f"#dayLink{i}"
        try:
            # 현재 페이지에 dayLink{i}가 존재할 때까지 대기
            await page.wait_for_selector(link_id, timeout=3000)
            await page.click(link_id)
            print(f"Clicked {link_id}")
            await asyncio.sleep(2)  # 페이지 로딩 대기 (혹은 wait_for_selector)

            try:
                table_locator = page.locator("#dayTable")
                await helper.wait_with_retry(table_locator)
                table_html = await table_locator.inner_html()
                mylogger.debug(table_html[:100])

                df = await helper.get_df_from_table(table_locator)
                df = df.dropna(how="all").reset_index(drop=True)  # 전부 NaN인 행 제거
                df.columns = ['날짜', '종가', '전일대비', '시가', '고가', '저가']
                mylogger.debug(df)

                if df.empty:
                    mylogger.warning("SP500 테이블이 비어있음")
                else:
                    df_list.append(df)
            except Exception as e:
                mylogger.error(f"SP500 테이블 파싱 실패: {e}")

            i += 1  # 정상 처리 후 증가

        except Exception as e:
            mylogger.warning(f"{link_id} 클릭 실패, 다음 버튼 시도: {e}")
            try:
                # "다음" 버튼 클릭
                next_button = page.locator("a.next")
                if await next_button.is_visible():
                    await next_button.click()
                    mylogger.info("Clicked next button for more page links")
                    await asyncio.sleep(2)  # 페이지 전환 대기
                    # i는 증가하지 않음 → 다시 시도
                else:
                    mylogger.warning("다음 버튼이 더 이상 없음")
                    break
            except Exception as next_err:
                mylogger.error(f"다음 버튼 클릭 실패: {next_err}")
                break

    result_df = pd.concat(df_list, ignore_index=True)
    mylogger.debug(result_df)
    mylogger.debug(result_df.shape)
    return result_df


async def parse_markets_type1(page: Page, market:str, url_prefix: str, last_page: int, columns: list | None, header: int | list, selector: str) -> pd.DataFrame:
    df_list = []
    for page_link in range(1, last_page + 1):
        url = url_prefix + str(page_link)
        page.set_default_timeout(3000)
        print(f"Fetching {market} from {url} - {last_page} pages")
        await page.goto(url, timeout=10000, wait_until="domcontentloaded")
        mylogger.debug(f"페이지 제목: {await page.title()}")
        await asyncio.sleep(2)

        try:
            table_locator = page.locator(selector)
            await helper.wait_with_retry(table_locator)
            table_html = await table_locator.inner_html()
            mylogger.debug(table_html[:100])

            df = await helper.get_df_from_table(table_locator, header)
            df = df.dropna(how="all").reset_index(drop=True)  # 전부 NaN인 행 제거
            if columns:
                df.columns = columns
            mylogger.debug(df)

            if df.empty:
                mylogger.warning(f"{market} 테이블이 비어있음")
            else:
                df_list.append(df)

        except Exception as e:
            mylogger.error(f"{market} 테이블 파싱 실패: {e}")

    result_df = pd.concat(df_list, ignore_index=True)
    mylogger.debug(result_df)
    mylogger.debug(result_df.shape)
    return result_df


async def parse_kospi(page: Page, years=1) -> pd.DataFrame:
    market = 'kospi'
    url_prefix = f'https://finance.naver.com/sise/sise_index_day.nhn?code=KOSPI&page='
    last_page = int(42 * years)
    columns = None
    header = 0
    selector = "table.type_1"
    df = await parse_markets_type1(page, market, url_prefix, last_page, columns, header, selector)
    df = df.rename(columns={
        "거래량(천주)": "거래량",
        "거래대금(백만)": "거래대금"
    })

    df["거래량"] *= 1_000  # 천주  → 주
    df["거래대금"] *= 1_000_000  # 백만  → 원(또는 해당 화폐 단위)

    return df


async def parse_kosdaq(page: Page, years=1) -> pd.DataFrame:
    market = 'kosdaq'
    url_prefix = f'https://finance.naver.com/sise/sise_index_day.nhn?code=KOSDAQ&page='
    last_page = int(42 * years)
    columns = None
    header = 0
    selector = "table.type_1"
    df = await parse_markets_type1(page, market, url_prefix, last_page, columns, header, selector)
    df = df.rename(columns={
        "거래량(천주)": "거래량",
        "거래대금(백만)": "거래대금"
    })

    df["거래량"] *= 1_000  # 천주  → 주
    df["거래대금"] *= 1_000_000  # 백만  → 원(또는 해당 화폐 단위)

    return df


async def parse_wti(page: Page, years=1) -> pd.DataFrame:
    market = 'wti'
    url_prefix = f'https://finance.naver.com/marketindex/worldDailyQuote.nhn?marketindexCd=OIL_CL&fdtc=2&page='
    last_page = int(38 * years)
    columns = ['날짜', '종가', '전일대비', '등략률']
    header = 0
    selector = "body > div > table"
    return await parse_markets_type1(page, market, url_prefix, last_page, columns, header, selector)


async def parse_usdkrw(page: Page, years=1) -> pd.DataFrame:
    market = 'usdkrw'
    url_prefix = f'https://finance.naver.com/marketindex/exchangeDailyQuote.nhn?marketindexCd=FX_USDKRW&page='
    last_page = int(26 * years)
    columns = ['날짜', '매매기준율', '전일대비', '현찰로 사실 때', '현찰로 파실 때', '송금 보내실 때', '송금 받으실 때']
    header = [0, 1]
    selector = "body > div > table"
    return await parse_markets_type1(page, market, url_prefix, last_page, columns, header, selector)


async def parse_silver(page: Page, years=1) -> pd.DataFrame:
    market = 'silver'
    url_prefix = f'https://finance.naver.com/marketindex/worldDailyQuote.nhn?marketindexCd=CMDT_SI&fdtc=2&page='
    last_page = int(38 * years)
    columns = ['날짜', '종가', '전일대비', '등략률']
    header = 0
    selector = "body > div > table"
    return await parse_markets_type1(page, market, url_prefix, last_page, columns, header, selector)


async def parse_gold(page: Page, years=1) -> pd.DataFrame:
    market = 'gold'
    url_prefix = f'https://finance.naver.com/marketindex/worldDailyQuote.nhn?marketindexCd=CMDT_GC&fdtc=2&page='
    last_page = int(38 * years)
    columns = ['날짜', '종가', '전일대비', '등략률']
    header = 0
    selector = "body > div > table"
    return await parse_markets_type1(page, market, url_prefix, last_page, columns, header, selector)


async def parse_gbond3y(page: Page, years=1) -> pd.DataFrame:
    market = 'gbond3y'
    url_prefix = f'https://finance.naver.com/marketindex/interestDailyQuote.nhn?marketindexCd=IRR_GOVT03Y&page='
    last_page = int(38 * years)
    columns = ['날짜', '종가', '전일대비', '등략률']
    header = 0
    selector = "body > div > table"
    return await parse_markets_type1(page, market, url_prefix, last_page, columns, header, selector)


async def parse_markets_type2(page: Page, market:str, url: str, last_page: int) -> pd.DataFrame:
    page.set_default_timeout(3000)
    print(f"Fetching {market} from {url} - {last_page} pages")
    await page.goto(url, timeout=10000, wait_until="domcontentloaded")
    mylogger.debug(f"페이지 제목: {await page.title()}")
    await asyncio.sleep(2)

    paging_locator = page.locator(".paging")
    await helper.wait_with_retry(paging_locator)
    paging_html = await paging_locator.inner_html()
    mylogger.debug(paging_html)

    df_list = []

    i = 1
    while i <= last_page:
        try:
            # 현재 페이지에서 텍스트가 i인 링크 찾기
            link_locator = page.locator(f'a:text("{i}")')

            await page.wait_for_selector(f'a:text("{i}")', timeout=3000)
            await link_locator.first.click()
            print(f"Clicked page {i}")
            await asyncio.sleep(2)  # 페이지 로딩 대기

            try:
                table_locator = page.locator("body > div > table")
                await helper.wait_with_retry(table_locator)
                table_html = await table_locator.inner_html()
                mylogger.debug(table_html[:100])

                df = await helper.get_df_from_table(table_locator, 0)
                df = df.dropna(how="all").reset_index(drop=True)  # 전부 NaN인 행 제거
                df.columns = ['날짜', '종가', '전일대비', '등략률']  # 열 이름 교체
                mylogger.debug(df)

                if df.empty:
                    mylogger.warning(f"{market} 테이블이 비어있음")
                else:
                    df_list.append(df)
            except Exception as e:
                mylogger.error(f"{market} 테이블 파싱 실패: {e}")

            i += 1  # 성공했으니 다음 페이지로 넘어감

        except Exception as e:
            mylogger.warning(f"{i}번 페이지 클릭 실패, 다음 버튼 시도: {e}")
            try:
                next_button = page.locator("a.next")
                if await next_button.is_visible():
                    await next_button.click()
                    mylogger.info("Clicked next button for more page links")
                    await asyncio.sleep(2)  # 페이지 전환 대기
                    # i는 증가하지 않음 → 다시 시도
                else:
                    mylogger.warning("다음 버튼이 더 이상 없음")
                    break
            except Exception as next_err:
                mylogger.error(f"다음 버튼 클릭 실패: {next_err}")
                break

    result_df = pd.concat(df_list, ignore_index=True)
    mylogger.debug(result_df)
    mylogger.debug(result_df.shape)
    return result_df


async def parse_chf(page: Page, years=1) -> pd.DataFrame:
    market = 'chf'
    url = f'https://finance.naver.com/marketindex/worldDailyQuote.nhn?fdtc=4&marketindexCd=FX_USDCHF'
    last_page = int(46 * years)
    return await parse_markets_type2(page, market, url, last_page)


async def parse_aud(page: Page, years=1) -> pd.DataFrame:
    market = 'aud'
    url = f'https://finance.naver.com/marketindex/worldDailyQuote.nhn?fdtc=4&marketindexCd=FX_USDAUD'
    last_page = int(46 * years)
    return await parse_markets_type2(page, market, url, last_page)

