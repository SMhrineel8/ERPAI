from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os

# Import your modules (make sure these files exist)
try:
    from ai.chat_engine import chat_to_erp
    from odoo_connector import fetch_invoices, fetch_inventory
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback functions if imports fail
    def chat_to_erp(question):
        return f"AI Response to: {question}"
    
    def fetch_invoices(limit=10):
        return [{"id": i, "name": f"Invoice {i}", "amount": 1000 + i*100} for i in range(limit)]
    
    def fetch_inventory(limit=10):
        return [{"id": i, "name": f"Product {i}", "qty": 50 + i*10} for i in range(limit)]

app = FastAPI(title="Odoo AI Copilot", description="AI-powered ERP assistant")

@app.get("/")
async def root():
    return {"message": "Odoo AI Copilot is running!", "status": "active"}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "odoo-ai-copilot"}

class ChatRequest(BaseModel):
    question: str

@app.post("/api/v1/chat")
async def api_chat(req: ChatRequest):
    try:
        response = chat_to_erp(req.question)
        return {"answer": response, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@app.get("/api/v1/invoices")
async def api_invoices():
    try:
        invoices = fetch_invoices(limit=10)
        return {"invoices": invoices, "count": len(invoices)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Invoice fetch error: {str(e)}")

@app.get("/api/v1/inventory")
async def api_inventory():
    try:
        inventory = fetch_inventory(limit=10)
        return {"inventory": inventory, "count": len(inventory)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inventory fetch error: {str(e)}")

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
