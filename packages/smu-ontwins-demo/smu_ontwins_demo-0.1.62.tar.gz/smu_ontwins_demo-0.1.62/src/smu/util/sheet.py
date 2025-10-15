from google.colab import auth
from google.auth import default
from googleapiclient.discovery import build

import gspread
from gspread_dataframe import set_with_dataframe, get_as_dataframe
import pandas as pd
import re

gc = None
drive = None

def access_google():
    """Colab에서 구글 인증 + gspread/Drive 준비 (쓰기 가능 스코프)"""
    global gc, drive
    auth.authenticate_user()

    creds, _ = default()
    # 쓰기 가능 스코프로 보강 (폴더/스프레드시트 생성 위해 필요)
    if getattr(creds, "requires_scopes", False) and creds.requires_scopes:
        creds = creds.with_scopes([
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets",
        ])

    gc = gspread.authorize(creds)
    drive = build("drive", "v3", credentials=creds)

def open_sheet_by_path(path: str, title: str, *, convert_excel: bool = True, trash_excel: bool = True):
    """
    path: '내 드라이브' 기준 폴더 경로 (예: "SMU_OnTwins_Demo/settings")
    title: 스프레드시트 '제목' (확장자 없이!)  예: "데피니션"
    convert_excel: 같은 폴더의 'title.xlsx' 엑셀이 있으면 구글시트로 변환해서 사용
    trash_excel: 변환 후 원본 엑셀을 휴지통으로 보낼지 여부
    returns: gspread Spreadsheet
    """
    assert gc is not None and drive is not None, "access_google() 먼저 호출하세요."
    parent = "root"

    # 1) 폴더 체인 보장
    for part in filter(None, path.split("/")):
        res = drive.files().list(
            q=("mimeType='application/vnd.google-apps.folder' "
               f"and name='{part}' and '{parent}' in parents and trashed=false"),
            fields="files(id,name)", pageSize=1
        ).execute()
        files = res.get("files", [])
        if files:
            parent = files[0]["id"]
        else:
            created = drive.files().create(
                body={
                    "name": part,
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [parent],
                },
                fields="id,name"
            ).execute()
            parent = created["id"]

    # 2) 네이티브 구글시트 먼저 찾기 (title 또는 title+".xlsx"로 저장된 경우 모두 허용)
    q_sheet = (
        f"mimeType='application/vnd.google-apps.spreadsheet' and "
        f"('{parent}' in parents) and trashed=false and "
        f"(name='{title}' or name='{title}.xlsx')"
    )
    res = drive.files().list(q=q_sheet, fields="files(id,name)", pageSize=1).execute()
    sheet_files = res.get("files", [])
    if sheet_files:
        sid = sheet_files[0]["id"]
        return gc.open_by_key(sid)

    # 3) 없으면 엑셀(.xlsx) 존재 여부 확인
    q_xlsx = (
        f"mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' and "
        f"'{parent}' in parents and trashed=false and name='{title}.xlsx'"
    )
    res = drive.files().list(q=q_xlsx, fields="files(id,name)", pageSize=1).execute()
    xlsx_files = res.get("files", [])

    if xlsx_files and convert_excel:
        xlsx_id = xlsx_files[0]["id"]
        # 엑셀 → 구글시트로 변환(복사)
        converted = drive.files().copy(
            fileId=xlsx_id,
            body={
                "name": title,  # 혼동 방지를 위해 확장자 없이
                "mimeType": "application/vnd.google-apps.spreadsheet",
                "parents": [parent],
            },
            fields="id,name"
        ).execute()
        if trash_excel:
            # 원본 엑셀은 휴지통으로
            drive.files().update(fileId=xlsx_id, body={"trashed": True}).execute()
        return gc.open_by_key(converted["id"])

    # 4) 아무것도 없으면 네이티브 구글시트 새로 만들기
    created = drive.files().create(
        body={
            "name": title,
            "mimeType": "application/vnd.google-apps.spreadsheet",
            "parents": [parent],
        },
        fields="id,name"
    ).execute()
    return gc.open_by_key(created["id"])


