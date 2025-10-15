import numpy as np
import pandas as pd
import re
from datetime import date, datetime as dt, timedelta

def simulate_customer_orders(
    products,
    year=2025,
    *,
    monthly_qty_means_df=None,     # index=상품, columns=월(1..12 또는 '1월' 등 숫자 포함 문자열) → 각 월의 '총 수량 기대값'
    qty_by_order_means_df=None,    # index=상품, 단일 컬럼 → 그 상품의 '주문당 수량 기대값'(연중 동일)
    weekend_scale=0.8,             # 토/일 가중치(월별 합계 기대값은 보존)
    peak_hours=(11, 15, 20),       # 하루 내 수요 피크 시각(시)
    peak_weights=(0.35, 0.40, 0.25),
    peak_sd_seconds=5400,          # 각 피크의 표준편차(초)
    seed=None,
):
    """
    월별 '총 수량 기대값'(상품×월)과 상품별 '주문당 수량 기대값'으로
    (datetime, product, quantity) 주문 레코드를 Poisson/ZTP 모형으로 시뮬레이션.

    핵심 아이디어
    -------------
    - 상품 p, 월 m에 대해 입력된 총 수량 기대값 Q[p,m]과 주문당 평균 μ[p]가 주어지면,
      ZTP의 평균 μ_eff[p] = μ[p] / (1 - exp(-μ[p])).
    - 그 달의 '주문 건수' 기대값 Λ_month[p,m] = Q[p,m] / μ_eff[p].
    - 달 내 각 날짜 d의 가중치 w_d(평일=1, 주말=weekend_scale)를 두고
      λ_{p,d} = Λ_month[p,m] * w_d / Σ(달 내 w)  → 일별 주문수 ~ Poisson(λ_{p,d}).
    - 각 주문의 수량 ~ ZTP(μ[p])  (최소 1개), 시간은 피크 혼합에서 생성.

    Returns
    -------
    pandas.DataFrame with columns ['datetime', 'product', 'quantity']
    """
    # ---------- helpers ----------
    def _to_month_int(x):
        s = str(x)
        m = re.search(r"\d+", s)
        if m:
            v = int(m.group())
            if 1 <= v <= 12:
                return v
        raise ValueError("월 라벨은 1~12 또는 '1월'과 같이 숫자를 포함해야 합니다.")

    def _pick_single_numeric_col(df):
        if not isinstance(df, pd.DataFrame):
            raise ValueError("DataFrame 형태여야 합니다.")
        if df.shape[1] == 1:
            return df.iloc[:, 0]
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if len(num_cols) == 1:
            return df[num_cols[0]]
        raise ValueError("단일(숫자) 컬럼의 DataFrame을 제공해주세요.")

    def _sample_ztp_poisson(rng, lam_arr):
        """lam_arr: 각 주문의 ZTP 파라미터 μ (array-like).
        Rejection sampling으로 0을 제거."""
        lam_arr = np.asarray(lam_arr, dtype=float)
        q = rng.poisson(lam_arr)
        mask = (q == 0)
        # 필요 시 반복 샘플
        while mask.any():
            q[mask] = rng.poisson(lam_arr[mask])
            mask = (q == 0)
        return q

    # ---------- validate inputs ----------
    products = list(products)
    if not products:
        raise ValueError("products가 비어 있습니다.")

    if monthly_qty_means_df is None:
        raise ValueError("monthly_qty_means_df를 제공하세요 (index=상품, columns=월별 총 수량 기대값).")
    if qty_by_order_means_df is None:
        raise ValueError("qty_by_order_means_df를 제공하세요 (index=상품, 단일 컬럼=주문당 수량 기대값).")

    # 월별 총 수량 기대값 테이블 정규화
    mqty = monthly_qty_means_df.copy()
    mqty.columns = [_to_month_int(c) for c in mqty.columns]
    missing_months = set(range(1, 13)) - set(mqty.columns)
    if missing_months:
        raise ValueError(f"monthly_qty_means_df에 누락된 월이 있습니다: {sorted(missing_months)} (1~12 모두 필요)")
    # 필요한 상품만 추출(없으면 오류)
    missing_prod = [p for p in products if p not in mqty.index]
    if missing_prod:
        raise ValueError(f"monthly_qty_means_df에 없는 상품: {missing_prod}")
    mqty = mqty.loc[products, list(range(1, 13))].astype(float).clip(lower=0.0)

    # 주문당 수량 기대값(단일 컬럼)
    mu_series = _pick_single_numeric_col(qty_by_order_means_df)
    missing_mu = [p for p in products if p not in mu_series.index]
    if missing_mu:
        raise ValueError(f"qty_by_order_means_df에 없는 상품: {missing_mu}")
    mu = mu_series.loc[products].astype(float).values
    if (mu <= 0).any():
        raise ValueError("주문당 수량 기대값은 양수여야 합니다.")

    # ZTP 평균 μ_eff
    mu_eff = mu / (1.0 - np.exp(-mu))  # shape=(n_products,)

    rng = np.random.default_rng(seed)
    rows = []

    # ---------- simulate ----------
    for pi, prod in enumerate(products):
        # 이 상품의 월별 총 수량 기대값(Q[p,1..12])과 μ_eff[p]
        Q_months = mqty.loc[prod].values  # shape=(12,)
        for month in range(1, 13):
            Q = float(Q_months[month - 1])
            if Q <= 0:
                continue

            # 월별 주문건수 기대값 Λ_month = Q / μ_eff
            Lambda_month = Q / float(mu_eff[pi])

            # 월의 날짜와 가중치
            first = date(year, month, 1)
            last = date(year + (month == 12), 1 if month == 12 else month + 1, 1) - timedelta(days=1)
            days = [first + timedelta(days=i) for i in range((last - first).days + 1)]
            w = np.array([weekend_scale if d.weekday() >= 5 else 1.0 for d in days], dtype=float)
            if w.sum() <= 0:
                w = np.ones_like(w)

            # 일별 주문수 λ 분배 및 샘플링
            lambdas_d = Lambda_month * (w / w.sum())
            daily_n = rng.poisson(lambdas_d)

            # 각 일자별 주문 생성
            for d, n in zip(days, daily_n):
                if n <= 0:
                    continue

                # 시간 생성: 피크 혼합
                ph = np.asarray(peak_hours, dtype=int)
                pw = np.asarray(peak_weights, dtype=float)
                pw = pw / pw.sum()
                comp = rng.choice(len(ph), size=n, p=pw)
                peak_sec = ph * 3600
                sd = np.full_like(peak_sec, int(peak_sd_seconds))
                secs = rng.normal(peak_sec[comp], sd[comp]).astype(int)
                secs = np.clip(secs, 0, 24 * 3600 - 1)
                dts = [dt.combine(d, dt.min.time()) + timedelta(seconds=int(s)) for s in secs]

                # 주문당 수량(ZTP) 샘플
                q = _sample_ztp_poisson(rng, np.full(n, mu[pi], dtype=float))

                rows.extend({"datetime": dts[i], "product": prod, "quantity": int(q[i])}
                            for i in range(n))

    df = pd.DataFrame(rows, columns=["datetime", "product", "quantity"])
    if not df.empty:
        df.sort_values("datetime", inplace=True)
        df.reset_index(drop=True, inplace=True)
    return df

