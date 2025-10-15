import requests
import json
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
            timeout: int = 10
            ) -> list[dict]:
    """
    dict 리스트 -> (필요시 키 매핑) -> JSON POST. 응답 요약 리스트 반환.
    """
    url = server.rstrip("/") + "/data/insert"
    event = format_ts_of(event)

    s = requests.Session()
    res = []

    def _send_order(customer_order: dict | None):
        if not customer_order: return

        body = {
            "bucket": bucket,
            "measurement": "customer_order_event",
            "tags": {
                "username": username,
                "team": event.get("team", None),
                "product": customer_order.get("product", None),
            },
            "fields": {
                "received": event.get("consumable", None),
                "quantity": customer_order.get("quantity", None),
            },
            "timestamp": event.get("datetime", None)
        }

        r = s.post(url, json=body, headers=headers, timeout=timeout)
        try:
            payload = r.json()
        except Exception:
            payload = r.text
        res.append({"ok": r.ok, "status": r.status_code, "request": body, "response": payload})

    def _send_stock(stock_status: dict | None):
        if not stock_status: return

        body = {
            "bucket": bucket,
            "measurement": "stock_status_event",
            "tags": {
                "username": username,
                "team": event.get("team", None),
                "task": event.get("task", None),
                "product": stock_status.get("product", None),
            },
            "fields": {
                "quantity": stock_status.get("total_quantity", None),
            },
            "timestamp": event.get("datetime", None)
        }

        r = s.post(url, json=body, headers=headers, timeout=timeout)
        try:
            payload = r.json()
        except Exception:
            payload = r.text
        res.append({"ok": r.ok, "status": r.status_code, "request": body, "response": payload})

    def _send_rack_status(rack_status: list[dict]):
        handled_status = [format_ts_of(r) for r in rack_status]
        for rack in handled_status:
            pos = rack.get("position", None)
            body = {
                "bucket": bucket,
                "measurement": "rack_status_event",
                "tags": {
                    "username": username,
                    "team": event.get("team", None),
                    "task": event.get("task", None),
                    "rack": rack.get("rack", None),
                    "level": rack.get("level", None),
                    "cell": rack.get("cell", None),
                    "product": rack.get("product", None),
                },
                "fields": {
                    "quantity": rack.get("qty", None),
                    "utilization": rack.get("utilization", None),
                    "mean_ts": rack.get("mean_ts", None),
                    "position": json.dumps(pos) if pos else None,
                    "color": rack.get("color", None)
                },
                "timestamp": event.get("datetime", None)
            }

            r = s.post(url, json=body, headers=headers, timeout=timeout)
            try:
                payload = r.json()
            except Exception:
                payload = r.text
            res.append({"ok": r.ok, "status": r.status_code, "request": body, "response": payload})

    def _send_box_status(rack_status: list[dict]):
        handled_status = [format_ts_of(r) for r in rack_status]
        for rack in handled_status:
            body = {
                "bucket": bucket,
                "measurement": "rack_status_event",
                "tags": {
                    "username": username,
                    "team": event.get("team", None),
                    "task": event.get("task", None),
                    "rack": rack.get("rack", None),
                    "level": rack.get("level", None),
                    "cell": rack.get("cell", None),
                    "product": rack.get("product", None),
                },
                "fields": {
                    "quantity": rack.get("qty", None),
                    "utilization": rack.get("utilization", None),
                    "mean_ts": rack.get("mean_ts", None)
                },
                "timestamp": event.get("datetime", None)
            }

            r = s.post(url, json=body, headers=headers, timeout=timeout)
            try:
                payload = r.json()
            except Exception:
                payload = r.text
            res.append({"ok": r.ok, "status": r.status_code, "request": body, "response": payload})

    _send_order(event.get("customer_order", None))
    _send_stock(event.get("stock_status", None))
    _send_rack_status(event.get("rack_status", []))

    return res
