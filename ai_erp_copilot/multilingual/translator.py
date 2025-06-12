from typing import Optional, Dict, Any
import openai
from langdetect import detect
from deep_translator import GoogleTranslator
import json
import logging

logger = logging.getLogger(__name__)

class MultilingualProcessor:
    """Handle multilingual processing for AI Copilot"""
    
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'es': 'Spanish', 
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'zh': 'Chinese',
        'ja': 'Japanese',
        'ko': 'Korean',
        'ar': 'Arabic',
        'hi': 'Hindi',
        'th': 'Thai',
        'vi': 'Vietnamese'
    }
    
    def __init__(self):
        self.translator = GoogleTranslator()
        self.language_cache = {}  # Cache for performance
    
    def detect_language(self, text: str) -> str:
        """Detect language of input text"""
        try:
            if text in self.language_cache:
                return self.language_cache[text]
            
            detected_lang = detect(text)
            
            # Map to supported languages
            if detected_lang in self.SUPPORTED_LANGUAGES:
                self.language_cache[text] = detected_lang
                return detected_lang
            else:
                # Default to English for unsupported languages
                return 'en'
                
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return 'en'  # Default to English
    
    def translate_to_english(self, text: str, source_lang: str = None) -> str:
        """Translate text to English for AI processing"""
        if not source_lang:
            source_lang = self.detect_language(text)
        
        if source_lang == 'en':
            return text
        
        try:
            translator = GoogleTranslator(source=source_lang, target='en')
            translated = translator.translate(text)
            return translated
        except Exception as e:
            logger.error(f"Translation to English failed: {e}")
            return text  # Return original if translation fails
    
    def translate_from_english(self, text: str, target_lang: str) -> str:
        """Translate English text back to target language"""
        if target_lang == 'en':
            return text
        
        try:
            translator = GoogleTranslator(source='en', target=target_lang)
            translated = translator.translate(text)
            return translated
        except Exception as e:
            logger.error(f"Translation from English failed: {e}")
            return text  # Return original if translation fails
    
    def get_language_name(self, lang_code: str) -> str:
        """Get human-readable language name"""
        return self.SUPPORTED_LANGUAGES.get(lang_code, 'Unknown')

# Odoo Model for Language Support
class AiLanguageSupport(models.Model):
    _name = 'ai.language.support'
    _description = 'AI Multilingual Support Configuration'

    name = fields.Char(string='Language Name', required=True)
    code = fields.Char(string='Language Code', required=True)
    is_active = fields.Boolean(string='Active', default=True)
    
    # Translation settings
    auto_detect = fields.Boolean(string='Auto Detect', default=True)
    translate_prompts = fields.Boolean(string='Translate User Prompts', default=True)
    translate_responses = fields.Boolean(string='Translate AI Responses', default=True)
    
    # Usage statistics
    usage_count = fields.Integer(string='Usage Count', default=0)
    last_used = fields.Datetime(string='Last Used')

class AiTranslationLog(models.Model):
    _name = 'ai.translation.log'
    _description = 'AI Translation Activity Log'

    user_id = fields.Many2one('res.users', string='User', required=True)
    session_id = fields.Char(string='Session ID')
    
    original_text = fields.Text(string='Original Text', required=True)
    translated_text = fields.Text(string='Translated Text', required=True)
    
    source_language = fields.Char(string='Source Language')
    target_language = fields.Char(string='Target Language')
    
    translation_type = fields.Selection([
        ('prompt_to_english', 'Prompt to English'),
        ('response_to_user', 'Response to User Language')
    ], string='Translation Type')
    
    confidence_score = fields.Float(string='Confidence Score')
    processing_time = fields.Float(string='Processing Time (seconds)')
    
    created_at = fields.Datetime(string='Created At', default=fields.Datetime.now)