def load_settings(path: str, title: str):
    sh = open_sheet_by_path(path, title)
    df_goods = _load_goods(sh)
    df_exp_2023 = _load_expectation_2023(sh)
    df_exp_2024 = _load_expectation_2024(sh)
    df_exp_2025 = _load_expectation_2025(sh)
    _delete_sheet1_if_empty(sh)
    return df_goods, df_exp_2023, df_exp_2024, df_exp_2025

def _delete_sheet1_if_empty(sh) -> bool:
    """
    첫 번째 시트(sh.sheet1)가 완전히 비어 있고,
    통합문서에 시트가 2개 이상일 때만 삭제.
    삭제했으면 True, 아니면 False 반환.
    """
    ws = sh.sheet1

    # 시트가 1개뿐이면 삭제 불가(구글시트 제약)
    if len(sh.worksheets()) <= 1:
        return False

    # 값 존재 여부 체크: 모든 셀이 비어 있으면 get_all_values()는 빈 리스트/빈 행들
    values = ws.get_all_values()
    has_any_value = any(any(cell not in ("", None) for cell in row) for row in values)

    if not has_any_value:
        sh.del_worksheet(ws)
        return True
    return False

def _load_worksheet(sh, title, HEADERS, df, index = None) -> pd.DataFrame:
    try:
        ws = sh.worksheet(title)
        created = False
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=title, rows=10, cols=len(HEADERS))
        created = True

    if created:
        # 헤더 포함으로 기록
        set_with_dataframe(
            ws, df,
            include_index=False,
            include_column_header=True,
            resize=True,     # 시트 크기를 DF에 맞춰 조정
        )
        return df

    # ---- 기존 시트가 있는 경우: 로드 + 헤더 검증만 ----
    # 첫 행을 헤더로 읽어오기
    df = get_as_dataframe(
        ws,
        evaluate_formulas=True,
        header=0,
        dtype=None
    )

    # 완전 빈 행/열 제거 (사용자가 넓게 써놓았을 수 있음)
    df = df.dropna(how="all").dropna(axis=1, how="all")

    actual_headers = [str(c) for c in df.columns.tolist()]
    if actual_headers != HEADERS:
        raise ValueError(f"'{title}' 시트의 형식이 잘못되었습니다.\n\n기대={HEADERS}\n실제={actual_headers}")

    if index is not None:
        df.set_index(index, inplace=True, drop=False)
    return df

def _save_worksheet(sh, title, df: pd.DataFrame, include_index=False):
    try:
        ws = sh.worksheet(title)
        created = False
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=title, rows=10, cols=len(df.columns))
        created = True

    # 헤더 포함으로 기록
    set_with_dataframe(
        ws, df,
        include_index=include_index,
        include_column_header=True,
        resize=True,
    )
    return created

def _load_goods(sh) -> pd.DataFrame:
    HEADERS = ["품명", "분류", "가격", "주문당 수량 기대값"]
    df = pd.DataFrame(
        [
            {"품명": "젖병",   "분류": "육아용품", "가격": 13900, "주문당 수량 기대값": 1},
            {"품명": "턱받이", "분류": "육아용품",  "가격": 7500, "주문당 수량 기대값": 1},
            {"품명": "분유",   "분류": "육아용품", "가격": 24000, "주문당 수량 기대값": 2},
            {"품명": "입마개", "분류": "펫용품",   "가격": 12500, "주문당 수량 기대값": 1},
            {"품명": "사료",   "분류": "펫용품",  "가격": 18900, "주문당 수량 기대값": 2},
        ],
        columns=HEADERS,
    )
    return _load_worksheet(sh, "상품", HEADERS, df, index="품명")

