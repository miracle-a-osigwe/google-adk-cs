"""FastAPI application with Google Speech and Translation APIs integration."""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import asyncio
import base64

# from tools.voice_tools import (
#     speech_to_text,
#     text_to_speech,
#     analyze_voice_sentiment,
#     get_available_voices
# )
# from tools.translation_tools import (
#     detect_language,
#     translate_text,
#     get_supported_languages
# )
# from config import Config

# Initialize FastAPI app
app = FastAPI(
    title="ADK Customer Service Ecosystem with Google APIs",
    description="Multi-agent customer service system with Google Speech and Translation APIs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)