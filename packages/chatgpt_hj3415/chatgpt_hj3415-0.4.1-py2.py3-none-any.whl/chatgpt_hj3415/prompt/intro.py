from db2_hj3415.nfs import c101
from .by_nfs import extract_code
from datetime import datetime, timedelta, timezone


KST = timezone(timedelta(hours=9))

def _date_range_last_year() -> tuple[str, str]:
    end = datetime.now(KST).date()
    start = end - timedelta(days=365)
    return start.isoformat(), end.isoformat()

async def _build_chatgpt_prompt(ticker: str) -> str:
    name = await c101.get_name(extract_code(ticker))

    start_date, end_date = _date_range_last_year()
    today = datetime.now(KST).date().isoformat()
    display_name = f"{ticker} {name}".strip()

    return (
        f"너는 한국어 사용 애널리스트다. 지금 날짜는 {today}(Asia/Seoul)다.\n"
        f"대상: {display_name}\n\n"
        "요구:\n"
        f"1) 간단한 기업개요:\n"
        "   - 정식 회사명(한글/영문), 설립일, 상장일, 본사 위치, 주요 경영진\n"
        "   - 핵심 사업(주요 제품 및 서비스) 2~3줄 요약\n"
        "   - 상장 시장, 시가총액(기준일 명시), 직원 수(가능하다면)\n"
        "   - 위 항목 중 데이터가 없으면 '미확인'으로 표기\n"
        f"2) 가장 마지막 데이터 기준으로 ‘사업부문별 매출과 비중’을 표로 제시:\n"
        "   - 컬럼: 사업부명 | 매출(KRW 억) | 비중(%) | 기준기간(yyyy-mm)\n"
        "   - 출처 없는 수치는 생성 금지. 구간이 다르면 각 행에 기간 명시.\n"
        "3) 최근 1년 ‘주요 동향’(M&A/신사업/주요 계약/공장 증설 등) 5줄 이내 불릿 요약:\n"
        "   - 각 항목에 발생일(yyyy-mm-dd)과 간단한 영향(매출/마진/CAPEX 등) 포함.\n"
        "4) 맨 끝에 ‘출처’ 섹션:\n"
        "   - [1], [2] 형식 번호 매기고, 제목 요약 + URL. 최근 순으로 정렬.\n\n"
        "규칙:\n"
        " - 모든 날짜는 절대날짜(yyyy-mm-dd)로.\n"
        " - 확실치 않으면 “미확인/추정(근거: [n])” 표기.\n"
        " - 숫자는 천 단위 구분 없이 정수 또는 한 자리 소수.\n"
        " - 표/불릿 외 불필요한 서론 금지.\n"
    )

async def get_prompt(ticker:str) -> list[dict]:
    content = await _build_chatgpt_prompt(ticker)

    return [
        {"role": "system",
         "content": "너의 역할은 한국어 사용 기술·기업 애널리스트다."
                    "사실성, 근거, 날짜 정확도를 최우선으로 하고, 요청한 형식만 출력하라."},
        {"role": "user",
         "content": content},
    ]