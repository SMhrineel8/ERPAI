# ai_erp_copilot/__manifest__.py
{
    # Basic Info
    "name": "🤖 AI Copilot for ERP",  # Added emoji for better visibility
    "version": "16.0.1.0.0",
    "category": "Productivity",  # Changed from "Tools" - better for App Store
    "summary": "⚡ Transform your ERP with AI-powered natural language interface",  # More descriptive
    "description": """
AI Copilot for Odoo ERP
=======================

🔍 **Natural Language Search** - Find invoices, leads, inventory with plain English
🤖 **Auto-Generate Reports** - Sales, Tax, HR, P&L reports with GPT intelligence  
🧠 **Smart Recommendations** - Purchase planning, employee performance insights
🗣️ **Chat Interface** - Manage your ERP via conversational AI
📊 **Forecasting & Alerts** - Low stock warnings, missed invoices, revenue predictions

Perfect for SMEs and enterprises wanting to democratize ERP access and boost productivity by 5x.

For detailed features and screenshots, see: static/description/index.html
    """,
    
    # Author & Licensing
    "author": "SMhrineel8",  # Your GitHub username
    "website": "https://github.com/SMhrineel8/odoo_ai_copilot",
    "license": "LGPL-3",
    "maintainer": "SMhrineel8",
    
    # Pricing (optional)
    "price": 119.0,
    "currency": "USD",
    
    # Dependencies
    "depends": [
        "base",
        "web",
        "sale",
        "purchase", 
        "stock",
        "account",
        "hr",
    ],
    
    # Data files
    "data": [
        "security/ir.model.access.csv",
        "views/ai_copilot_views.xml",
        "views/menu_items.xml",
        "data/ai_copilot_data.xml",  # Add sample data
    ],
    
    # Backend assets
    "assets": {
        "web.assets_backend": [
            "ai_erp_copilot/static/src/js/ai_chat_widget.js",
            "ai_erp_copilot/static/src/css/ai_copilot.css",
        ],
    },
    
    # App Store images - KEY FIX
    "images": ["static/description/cover.png"],  # Only cover image needed
    
    # Install flags
    "installable": True,
    "auto_install": False,
    "application": True,
    
    # Additional metadata for better App Store ranking
    "external_dependencies": {
        "python": ["openai", "requests", "fastapi"],  # Optional: mention key deps
    },
    
    # Support info
    "support": "https://github.com/SMhrineel8/odoo_ai_copilot/issues",
}
