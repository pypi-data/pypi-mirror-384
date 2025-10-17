# 항상 모든 모듈의 처음에 선언해야 환경변수를 문제없이 사용할수 있다.
#from setup_env.env import *
#setup_env()

import argparse
import asyncio

from playwright.async_api import async_playwright

from db2_hj3415.nfs import c101, c103, c104, c106, c108
from db2_hj3415.nfs import C101, C103, C104, C106, C108

from ..scraper import nfs
from ..krx300 import krx300

from utils_hj3415 import tools

# 공통 맵
PARSER_MAP = {
    'c101': nfs.parse_c101,
    'c103': nfs.parse_c103,
    'c104': nfs.parse_c104,
    'c106': nfs.parse_c106,
    'c108': nfs.parse_c108,
}

PARSER_MANY_MAP = {
    'c101': nfs.parse_c101_many,
    'c103': nfs.parse_c103_many,
    'c104': nfs.parse_c104_many,
    'c106': nfs.parse_c106_many,
    'c108': nfs.parse_c108_many,
}

COL_FUNC_MAP = {
    'c101': c101.save,
    'c103': c103.save,
    'c104': c104.save,
    'c106': c106.save,
    'c108': c108.save,
}

COL_FUNC_MANY_MAP = {
    'c101': c101.save_many,
    'c103': c103.save_many,
    'c104': c104.save_many,
    'c106': c106.save_many,
    'c108': c108.save,
}

T = C101 | C103 | C104 | C106 | list[C108] | None

async def parse_data(col: str, target: str) -> T:
    parser = PARSER_MAP.get(col)
    if not parser:
        raise ValueError(f"지원하지 않는 컬렉션: {col}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        data = await parser(target, page)
        await browser.close()
        return data


async def save_data(col: str, target: str, data: T):
    func = COL_FUNC_MAP.get(col)
    if not func:
        raise ValueError(f"저장 함수 없음: {col}")

    match col:
        case "c101" | "c108":
            result = await func(data)
        case "c103" | "c104" | "c106":
            result = await func(target, data)
        case _:
            raise ValueError(f"알 수 없는 컬렉션: {col}")
    print(result)

T_MANY = list[C101 | None] | dict[str, C103 | C104 | C106 | None] | list[C108 | None]

async def parse_many_data(col: str, targets: list[str]) -> T_MANY:
    parser_many = PARSER_MANY_MAP.get(col)
    if parser_many is None:
        raise ValueError(f"지원하지 않는 컬렉션: {col}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(
                user_agent=tools.get_random_user_agent(),
                locale="ko-KR"
            )
            page = await context.new_page()
            try:
                # ➜ 핵심 호출
                data: T_MANY = await parser_many(targets, page)
                return data
            finally:
                await page.close()
                await context.close()
        finally:
            await browser.close()


async def save_many_data(col: str, many_data: T_MANY):
    func = COL_FUNC_MANY_MAP.get(col)
    if not func:
        raise ValueError(f"저장 함수 없음: {col}")
    #print(many_data)
    result = await func(many_data)
    print(result)


def handle_save_command(col: str, target: str):
    if not tools.is_6digit(target):
        print(f"잘못된 코드: {target}")
        return

    async def main():
        data = await parse_data(col, target)
        await save_data(col, target, data)

    asyncio.run(main())


BATCH_SIZE = 10        # 한 번에 처리할 종목 수

def handle_save_many_command(col: str, targets: list[str]) -> None:
    """targets 를 BATCH_SIZE 단위로 잘라가며 파싱+저장"""

    # 1) 6자리 코드만 필터링
    valid = [code for code in targets if tools.is_6digit(code)]
    if not valid:
        print("유효한 종목 코드가 없습니다.")
        return

    async def main() -> None:
        # 2) 슬라이싱으로 간단하게 배치 반복
        for i in range(0, len(valid), BATCH_SIZE):
            batch = valid[i: i + BATCH_SIZE]  # ← 요 한 줄이 핵심
            print(f"Batch {i // BATCH_SIZE + 1}: {batch}")

            many_data = await parse_many_data(col, batch)
            await save_many_data(col, many_data)

            # (선택) 서버 부하를 줄이고 싶다면 잠깐 대기
            # await asyncio.sleep(0.2)

    asyncio.run(main())


def main():
    parser = argparse.ArgumentParser(description="Naver Financial Scraper CLI")
    subparsers = parser.add_subparsers(dest='command', help='명령어', required=True)

    # save 명령
    save_parser = subparsers.add_parser('save', help='데이터 저장 실행')
    save_parser.add_argument('col', type=str, help="컬렉션 이름 (예: c101, c103, c104, c106, c108)")
    save_parser.add_argument('targets', nargs='*', help="종목코드 (예: 005930, 000660... and all)")

    args = parser.parse_args()

    from scraper2_hj3415.scraper.helper import ensure_playwright_installed
    ensure_playwright_installed()

    if args.command == 'save':
        col = args.col.lower()
        if len(args.targets) == 1 and args.targets[0].lower() == "all":
            handle_save_many_command(col, krx300.get_codes())
        elif len(args.targets) == 1:
            handle_save_command(col, args.targets[0])
        else:
            handle_save_many_command(col, args.targets)

