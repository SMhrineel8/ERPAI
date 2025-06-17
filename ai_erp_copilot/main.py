from fastapi import FastAPI, HTTPException, Query, File, UploadFile, Response
from pydantic import BaseModel
import uvicorn
import os

# Import your modules (make sure these files exist)
try:
    from ai_erp_copilot.ai.chat_engine import chat_to_erp
    from ai_erp_copilot.odoo_connector import fetch_invoices, fetch_inventory
    from ai_erp_copilot.dashboard_connector import (
        generate_dashboard_items,
        export_dashboard,
        import_dashboard,
    )
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback stubs
    def chat_to_erp(question):
        return f"AI Response to: {question}"
    def fetch_invoices(limit=10):
        return [{"id": i, "name": f"Invoice {i}", "amount": 1000 + i*100} for i in range(limit)]
    def fetch_inventory(limit=10):
        return [{"id": i, "name": f"Product {i}", "qty": 50 + i*10} for i in range(limit)]
    def generate_dashboard_items(keywords: list[str]) -> list[dict]:
        return [{"id": k, "title": k.title(), "type": "line_chart"} for k in keywords]
    def export_dashboard(items, fmt):
        return b""
    def import_dashboard(data, fmt):
        return []

# Initialize FastAPI app
app = FastAPI(
    title="Odoo AI Copilot",
    description="AI-powered ERP assistant + Dashboard generator",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Odoo AI Copilot is running!", "status": "active"}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "odoo-ai-copilot"}

# ——— Chat API —————————————————————————————————————————

class ChatRequest(BaseModel):
    question: str

@app.post("/api/v1/chat")
async def api_chat(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(422, detail="`question` cannot be empty")
    try:
        answer = chat_to_erp(req.question)
        return {"answer": answer, "status": "success"}
    except Exception as e:
        raise HTTPException(500, detail=f"Chat error: {e}")

@app.post("/chat")
async def simple_chat(req: ChatRequest):
    return await api_chat(req)

# ——— ERP Data Endpoints ——————————————————————————————————

@app.get("/api/v1/invoices")
async def api_invoices():
    try:
        inv = fetch_invoices(limit=10)
        return {"invoices": inv, "count": len(inv)}
    except Exception as e:
        raise HTTPException(500, detail=f"Invoice fetch error: {e}")

@app.get("/api/v1/inventory")
async def api_inventory():
    try:
        inv = fetch_inventory(limit=10)
        return {"inventory": inv, "count": len(inv)}
    except Exception as e:
        raise HTTPException(500, detail=f"Inventory fetch error: {e}")

# ——— Dashboard Ninja–Style Endpoints ———————————————————————————

@app.post("/api/v1/dashboard/generate")
async def api_generate_dashboard(body: dict):
    """
    Generate dashboard items from keywords:
      POST {"keywords": ["sales","inventory","orders"]}
    """
    kws = body.get("keywords")
    if not isinstance(kws, list) or not all(isinstance(k, str) for k in kws):
        raise HTTPException(422, detail="`keywords` must be list of strings")
    items = generate_dashboard_items(kws)
    return {"items": items, "count": len(items)}

@app.get("/api/v1/dashboard/export")
async def api_export_dashboard(
    fmt: str = Query("json", pattern="^(json|csv)$")
):
    """
    Export a sample dashboard:
      GET /api/v1/dashboard/export?fmt=csv
    """
    # you could fetch real items here instead of hardcoded ones
    items = generate_dashboard_items(["sales", "inventory", "revenue"])
    data = export_dashboard(items, fmt)
    media = "application/json" if fmt=="json" else "text/csv"
    return Response(content=data, media_type=media)

@app.post("/api/v1/dashboard/import")
async def api_import_dashboard(
    file: UploadFile = File(...),
    fmt: str = Query("json", pattern="^(json|csv)$")
):
    """
    Import dashboard items file:
      POST multipart/form-data; file=@yourfile.csv; fmt=csv
    """
    raw = await file.read()
    items = import_dashboard(raw, fmt)
    return {"imported_count": len(items), "items": items}

# ——— Launch ——————————————————————————————————————————————

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