def _load_expectation_2023(sh) -> pd.DataFrame:
    HEADERS = ["품명", "1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"]
    df = pd.DataFrame(
        [
            {"품명": "젖병", "1월": 273, "2월": 299, "3월": 308, "4월": 354, "5월": 312, "6월": 296, "7월": 240, "8월": 192, "9월": 164, "10월": 163, "11월": 154, "12월": 205},
            {"품명": "턱받이", "1월": 292, "2월": 297, "3월": 375, "4월": 251, "5월": 326, "6월": 309, "7월": 289, "8월": 240, "9월": 247, "10월": 253, "11월": 330, "12월": 223},
            {"품명": "분유", "1월": 247, "2월": 252, "3월": 229, "4월": 221, "5월": 154, "6월": 146, "7월": 146, "8월": 184, "9월": 231, "10월": 241, "11월": 268, "12월": 276},
            {"품명": "입마개", "1월": 253, "2월": 214, "3월": 245, "4월": 239, "5월": 203, "6월": 176, "7월": 218, "8월": 184, "9월": 166, "10월": 163, "11월": 161, "12월": 144},
            {"품명": "사료", "1월": 240, "2월": 298, "3월": 233, "4월": 267, "5월": 278, "6월": 314, "7월": 365, "8월": 271, "9월": 280, "10월": 399, "11월": 322, "12월": 373},
        ],
        columns=HEADERS,
    )
    return _load_worksheet(sh, "2023_기대값", HEADERS, df, index="품명")

def _load_expectation_2024(sh) -> pd.DataFrame:
    HEADERS = ["품명", "1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"]
    df = pd.DataFrame(
        [
            {"품명": "젖병", "1월": 251, "2월": 269, "3월": 331, "4월": 378, "5월": 317, "6월": 296, "7월": 246, "8월": 206, "9월": 176, "10월": 135, "11월": 156, "12월": 179},
            {"품명": "턱받이", "1월": 250, "2월": 210, "3월": 177, "4월": 191, "5월": 208, "6월": 246, "7월": 219, "8월": 143, "9월": 165, "10월": 177, "11월": 169, "12월": 144},
            {"품명": "분유", "1월": 290, "2월": 290, "3월": 249, "4월": 219, "5월": 265, "6월": 303, "7월": 336, "8월": 314, "9월": 326, "10월": 328, "11월": 335, "12월": 325},
            {"품명": "입마개", "1월": 143, "2월": 131, "3월": 84, "4월": 113, "5월": 119, "6월": 59, "7월": 101, "8월": 71, "9월": 76, "10월": 122, "11월": 131, "12월": 145},
            {"품명": "사료", "1월": 358, "2월": 341, "3월": 337, "4월": 400, "5월": 415, "6월": 416, "7월": 353, "8월": 447, "9월": 418, "10월": 392, "11월": 431, "12월": 475},
        ],
        columns=HEADERS,
    )
    return _load_worksheet(sh, "2024_기대값", HEADERS, df, index="품명")

def _load_expectation_2025(sh) -> pd.DataFrame:
    HEADERS = ["품명", "1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"]
    df = pd.DataFrame(
        [
            {"품명": "젖병", "1월": 267, "2월": 332, "3월": 326, "4월": 396, "5월": 312, "6월": 274, "7월": 263, "8월": 226, "9월": 159, "10월": 152, "11월": 168, "12월": 199},
            {"품명": "턱받이", "1월": 133, "2월": 153, "3월": 108, "4월": 156, "5월": 52, "6월": 71, "7월": 91, "8월": 83, "9월": 46, "10월": 0, "11월": 63, "12월": 44},
            {"품명": "분유", "1월": 284, "2월": 239, "3월": 266, "4월": 248, "5월": 233, "6월": 229, "7월": 238, "8월": 208, "9월": 188, "10월": 172, "11월": 150, "12월": 150},
            {"품명": "입마개", "1월": 171, "2월": 178, "3월": 185, "4월": 198, "5월": 180, "6월": 198, "7월": 226, "8월": 293, "9월": 256, "10월": 268, "11월": 285, "12월": 284},
            {"품명": "사료", "1월": 410, "2월": 516, "3월": 397, "4월": 513, "5월": 498, "6월": 445, "7월": 493, "8월": 576, "9월": 560, "10월": 548, "11월": 499, "12월": 527},
        ],
        columns=HEADERS,
    )
    return _load_worksheet(sh, "2025_기대값", HEADERS, df, index="품명")

