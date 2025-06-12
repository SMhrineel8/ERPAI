from odoo import models, fields, api
import json
from datetime import datetime, timedelta

class AiFeedback(models.Model):
    _name = 'ai.feedback'
    _description = 'AI Copilot User Feedback'
    _order = 'create_date desc'

    # User and Session Info
    user_id = fields.Many2one('res.users', string='User', required=True)
    session_id = fields.Char(string='Session ID')
    interaction_id = fields.Many2one('ai.chat.memory', string='Related Interaction')
    
    # Feedback Details
    feedback_type = fields.Selection([
        ('rating', 'Rating'),
        ('bug_report', 'Bug Report'),
        ('feature_request', 'Feature Request'),
        ('general', 'General Feedback'),
        ('performance', 'Performance Issue')
    ], string='Feedback Type', required=True, default='rating')
    
    rating = fields.Selection([
        ('1', '1 - Very Poor'),
        ('2', '2 - Poor'),
        ('3', '3 - Average'),
        ('4', '4 - Good'),
        ('5', '5 - Excellent')
    ], string='Rating')
    
    title = fields.Char(string='Title')
    description = fields.Text(string='Description', required=True)
    
    # Categorization
    category = fields.Selection([
        ('accuracy', 'Response Accuracy'),
        ('speed', 'Response Speed'),
        ('usability', 'User Interface'),
        ('features', 'Features'),
        ('documentation', 'Documentation'),
        ('integration', 'ERP Integration'),
        ('other', 'Other')
    ], string='Category', default='other')
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string='Priority', default='medium')
    
    # Status Tracking
    status = fields.Selection([
        ('new', 'New'),
        ('reviewing', 'Under Review'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ], string='Status', default='new')
    
    # Response from Team
    admin_response = fields.Text(string='Admin Response')
    responded_by = fields.Many2one('res.users', string='Responded By')
    response_date = fields.Datetime(string='Response Date')
    
    # Additional Data
    browser_info = fields.Text(string='Browser Info')
    user_agent = fields.Char(string='User Agent')
    ip_address = fields.Char(string='IP Address')
    attachments = fields.Text(string='Attachments', help='JSON array of attachment info')
    
    # Metrics
    helpful_votes = fields.Integer(string='Helpful Votes', default=0)
    total_votes = fields.Integer(string='Total Votes', default=0)
    
    @api.model
    def create_feedback(self, feedback_data):
        """Create feedback entry with validation"""
        # Validate required fields
        required_fields = ['user_id', 'feedback_type', 'description']
        for field in required_fields:
            if not feedback_data.get(field):
                return {'success': False, 'error': f'Field {field} is required'}
        
        # Auto-assign priority based on feedback type
        if feedback_data['feedback_type'] == 'bug_report':
            feedback_data['priority'] = 'high'
        elif feedback_data['feedback_type'] == 'performance':
            feedback_data['priority'] = 'medium'
        
        feedback = self.create(feedback_data)
        
        # Trigger notifications for high priority feedback
        if feedback.priority in ['high', 'critical']:
            self._send_priority_notification(feedback)
        
        return {'success': True, 'feedback_id': feedback.id}
    
    def _send_priority_notification(self, feedback):
