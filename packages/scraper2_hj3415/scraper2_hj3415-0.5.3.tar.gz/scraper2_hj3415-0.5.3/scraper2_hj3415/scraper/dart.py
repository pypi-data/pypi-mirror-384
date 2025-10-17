import os
import time
import re
import json
import random
import requests

from db2_hj3415.nfs import Dart

from ..krx300 import krx300
from . import helper

from utils_hj3415 import noti  # 텔레그램 알림 전송용
from utils_hj3415 import setup_logger, tools

mylogger = setup_logger(__name__, 'WARNING')


class OverView:
    API_KEY=os.getenv('DART_API_KEY', "")
    BASE_URL = "https://opendart.fss.or.kr/api/list.json"
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SAVE_FILENAME = os.path.join(BASE_DIR, "dart_data.json")
    MAX_RETRIES = 3

    report_nm_types = {
        'A': ['분기보고서', '반기보고서', '사업보고서'],
        'B': ['무상증자결정', '자기주식취득결정', '자기주식처분결정', '유상증자결정', '전환사채권발행결정',
              '신주인수권부사채권발행결정', '교환사채권발행결정', '회사합병결정', '회사분할결정'],
        'I': ['공급계약체결', '주식분할결정', '주식병합결정', '주식소각결정', '만기전사채취득', '신주인수권행사',
              '소송등의', '자산재평가실시결정', '현물배당결정', '주식배당결정', '매출액또는손익', '주주총회소집결의'],
        'D': ['공개매수신고서', '특정증권등소유상황보고서', '주식등의대량보유상황보고서'],
    }

    def __init__(self, sdate: str = "", edate: str = "", code: str = ""):
        self.sdate = sdate
        self.edate = edate
        self.code = code

    @property
    def sdate(self) -> str:
        return self._sdate

    @sdate.setter
    def sdate(self, sdate: str):
        assert helper.is_ymd_format(sdate) or sdate == "", "sdate 형식이 맞지 않습니다.(Ymd)"
        self._sdate = sdate

    @property
    def edate(self) -> str:
        return self._edate

    @edate.setter
    def edate(self, edate: str):
        assert helper.is_ymd_format(edate) or edate == "", "edate 형식이 맞지 않습니다.(Ymd)"
        self._edate = edate

    @property
    def code(self) -> str:
        return self._code

    @code.setter
    def code(self, code: str):
        assert tools.is_6digit(code) or code == "", "code 형식이 맞지 않습니다.(6자리 숫자 문자열)"
        self._code = code

    @staticmethod
    def ping_opendart(date: str | None = None, timeout: int = 5) -> tuple[str, str]:
        if date is None:
            from datetime import datetime
            date = datetime.now().strftime('%Y%m%d')
        assert helper.is_ymd_format(date), "날짜 형식은 Ymd여야 합니다."

        try:
            url = f"{OverView.BASE_URL}?crtfc_key={OverView.API_KEY}&end_de={date}"
            res = requests.get(url, timeout=timeout, headers={'User-Agent': tools.get_random_user_agent()}).json()
            return res.get('status', '900'), res.get('message', '알 수 없는 에러')
        except requests.RequestException:
            return '900', "Connection Error on opendart.fss.or.kr"

    def _build_query_string(self, last_report: str = "N", page_no: int = 1) -> str:
        assert last_report in ['Y', 'N'], "last_report는 'Y' 또는 'N'이어야 합니다."
        params = {
            "crtfc_key": OverView.API_KEY,
            "last_reprt_at": last_report,
            "page_no": page_no,
            "page_count": 100,
        }
        if self.sdate:
            params["bgn_de"] = self.sdate
        if self.edate:
            params["end_de"] = self.edate
        if self.code:
            params["corp_code"] = self.code

        return "&".join(f"{k}={v}" for k, v in params.items())

    def _make_url(self, last_report="N", page_no=1) -> str:
        return f"{self.BASE_URL}?{self._build_query_string(last_report, page_no)}"

    def fetch_page(self, url: str) -> list[dict[str, str]]:
        for attempt in range(self.MAX_RETRIES):
            try:
                mylogger.debug(f"Fetching: {url}")
                r = requests.get(url, timeout=(10, 30), headers={'User-Agent': tools.get_random_user_agent()})
                return r.json().get("list", [])
            except requests.RequestException as e:
                mylogger.warning(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(2)
        return []

    def get(self, save_to_file: bool = False) -> list[dict[str, str]]:
        if OverView.API_KEY == "":
            mylogger.warning("DART_API_KEY가 설정되지 않았습니다. 작업을 종료합니다.")
            return []

        full_url = self._make_url()
        res = requests.get(full_url, headers={'User-Agent': tools.get_random_user_agent()}).json()

        total_overviews = []

        if res.get('status') == '000':
            total_page = int(res.get('total_page', 1))
            print(f"총 {total_page} 페이지 추출 시작")

            for i in range(total_page):
                url = re.sub(r"&page_no=\d+", f"&page_no={i+1}", full_url)
                if i != 0:
                    sec = random.randint(8, 12)
                    print(f"Sleep for {sec} seconds...")
                    time.sleep(sec)
                total_overviews.extend(self.fetch_page(url))

        elif res.get('status') == '013':
            print("조회된 데이터가 없습니다.")
        else:
            noti.telegram_to(botname='dart', text=res.get('message', '정의되지 않은 오류'))

        if save_to_file:
            with open(self.SAVE_FILENAME, 'w', encoding='utf-8') as f:
                json.dump(total_overviews, f, ensure_ascii=False, indent=2)

        return total_overviews


class PostProcess:
    USELESS_TITLES = ['기재정정', '첨부정정', '자회사의', '종속회사의', '기타경영사항', '첨부추가']

    @staticmethod
    def all_in_one(overviews: list[dict[str, str]]) -> list[Dart]:
        """
        종합 후처리 함수.
        - 문서 링크 추가
        - 보고서 제목 공백 제거
        - KOSPI/KOSDAQ 종목만 필터링
        - krx300 종목 코드에 해당하는 항목만 필터링
        """
        codes = krx300.get_codes()

        cleaned_data: list[Dart] = PostProcess._to_dart_models(
            PostProcess._filtering_title(
                PostProcess._gathering_by_code(
                    PostProcess._gathering_kospi_kosdaq(
                        PostProcess._normalize_title(
                            PostProcess._add_doc_link(overviews)
                        )
                    )
                ,codes)
            ,PostProcess.USELESS_TITLES)
        )

        mylogger.debug(cleaned_data)
        return cleaned_data

    @staticmethod
    def _add_doc_link(overviews: list[dict[str, str]]) -> list[dict[str, str]]:
        """
        각 공시 항목에 'link' 키를 추가하여 문서 링크를 포함시킨다.
        """
        header = 'http://dart.fss.or.kr/dsaf001/main.do?rcpNo='
        for item in overviews:
            item['link'] = header + item['rcept_no']
        return overviews

    @staticmethod
    def _normalize_title(overviews: list[dict[str, str]]) -> list[dict[str, str]]:
        """
        각 공시 제목(report_nm)의 좌우 공백을 제거하고, 중간의 다중 공백을 하나로 정리한다.
        """
        for item in overviews:
            title = item.get('report_nm', '')
            refined = re.sub(r'\s+', ' ', title.strip())
            item['report_nm'] = refined
        return overviews

    @staticmethod
    def _gathering_kospi_kosdaq(overviews: list[dict[str, str]]) -> list[dict[str, str]]:
        """
        코스피(Y), 코스닥(K) 시장에 해당하는 공시만 필터링하여 반환한다.
        """
        return [item for item in overviews if item['corp_cls'] in {'K', 'Y'}]

    @staticmethod
    def _gathering_by_code(overviews: list[dict[str, str]], codes: list[str]) -> list[dict[str, str]]:
        """
        stock_code가 제공된 코드 리스트(codes)에 포함되는 항목만 필터링한다.
        """
        code_set = set(codes)  # O(1) 검색을 위해 set 사용
        return [item for item in overviews if item['stock_code'] in code_set]

    @staticmethod
    def _filtering_title(overviews: list[dict[str, str]], filtering_words: list[str]) -> list[dict[str, str]]:
        result = []
        for item in overviews:
            raw_title = item.get("report_nm", "")
            clean_title = raw_title.replace(" ", "")
            if not any(word in clean_title for word in filtering_words):
                result.append({**item, "report_nm": clean_title})
        return result

    @staticmethod
    def _to_dart_models(overviews: list[dict[str, str]]) -> list[Dart]:
        return [Dart(**item) for item in overviews]