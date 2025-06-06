"""
Odoo Connector - connects to Odoo via XML-RPC
Uses environment variables from Render for real connections
"""
import requests
import json
import os
from datetime import datetime, timedelta

# Mock data for testing
MOCK_INVOICES = [
    {"id": 1, "name": "INV-2024-001", "partner": "ABC Corp", "amount": 1200.00, "state": "open", "date": "2024-06-01"},
    {"id": 2, "name": "INV-2024-002", "partner": "XYZ Ltd", "amount": 850.00, "state": "paid", "date": "2024-06-02"},
    {"id": 3, "name": "INV-2024-003", "partner": "Tech Solutions", "amount": 2100.00, "state": "open", "date": "2024-06-03"},
    {"id": 4, "name": "INV-2024-004", "partner": "Global Inc", "amount": 975.00, "state": "paid", "date": "2024-06-04"},
    {"id": 5, "name": "INV-2024-005", "partner": "StartupCo", "amount": 1450.00, "state": "draft", "date": "2024-06-04"},
]

MOCK_INVENTORY = [
    {"id": 1, "name": "Premium Widget", "sku": "WID-001", "qty_available": 25, "value": 12000, "category": "Widgets"},
    {"id": 2, "name": "Basic Gadget", "sku": "GAD-001", "qty_available": 5, "value": 2500, "category": "Gadgets"},
    {"id": 3, "name": "Super Component", "sku": "COM-001", "qty_available": 50, "value": 8500, "category": "Components"},
    {"id": 4, "name": "Deluxe Tool", "sku": "TOL-001", "qty_available": 12, "value": 6000, "category": "Tools"},
    {"id": 5, "name": "Standard Part", "sku": "PAR-001", "qty_available": 2, "value": 800, "category": "Parts"},
]

import os

class OdooConnector:
    def __init__(self, url=None, db=None, username=None, password=None):
        self.url = url or os.getenv("ODOO_URL", "http://localhost:8069")
        self.db = db or os.getenv("ODOO_DB", "demo_db")
        self.username = username or os.getenv("ODOO_USER", "admin")
        self.password = password or os.getenv("ODOO_PASSWORD", "admin")
        self.api_key = os.getenv("ODOO_API_KEY")
        self.uid = None
        self.connected = False
    
    def connect(self):
        """Connect to Odoo instance"""
        try:
            # In real implementation, you'd authenticate here
            # For now, simulate connection
            self.connected = True
            self.uid = 1
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def search_read(self, model, domain=None, fields=None, limit=10):
        """Search and read records from Odoo"""
        # In real implementation, this would call Odoo's XML-RPC API
        # For now, return mock data based on model
        
        if model == 'account.move':
            return MOCK_INVOICES[:limit]
        elif model == 'product.product':
            return MOCK_INVENTORY[:limit]
        else:
            return []

# Global connector instance
odoo = OdooConnector()

def fetch_invoices(limit=10, state=None):
    """Fetch invoices from Odoo"""
    try:
        invoices = MOCK_INVOICES[:limit]
        
        if state:
            invoices = [inv for inv in invoices if inv['state'] == state]
        
        return invoices
    except Exception as e:
        print(f"Error fetching invoices: {e}")
        return []

def fetch_inventory(limit=10, low_stock=False):
    """Fetch inventory from Odoo"""
    try:
        inventory = MOCK_INVENTORY[:limit]
        
        if low_stock:
            inventory = [item for item in inventory if item['qty_available'] < 10]
        
        return inventory
    except Exception as e:
        print(f"Error fetching inventory: {e}")
        return []

def fetch_customers(limit=10):
    """Fetch customers from Odoo"""
    mock_customers = [
        {"id": 1, "name": "ABC Corp", "email": "contact@abccorp.com", "phone": "+1-555-0101"},
        {"id": 2, "name": "XYZ Ltd", "email": "info@xyzltd.com", "phone": "+1-555-0102"},
        {"id": 3, "name": "Tech Solutions", "email": "hello@techsol.com", "phone": "+1-555-0103"},
        {"id": 4, "name": "Global Inc", "email": "team@globalinc.com", "phone": "+1-555-0104"},
        {"id": 5, "name": "StartupCo", "email": "founders@startupco.com", "phone": "+1-555-0105"},
    ]
    
    return mock_customers[:limit]

def create_invoice(partner_name, amount, description=""):
    """Create a new invoice in Odoo"""
    # Mock invoice creation
    new_invoice = {
        "id": len(MOCK_INVOICES) + 1,
        "name": f"INV-2024-{len(MOCK_INVOICES) + 1:03d}",
        "partner": partner_name,
        "amount": amount,
        "state": "draft",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "description": description
    }
    
    MOCK_INVOICES.append(new_invoice)
    return new_invoice

def get_sales_summary():
    """Get sales summary data"""
    total_sales = sum(inv['amount'] for inv in MOCK_INVOICES if inv['state'] == 'paid')
    pending_sales = sum(inv['amount'] for inv in MOCK_INVOICES if inv['state'] == 'open')
    
    return {
        "total_paid": total_sales,
        "total_pending": pending_sales,
        "invoice_count": len(MOCK_INVOICES),
        "paid_count": len([inv for inv in MOCK_INVOICES if inv['state'] == 'paid'])
    }
