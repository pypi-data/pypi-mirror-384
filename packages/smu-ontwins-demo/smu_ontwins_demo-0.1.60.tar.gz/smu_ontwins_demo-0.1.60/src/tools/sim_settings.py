from pathlib import Path
import pandas as pd

products_label = ["품명", "분류", "가격", "주문당 수량 기대값"]
years_label = ["품명","1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]
init_label = ["품명","수량","평균 에이징 일수"]
so_label = ["품명","수량","보관우선순위"]
co_label = ["datetime","product","quantity"]

def prepare_sim_settings(keyword: str,
                     year: int,
                     month: int,
                     base_dir: str = "/content/drive/MyDrive"):
    """
    /content/drive/MyDrive/{keyword}/settings 폴더를 보장하고,
    각 연도에 대해 'co-setting-YYYY.csv'를 생성/로딩합니다.

    Returns
    -------
    (dfs, message, paths)
      - dfs: list[pd.DataFrame | None]  # years와 동일한 순서
      - message: 모든 경고/오류를 줄바꿈으로 합친 문자열(없으면 None)
      - paths: list[str]  # 파일 경로들
    """
    settings_dir = Path(base_dir) / keyword / "settings"
    sim_settings_dir = Path(base_dir) / keyword / "sim_settings"
    settings_dir.mkdir(parents=True, exist_ok=True)
    sim_settings_dir.mkdir(parents=True, exist_ok=True)

    dfs, paths, msgs = [], [], []

    # 인덱스 라벨과 컬럼 스키마를 함께 검사 (True면 "스키마 불일치")
    def _schema_mismatch(df: pd.DataFrame, index_label: str, expected_cols: list[str]) -> bool:
        index_ok  = (str(df.index.name) == str(index_label))
        cols_ok   = [str(c) for c in df.columns] == [str(c) for c in expected_cols]
        return not (index_ok and cols_ok)

    def _looks_like_expected_columns(df: pd.DataFrame, expected_cols: list[str]) -> bool:
        return [str(c) for c in df.columns] != [str(c) for c in expected_cols]

    def _prepare_product_setting():
        path = settings_dir / f"products-setting.csv"
        paths.append(str(path))

        if not path.exists():
            # 인덱스 포함 '빈 파일' 생성
            pd.DataFrame(columns=products_label).to_csv(path, index=False)
            dfs.append(pd.DataFrame())
            msgs.append(f"[알림] 파일이 없어 빈 파일을 만들었습니다: {path}")

        # 파일 읽기
        try:
            df = pd.read_csv(path, index_col=0)
            warn_bits = []
            if df.empty:
                warn_bits.append("데이터가 없음")
            if _schema_mismatch(df, index_label=products_label[0], expected_cols=products_label[1:]):
                warn_bits.append("잘못된 형식의 설정 파일")
            if warn_bits:
                msgs.append(f"[경고] {path} → {', '.join(warn_bits)}")
            dfs.append(df)
        except Exception as e:
            dfs.append(None)
            msgs.append(f"[오류] {path} 읽기 실패: {e}")

    def _prepare_init_setting():
        path = sim_settings_dir / f"{year}-{month}-init.csv"
        paths.append(str(path))

        if not path.exists():
            # 인덱스 포함 '빈 파일' 생성
            pd.DataFrame(columns=init_label).to_csv(path, index=False)
            dfs.append(pd.DataFrame())
            msgs.append(f"[알림] 파일이 없어 빈 파일을 만들었습니다: {path}")

        # 파일 읽기
        try:
            df = pd.read_csv(path, index_col=0)
            warn_bits = []
            if df.empty:
                warn_bits.append("데이터가 없음")
            if _schema_mismatch(df, index_label=init_label[0], expected_cols=init_label[1:]):
                warn_bits.append("잘못된 형식의 설정 파일")
            if warn_bits:
                msgs.append(f"[경고] {path} → {', '.join(warn_bits)}")
            dfs.append(df)
        except Exception as e:
            dfs.append(None)
            msgs.append(f"[오류] {path} 읽기 실패: {e}")

    def _prepare_so_setting():
        path = sim_settings_dir / f"{year}-{month}-so.csv"
        paths.append(str(path))

        if not path.exists():
            # 인덱스 포함 '빈 파일' 생성
            pd.DataFrame(columns=so_label).to_csv(path, index=False)
            dfs.append(pd.DataFrame())
            msgs.append(f"[알림] 파일이 없어 빈 파일을 만들었습니다: {path}")

        # 파일 읽기
        try:
            df = pd.read_csv(path, index_col=0)
            warn_bits = []
            if df.empty:
                warn_bits.append("데이터가 없음")
            if _schema_mismatch(df, index_label=so_label[0], expected_cols=so_label[1:]):
                warn_bits.append("잘못된 형식의 설정 파일")
            if warn_bits:
                msgs.append(f"[경고] {path} → {', '.join(warn_bits)}")
            dfs.append(df)
        except Exception as e:
            dfs.append(None)
            msgs.append(f"[오류] {path} 읽기 실패: {e}")

    def _prepare_co_setting():
        path = sim_settings_dir / f"co-{year}.csv"
        paths.append(str(path))

        if not path.exists():
            # 인덱스 포함 '빈 파일' 생성
            pd.DataFrame(columns=co_label).to_csv(path, index=False)
            dfs.append(pd.DataFrame())
            msgs.append(f"[알림] 파일이 없어 빈 파일을 만들었습니다: {path}")

        # 파일 읽기
        try:
            df = pd.read_csv(path)
            warn_bits = []
            if df.empty:
                warn_bits.append("데이터가 없음")
            if _looks_like_expected_columns(df, co_label):
                warn_bits.append("잘못된 형식의 설정 파일")
            if warn_bits:
                msgs.append(f"[경고] {path} → {', '.join(warn_bits)}")
            dfs.append(df)
        except Exception as e:
            dfs.append(None)
            msgs.append(f"[오류] {path} 읽기 실패: {e}")

    _prepare_product_setting()
    _prepare_init_setting()
    _prepare_so_setting()
    _prepare_co_setting()

    message = "\n".join(msgs) if msgs else None
    message = "설정값에 문제를 발견하여 더 이상 처리할 수 없습니다.\n\n" + message if message else None
    return dfs, message, paths
