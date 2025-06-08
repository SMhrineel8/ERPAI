# ai_erp_copilot/__manifest__.py
{
    # Basic Info
    "name": "AI Copilot for ERP",
    "version": "16.0.1.0.0",
    "category": "Tools",
    "summary": "⚡ AI ERP assistant",
    "description": "file: static/description/index.html",

    # Author & Licensing
    "author": "Your Company",
    "website": "https://github.com/SMhrineel8/odoo_ai_copilot",
    "license": "LGPL-3",

    # Pricing (optional)
    "price": 119.0,          # price per user or flat one-shot
    "currency": "USD",

    # Dependencies
    "depends": [
        "base",
        "sale",
        "purchase",
        "stock",
        "account",
        "hr",
        "web",
    ],

    # Data files
    "data": [
        "security/ir.model.access.csv",
        "views/ai_copilot_views.xml",
        "views/menu_items.xml",
    ],

    # Backend assets
    "assets": {
        "web.assets_backend": [
            "ai_erp_copilot/static/src/js/ai_chat_widget.js",
            "ai_erp_copilot/static/src/css/ai_copilot.css",
        ],
    },

    # App Store images
    "images": [
        "static/description/icon.png",   # small square icon
        "static/description/cover.png",  # cover / thumbnail
    ],

    # Install flags
    "installable": True,
    "auto_install": False,
    "application": True,
}
