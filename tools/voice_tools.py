"""Voice processing tools with Google Speech-to-Text and Text-to-Speech integration."""

import logging
import asyncio
import base64
import io
from typing import Dict, Any, Optional
from google.cloud import speech, texttospeech
from google.cloud.speech import RecognitionConfig, RecognitionAudio
from google.cloud.texttospeech import SsmlVoiceGender, AudioConfig, AudioEncoding

logger = logging.getLogger(__name__)

# Initialize Google Cloud clients
speech_client = speech.SpeechClient()
tts_client = texttospeech.TextToSpeechClient()

def speech_to_text(
    audio_data: str, 
    language: str = "en-US",
    encoding: str = "WEBM_OPUS",
    sample_rate: int = 48000
) -> Dict[str, Any]:
    """
    Convert speech audio to text using Google Speech-to-Text API.
    
    Args:
        audio_data (str): Base64 encoded audio data
        language (str): Language code for speech recognition
        encoding (str): Audio encoding format
        sample_rate (int): Audio sample rate in Hz
    
    Returns:
        Dict containing transcription results
    """
    logger.info(f"Converting speech to text in language: {language}")
    
    try:
        # Decode base64 audio data
        audio_bytes = base64.b64decode(audio_data)
        
        # Configure recognition settings
        config = RecognitionConfig(
            encoding=getattr(RecognitionConfig.AudioEncoding, encoding),
            sample_rate_hertz=sample_rate,
            language_code=language,
            enable_automatic_punctuation=True,
            enable_word_confidence=True,
            enable_word_time_offsets=True,
            model="latest_long",  # Use latest model for better accuracy
            use_enhanced=True,    # Use enhanced model if available
        )
        
        # Create audio object
        audio = RecognitionAudio(content=audio_bytes)
        
        # Perform speech recognition
        response = speech_client.recognize(config=config, audio=audio)
        
        if not response.results:
            return {
                "transcription": "",
                "confidence": 0.0,
                "language": language,
                "error": "No speech detected in audio",
                "words_count": 0,
                "audio_duration": 0.0
            }
        
        # Get the best result
        result = response.results[0]
        alternative = result.alternatives[0]
        
        # Extract word-level information
        words_info = []
        for word in alternative.words:
            words_info.append({
                "word": word.word,
                "confidence": word.confidence,
                "start_time": word.start_time.total_seconds(),
                "end_time": word.end_time.total_seconds()
            })
        
        # Calculate audio duration
        audio_duration = words_info[-1]["end_time"] if words_info else 0.0
        
        return {
            "transcription": alternative.transcript,
            "confidence": alternative.confidence,
            "language": language,
            "words_count": len(alternative.transcript.split()),
            "audio_duration": audio_duration,
            "words_info": words_info,
            "encoding": encoding,
            "sample_rate": sample_rate
        }
        
    except Exception as e:
        logger.error(f"Error in speech-to-text conversion: {str(e)}")
        return {
            "transcription": "",
            "confidence": 0.0,
            "language": language,
            "error": str(e),
            "words_count": 0,
            "audio_duration": 0.0
        }

def text_to_speech(
    text: str, 
    language: str = "en-US", 
    voice_name: Optional[str] = None,
    voice_gender: str = "NEUTRAL",
    speaking_rate: float = 1.0,
    pitch: float = 0.0,
    audio_encoding: str = "MP3"
) -> Dict[str, Any]:
    """
    Convert text to speech using Google Text-to-Speech API.
    
    Args:
        text (str): Text to convert to speech
        language (str): Language code for speech synthesis
        voice_name (str): Specific voice name (optional)
        voice_gender (str): Voice gender (NEUTRAL, MALE, FEMALE)
        speaking_rate (float): Speaking rate (0.25 to 4.0)
        pitch (float): Voice pitch (-20.0 to 20.0)
        audio_encoding (str): Output audio encoding
    
    Returns:
        Dict containing audio generation results
    """
    logger.info(f"Converting text to speech: {text[:50]}...")
    
    try:
        # Create synthesis input
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Configure voice settings
        voice_config = texttospeech.VoiceSelectionParams(
            language_code=language,
            ssml_gender=getattr(SsmlVoiceGender, voice_gender)
        )
        
        # Set specific voice if provided
        if voice_name:
            voice_config.name = voice_name
        
        # Configure audio settings
        audio_config = AudioConfig(
            audio_encoding=getattr(AudioEncoding, audio_encoding),
            speaking_rate=speaking_rate,
            pitch=pitch,
            effects_profile_id=["telephony-class-application"]  # Optimize for telephony
        )
        
        # Perform text-to-speech synthesis
        response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice_config,
            audio_config=audio_config
        )
        
        # Encode audio content as base64
        audio_base64 = base64.b64encode(response.audio_content).decode('utf-8')
        
        # Estimate duration (rough calculation)
        estimated_duration = len(text.split()) * 0.6  # ~0.6 seconds per word
        
        return {
            "audio_content": audio_base64,
            "audio_format": audio_encoding.lower(),
            "duration": estimated_duration,
            "language": language,
            "voice_name": voice_name or f"{language}-{voice_gender}",
            "speaking_rate": speaking_rate,
            "pitch": pitch,
            "text_length": len(text),
            "word_count": len(text.split()),
            "file_size": len(response.audio_content)
        }
        
    except Exception as e:
        logger.error(f"Error in text-to-speech conversion: {str(e)}")
        return {
            "audio_content": "",
            "audio_format": audio_encoding.lower(),
            "duration": 0.0,
            "language": language,
            "error": str(e),
            "text_length": len(text),
            "word_count": len(text.split())
        }

