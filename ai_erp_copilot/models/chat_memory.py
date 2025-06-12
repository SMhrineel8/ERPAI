# models/chat_memory.py
from odoo import models, fields, api
import json

class AiChatMemory(models.Model):
    _name = 'ai.chat.memory'
    _description = 'AI Chat Memory for Context Tracking'
    _order = 'create_date desc'

    user_id = fields.Many2one('res.users', string='User', required=True, default=lambda self: self.env.user)
    session_id = fields.Char(string='Session ID', required=True)
    prompt = fields.Text(string='User Prompt', required=True)
    response = fields.Text(string='AI Response')
    context_data = fields.Text(string='Context Data')  # JSON string for additional context
    token_count = fields.Integer(string='Token Count', default=0)
    created_at = fields.Datetime(string='Created At', default=fields.Datetime.now)

    @api.model
    def get_recent_context(self, user_id, session_id, limit=3):
        """Get recent chat history for context"""
        records = self.search([
            ('user_id', '=', user_id),
            ('session_id', '=', session_id)
        ], limit=limit, order='create_date desc')
        
        context = []
        for record in reversed(records):  # Reverse to get chronological order
            context.append({
                'prompt': record.prompt,
                'response': record.response,
                'timestamp': record.created_at.isoformat(),
                'context_data': json.loads(record.context_data or '{}')
            })
        return context

    @api.model
    def save_chat_interaction(self, user_id, session_id, prompt, response, context_data=None, token_count=0):
        """Save chat interaction for future context"""
        return self.create({
            'user_id': user_id,
            'session_id': session_id,
            'prompt': prompt,
            'response': response,
            'context_data': json.dumps(context_data or {}),
            'token_count': token_count
        })

    @api.model
    def cleanup_old_memories(self, days_old=30):
        """Clean up old chat memories to manage storage"""
        cutoff_date = fields.Datetime.now() - timedelta(days=days_old)
        old_records = self.search([('created_at', '<', cutoff_date)])
        return old_records.unlink()

# FastAPI endpoints for chat memory
# api/chat_memory.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None
    include_context: bool = True

class ChatResponse(BaseModel):
    response: str
    session_id: str
    context_used: List[dict]
    token_count: int

@router.post("/message", response_model=ChatResponse)
async def send_chat_message(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    odoo_env = Depends(get_odoo_env)
):
    """Send chat message with context awareness"""
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get recent context
        context = []
        if request.include_context:
            ChatMemory = odoo_env['ai.chat.memory']
            context = ChatMemory.get_recent_context(
                current_user['id'], 
                session_id, 
                limit=3
            )
        
        # Prepare enhanced prompt with context
        enhanced_prompt = prepare_contextual_prompt(request.prompt, context)
        
        # Get AI response
        ai_response, token_count = await get_ai_response(enhanced_prompt)
        
        # Save interaction
        ChatMemory.save_chat_interaction(
            user_id=current_user['id'],
            session_id=session_id,
            prompt=request.prompt,
            response=ai_response,
            context_data={'enhanced_prompt': enhanced_prompt},
            token_count=token_count
        )
        
        return ChatResponse(
            response=ai_response,
            session_id=session_id,
            context_used=context,
            token_count=token_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    odoo_env = Depends(get_odoo_env)
):
    """Get chat history for a session"""
    try:
        ChatMemory = odoo_env['ai.chat.memory']
        history = ChatMemory.search_read([
            ('user_id', '=', current_user['id']),
            ('session_id', '=', session_id)
        ], fields=['prompt', 'response', 'created_at', 'token_count'], 
        limit=limit, order='create_date desc')
        
        return {"history": history}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def prepare_contextual_prompt(current_prompt: str, context: List[dict]) -> str:
    """Prepare enhanced prompt with conversation context"""
    if not context:
        return current_prompt
    
    context_text = "Previous conversation context:\n"
    for i, ctx in enumerate(context, 1):
        context_text += f"{i}. User: {ctx['prompt']}\n   AI: {ctx['response'][:100]}...\n"
    
    return f"{context_text}\nCurrent question: {current_prompt}"

async def get_ai_response(prompt: str) -> tuple[str, int]:
    """Get AI response using OpenAI API"""
    import openai
    
    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an ERP AI assistant with access to conversation history."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000
    )
    
    return response.choices[0].message.content, response.usage.total_tokens
