# 항상 모든 모듈의 처음에 선언해야 환경변수를 문제없이 사용할수 있다.
#from setup_env.env import *
#setup_env()

import argparse
import asyncio

from playwright.async_api import async_playwright

from db2_hj3415.mi import sp500, kospi, kosdaq, wti, usdkrw, silver, gold, gbond3y, chf, aud, usdidx

from ..scraper import mi_history as scraper_mi_history, mi as scraper_mi

PARSER_MAP = {
    'sp500': scraper_mi.parse_sp500,
    'kospi': scraper_mi.parse_kospi,
    'kosdaq': scraper_mi.parse_kosdaq,
    'wti': scraper_mi.parse_wti,
    'usdkrw': scraper_mi.parse_usdkrw,
    'usdidx': scraper_mi.parse_usdidx,
    'silver': scraper_mi.parse_silver,
    'gold': scraper_mi.parse_gold,
    'gbond3y': scraper_mi.parse_gbond3y,
    'chf': scraper_mi.parse_chf,
    'aud': scraper_mi.parse_aud
}

COL_FUNC_MAP = {
    'sp500': sp500.save,
    'kospi': kospi.save,
    'kosdaq': kosdaq.save,
    'wti': wti.save,
    'usdkrw': usdkrw.save,
    'usdidx': usdidx.save,
    'silver': silver.save,
    'gold': gold.save,
    'gbond3y': gbond3y.save,
    'chf': chf.save,
    'aud': aud.save,
}


HISTORY_PARSER_MAP = {
    'sp500': scraper_mi_history.parse_sp500,
    'kospi': scraper_mi_history.parse_kospi,
    'kosdaq': scraper_mi_history.parse_kosdaq,
    'wti': scraper_mi_history.parse_wti,
    'usdkrw': scraper_mi_history.parse_usdkrw,
    'silver': scraper_mi_history.parse_silver,
    'gold': scraper_mi_history.parse_gold,
    'gbond3y': scraper_mi_history.parse_gbond3y,
    'chf': scraper_mi_history.parse_chf,
    'aud': scraper_mi_history.parse_aud
}

HISTORY_COL_FUNC_MAP = {
    'sp500': sp500.save_history,
    'kospi': kospi.save_history,
    'kosdaq': kosdaq.save_history,
    'wti': wti.save_history,
    'usdkrw': usdkrw.save_history,
    'silver': silver.save_history,
    'gold': gold.save_history,
    'gbond3y': gbond3y.save_history,
    'chf': chf.save_history,
    'aud': aud.save_history,
}

def main():
    parser = argparse.ArgumentParser(description="Market Index Scraper CLI")
    subparsers = parser.add_subparsers(dest='command', help='명령어', required=True)

    save_parser = subparsers.add_parser('save', help='데이터 저장 실행')
    save_subparsers = save_parser.add_subparsers(dest='mode', required=True)

    save_subparsers.add_parser('today', help="오늘 데이터 저장")

    save_history = save_subparsers.add_parser('history', help="과거 데이터 저장")
    save_history.add_argument('col', type=str, help="컬렉션 이름 [sp500, kospi, kosdaq, wti, usdkrw, silver, gold, gbond3y, chf, aud]")
    save_history.add_argument('--years', type=int, default=1, help="저장할 과거 연도 수 (기본: 1년)")

    args = parser.parse_args()

    from scraper2_hj3415.scraper.helper import ensure_playwright_installed
    ensure_playwright_installed()

    match (args.command, args.mode):
        case ('save', 'today'):
            async def parsing():
                return await scraper_mi.parse_all()

            data = asyncio.run(parsing())

            async def save(data):
                for k, v in data.items():
                    save_func = COL_FUNC_MAP[k]
                    result = await save_func(v)
                    print(f"{k} : {result}")
            asyncio.run(save(data))

        case ('save', 'history'):
            col = args.col.lower()
            history_parser_func = HISTORY_PARSER_MAP.get(col)
            if not history_parser_func:
                print(f"지원하지 않는 컬렉션: {col}")
                return

            async def parsing():
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    data = await history_parser_func(page, args.years)
                await browser.close()
                return data

            data = asyncio.run(parsing())

            save_history_func = HISTORY_COL_FUNC_MAP.get(col)
            if not save_history_func:
                print(f"저장 함수가 등록되지 않음: {col}")
                return

            async def save(data):
                await save_history_func(data)

            asyncio.run(save(data))

        case _:
            print("지원하지 않는 명령입니다.")