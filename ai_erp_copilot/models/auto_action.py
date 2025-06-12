from odoo import models, fields, api
import json
import re
from datetime import datetime, timedelta

class AiAutoAction(models.Model):
    _name = 'ai.auto.action'
    _description = 'AI Auto Actions for ERP Automation'
    _order = 'create_date desc'

    name = fields.Char(string='Action Name', required=True)
    description = fields.Text(string='Description')
    trigger_phrase = fields.Char(string='Trigger Phrase', help='Natural language phrase that triggers this action')
    
    # Action Configuration
    action_type = fields.Selection([
        ('create', 'Create Record'),
        ('update', 'Update Records'),
        ('delete', 'Delete Records'),
        ('send_email', 'Send Email'),
        ('generate_report', 'Generate Report'),
        ('custom_code', 'Custom Code Execution')
    ], string='Action Type', required=True)
    
    target_model = fields.Char(string='Target Model', help='Odoo model to operate on')
    action_config = fields.Text(string='Action Configuration', help='JSON configuration for the action')
    
    # Approval & Safety
    requires_approval = fields.Boolean(string='Requires Approval', default=True)
    approval_user_ids = fields.Many2many('res.users', string='Approval Users')
    
    # Execution Tracking
    execution_count = fields.Integer(string='Execution Count', default=0)
    last_executed = fields.Datetime(string='Last Executed')
    is_active = fields.Boolean(string='Active', default=True)
    
    # Safety Limits
    max_executions_per_day = fields.Integer(string='Max Executions Per Day', default=10)
    max_records_affected = fields.Integer(string='Max Records Affected', default=100)

class AiActionExecution(models.Model):
    _name = 'ai.action.execution'
    _description = 'AI Action Execution Log'
    _order = 'create_date desc'

    action_id = fields.Many2one('ai.auto.action', string='Action', required=True)
    user_id = fields.Many2one('res.users', string='User', required=True)
    
    # Request Details
    original_prompt = fields.Text(string='Original Prompt')
    parsed_parameters = fields.Text(string='Parsed Parameters')
    
    # Execution Details
    status = fields.Selection([
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('executing', 'Executing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='pending')
    
    execution_result = fields.Text(string='Execution Result')
    records_affected = fields.Integer(string='Records Affected', default=0)
    
    # Approval Workflow
    approved_by = fields.Many2one('res.users', string='Approved By')
    approved_at = fields.Datetime(string='Approved At')
    approval_notes = fields.Text(string='Approval Notes')

class AiActionProcessor(models.Model):
    _name = 'ai.action.processor'
    _description = 'AI Action Processing Engine'

    @api.model
    def process_natural_language_request(self, prompt, user_id):
        """Process natural language request and identify potential actions"""
        try:
            # Find matching actions
            matching_actions = self._find_matching_actions(prompt)
            
            if not matching_actions:
                return {
                    'status': 'no_match',
                    'message': 'No matching actions found for this request.'
                }
            
            # Parse parameters from prompt
            best_match = matching_actions[0]
            parameters = self._parse_action_parameters(prompt, best_match)
            
            # Create execution request
            execution = self.env['ai.action.execution'].create({
                'action_id': best_match.id,
                'user_id': user_id,
                'original_prompt': prompt,
                'parsed_parameters': json.dumps(parameters),
                'status': 'pending' if best_match.requires_approval else 'approved'
            })
            
            # If no approval required, execute immediately
            if not best_match.requires_approval:
                return self._execute_action(execution.id)
            
            return {
                'status': 'pending_approval',
                'execution_id': execution.id,
                'action_name': best_match.name,
                'parameters': parameters,
                'message': f'Action "{best_match.name}" requires approval. Execution ID: {execution.id}'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _find_matching_actions(self, prompt):
        """Find actions that match the natural language prompt"""
        actions = self.env['ai.auto.action'].search([('is_active', '=', True)])
        
        matches = []
        prompt_lower = prompt.lower()
        
        for action in actions:
            if action.trigger_phrase and action.trigger_phrase.lower() in prompt_lower:
                matches.append(action)
        
        # Sort by trigger phrase length (more specific matches first)
        matches.sort(key=lambda x: len(x.trigger_phrase or ''), reverse=True)
        return matches
    
    def _parse_action_parameters(self, prompt, action):
        """Parse parameters from natural language prompt"""
        parameters = {}
        
        # Load action configuration
        config = json.loads(action.action_config or '{}')
        parameter_patterns = config.get('parameter_patterns', {})
        
        for param_name, pattern in parameter_patterns.items():
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                parameters[param_name] = match.group(1)
        
        return parameters
    
    @api.model
    def execute_action(self, execution_id):
        """Execute an approved action"""
        return self._execute_action(execution_id)
    
    def _execute_action(self, execution_id):
        """Internal method to execute action"""
        execution = self.env['ai.action.execution'].browse(execution_id)
        if not execution.exists():
            return {'status': 'error', 'message': 'Execution not found'}
        
        try:
            execution.status = 'executing'
            action = execution.action_id
            parameters = json.loads(execution.parsed_parameters or '{}')
            
            # Safety checks
            if not self._safety_checks(action, execution.user_id):
                execution.status = 'failed'
                execution.execution_result = 'Safety checks failed'
                return {'status': 'error', 'message': 'Safety checks failed'}
            
            # Execute based on action type
            result = self._dispatch_action(action, parameters)
            
            # Update execution record
            execution.status = 'completed'
            execution.execution_result = json.dumps(result)
            execution.records_affected = result.get('records_affected', 0)
            
            # Update action statistics
            action.execution_count += 1
            action.last_executed = fields.Datetime.now()
            
            return {
                'status': 'completed',
                'result': result,
                'execution_id': execution_id
            }
            
        except Exception as e:
            execution.status = 'failed'
            execution.execution_result = str(e)
            return {'status': 'error', 'message': str(e)}
    
    def _safety_checks(self, action, user_id):
        """Perform safety checks before execution"""
        # Check daily execution limit
        today = fields.Date.today()
        today_executions = self.env['ai.action.execution'].search_count([
            ('action_id', '=', action.id),
            ('user_id', '=', user_id),
            ('create_date', '>=', today),
            ('status', '=', 'completed')
        ])
        
        if today_executions >= action.max_executions_per_day:
            return False
        
        return True
    
    def _dispatch_action(self, action, parameters):
        """Dispatch action execution based on type"""
        if action.action_type == 'create':
            return self._execute_create_action(action, parameters)
        elif action.action_type == 'update':
            return self._execute_update_action(action, parameters)
        elif action.action_type == 'send_email':
            return self._execute_email_action(action, parameters)
        elif action.action_type == 'generate_report':
            return self._execute_report_action(action, parameters)
        else:
            raise ValueError(f"Unsupported action type: {action.action_type}")
    
    def _execute_create_action(self, action, parameters):
        """Execute record creation action"""
        config = json.loads(action.action_config or '{}')
        model_name = action.target_model
        
        if not model_name:
            raise ValueError("Target model not specified")
