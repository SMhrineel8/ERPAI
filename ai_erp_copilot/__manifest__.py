{
    'name': 'AI Copilot for ERP',
    'version': '16.0.1.0.0',
    'category': 'Tools',
    'summary': 'AI-powered ERP assistant with natural language processing',
    'description': """
        AI Copilot Plugin for ERPs
        ==========================
        * Natural Language Search across invoices, leads, inventory
        * Auto-Generate Reports (Sales, Tax, HR, P&L) with GPT
        * Smart Recommendations (purchase planning, employee performance)
        * Chat Interface to manage the ERP via plain English
        * Forecasting & Alerts (low stock, missed invoices, revenue drops)
    """,
    'author': 'Your Company',
    'website': 'https://github.com/SMhrineel8/odoo_ai_copilot',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale',
        'purchase',
        'stock',
        'account',
        'hr',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/ai_copilot_views.xml',
        'views/menu_items.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ai_copilot/static/src/js/ai_chat_widget.js',
            'ai_copilot/static/src/css/ai_copilot.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}
