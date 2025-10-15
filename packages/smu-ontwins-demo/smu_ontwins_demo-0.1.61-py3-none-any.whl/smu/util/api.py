import requests, json
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import numpy as np
from datetime import datetime

def format_ts_of(obj):
    return {
        k: (pd.Timestamp(v).tz_localize('Asia/Seoul').isoformat(timespec="milliseconds")
            if isinstance(v, (pd.Timestamp, np.datetime64, datetime)) else v)
        for k, v in obj.items()
        }

def send_to(server: str,
            event: dict,
            *,
            username: str = "unknown",
            bucket: str = "demo",
            headers: dict | None = None,
            timeout: int = 10,
            max_workers: int | None = None
            ) -> list[dict]:
    """
    이벤트를 모두 바디로 만든 뒤 스레드풀로 병렬 POST.
    응답 요약 리스트를 요청 순서대로 반환.
    """
    url = server.rstrip("/") + "/data/insert"
    event = format_ts_of(event)

    # 0) 보낼 바디들 수집 -------------------------------------------------------
    bodies: list[dict] = []

    # customer_order
    co = event.get("customer_order")
    if co:
        bodies.append({
            "bucket": bucket,
            "measurement": "customer_order_event",
            "tags": {
                "username": username,
                "team": event.get("team"),
                "product": co.get("product"),
            },
            "fields": {
                "received": event.get("consumable"),
                "quantity": co.get("quantity"),
            },
            "timestamp": event.get("datetime"),
        })

    # stock_status
    st = event.get("stock_status")
    if st:
        bodies.append({
            "bucket": bucket,
            "measurement": "stock_status_event",
            "tags": {
                "username": username,
                "team": event.get("team"),
                "task": event.get("task"),
                "product": st.get("product"),
            },
            "fields": {
                "quantity": st.get("total_quantity"),
            },
            "timestamp": event.get("datetime"),
        })

    # economic_status
    est = event.get("economic_status")
    if est:
        bodies.append({
            "bucket": bucket,
            "measurement": "economic_status",
            "tags": {
                "username": username,
                "team": event.get("team"),
                "task": event.get("task"),
                "month": est.get("month"),
                "day": est.get("day"),
            },
            "fields": {
                "so_cost": est.get("so_cost"),
                "co_profit": est.get("co_profit"),
            },
            "timestamp": event.get("datetime"),
        })

    # rack_status (여러 건)
    for rack in event.get("rack_status", []):
        rack = format_ts_of(rack)
        pos = rack.get("position")
        bodies.append({
            "bucket": bucket,
            "measurement": "rack_status_event",
            "tags": {
                "username": username,
                "team": event.get("team"),
                "task": event.get("task"),
                "rack": rack.get("rack"),
                "level": rack.get("level"),
                "cell": rack.get("cell"),
                "product": rack.get("product"),
            },
            "fields": {
                "quantity": rack.get("qty"),
                "utilization": rack.get("utilization"),
                "mean_ts": rack.get("mean_ts"),
                "position": json.dumps(pos) if pos else None,
                "color": rack.get("color"),
            },
            "timestamp": event.get("datetime"),
        })

    if not bodies:
        return []

    # 1) 세션/어댑터 세팅 (커넥션 풀 + 재시도) -----------------------------------
    s = requests.Session()
    if headers:
        s.headers.update(headers)

    # 동시 연결 수만큼 풀 사이즈 확보
    workers = max_workers or min(8, len(bodies))
    adapter = HTTPAdapter(
        pool_connections=workers,
        pool_maxsize=workers,
        max_retries=Retry(
            total=2,
            backoff_factor=0.2,
            status_forcelist=[502, 503, 504],
            allowed_methods=["POST"],
        ),
    )
    s.mount("http://", adapter)
    s.mount("https://", adapter)

    # 2) 병렬 POST --------------------------------------------------------------
    def _post(idx: int, body: dict):
        r = s.post(url, json=body, timeout=timeout)
        try:
            payload = r.json()
        except Exception:
            payload = r.text
        return idx, {
            "ok": r.ok,
            "status": r.status_code,
            "request": body,
            "response": payload,
        }

    results = [None] * len(bodies)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_post, i, b) for i, b in enumerate(bodies)]
        for f in as_completed(futs):
            i, item = f.result()
            results[i] = item

    return results
