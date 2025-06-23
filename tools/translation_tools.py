"""Translation and multi-language support tools with Google Translate API."""

import logging
from typing import Dict, Any, List, Optional
from google.cloud import translate_v2 as translate


logger = logging.getLogger(__name__)

# Initialize Google Translate client
translate_client = translate.Client()

def detect_language(text: str) -> Dict[str, Any]:
    """
    Detect the language of customer input using Google Translate API.
    
    Args:
        text (str): Text to analyze
    
    Returns:
        Dict containing language detection results
    """
    logger.info(f"Detecting language for text: {text[:50]}...")
    
    try:
        # Use Google Translate API for language detection
        result = translate_client.detect_language(text)
        
        detected_language = result['language']
        confidence = result['confidence']
        
        # Check if language is supported
        supported_languages = get_supported_languages()
        is_supported = detected_language in supported_languages
        
        return {
            "detected_language": detected_language,
            "confidence": confidence,
            "supported": is_supported,
            "input_text": text[:100],  # First 100 chars for reference
            "is_reliable": confidence > 0.7
        }
        
    except Exception as e:
        logger.error(f"Error in language detection: {str(e)}")
        return {
            "detected_language": "en",  # Default to English
            "confidence": 0.0,
            "supported": True,
            "error": str(e),
            "input_text": text[:100]
        }

