from odoo import models, fields, api
import requests
import json
import logging

_logger = logging.getLogger(__name__)

class AICopilot(models.Model):
    _name = 'ai.copilot'
    _description = 'AI Copilot Assistant'
    _rec_name = 'query'

    query = fields.Text('User Query', required=True)
    response = fields.Text('AI Response')
    query_type = fields.Selection([
        ('search', 'Natural Language Search'),
        ('report', 'Report Generation'),
        ('recommendation', 'Smart Recommendation'),
        ('forecast', 'Forecasting'),
        ('general', 'General Query')
    ], string='Query Type', default='general')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    create_date = fields.Datetime('Created On', default=fields.Datetime.now)

    @api.model
    def process_natural_language_query(self, query):
        """Process natural language query and return structured response"""
        try:
            # Determine query type
            query_type = self._detect_query_type(query)
            
            # Process based on type
            if query_type == 'search':
                return self._handle_search_query(query)
            elif query_type == 'report':
                return self._handle_report_query(query)
            elif query_type == 'recommendation':
                return self._handle_recommendation_query(query)
            elif query_type == 'forecast':
                return self._handle_forecast_query(query)
            else:
                return self._handle_general_query(query)
                
        except Exception as e:
            _logger.error(f"Error processing query: {str(e)}")
            return {'error': str(e)}

    def _detect_query_type(self, query):
        """Detect the type of query using keywords"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['search', 'find', 'show me', 'list']):
            return 'search'
        elif any(word in query_lower for word in ['report', 'generate', 'create report']):
            return 'report'
        elif any(word in query_lower for word in ['recommend', 'suggest', 'advice']):
            return 'recommendation'
        elif any(word in query_lower for word in ['forecast', 'predict', 'trend']):
            return 'forecast'
        else:
            return 'general'

    def _handle_search_query(self, query):
        """Handle natural language search queries"""
        # Example: "Show me all invoices from last month"
        results = {}
        
        # Search invoices
        if 'invoice' in query.lower():
            invoices = self.env['account.move'].search([
                ('move_type', 'in', ['out_invoice', 'in_invoice']),
                ('state', '!=', 'draft')
            ], limit=10)
            results['invoices'] = [{'name': inv.name, 'partner': inv.partner_id.name, 'amount': inv.amount_total} for inv in invoices]
        
        # Search products
        if 'product' in query.lower() or 'inventory' in query.lower():
            products = self.env['product.product'].search([], limit=10)
            results['products'] = [{'name': prod.name, 'qty': prod.qty_available} for prod in products]
        
        # Search customers/leads
        if 'customer' in query.lower() or 'lead' in query.lower():
            partners = self.env['res.partner'].search([('is_company', '=', True)], limit=10)
            results['customers'] = [{'name': partner.name, 'email': partner.email} for partner in partners]
        
        return results

    def _handle_report_query(self, query):
        """Handle report generation queries"""
        # Example: "Generate sales report for this month"
        report_data = {}
        
        if 'sales' in query.lower():
            # Generate sales report
            sales_orders = self.env['sale.order'].search([('state', 'in', ['sale', 'done'])])
            total_sales = sum(order.amount_total for order in sales_orders)
            report_data = {
                'type': 'sales_report',
                'total_orders': len(sales_orders),
                'total_amount': total_sales,
                'orders': [{'name': o.name, 'partner': o.partner_id.name, 'amount': o.amount_total} for o in sales_orders[:5]]
            }
        
        return report_data

    def _handle_recommendation_query(self, query):
        """Handle smart recommendation queries"""
        recommendations = {}
        
        if 'purchase' in query.lower():
            # Low stock recommendations
            low_stock_products = self.env['product.product'].search([
                ('qty_available', '<', 10),
                ('type', '=', 'product')
            ])
            recommendations = {
                'type': 'purchase_recommendation',
                'low_stock_products': [{'name': p.name, 'qty': p.qty_available} for p in low_stock_products]
            }
        
        return recommendations

    def _handle_forecast_query(self, query):
        """Handle forecasting queries"""
        # Simple forecasting logic
        forecast_data = {}
        
        if 'sales' in query.lower():
            # Basic sales forecast
            recent_sales = self.env['sale.order'].search([
                ('state', 'in', ['sale', 'done']),
                ('create_date', '>=', fields.Date.today() - fields.timedelta(days=30))
            ])
            avg_monthly_sales = sum(order.amount_total for order in recent_sales)
            
            forecast_data = {
                'type': 'sales_forecast',
                'current_month_sales': avg_monthly_sales,
                'predicted_next_month': avg_monthly_sales * 1.1  # Simple 10% growth assumption
            }
        
        return forecast_data

    def _handle_general_query(self, query):
        """Handle general queries with AI integration"""
        # This is where you'd integrate with OpenAI or other AI services
        # For now, return a simple response
        return {
            'type': 'general_response',
            'message': f"I understand you're asking about: {query}. I'm here to help with your ERP needs!"
        }

    @api.model
    def create_chat_session(self, query):
        """Create a new chat session and process the query"""
        query_type = self._detect_query_type(query)
        response = self.process_natural_language_query(query)
        
        # Create record
        chat_record = self.create({
            'query': query,
            'response': json.dumps(response),
            'query_type': query_type
        })
        
        return {
            'id': chat_record.id,
            'query': query,
            'response': response,
            'query_type': query_type
        }
