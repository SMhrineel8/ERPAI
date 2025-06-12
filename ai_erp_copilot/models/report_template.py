# models/report_template.py
from odoo import models, fields, api
import json

class AiReportTemplate(models.Model):
    _name = 'ai.report.template'
    _description = 'AI Custom Report Templates'
    _order = 'name'

    name = fields.Char(string='Template Name', required=True)
    description = fields.Text(string='Description')
    category = fields.Selection([
        ('sales', 'Sales Reports'),
        ('finance', 'Financial Reports'),
        ('inventory', 'Inventory Reports'),
        ('hr', 'HR Reports'),
        ('custom', 'Custom Reports')
    ], string='Category', required=True, default='custom')
    
    # Template Configuration
    data_sources = fields.Text(string='Data Sources', help='JSON config of Odoo models to query')
    filters = fields.Text(string='Default Filters', help='JSON config of default filters')
    grouping = fields.Text(string='Grouping Configuration', help='JSON config for data grouping')
    calculations = fields.Text(string='Calculations', help='JSON config for calculations and aggregations')
    
    # AI Prompt Configuration
    ai_prompt_template = fields.Text(string='AI Prompt Template', 
                                   help='Template for AI to generate natural language reports')
    output_format = fields.Selection([
        ('text', 'Natural Language Text'),
        ('table', 'Structured Table'),
        ('chart', 'Chart Description'),
        ('mixed', 'Mixed Format')
    ], string='Output Format', default='text')
    
    # Metadata
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    is_public = fields.Boolean(string='Public Template', default=False)
    usage_count = fields.Integer(string='Usage Count', default=0)
    
    @api.model
    def generate_report(self, template_id, custom_filters=None, ai_enhance=True):
        """Generate report using template"""
        template = self.browse(template_id)
        if not template.exists():
            return {'error': 'Template not found'}
        
        try:
            # Parse configuration
            data_sources = json.loads(template.data_sources or '{}')
            filters = json.loads(template.filters or '{}')
            grouping = json.loads(template.grouping or '{}')
            calculations = json.loads(template.calculations or '{}')
            
            # Apply custom filters
            if custom_filters:
                filters.update(custom_filters)
            
            # Execute data query
            report_data = self._execute_report_query(data_sources, filters, grouping, calculations)
            
            # AI Enhancement
            if ai_enhance and template.ai_prompt_template:
                ai_report = self._generate_ai_report(template, report_data)
                return {
                    'raw_data': report_data,
                    'ai_report': ai_report,
                    'template': template.name,
                    'generated_at': fields.Datetime.now().isoformat()
                }
            
            return {
                'raw_data': report_data,
                'template': template.name,
                'generated_at': fields.Datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _execute_report_query(self, data_sources, filters, grouping, calculations):
        """Execute the actual data query"""
        results = {}
        
        for source_name, source_config in data_sources.items():
            model_name = source_config.get('model')
            fields_to_read = source_config.get('fields', [])
            
            if not model_name:
                continue
                
            # Build domain from filters
            domain = []
            if source_name in filters:
                for filter_key, filter_value in filters[source_name].items():
                    if filter_value:
                        domain.append((filter_key, '=', filter_value))
            
            # Execute query
            Model = self.env[model_name]
            records = Model.search_read(domain, fields_to_read)
            
            # Apply grouping if specified
            if source_name in grouping:
                records = self._apply_grouping(records, grouping[source_name])
            
            # Apply calculations
            if source_name in calculations:
                records = self._apply_calculations(records, calculations[source_name])
            
            results[source_name] = records
        
        return results
    
    def _apply_grouping(self, records, group_config):
        """Apply grouping to records"""
        group_by_field = group_config.get('field')
        if not group_by_field:
            return records
        
        grouped = {}
        for record in records:
            key = record.get(group_by_field, 'Unknown')
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(record)
        
        return grouped
    
    def _apply_calculations(self, records, calc_config):
        """Apply calculations to records"""
        if isinstance(records, dict):  # Grouped data
            for group_key, group_records in records.items():
                records[group_key] = self._calculate_metrics(group_records, calc_config)
        else:  # Flat data
            records = self._calculate_metrics(records, calc_config)
        
        return records
    
    def _calculate_metrics(self, records, calc_config):
        """Calculate metrics for a set of records"""
        if not records:
            return records
        
        calculations = {}
        for calc_name, calc_def in calc_config.items():
            field = calc_def.get('field')
            operation = calc_def.get('operation', 'sum')
            
            if field and operation:
                values = [record.get(field, 0) for record in records if record.get(field)]
                
                if operation == 'sum':
                    calculations[calc_name] = sum(values)
                elif operation == 'avg':
                    calculations[calc_name] = sum(values) / len(values) if values else 0
                elif operation == 'count':
                    calculations[calc_name] = len(values)
                elif operation == 'max':
                    calculations[calc_name] = max(values) if values else 0
                elif operation == 'min':
                    calculations[calc_name] = min(values) if values else 0
        
        return {
            'records': records,
            'metrics': calculations
        }
    
    def _generate_ai_report(self, template, report_data):
        """Generate AI-enhanced report"""
        prompt = template.ai_prompt_template.format(
            report_data=json.dumps(report_data, indent=2, default=str)
        )
        
        # This would call your AI service
        # For now, returning a placeholder
        return f"AI-generated report based on {template.name} template with {len(report_data)} data sources"

# FastAPI endpoints for report builder
# api/reports.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/api/reports", tags=["reports"])

class ReportTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    data_sources: Dict[str, Any]
    filters: Optional[Dict[str, Any]] = None
    grouping: Optional[Dict[str, Any]] = None
    calculations: Optional[Dict[str, Any]] = None
    ai_prompt_template: Optional[str] = None
    output_format: str = "text"
    is_public: bool = False

class ReportGenerateRequest(BaseModel):
    template_id: int
    custom_filters: Optional[Dict[str, Any]] = None
    ai_enhance: bool = True

@router.post("/templates")
async def create_report_template(
    template: ReportTemplateCreate,
    current_user: dict = Depends(get_current_user),
    odoo_env = Depends(get_odoo_env)
):
    """Create a new report template"""
    try:
        ReportTemplate = odoo_env['ai.report.template']
        
        template_data = {
            'name': template.name,
            'description': template.description,
            'category': template.category,
            'data_sources': json.dumps(template.data_sources),
            'filters': json.dumps(template.filters or {}),
            'grouping': json.dumps(template.grouping or {}),
            'calculations': json.dumps(template.calculations or {}),
            'ai_prompt_template': template.ai_prompt_template,
            'output_format': template.output_format,
            'is_public': template.is_public,
            'created_by': current_user['id']
        }
        
        new_template = ReportTemplate.create(template_data)
        return {"id": new_template.id, "message": "Template created successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates")
async def get_report_templates(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    odoo_env = Depends(get_odoo_env)
):
    """Get available report templates"""
    try:
        ReportTemplate = odoo_env['ai.report.template']
        
        domain = [
            '|',
            ('created_by', '=', current_user['id']),
            ('is_public', '=', True)
        ]
        
        if category:
            domain.append(('category', '=', category))
        
        templates = ReportTemplate.search_read(
            domain,
            ['name', 'description', 'category', 'created_by', 'usage_count']
        )
        
        return {"templates": templates}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate")
async def generate_report(
    request: ReportGenerateRequest,
    current_user: dict = Depends(get_current_user),
    odoo_env = Depends(get_odoo_env)
):
    """Generate a report using a template"""
    try:
        ReportTemplate = odoo_env['ai.report.template']
        
        result = ReportTemplate.generate_report(
            template_id=request.template_id,
            custom_filters=request.custom_filters,
            ai_enhance=request.ai_enhance
        )
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        # Update usage count
        template = ReportTemplate.browse(request.template_id)
        template.usage_count += 1
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Frontend component for report builder
# static/js/report_builder.js
class ReportBuilder {
    constructor() {
        this.currentTemplate = null;
        this.previewData = null;
    }
    
    async loadTemplates() {
        try {
            const response = await fetch('/api/reports/templates');
            const data = await response.json();
            this.renderTemplatesList(data.templates);
        } catch (error) {
            console.error('Error loading templates:', error);
        }
    }
    
    renderTemplatesList(templates) {
        const container = document.getElementById('templates-list');
        container.innerHTML = templates.map(template => `
            <div class="template-card" data-template-id="${template.id}">
                <h3>${template.name}</h3>
                <p>${template.description || 'No description'}</p>
                <span class="category">${template.category}</span>
                <span class="usage">Used ${template.usage_count} times</span>
                <button onclick="reportBuilder.generateReport(${template.id})">Generate</button>
                <button onclick="reportBuilder.editTemplate(${template.id})">Edit</button>
            </div>
        `).join('');
    }
    
    async generateReport(templateId, customFilters = null) {
        try {
            const response = await fetch('/api/reports/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    template_id: templateId,
                    custom_filters: customFilters,
                    ai_enhance: true
                })
            });
            
            const result = await response.json();
            this.displayReport(result);
        } catch (error) {
            console.error('Error generating report:', error);
        }
    }
    
    displayReport(reportData) {
        const container = document.getElementById('report-output');
        container.innerHTML = `
            <div class="report-header">
                <h2>Report: ${reportData.template}</h2>
                <p>Generated: ${new Date(reportData.generated_at).toLocaleString()}</p>
            </div>
            <div class="report-content">
                ${reportData.ai_report ? `
                    <div class="ai-report">
                        <h3>AI Analysis</h3>
                        <p>${reportData.ai_report}</p>
                    </div>
                ` : ''}
                <div class="raw-data">
                    <h3>Data</h3>
                    <pre>${JSON.stringify(reportData.raw_data, null, 2)}</pre>
                </div>
            </div>
        `;
    }
}

const reportBuilder = new ReportBuilder();