def get_available_voices(language_code: str = None) -> Dict[str, Any]:
    """
    Get list of available voices for text-to-speech.
    
    Args:
        language_code (str): Filter by language code (optional)
    
    Returns:
        Dict containing available voices
    """
    logger.info(f"Getting available voices for language: {language_code}")
    
    try:
        # List available voices
        voices_response = tts_client.list_voices(language_code=language_code)
        
        voices = []
        for voice in voices_response.voices:
            voice_info = {
                "name": voice.name,
                "language_codes": list(voice.language_codes),
                "gender": voice.ssml_gender.name,
                "natural_sample_rate": voice.natural_sample_rate_hertz
            }
            voices.append(voice_info)
        
        return {
            "voices": voices,
            "total_count": len(voices),
            "language_filter": language_code,
            "supported_languages": list(set(
                lang for voice in voices for lang in voice["language_codes"]
            ))
        }
        
    except Exception as e:
        logger.error(f"Error getting available voices: {str(e)}")
        return {
            "voices": [],
            "total_count": 0,
            "error": str(e)
        }

def analyze_voice_sentiment(audio_data: str, language: str = "en-US") -> Dict[str, Any]:
    """
    Analyze sentiment and emotions from voice audio.
    
    Args:
        audio_data (str): Base64 encoded audio data
        language (str): Language code for analysis
    
    Returns:
        Dict containing voice sentiment analysis
    """
    logger.info("Analyzing voice sentiment and emotions")
    
    try:
        # First, transcribe the audio to get text
        transcription_result = speech_to_text(audio_data, language)
        
        if transcription_result.get("error"):
            return {
                "sentiment": "unknown",
                "confidence": 0.0,
                "error": transcription_result["error"],
                "transcription": ""
            }
        
        text = transcription_result["transcription"]
        words_info = transcription_result.get("words_info", [])
        
        # Analyze text sentiment (basic implementation)
        sentiment_score = _analyze_text_sentiment(text)
        
        # Analyze speech patterns from word timing
        speech_patterns = _analyze_speech_patterns(words_info)
        
        # Combine text and speech analysis
        overall_sentiment = _combine_sentiment_analysis(sentiment_score, speech_patterns)
        
        return {
            "sentiment": overall_sentiment["sentiment"],
            "confidence": overall_sentiment["confidence"],
            "emotions": overall_sentiment["emotions"],
            "stress_level": speech_patterns["stress_level"],
            "speaking_rate": speech_patterns["speaking_rate"],
            "transcription": text,
            "speech_patterns": speech_patterns,
            "text_sentiment": sentiment_score
        }
        
    except Exception as e:
        logger.error(f"Error in voice sentiment analysis: {str(e)}")
        return {
            "sentiment": "unknown",
            "confidence": 0.0,
            "error": str(e),
            "transcription": ""
        }

def _analyze_text_sentiment(text: str) -> Dict[str, Any]:
    """Analyze sentiment from transcribed text."""
    # Simple keyword-based sentiment analysis
    positive_words = ["good", "great", "excellent", "happy", "satisfied", "thank", "thanks", "perfect"]
    negative_words = ["bad", "terrible", "awful", "angry", "frustrated", "hate", "problem", "issue"]
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count > negative_count:
        sentiment = "positive"
        confidence = min(0.9, 0.5 + (positive_count - negative_count) * 0.1)
    elif negative_count > positive_count:
        sentiment = "negative"
        confidence = min(0.9, 0.5 + (negative_count - positive_count) * 0.1)
    else:
        sentiment = "neutral"
        confidence = 0.6
    
    return {
        "sentiment": sentiment,
        "confidence": confidence,
        "positive_indicators": positive_count,
        "negative_indicators": negative_count
    }

