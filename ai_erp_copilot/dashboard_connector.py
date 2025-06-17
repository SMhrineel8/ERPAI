# ai_erp_copilot/dashboard_connector.py
import csv
import io
import json
from fastapi import HTTPException

def generate_dashboard_items(keywords: list[str]) -> list[dict]:
    """
    Given a list of keywords, return fake 'dashboard item' specs.
    Replace this stub with real Odoo RPC logic.
    """
    items = []
    for k in keywords:
        items.append({
            "id": k.lower().replace(" ", "_"),
            "title": k.title(),
            "data_source": f"model:{k.lower()}",
            "type": "line_chart",
            "options": {"animated": True, "refresh_interval": 30}
        })
    return items

def export_dashboard(items: list[dict], fmt: str) -> bytes:
    if fmt == "json":
        return json.dumps(items).encode("utf-8")
    elif fmt == "csv":
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=items[0].keys())
        w.writeheader()
        w.writerows(items)
        return buf.getvalue().encode("utf-8")
    else:
        raise HTTPException(400, f"Unsupported format: {fmt}")

def import_dashboard(data: bytes, fmt: str) -> list[dict]:
    if fmt == "json":
        return json.loads(data)
    elif fmt == "csv":
        buf = io.StringIO(data.decode("utf-8"))
        r = csv.DictReader(buf)
        return [dict(row) for row in r]
    else:
        raise HTTPException(400, f"Unsupported format: {fmt}")