def save_orders(path: str, title: str, dfs: dict[str, pd.DataFrame]):
    sh = open_sheet_by_path(path, title)
    for sheet_name, df in dfs.items():
        _save_worksheet(sh, sheet_name, df)
    _delete_sheet1_if_empty(sh)

def load_sim_settings(path: str, title: str, year: int, month: int = None):
    sh = open_sheet_by_path(path, title)
    month = _last_month_number(sh) if month is None else month

    df_goods = _load_goods(sh)
    df_init_stocks = _load_init_stock(sh, month)
    _delete_sheet1_if_empty(sh)

    co = open_sheet_by_path(path, "customer_orders")
    df_customer_orders = _load_worksheet(co, f"{year}", ["datetime", "product", "quantity"], pd.DataFrame(columns=["datetime", "product", "quantity"]))
    _delete_sheet1_if_empty(co)

    so = open_sheet_by_path(path, "supply_orders")
    df_supply_orders = _load_supply_order(so, month)
    _delete_sheet1_if_empty(so)

    return df_goods, df_init_stocks, df_customer_orders, df_supply_orders, month

def _last_month_number(sh, default: int = 1) -> int:
    """시트 제목 중 '01월', '1월', '03월내역' 같은 것들에서 월 숫자 최댓값을 반환.
    없으면 default 반환."""
    titles = [ws.title for ws in sh.worksheets()]
    months = []
    for t in titles:
        m = re.search(r'(\d{1,2})\s*월', t)  # 앞에 1~2자리 숫자 + '월'
        if m:
            n = int(m.group(1))
            if 1 <= n <= 12:
                months.append(n)
    return max(months) if months else default

def _load_init_stock(sh, month) -> pd.DataFrame:
    HEADERS = ["품명", "수량", "평균 에이징 일수"]
    df = pd.DataFrame(
        [
            {"품명": "젖병", "수량": 0, "평균 에이징 일수": 0},
            {"품명": "턱받이", "수량": 0, "평균 에이징 일수": 0},
            {"품명": "분유", "수량": 0, "평균 에이징 일수": 0},
            {"품명": "입마개", "수량": 0, "평균 에이징 일수": 0},
            {"품명": "사료", "수량": 0, "평균 에이징 일수": 0},
        ],
        columns=HEADERS,
    )
    return _load_worksheet(sh, f"{month:02d}월", HEADERS, df, index="품명")

def _load_supply_order(sh, month) -> pd.DataFrame:
    HEADERS = ["품명", "수량", "보관우선순위"]
    df = pd.DataFrame(
        [
            {"품명": "젖병", "수량": 0, "보관우선순위": 0},
            {"품명": "턱받이", "수량": 0, "보관우선순위": 0},
            {"품명": "분유", "수량": 0, "보관우선순위": 0},
            {"품명": "입마개", "수량": 0, "보관우선순위": 0},
            {"품명": "사료", "수량": 0, "보관우선순위": 0},
        ],
        columns=HEADERS,
    )
    return _load_worksheet(sh, f"{month:02d}월", HEADERS, df, index="품명")

def save_next_init(path: str, title: str, month: int, df: pd.DataFrame):
    sh = open_sheet_by_path(path, title)
    _save_worksheet(sh, f"{month:02d}월", df, True)
    _delete_sheet1_if_empty(sh)
