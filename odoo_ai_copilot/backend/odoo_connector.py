import xmlrpc.client
import os
from datetime import datetime

ODOO_URL = os.getenv("ODOO_URL")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_USER = os.getenv("ODOO_USER")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")

if not all([ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD]):
    raise RuntimeError("All Odoo env vars must be set.")

def get_client():
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
    return uid, models

def fetch_invoices(limit=10):
    uid, models = get_client()
    return models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'account.move', 'search_read',
                             [[['move_type', '=', 'out_invoice']]], {'fields': ['name', 'amount_total', 'invoice_date'], 'limit': limit})

def fetch_inventory(limit=10):
    uid, models = get_client()
    return models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'stock.quant', 'search_read',
                             [[['quantity', '<', 10]]], {'fields': ['product_id', 'quantity', 'location_id'], 'limit': limit})