def translate_text(
    text: str, 
    target_language: str, 
    source_language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Translate text to target language using Google Translate API.
    
    Args:
        text (str): Text to translate
        target_language (str): Target language code
        source_language (str): Source language code (optional, auto-detected if None)
    
    Returns:
        Dict containing translation results
    """
    logger.info(f"Translating text to {target_language}")
    
    try:
        # Perform translation
        result = translate_client.translate(
            text,
            target_language=target_language,
            source_language=source_language
        )
        
        return {
            "original_text": text,
            "translated_text": result['translatedText'],
            "source_language": result['detectedSourceLanguage'] if source_language is None else source_language,
            "target_language": target_language,
            "confidence": 0.95,  # Google Translate is generally high confidence
            "translation_model": "google_translate_v2"
        }
        
    except Exception as e:
        logger.error(f"Error in translation: {str(e)}")
        return {
            "original_text": text,
            "translated_text": text,  # Return original if translation fails
            "source_language": source_language or "unknown",
            "target_language": target_language,
            "confidence": 0.0,
            "error": str(e)
        }

def get_supported_languages() -> List[str]:
    """
    Get list of supported languages from Google Translate API.
    
    Returns:
        List of supported language codes
    """
    logger.info("Getting supported languages from Google Translate")
    
    try:
        # Get supported languages
        results = translate_client.get_languages()
        
        language_codes = [lang['language'] for lang in results]
        
        return language_codes
        
    except Exception as e:
        logger.error(f"Error getting supported languages: {str(e)}")
        # Return common languages as fallback
        return [
            "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh",
            "ar", "hi", "th", "vi", "tr", "pl", "nl", "sv", "da", "no"
        ]

def get_language_info(language_code: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific language.
    
    Args:
        language_code (str): Language code to get info for
    
    Returns:
        Dict containing language information
    """
    logger.info(f"Getting language info for: {language_code}")
    
    try:
        # Get languages with target parameter to get names in specific language
        results = translate_client.get_languages(target_language='en')
        
        language_info = None
        for lang in results:
            if lang['language'] == language_code:
                language_info = lang
                break
        
        if language_info:
            return {
                "language_code": language_code,
                "language_name": language_info['name'],
                "supported": True,
                "rtl": language_code in ['ar', 'he', 'fa', 'ur'],  # Right-to-left languages
                "voice_supported": language_code in get_voice_supported_languages()
            }
        else:
            return {
                "language_code": language_code,
                "language_name": "Unknown",
                "supported": False,
                "rtl": False,
                "voice_supported": False
            }
            
    except Exception as e:
        logger.error(f"Error getting language info: {str(e)}")
        return {
            "language_code": language_code,
            "language_name": "Unknown",
            "supported": False,
            "error": str(e)
        }

def get_voice_supported_languages() -> List[str]:
    """Get languages supported by Google Text-to-Speech."""
    # Common languages supported by Google TTS
    return [
        "en-US", "en-GB", "en-AU", "en-IN",
        "es-ES", "es-US", "es-MX",
        "fr-FR", "fr-CA",
        "de-DE",
        "it-IT",
        "pt-BR", "pt-PT",
        "ru-RU",
        "ja-JP",
        "ko-KR",
        "zh-CN", "zh-TW",
        "ar-XA",
        "hi-IN",
        "th-TH",
        "vi-VN",
        "tr-TR",
        "pl-PL",
        "nl-NL",
        "sv-SE",
        "da-DK",
        "no-NO"
    ]

def get_localized_responses(language: str) -> Dict[str, str]:
    """
    Get localized response templates for a specific language.
    
    Args:
        language (str): Language code
    
    Returns:
        Dict of localized response templates
    """
    logger.info(f"Getting localized responses for language: {language}")
    
    # Base templates in English
    base_templates = {
        "greeting": "Hello! How can I help you today?",
        "escalation": "I'm connecting you with a specialist who can help.",
        "resolution": "Is your issue resolved?",
        "thanks": "Thank you for contacting support!",
        "wait": "Please wait while I process your request.",
        "error": "I'm sorry, I encountered an error. Please try again.",
        "clarification": "Could you please provide more details?",
        "satisfaction": "How would you rate your support experience?",
        "goodbye": "Thank you for contacting us. Have a great day!"
    }
    
    # If language is English, return base templates
    if language.startswith('en'):
        return base_templates
    
    try:
        # Translate all templates to target language
        localized_templates = {}
        
        for key, template in base_templates.items():
            translation_result = translate_text(template, language, "en")
            localized_templates[key] = translation_result["translated_text"]
        
        return localized_templates
        
    except Exception as e:
        logger.error(f"Error getting localized responses: {str(e)}")
        # Return English templates as fallback
        return base_templates

def translate_conversation_history(
    conversation: List[Dict[str, Any]], 
    target_language: str
) -> List[Dict[str, Any]]:
    """
    Translate entire conversation history to target language.
    
    Args:
        conversation (List): List of conversation messages
        target_language (str): Target language code
    
    Returns:
        List of translated conversation messages
    """
    logger.info(f"Translating conversation history to {target_language}")
    
    translated_conversation = []
    
    try:
        for message in conversation:
            translated_message = message.copy()
            
            # Translate the message content
            if 'content' in message and message['content']:
                translation_result = translate_text(
                    message['content'], 
                    target_language,
                    message.get('language', 'en')
                )
                translated_message['content'] = translation_result['translated_text']
                translated_message['original_content'] = message['content']
                translated_message['translated_language'] = target_language
            
            translated_conversation.append(translated_message)
        
        return translated_conversation
        
    except Exception as e:
        logger.error(f"Error translating conversation: {str(e)}")
        return conversation  # Return original if translation fails

def create_multilingual_response(
    text: str, 
    primary_language: str, 
    additional_languages: List[str] = None
) -> Dict[str, Any]:
    """
    Create response in multiple languages.
    
    Args:
        text (str): Original response text
        primary_language (str): Primary language code
        additional_languages (List): Additional languages to translate to
    
    Returns:
        Dict containing response in multiple languages
    """
    logger.info(f"Creating multilingual response in {primary_language} + {additional_languages}")
    
    if additional_languages is None:
        additional_languages = []
    
    multilingual_response = {
        "primary_language": primary_language,
        "primary_text": text,
        "translations": {}
    }
    
    try:
        # Translate to additional languages
        for lang in additional_languages:
            if lang != primary_language:
                translation_result = translate_text(text, lang, primary_language)
                multilingual_response["translations"][lang] = {
                    "text": translation_result["translated_text"],
                    "confidence": translation_result["confidence"]
                }
        
        multilingual_response["total_languages"] = 1 + len(multilingual_response["translations"])
        multilingual_response["status"] = "success"
        
        return multilingual_response
        
    except Exception as e:
        logger.error(f"Error creating multilingual response: {str(e)}")
        multilingual_response["error"] = str(e)
        multilingual_response["status"] = "partial"
        return multilingual_response