from typing import Dict

def summarize_orders(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    주문 로그 df(datetime, product, quantity)를 요약합니다.

    Returns (dict of DataFrame)
    - 'monthly_qty':        [상품 x 1..12]  값=월별 총 주문 '수량' 합계
    - 'monthly_orders':     [상품 x 1..12]  값=월별 '주문 건수' (행 개수)
    - 'monthly_avg_qty':    [상품 x 1..12]  값=월별 주문당 평균 수량(= qty 합 / 주문 건수)
    - 'product_totals':     [상품 x (orders, qty)] 연간 총합 (건수/수량)
    - 'month_totals':       [월 x (orders, qty)] 월별 총합 (건수/수량)

    Notes
    - 월 컬럼은 1..12 고정으로 반환하며, 없는 달은 0으로 채웁니다.
    - quantity는 수치형이어야 합니다.
    """
    required = {"datetime", "product", "quantity"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"필수 컬럼이 없습니다: {missing}")

    d = df.copy()
    d["datetime"] = pd.to_datetime(d["datetime"], errors="raise")
    d["quantity"] = pd.to_numeric(d["quantity"], errors="raise")
    d["month"] = d["datetime"].dt.month

    # 상품 x 월 피벗: 총 '수량' 합
    monthly_qty = (
        d.pivot_table(index="product", columns="month", values="quantity", aggfunc="sum", fill_value=0)
        .reindex(columns=range(1, 12 + 1), fill_value=0)
        .sort_index(axis=1)
    )

    # 상품 x 월 피벗: '주문 건수'
    monthly_orders = (
        d.groupby(["product", "month"]).size().unstack(fill_value=0)
        .reindex(columns=range(1, 12 + 1), fill_value=0)
        .sort_index(axis=1)
    )

    # 상품 x 월: 주문당 평균 수량
    monthly_avg_qty = (monthly_qty / monthly_orders.replace(0, np.nan)).fillna(0)

    # 연간 총합(상품별)
    product_totals = pd.DataFrame({
        "orders": monthly_orders.sum(axis=1).astype(int),
        "qty": monthly_qty.sum(axis=1).astype(float)
    }).sort_values(["qty", "orders"], ascending=False)

    # 월별 총합
    month_totals = pd.DataFrame({
        "orders": monthly_orders.sum(axis=0).astype(int),
        "qty": monthly_qty.sum(axis=0).astype(float)
    }).rename_axis("month").reset_index()

    return {
        "monthly_qty": monthly_qty,
        "monthly_orders": monthly_orders,
        "monthly_avg_qty": monthly_avg_qty,
        "product_totals": product_totals,
        "month_totals": month_totals,
    }
