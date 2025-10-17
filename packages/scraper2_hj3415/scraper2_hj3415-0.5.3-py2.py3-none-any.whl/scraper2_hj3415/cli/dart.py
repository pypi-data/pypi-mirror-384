# 항상 모든 모듈의 처음에 선언해야 환경변수를 문제없이 사용할수 있다.
#from setup_env.env import *
#setup_env()

import argparse
import asyncio
import json
import os

from ..scraper import dart
from db2_hj3415.nfs import dart as db_dart

async def save_today_darts(data_from_file=False):
    if data_from_file:
        file_path = dart.OverView.SAVE_FILENAME
        print(f"공시 데이터를 {file_path} 파일에서 가져옵니다.")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일이 존재하지 않습니다: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as file:
            raw_data = json.load(file)
    else:
        print(f"오늘의 Dart data를 얻어옵니다.")
        raw_data = dart.OverView().get(save_to_file=True)

    print(f"총 {len(raw_data)}개의 데이터가 수집되었습니다.")

    print("원본 데이터에서 후처리를 시행합니다...")
    cleaned_data = dart.PostProcess.all_in_one(raw_data)

    result = await db_dart.save_many(cleaned_data)
    print(f"저장 결과: {len(cleaned_data)}건 삽입됨")


def main():
    parser = argparse.ArgumentParser(description="Dart Commands")
    subparsers = parser.add_subparsers(dest='command', help='명령어', required=True)

    save_parser = subparsers.add_parser('save', help='공시 저장')
    save_parser.add_argument('--from-file', action='store_true', help='파일에서 JSON 데이터를 불러옴')

    args = parser.parse_args()

    match args.command:
        case 'save':
            try:
                async def run_save():
                    await save_today_darts(data_from_file=args.from_file)
                asyncio.run(run_save())
            except Exception as e:
                import sys
                print(f'실행 중 오류 발생: {e}', file=sys.stderr)
        case _:
            parser.print_help()