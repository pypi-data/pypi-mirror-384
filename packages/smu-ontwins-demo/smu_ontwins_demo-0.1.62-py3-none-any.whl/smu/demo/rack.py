import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Union, List, Any

def hsl_for(product: str, products: set[str], qty: int, capa: int) -> str:
    # set은 순서가 없으므로, 정렬로 안정적인 인덱스를 만듭니다.
    items = sorted(products)
    if not items:
        raise ValueError("products가 비어 있습니다.")
    if product not in products:
        raise KeyError(f"{product!r} 가 products에 없습니다.")

    idx = items.index(product)
    n = len(items)
    hue = (360.0 * idx) / n          # 0 ≤ hue < 360
    return f"hsl({int(hue)}, 100%, {int(60+30*(1-qty/capa))}%)"

@dataclass
class RackConfig:
    racks: int = 2
    levels: int = 4
    cells_per_level: int = 4
    cell_capacity: int = 100
    rack_entities:List[Any] = field(default_factory=list)
    df_goods: pd.DataFrame = None

class Racks:
    def __init__(self, config: RackConfig):
        self.cfg = config
        self.state_df = pd.DataFrame(
            columns=["rack","level","cell","product","qty","capacity","utilization","mean_ts"]
        )
        self.discarded = pd.Series(dtype="int64")
        self.aging_ref: Optional[pd.Timestamp] = None
        self.products = set()
        self.so_cost = 0
        self.co_profit = 0

    def _get_cell_position(self, rack: int, level: int, cell: int):
        props = self.cfg.rack_entities[(rack-1)].get("properties") if (rack-1) < len(self.cfg.rack_entities) else {}
        rack_pos = props.get("worldPosition", props.get("position", [0, 0, 0]))

        PER_LEVEL = 1.8725
        CELL_HALF = 0.6

        position = [
            rack_pos[0],
            rack_pos[1] + ((cell - 1) / (self.cfg.cells_per_level - 1) * 2 - 1) * CELL_HALF,
            rack_pos[2] + min(5.33, (level - 1) * PER_LEVEL),
        ]

        return position

    @staticmethod
    def _to_int_qty(s: pd.Series, col: str) -> pd.Series:
        return pd.to_numeric(s.get(col, 0), errors="coerce").fillna(0).astype("int64")

    def fill_from(
        self,
        init_df: pd.DataFrame,
        so_df: pd.DataFrame,
        *,
        aging_ref: Union[str, pd.Timestamp],   # 예: "2025-01-01"
        qty_col_init: str = "수량",
        qty_col_so: str = "수량",
        prio_col: str = "보관우선순위",
        age_col_init: str = "평균 에이징 일수",
        default_prio: int = 10_000,
    ) -> None:
        """
        init_df: index='품명', [수량, 평균 에이징 일수]
        so_df  : index='품명', [수량, 보관우선순위]
        """
        self.so_cost = int((so_df.get("수량", 0) * self.cfg.df_goods.get("가격", 0)).sum())

        self.aging_ref = pd.Timestamp(aging_ref)
        ref_ns = self.aging_ref.value  # ns since epoch

        # ----- 1) 상품 목록/수량/우선순위/초기 에이징 -----
        products = sorted(set(init_df.index) | set(so_df.index))
        self.products = set(init_df.index) | set(so_df.index)

        init_q = self._to_int_qty(init_df.reindex(products), qty_col_init)
        so_q   = self._to_int_qty(so_df.reindex(products), qty_col_so)

        # 평균 에이징(일) → 등가 timestamp
        init_age_days = pd.to_numeric(init_df.reindex(products).get(age_col_init, 0),
                                      errors="coerce").fillna(0.0)
        init_ts = (self.aging_ref - pd.to_timedelta(init_age_days, unit="D")).astype("datetime64[ns]").values
        so_ts   = np.full(len(products), self.aging_ref.to_datetime64())

        # 우선순위 (작을수록 먼저 배치)
        prio = pd.to_numeric(so_df.reindex(products).get(prio_col), errors="coerce").fillna(default_prio).astype(int)

        # 작업 리스트: (prio, product, batches=[(qty, ts_ns), ...])
        jobs = []
        for i, p in enumerate(products):
            batches = []
            if init_q.iloc[i] > 0:
                batches.append((int(init_q.iloc[i]), pd.Timestamp(init_ts[i]).value))
            if so_q.iloc[i] > 0:
                batches.append((int(so_q.iloc[i]), pd.Timestamp(so_ts[i]).value))
            total = sum(q for q, _ in batches)
            if total > 0:
                jobs.append((int(prio.iloc[i]), p, batches))

        # 우선순위, 품명순으로 안정 정렬
        jobs.sort(key=lambda x: (x[0], x[1]))

        # ----- 2) 셀 목록 (아래→위, 좌→우, 랙1→N) -----
        cells = []
        for lv in range(1, self.cfg.levels + 1):      # 1이 바닥
            for r in range(1, self.cfg.racks + 1):
                for c in range(1, self.cfg.cells_per_level + 1):
                    cells.append({"rack": r, "level": lv, "cell": c,
                                  "product": None, "qty": 0, "capacity": self.cfg.cell_capacity,
                                  "mean_ts_ns": None})

        next_empty = 0
        # 현재 부분충전 셀 인덱스: 같은 product면 이어서 채움
        open_cell_for = {}  # product -> cell_idx
        discarded = {}

        # ----- 3) 채우기 -----
        for pr, prod, batches in jobs:
            for qty_batch, ts_ns in batches:
                remain = qty_batch
                while remain > 0:
                    # 3-1) 기존에 같은 상품을 담은 '미완' 셀 있으면 그 셀 먼저
                    idx = open_cell_for.get(prod)
                    if idx is not None:
                        cell = cells[idx]
                        space = cell["capacity"] - cell["qty"]
                        if space <= 0:
                            # 안전장치: 공간이 없으면 open 상태 해제
                            open_cell_for.pop(prod, None)
                            continue
                        put = min(remain, space)
                        # 가중 평균 timestamp 갱신
                        old_qty = cell["qty"]
                        old_ts = cell["mean_ts_ns"] if cell["mean_ts_ns"] is not None else ts_ns
                        new_ts = int(round((old_qty * old_ts + put * ts_ns) / (old_qty + put)))
                        cell["qty"] = old_qty + put
                        cell["mean_ts_ns"] = new_ts
                        remain -= put
                        if cell["qty"] >= cell["capacity"]:
                            open_cell_for.pop(prod, None)
                        continue

                    # 3-2) 새 빈 셀 확보
                    if next_empty >= len(cells):
                        # 더 둘 곳 없음 → 버림
                        discarded[prod] = discarded.get(prod, 0) + remain
                        break

                    cell = cells[next_empty]
                    # 비어있어야 함
                    put = min(remain, cell["capacity"])
                    cell["product"] = prod
                    cell["qty"] = put
                    cell["mean_ts_ns"] = ts_ns  # 처음엔 이 배치의 ts로 시작
                    remain -= put
                    # 다음 빈 셀로 포인터 전진 (이 셀은 해당 상품에 '예약'됨)
                    if cell["qty"] < cell["capacity"]:
                        open_cell_for[prod] = next_empty  # 이후 같은 상품이 오면 같은 셀로 혼합
                    next_empty += 1

        # ----- 4) state_df 구성 -----
        df = pd.DataFrame(cells)
        df["utilization"] = df["qty"] / df["capacity"]
        # ns → Timestamp
        df["mean_ts"] = pd.to_datetime(df["mean_ts_ns"])
        df.drop(columns=["mean_ts_ns"], inplace=True)
        df.sort_values(["rack", "level", "cell"], inplace=True)
        df.reset_index(drop=True, inplace=True)

        self.state_df = df
        self.discarded = (pd.Series(discarded, dtype="int64")
                          if discarded else pd.Series(dtype="int64"))

    # 편의 요약
    def summary(self) -> dict:
        filled = int((self.state_df["qty"] > 0).sum())
        total_cells = self.cfg.racks * self.cfg.levels * self.cfg.cells_per_level
        used_capacity = int(self.state_df["qty"].sum())
        total_capacity = total_cells * self.cfg.cell_capacity
        return {
            "cells_total": total_cells,
            "cells_filled": filled,
            "cells_empty": total_cells - filled,
            "capacity_used": used_capacity,
            "capacity_total": total_capacity,
            "utilization_pct": round(100 * used_capacity / total_capacity, 2) if total_capacity else 0.0,
            "discarded": None if self.discarded.empty else self.discarded.to_dict(),
        }

    # 지정 시점의 평균 에이징(일) 계산용 보조 메서드
    def age_snapshot(self, at: Union[str, pd.Timestamp]) -> pd.DataFrame:
        """
        각 셀의 평균 에이징(일)을 계산해 DataFrame을 반환.
        빈 셀(mean_ts NaT)은 age_days=0으로 표시.
        """
        at = pd.Timestamp(at)
        out = self.state_df.copy()
        delta = (at - out["mean_ts"]).dt.total_seconds() / 86400.0
        out["avg_age_days"] = np.where(out["qty"] > 0, np.maximum(delta, 0.0), 0.0)
        return out

    def consume(self, product: str, quantity: int, *, when, order: str = "fefo") -> dict:
        """
        재고 차감 요청을 단일 Event 객체(dict)로 반환합니다.

        [반환 형식]
        {
            "consumable": bool,               # 처리 가능 여부
            "datetime": Timestamp,            # 이벤트 발생 시각
            "customer_order": {               # 요청받은 주문 정보
                "product": str,
                "quantity": int
            },
            "stock_status": {                 # 처리 후 상품 재고 상태
                "product": str,
                "total_quantity": int
            },
            "rack_status": [                  # 상태가 변경된 셀 목록
                {
                    "rack": int, "level": int, "cell": int,
                    "product": str|None, "qty": int,
                    "utilization": float, "mean_ts": Timestamp|NaT
                }, ...
            ]
        }
        """
        when = pd.to_datetime(when)
        
        df = self.state_df
        mask = (df["product"] == product) & (df["qty"] > 0)
        total_available = int(df.loc[mask, "qty"].sum())

        # ----- 1. 처리 불가 케이스 (요청 수량 <= 0 또는 재고 부족) -----
        if quantity <= 0 or quantity > total_available:
            return {
                "consumable": False,
                "datetime": when,
                "customer_order": {"product": product, "quantity": quantity},
                "stock_status": {"product": product, "total_quantity": total_available},
                "rack_status": [] # 변경된 셀 없음
            }

        # ----- 2. 처리 가능 케이스 -----
        
        # 차감 순서 선택
        sub = df[mask].copy()
        if order.lower() == "fefo":
            sub["sort_key"] = pd.to_datetime(sub["mean_ts"], errors="coerce")
            sub = sub.sort_values(["sort_key", "rack", "level", "cell"], na_position="last")
        elif order.lower() == "bottom":
            sub = sub.sort_values(["rack", "level", "cell"])
        else:
            raise ValueError("order는 'fefo' 또는 'bottom' 중 하나여야 합니다.")

        remain = int(quantity)
        changed_cells = [] # 변경된 셀 정보만 저장할 리스트

        for idx, row in sub.iterrows():
            if remain <= 0:
                break
            
            avail = int(row["qty"])
            if avail <= 0:
                continue

            take = min(avail, remain)
            new_qty = avail - take

            # 상태 반영
            self.state_df.at[idx, "qty"] = new_qty
            util = new_qty / float(self.state_df.at[idx, "capacity"])
            self.state_df.at[idx, "utilization"] = util

            # 비면 product/mean_ts 초기화
            if new_qty == 0:
                self.state_df.at[idx, "product"] = None
                self.state_df.at[idx, "mean_ts"] = pd.NaT

            # 변경된 셀 정보 기록
            changed_cells.append({
                "rack": int(row["rack"]),
                "level": int(row["level"]),
                "cell": int(row["cell"]),
                "product": self.state_df.at[idx, "product"], # 비면 None
                "qty": int(new_qty),
                "utilization": float(util),
                "mean_ts": self.state_df.at[idx, "mean_ts"], # 비면 NaT
                "position": self._get_cell_position(int(row["rack"]), int(row["level"]), int(row["cell"])),
                "color": hsl_for(product, self.products, new_qty, self.cfg.cell_capacity) if product else None,
            })
            
            remain -= take

        self.co_profit += int(self.cfg.df_goods.get("가격")[product]) * quantity

        # 최종 결과 조합
        return {
            "consumable": True,
            "datetime": when,
            "customer_order": {"product": product, "quantity": quantity},
            "stock_status": {
                "product": product,
                "total_quantity": total_available - quantity # 처리 후 총 재고
            },
            "economic_status": {
                "month": when.month,
                "day": when.day,
                "co_profit": self.co_profit,
            },
            "rack_status": changed_cells
        }

    def consume_row(self, row, *, order: str = "fefo") -> list[dict]:
        """
        {'datetime','product','quantity'} 한 행(Series/dict)을 받아 consume 수행.
        """
        prod = row["product"] if isinstance(row, dict) else row.get("product")
        qty  = row["quantity"] if isinstance(row, dict) else row.get("quantity")
        when = row["datetime"] if isinstance(row, dict) else row.get("datetime")
        return self.consume(str(prod), int(qty), when=pd.to_datetime(when), order=order)

    def state_current(self, *, at=None) -> dict:
        """
        현재 전체 셀 상태를 consume과 동일한 형식의 단일 Event(dict)로 반환합니다.

        [반환 형식]
        {
            "consumable": None,               # 의미 없음
            "datetime": Timestamp,            # 조회 시각
            "customer_order": None,           # 특정 주문이 아니므로 None
            "stock_status": [                 # 현재 보관된 상품별 총재고 목록
                {"product": str, "total_quantity": int}, ...
            ],
            "rack_status": [                  # 모든 셀의 현재 상태 목록
                {
                    "rack": int, "level": int, "cell": int,
                    "product": str|None, "qty": int,
                    "utilization": float, "mean_ts": Timestamp|NaT
                }, ...
            ]
        }
        """
        now_ts = pd.to_datetime(at) if at is not None else pd.Timestamp.now()

        # rack_status: 모든 셀의 현재 상태를 리스트로 정리
        all_cell_states = []
        for _, r in self.state_df.iterrows():
            product = None if pd.isna(r["product"]) else r["product"]
            qty = int(r["qty"])
            all_cell_states.append({
                "rack": int(r["rack"]),
                "level": int(r["level"]),
                "cell": int(r["cell"]),
                "product": product,
                "qty": int(r["qty"]),
                "utilization": float(r["utilization"]),
                "mean_ts": r["mean_ts"],
                "position": self._get_cell_position(int(r["rack"]), int(r["level"]), int(r["cell"])),
                "color": hsl_for(product, self.products, qty, self.cfg.cell_capacity) if product else None,
            })

        # 최종 결과 조합
        return {
            "consumable": None,  # 상태 조회는 소비 이벤트가 아니므로 None
            "datetime": now_ts,
            "customer_order": None, # 특정 주문과 무관
            "stock_status": None,
            "economic_status": {
                "month": now_ts.month,
                "day": now_ts.day,
                "so_cost": self.so_cost,
                "co_profit": self.co_profit,
            },
            "rack_status": all_cell_states
        }

    def state_next_init(self, products: list[str] | None = None, *, at=None, decimals: int = 2) -> pd.DataFrame:
        """
        현재 랙 상태를 품목별로 집계해 init_df 형태로 반환.
        - index: '품명'
        - columns: ['수량', '평균 에이징 일수']  (평균은 qty 가중평균, 소수점 둘째자리)
        - products를 주면 그 순서/목록으로 reindex하여 0 채움
        - at 미지정이면 "지금" 기준으로 에이징 계산
        """
        at_ts = pd.to_datetime(at) if at is not None else pd.Timestamp.now()

        sdf = self.state_df
        used = sdf[(sdf["qty"] > 0) & sdf["product"].notna()].copy()

        if used.empty:
            prods = (products or [])
            out = pd.DataFrame(
                {"수량": [0] * len(prods), "평균 에이징 일수": [0.0] * len(prods)},
                index=pd.Index(prods, name="품명"),
            )
            return out

        # 셀별 평균 에이징(일) 계산 (음수면 0으로 클립)
        used["mean_ts"] = pd.to_datetime(used["mean_ts"])
        used["age_days"] = (at_ts - used["mean_ts"]).dt.total_seconds() / 86400.0
        used["age_days"] = used["age_days"].clip(lower=0.0).fillna(0.0)

        # 품목별 qty 합 + 가중평균 에이징
        used["age_x_qty"] = used["age_days"] * used["qty"]
        qty_sum = used.groupby("product", sort=True)["qty"].sum()
        age_sum = used.groupby("product", sort=True)["age_x_qty"].sum()
        avg_age = (age_sum / qty_sum).fillna(0.0).round(decimals)

        out = pd.DataFrame({"수량": qty_sum.astype("int64"),
                            "평균 에이징 일수": avg_age.astype("float64")})
        out.index.name = "품명"

        # 지정 목록 기준으로 정렬/누락 채움
        if products is not None:
            out = out.reindex(products).fillna({"수량": 0, "평균 에이징 일수": 0.0})
            out["수량"] = out["수량"].astype("int64")
            out["평균 에이징 일수"] = out["평균 에이징 일수"].astype("float64").round(decimals)

        return out
