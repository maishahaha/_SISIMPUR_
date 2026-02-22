"""
API Configuration for Sisimpur Brain Engine.

This module contains all API endpoint configurations and settings for external AI services.
"""

import os
from django.conf import settings

# Single API Base URL (n8n webhook)
API_BASE_URL = os.getenv('SISIMPUR_API_URL', 'https://rsegh.millenniumonline.tv/webhook/sisimpur')

# Single API Endpoint (all operations via event query)
API_ENDPOINTS = {
    'single': {
        'url': API_BASE_URL,
        'method': 'POST',
        'timeout': 300,
        'description': 'Single endpoint; select operation via event query param'
    }
}

# API Headers Configuration
API_HEADERS = {
    'User-Agent': 'Sisimpur-Brain-Engine/1.0',
    'Accept': 'application/json',
}

# API Authentication (if needed)
API_AUTH = {
    'api_key': os.getenv('SISIMPUR_API_KEY', ''),
    'api_secret': os.getenv('SISIMPUR_API_SECRET', ''),
}

# Request/Response Configuration
API_CONFIG = {
    'max_retries': 3,
    'retry_delay': 1,  # seconds
    'max_file_size': 50 * 1024 * 1024,  # 50MB
    'supported_formats': ['.pdf', '.jpg', '.jpeg', '.png', '.txt'],
    'chunk_size': 1024 * 1024,  # 1MB chunks for file uploads
}

# Language Mapping
LANGUAGE_MAPPING = {
    'auto': 'auto',
    'english': 'en',
    'bengali': 'bn',
    'bangla': 'bn',
}

# Question Type Mapping
QUESTION_TYPE_MAPPING = {
    'SHORT': 'short_answer',
    'MULTIPLECHOICE': 'multiple_choice',
}

# Short Question API Configuration
SHORT_QUESTION_CONFIG = {
    'evaluation_endpoint': 'short_answer_evaluation',
    'max_score_per_question': 10,
    'evaluation_criteria': {
        'accuracy': 0.4,  # 40% weight for accuracy
        'completeness': 0.3,  # 30% weight for completeness
        'clarity': 0.2,  # 20% weight for clarity
        'structure': 0.1,  # 10% weight for structure
    }
}

# Document Type Mapping
DOCUMENT_TYPE_MAPPING = {
    'text_pdf': 'text_pdf',
    'image_pdf': 'image_pdf',
    'image': 'image',
    'text': 'text',
}

# Error Messages
ERROR_MESSAGES = {
    'api_timeout': '⏰ API request timed out. Please try again.',
    'api_error': '❌ API service error. Please try again later.',
    'file_too_large': '📁 File is too large. Maximum size is 50MB.',
    'unsupported_format': '📄 Unsupported file format.',
    'no_text_extracted': '📝 No text could be extracted from the document.',
    'generation_failed': '🤖 Question generation failed. Please try again.',
    'network_error': '🌐 Network error. Please check your connection.',
    'api_unavailable': '🔧 API service is temporarily unavailable.',
}

# Success Messages
SUCCESS_MESSAGES = {
    'text_extracted': '✅ Text extracted successfully',
    'questions_generated': '🎯 Questions generated successfully',
    'document_processed': '📚 Document processed successfully',
    'analysis_complete': '🔍 Document analysis complete',
}

# Logging Configuration
API_LOGGING = {
    'log_requests': True,
    'log_responses': True,
    'log_errors': True,
    'log_level': 'INFO',
}
