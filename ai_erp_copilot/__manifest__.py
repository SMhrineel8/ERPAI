{
    'name': 'AI Copilot for ERP',
    'version': '16.0.1.0.0',
    'category': 'Tools',
    'summary': '⚡ AI-powered ERP assistant: Talk to Odoo in plain English',
    'description': """
        <p><strong>AI Copilot Plugin for Odoo ERP</strong></p>
        <ul>
            <li>💬 Natural Language Search across invoices, leads, inventory</li>
            <li>📊 Auto-Generate Reports (Sales, Tax, HR, P&L) using GPT</li>
            <li>📦 Smart Recommendations (purchase, performance, reordering)</li>
            <li>🤖 Chat Interface to manage the ERP in English</li>
            <li>🔮 Forecasting & Alerts (low stock, invoice delays, revenue drops)</li>
        </ul>
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
            'ai_erp_copilot/static/src/js/ai_chat_widget.js',
            'ai_erp_copilot/static/src/css/ai_copilot.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}