# Enhanced Chat API with Multilingual Support
@router.post("/api/chat/multilingual")
async def multilingual_chat(
    request: dict,
    current_user: dict = Depends(get_current_active_user),
    odoo_env = Depends(get_odoo_env)
):
    """Process chat with automatic language detection and translation"""
    start_time = time.time()
    
    try:
        user_prompt = request.get('prompt', '')
        session_id = request.get('session_id', str(uuid.uuid4()))
        force_language = request.get('language')  # Optional: force specific language
        
        processor = MultilingualProcessor()
        
        # Step 1: Detect user's language
        if force_language:
            detected_lang = force_language
        else:
            detected_lang = processor.detect_language(user_prompt)
        
        logger.info(f"Detected language: {detected_lang}")
        
        # Step 2: Translate prompt to English for AI processing
        english_prompt = processor.translate_to_english(user_prompt, detected_lang)
        
        # Log translation if it occurred
        if detected_lang != 'en':
            TranslationLog = odoo_env['ai.translation.log']
            TranslationLog.create({
                'user_id': current_user['id'],
                'session_id': session_id,
                'original_text': user_prompt,
                'translated_text': english_prompt,
                'source_language': detected_lang,
                'target_language': 'en',
                'translation_type': 'prompt_to_english',
                'processing_time': time.time() - start_time
            })
        
        # Step 3: Get context (previous conversations)
        ChatMemory = odoo_env['ai.chat.memory']
        context = ChatMemory.get_recent_context(current_user['id'], session_id, limit=3)
        
        # Step 4: Prepare enhanced prompt with context
        enhanced_prompt = prepare_multilingual_prompt(english_prompt, context, detected_lang)
        
        # Step 5: Get AI response
        ai_response_english = await get_multilingual_ai_response(enhanced_prompt, detected_lang)
        
        # Step 6: Translate response back to user's language
        if detected_lang != 'en':
            ai_response_user_lang = processor.translate_from_english(ai_response_english, detected_lang)
            
            # Log response translation
            TranslationLog.create({
                'user_id': current_user['id'],
                'session_id': session_id,
                'original_text': ai_response_english,
                'translated_text': ai_response_user_lang,
                'source_language': 'en',
                'target_language': detected_lang,
                'translation_type': 'response_to_user',
                'processing_time': time.time() - start_time
            })
        else:
            ai_response_user_lang = ai_response_english
        
        # Step 7: Save interaction to memory
        ChatMemory.save_chat_interaction(
            user_id=current_user['id'],
            session_id=session_id,
            prompt=user_prompt,  # Save original language
            response=ai_response_user_lang,  # Save in user's language
            context_data={
                'detected_language': detected_lang,
                'english_prompt': english_prompt,
                'english_response': ai_response_english
            }
        )
        
        # Step 8: Update language usage statistics
        LanguageSupport = odoo_env['ai.language.support']
        lang_record = LanguageSupport.search([('code', '=', detected_lang)], limit=1)
        if lang_record:
            lang_record.usage_count += 1
            lang_record.last_used = fields.Datetime.now()
        
        total_time = time.time() - start_time
        
        return {
            'response': ai_response_user_lang,
            'session_id': session_id,
            'detected_language': detected_lang,
            'language_name': processor.get_language_name(detected_lang),
            'translation_occurred': detected_lang != 'en',
            'processing_time': round(total_time, 2),
            'original_prompt': user_prompt,
            'english_version': english_prompt if detected_lang != 'en' else None
        }
        
    except Exception as e:
        logger.error(f"Multilingual chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def prepare_multilingual_prompt(prompt: str, context: list, user_language: str) -> str:
    """Prepare enhanced prompt with multilingual context"""
    system_message = f"""
    You are an AI assistant for ERP systems with multilingual support.
    The user's preferred language is: {user_language}
    
    Previous conversation context (translated to English):
    """
    
    if context:
        for i, ctx in enumerate(context, 1):
            system_message += f"{i}. User: {ctx.get('english_prompt', ctx['prompt'])}\n"
            system_message += f"   AI: {ctx.get('english_response', ctx['response'])[:100]}...\n"
    
    system_message += f"\nCurrent question (translated to English): {prompt}\n"
    system_message += """
    Please provide a helpful response. Be culturally appropriate and consider 
    regional business practices when relevant.
    """
    
    return system_message

async def get_multilingual_ai_response(prompt: str, user_language: str) -> str:
    """Get AI response with language context"""
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {
                    "role": "system", 
                    "content": f"You are an ERP AI assistant. The user's language is {user_language}. "
                              f"Provide responses that are culturally appropriate and consider regional business practices."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "I apologize, but I'm having trouble processing your request right now. Please try again."

# Language Management Endpoints
@router.get("/api/languages/supported")
async def get_supported_languages():
    """Get list of supported languages"""
    processor = MultilingualProcessor()
    return {
        "languages": [
            {"code": code, "name": name}
            for code, name in processor.SUPPORTED_LANGUAGES.items()
        ]
    }

@router.get("/api/languages/statistics")
async def get_language_statistics(
    current_user: dict = Depends(require_permission("view_analytics")),
    odoo_env = Depends(get_odoo_env)
):
    """Get language usage statistics"""
    LanguageSupport = odoo_env['ai.language.support']
    TranslationLog = odoo_env['ai.translation.log']
    
    # Get usage statistics
    language_stats = LanguageSupport.search_read(
        [('is_active', '=', True)],
        ['code', 'name', 'usage_count', 'last_used']
    )
    
    # Get recent translation activity
    recent_translations = TranslationLog.search_read(
        [('create_date', '>=', fields.Datetime.now() - timedelta(days=30))],
        ['source_language', 'target_language', 'translation_type', 'processing_time'],
        limit=100
    )
    
    return {
        "language_usage": language_stats,
        "recent_activity": recent_translations,
        "total_translations_last_30_days": len(recent_translations)
    }

@router.post("/api/languages/configure")
async def configure_language_support(
    config: dict,
    current_user: dict = Depends(require_permission("configure_system")),
    odoo_env = Depends(get_odoo_env)
):
    """Configure language support settings"""
    LanguageSupport = odoo_env['ai.language.support']
    
    language_code = config.get('language_code')
    settings = config.get('settings', {})
    
    lang_record = LanguageSupport.search([('code', '=', language_code)], limit=1)
    
    if lang_record:
        lang_record.write(settings)
    else:
        settings.update({
            'code': language_code,
            'name': config.get('language_name', language_code.upper())
        })
        LanguageSupport.create(settings)
    
    return {"message": f"Language configuration updated for {language_code}"}
