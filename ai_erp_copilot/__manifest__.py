{
    "name": "AI Copilot for ERP",  # Exactly 18 chars, no emoji
    "version": "16.0.1.0.0",
    "license": "LGPL-3",
    "category": "Productivity",
    "summary": "Transform your ERP with AI-powered natural language interface",
    "description": """
AI Copilot for Odoo ERP
=======================

Natural Language Search - Find invoices, leads, inventory with plain English
Auto-Generate Reports - Sales, Tax, HR, P&L reports with AI intelligence  
Smart Recommendations - Purchase planning, employee performance insights
Chat Interface - Manage your ERP via conversational AI
Forecasting & Alerts - Low stock warnings, missed invoices, revenue predictions

Perfect for SMEs and enterprises wanting to democratize ERP access and boost productivity.
    """,
    "author": "SMhrineel8",
    "website": "https://github.com/SMhrineel8/odoo_ai_copilot",
    "maintainer": "SMhrineel8",
    "price": 119.0,
    "currency": "USD",
    "depends": ["base", "web", "sale", "purchase", "stock", "account", "hr"],
    "data": [
        "security/ir.model.access.csv",
        "views/ai_copilot_views.xml",
        "views/menu_items.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "ai_erp_copilot/static/src/js/ai_chat_widget.js",
            "ai_erp_copilot/static/src/css/ai_copilot.css",
        ],
    },
    "images": ["static/description/banner.png"],  # Fixed image name
    "installable": True,
    "auto_install": False,
    "application": True,
    "support": "https://github.com/SMhrineel8/odoo_ai_copilot/issues",
}
