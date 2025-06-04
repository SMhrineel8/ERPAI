"""
AI Chat Engine for ERP
Uses OpenAI API when available, falls back to rule-based responses
"""
import re
import json
import os
import requests

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def chat_to_erp(question: str) -> str:
    """
    Process natural language queries and return responses
    Uses OpenAI if API key is available, otherwise uses rule-based logic
    """
    # Try OpenAI first if API key is available
    if OPENAI_API_KEY:
        try:
            return get_openai_response(question)
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fall back to rule-based response
    
    # Rule-based response as fallback
    question_lower = question.lower()
    
    # Invoice queries
    if any(word in question_lower for word in ['invoice', 'bill', 'payment']):
        return handle_invoice_query(question_lower)
    
    # Inventory queries  
    elif any(word in question_lower for word in ['inventory', 'stock', 'product', 'item']):
        return handle_inventory_query(question_lower)
    
    # Sales queries
    elif any(word in question_lower for word in ['sales', 'revenue', 'customer', 'order']):
        return handle_sales_query(question_lower)
    
    # General queries
    else:
        return f"I understand you're asking about: '{question}'. I can help you with invoices, inventory, sales, and more ERP tasks. Try asking something like 'show me recent invoices' or 'check low stock items'."

def get_openai_response(question: str) -> str:
    """Get response from OpenAI API"""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are an AI assistant for ERP systems. Help users with invoices, inventory, sales, and business operations. Be concise and helpful."},
            {"role": "user", "content": question}
        ],
        "max_tokens": 150,
        "temperature": 0.7
    }
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    else:
        raise Exception(f"OpenAI API error: {response.status_code}")

def handle_invoice_query(query: str) -> str:
    """Handle invoice-related queries"""
    if 'recent' in query or 'latest' in query:
        return "Here are your recent invoices: INV-2024-001 ($1,200), INV-2024-002 ($850), INV-2024-003 ($2,100). Total outstanding: $4,150"
    elif 'overdue' in query or 'pending' in query:
        return "You have 3 overdue invoices totaling $1,800. INV-2024-001 is 15 days overdue ($1,200)."
    elif 'paid' in query:
        return "This month you've received $12,500 in payments across 8 invoices. Payment rate: 85%"
    else:
        return "I can help you check recent invoices, overdue payments, or payment status. What specifically would you like to know?"

def handle_inventory_query(query: str) -> str:
    """Handle inventory-related queries"""
    if 'low' in query or 'stock' in query:
        return "Low stock alert: Widget A (5 units left), Gadget B (2 units), Component C (8 units). Recommended reorder: Widget A (50 units), Gadget B (25 units)."
    elif 'value' in query or 'worth' in query:
        return "Current inventory value: $45,230. Top items by value: Premium Widget ($12,000), Deluxe Gadget ($8,500)."
    elif 'movement' in query or 'activity' in query:
        return "Top moving items this week: Widget A (25 sold), Basic Gadget (18 sold), Standard Component (32 sold)."
    else:
        return "I can check stock levels, inventory value, or product movement. What would you like to know?"

def handle_sales_query(query: str) -> str:
    """Handle sales-related queries"""
    if 'this month' in query or 'monthly' in query:
        return "This month's sales: $23,400 (18 orders). vs last month: +12% growth. Top customer: ABC Corp ($4,200)."
    elif 'today' in query or 'daily' in query:
        return "Today's sales: $1,850 (3 orders). Average order value: $617. Still 6 hours left in business day!"
    elif 'forecast' in query or 'predict' in query:
        return "Sales forecast for next month: $26,200 (based on current trends +12% growth). Confidence: 78%"
    else:
        return "I can show sales performance, forecasts, or customer insights. What interests you most?"

def extract_numbers(text: str) -> list:
    """Extract numbers from text for processing"""
    return re.findall(r'\d+', text)

def detect_intent(query: str) -> str:
    """Detect user intent from query"""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['show', 'list', 'display', 'get']):
        return 'retrieve'
    elif any(word in query_lower for word in ['create', 'add', 'new', 'make']):
        return 'create'
    elif any(word in query_lower for word in ['update', 'change', 'modify', 'edit']):
        return 'update'
    elif any(word in query_lower for word in ['delete', 'remove', 'cancel']):
        return 'delete'
    elif any(word in query_lower for word in ['forecast', 'predict', 'estimate']):
        return 'forecast'
    else:
        return 'general'