def _analyze_speech_patterns(words_info: list) -> Dict[str, Any]:
    """Analyze speech patterns from word timing information."""
    if not words_info:
        return {
            "speaking_rate": "unknown",
            "stress_level": "unknown",
            "pace_variation": 0.0
        }
    
    # Calculate speaking rate (words per minute)
    total_duration = words_info[-1]["end_time"] - words_info[0]["start_time"]
    words_per_minute = (len(words_info) / total_duration) * 60 if total_duration > 0 else 0
    
    # Determine speaking rate category
    if words_per_minute > 180:
        speaking_rate = "fast"
        stress_indicator = 0.7
    elif words_per_minute > 120:
        speaking_rate = "normal"
        stress_indicator = 0.3
    else:
        speaking_rate = "slow"
        stress_indicator = 0.5
    
    # Calculate pace variation
    word_durations = []
    for i in range(len(words_info)):
        duration = words_info[i]["end_time"] - words_info[i]["start_time"]
        word_durations.append(duration)
    
    if word_durations:
        avg_duration = sum(word_durations) / len(word_durations)
        pace_variation = sum(abs(d - avg_duration) for d in word_durations) / len(word_durations)
    else:
        pace_variation = 0.0
    
    # Determine stress level
    if pace_variation > 0.3 or words_per_minute > 200:
        stress_level = "high"
    elif pace_variation > 0.15 or words_per_minute > 160:
        stress_level = "medium"
    else:
        stress_level = "low"
    
    return {
        "speaking_rate": speaking_rate,
        "words_per_minute": words_per_minute,
        "stress_level": stress_level,
        "pace_variation": pace_variation,
        "total_duration": total_duration
    }

def _combine_sentiment_analysis(text_sentiment: Dict, speech_patterns: Dict) -> Dict[str, Any]:
    """Combine text sentiment and speech pattern analysis."""
    text_sent = text_sentiment["sentiment"]
    stress_level = speech_patterns["stress_level"]
    
    # Adjust sentiment based on speech patterns
    if stress_level == "high" and text_sent == "neutral":
        final_sentiment = "negative"
        confidence = 0.7
    elif stress_level == "low" and text_sent == "negative":
        final_sentiment = "neutral"
        confidence = 0.6
    else:
        final_sentiment = text_sent
        confidence = text_sentiment["confidence"]
    
    # Generate emotion breakdown
    emotions = {
        "frustration": 0.1,
        "satisfaction": 0.1,
        "neutral": 0.8
    }
    
    if final_sentiment == "negative":
        emotions["frustration"] = 0.6
        emotions["neutral"] = 0.3
        emotions["satisfaction"] = 0.1
    elif final_sentiment == "positive":
        emotions["satisfaction"] = 0.7
        emotions["neutral"] = 0.2
        emotions["frustration"] = 0.1
    
    if stress_level == "high":
        emotions["frustration"] += 0.2
        emotions["neutral"] -= 0.2
    
    return {
        "sentiment": final_sentiment,
        "confidence": confidence,
        "emotions": emotions
    }

async def process_voice_message_async(
    audio_data: str,
    language: str = "en-US",
    include_sentiment: bool = True
) -> Dict[str, Any]:
    """
    Asynchronously process voice message with transcription and sentiment analysis.
    
    Args:
        audio_data (str): Base64 encoded audio data
        language (str): Language code
        include_sentiment (bool): Whether to include sentiment analysis
    
    Returns:
        Dict containing complete voice processing results
    """
    logger.info("Processing voice message asynchronously")
    
    try:
        # Run transcription and sentiment analysis concurrently
        tasks = [
            asyncio.create_task(asyncio.to_thread(speech_to_text, audio_data, language))
        ]
        
        if include_sentiment:
            tasks.append(
                asyncio.create_task(asyncio.to_thread(analyze_voice_sentiment, audio_data, language))
            )
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        transcription_result = results[0]
        sentiment_result = results[1] if include_sentiment and len(results) > 1 else None
        
        return {
            "transcription": transcription_result,
            "sentiment_analysis": sentiment_result,
            "processing_time": "async",
            "language": language,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Error in async voice processing: {str(e)}")
        return {
            "transcription": {"error": str(e)},
            "sentiment_analysis": None,
            "error": str(e),
            "status": "failed"
        }

def create_voice_response(
    text: str,
    language: str = "en-US",
    emotion: str = "neutral",
    urgency: str = "normal"
) -> Dict[str, Any]:
    """
    Create voice response with appropriate tone and emotion.
    
    Args:
        text (str): Response text
        language (str): Language code
        emotion (str): Desired emotion (neutral, empathetic, professional)
        urgency (str): Response urgency (normal, urgent, calm)
    
    Returns:
        Dict containing voice response
    """
    logger.info(f"Creating voice response with {emotion} emotion and {urgency} urgency")
    
    # Adjust voice parameters based on emotion and urgency
    voice_params = {
        "language": language,
        "speaking_rate": 1.0,
        "pitch": 0.0,
        "voice_gender": "NEUTRAL"
    }
    
    # Emotion adjustments
    if emotion == "empathetic":
        voice_params["speaking_rate"] = 0.9
        voice_params["pitch"] = -2.0
    elif emotion == "professional":
        voice_params["speaking_rate"] = 1.1
        voice_params["pitch"] = 1.0
    
    # Urgency adjustments
    if urgency == "urgent":
        voice_params["speaking_rate"] = 1.2
    elif urgency == "calm":
        voice_params["speaking_rate"] = 0.8
        voice_params["pitch"] = -1.0
    
    # Generate speech
    tts_result = text_to_speech(text, **voice_params)
    
    return {
        **tts_result,
        "emotion": emotion,
        "urgency": urgency,
        "voice_parameters": voice_params
    }