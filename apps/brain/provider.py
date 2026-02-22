"""
API Service for Sisimpur Brain Engine.

This module handles all external API calls for document processing, text extraction, and question generation.
"""

import requests
import json
import logging
import time
from typing import Dict, Any, Optional, List
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
import base64
import mimetypes
from pathlib import Path

from .config import (
    API_ENDPOINTS, API_HEADERS, API_AUTH, API_CONFIG,
    LANGUAGE_MAPPING, QUESTION_TYPE_MAPPING, DOCUMENT_TYPE_MAPPING,
    ERROR_MESSAGES, SUCCESS_MESSAGES, API_LOGGING, SHORT_QUESTION_CONFIG
)

logger = logging.getLogger("sisimpur.brain.api_service")


class APIService:
    """Service class for handling all external API calls"""
    
    def __init__(self):
        """Initialize the API service"""
        self.session = requests.Session()
        self.session.headers.update(API_HEADERS)
        
        # Add authentication if configured
        if API_AUTH.get('api_key'):
            self.session.headers['X-API-Key'] = API_AUTH['api_key']
        if API_AUTH.get('api_secret'):
            self.session.headers['X-API-Secret'] = API_AUTH['api_secret']
    
    def _log_request(self, endpoint: str, method: str, data: Dict = None, files: Dict = None):
        """Log API request details"""
        if API_LOGGING.get('log_requests'):
            logger.info(f"🌐 API Request: {method} {endpoint}")
            if data and API_LOGGING.get('log_requests'):
                # Log data without sensitive information
                log_data = {k: v for k, v in data.items() if k not in ['file_content', 'image_data']}
                logger.info(f"📤 Request Data: {json.dumps(log_data, indent=2)}")
    
    def _log_response(self, endpoint: str, response: requests.Response, success: bool = True):
        """Log API response details"""
        if API_LOGGING.get('log_responses'):
            status_emoji = "✅" if success else "❌"
            logger.info(f"{status_emoji} API Response: {response.status_code} {endpoint}")
            
            if success and API_LOGGING.get('log_responses'):
                try:
                    response_data = response.json()
                    logger.info(f"📥 Response Data: {json.dumps(response_data, indent=2)}")
                except:
                    logger.info(f"📥 Response Text: {response.text[:500]}...")
    
    def _make_request(self, endpoint_name: str, data: Dict = None, files: Dict = None, query: Dict = None, use_multipart: bool = False) -> Dict[str, Any]:
        """Make API request with retry logic"""
        endpoint_config = API_ENDPOINTS.get(endpoint_name)
        if not endpoint_config:
            raise ValueError(f"Unknown endpoint: {endpoint_name}")
        
        url = endpoint_config['url']
        method = endpoint_config['method']
        timeout = endpoint_config['timeout']
        params = query or {}
        
        self._log_request(url, method, data, files)
        
        for attempt in range(API_CONFIG['max_retries']):
            try:
                if method == 'GET':
                    response = self.session.get(url, params={**params, **(data or {})}, timeout=timeout)
                elif method == 'POST':
                    if use_multipart:
                        response = self.session.post(url, params=params, data=data, files=files, timeout=timeout)
                    elif files:
                        response = self.session.post(url, params=params, data=data, files=files, timeout=timeout)
                    else:
                        response = self.session.post(url, params=params, json=data, timeout=timeout)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Check if request was successful
                if response.status_code == 200:
                    self._log_response(url, response, success=True)

                    # Normalize n8n webhook response shapes
                    # Expected possibilities:
                    # 1) { success: true, data: { questions: [...] } }
                    # 2) [ { output: { success: true, data: { questions: [...] } } } ]
                    # 3) { questions: [...] }
                    try:
                        raw = response.json()
                    except Exception:
                        raw = None

                    normalized_data = None
                    normalized_success = True
                    if isinstance(raw, list) and raw:
                        first = raw[0]
                        if isinstance(first, dict):
                            output = first.get('output') or first
                            # Some n8n nodes wrap inside `output`
                            if isinstance(output, dict):
                                if 'data' in output and isinstance(output['data'], dict):
                                    normalized_data = output['data']
                                elif 'questions' in output:
                                    normalized_data = output
                                normalized_success = output.get('success', True)
                    elif isinstance(raw, dict):
                        # Some n8n workflows return a single dict with `output` wrapper
                        if 'output' in raw and isinstance(raw.get('output'), dict):
                            output = raw.get('output') or {}
                            if 'data' in output and isinstance(output['data'], dict):
                                normalized_data = output['data']
                            elif 'questions' in output:
                                normalized_data = output
                            else:
                                normalized_data = output
                            normalized_success = output.get('success', True)
                        elif 'data' in raw and isinstance(raw['data'], dict):
                            normalized_data = raw['data']
                            normalized_success = raw.get('success', True)
                        else:
                            # Direct questions at top-level
                            normalized_data = raw

                    if not isinstance(normalized_data, dict):
                        # Fallback to raw json if we couldn't normalize into dict
                        normalized_data = {'raw': raw}

                    return {
                        'success': bool(normalized_success),
                        'data': normalized_data,
                        'status_code': response.status_code,
                        'message': SUCCESS_MESSAGES.get('document_processed', 'Request successful')
                    }
                else:
                    self._log_response(url, response, success=False)
                    return {
                        'success': False,
                        'error': f"API Error: {response.status_code} - {response.text}",
                        'status_code': response.status_code,
                        'message': ERROR_MESSAGES.get('api_error', 'API request failed')
                    }
                    
            except requests.exceptions.Timeout:
                logger.warning(f"⏰ API timeout on attempt {attempt + 1}/{API_CONFIG['max_retries']}")
                if attempt == API_CONFIG['max_retries'] - 1:
                    return {
                        'success': False,
                        'error': 'Request timeout',
                        'message': ERROR_MESSAGES.get('api_timeout', 'Request timed out')
                    }
                time.sleep(API_CONFIG['retry_delay'] * (attempt + 1))
                
            except requests.exceptions.ConnectionError:
                logger.warning(f"🌐 Connection error on attempt {attempt + 1}/{API_CONFIG['max_retries']}")
                if attempt == API_CONFIG['max_retries'] - 1:
                    return {
                        'success': False,
                        'error': 'Connection error',
                        'message': ERROR_MESSAGES.get('network_error', 'Network error')
                    }
                time.sleep(API_CONFIG['retry_delay'] * (attempt + 1))
                
            except Exception as e:
                logger.error(f"❌ Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == API_CONFIG['max_retries'] - 1:
                    return {
                        'success': False,
                        'error': str(e),
                        'message': ERROR_MESSAGES.get('api_error', 'Unexpected error')
                    }
                time.sleep(API_CONFIG['retry_delay'] * (attempt + 1))
        
        return {
            'success': False,
            'error': 'Max retries exceeded',
            'message': ERROR_MESSAGES.get('api_error', 'Request failed after multiple attempts')
        }
    
    def _prepare_file_multipart(self, file_path: str, file_type: str = None) -> Dict[str, Any]:
        """Prepare multipart form-data file for API upload"""
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()

            # Check file size
            if len(file_content) > API_CONFIG['max_file_size']:
                raise ValueError(ERROR_MESSAGES.get('file_too_large', 'File too large'))

            # Determine MIME type
            if not file_type:
                file_type, _ = mimetypes.guess_type(file_path)
                if not file_type:
                    file_type = 'application/octet-stream'

            # files payload for requests
            files = {
                'file': (Path(file_path).name, file_content, file_type)
            }
            return files
        except Exception as e:
            logger.error(f"Error preparing multipart file: {e}")
            raise

    def _prepare_file_data(self, file_path: str) -> Dict[str, Any]:
        """
        Prepare a JSON-friendly representation of a file (base64 + metadata).
        Used by legacy analysis/detection endpoints.
        """
        try:
            path = Path(file_path)
            if not path.exists() or not path.is_file():
                raise FileNotFoundError(f"File not found: {file_path}")
            raw = path.read_bytes()
            if len(raw) > API_CONFIG.get('max_file_size', 10_000_000):
                raise ValueError(ERROR_MESSAGES.get('file_too_large', 'File too large'))
            mime, _ = mimetypes.guess_type(str(path))
            if not mime:
                mime = 'application/octet-stream'
            return {
                'filename': path.name,
                'size': len(raw),
                'content_type': mime,
                'base64': base64.b64encode(raw).decode('utf-8')
            }
        except Exception as e:
            logger.error(f"Error preparing file data: {e}")
            raise
    
    def process_document(self, file_path: str, num_questions: int, language: str = 'auto', 
                       question_type: str = 'MULTIPLECHOICE') -> Dict[str, Any]:
        """
        Process document and generate Q&A pairs using combined API endpoint.
        
        Args:
            file_path: Path to the document file
            num_questions: Number of questions to generate
            language: Language for processing
            question_type: Type of questions to generate
            
        Returns:
            API response with Q&A pairs
        """
        try:
            logger.info(f"🚀 Processing document: {file_path}")
            
            # Prepare multipart file and fields
            files = self._prepare_file_multipart(file_path)
            request_fields = {
                'question_number': str(num_questions) if num_questions else 'optimal',
                'language': LANGUAGE_MAPPING.get(language, language),
                'question_type': QUESTION_TYPE_MAPPING.get(question_type, question_type)
            }
            # Single endpoint with event=mcq_question
            response = self._make_request(
                'single',
                data=request_fields,
                files=files,
                query={'event': 'mcq_question'},
                use_multipart=True
            )
            
            if response['success']:
                logger.info(f"✅ Document processed successfully: {file_path}")
            else:
                logger.error(f"❌ Document processing failed: {response.get('error', 'Unknown error')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': ERROR_MESSAGES.get('api_error', 'Document processing failed')
            }
    
    # Text extraction, analysis, and question paper detection are now handled inside n8n
    # via the single endpoint and event workflow. No separate client calls are needed here.
    
    def generate_questions(self, text: str, num_questions: int, language: str = 'auto', 
                          question_type: str = 'MULTIPLECHOICE', is_question_paper: bool = False) -> Dict[str, Any]:
        """
        Generate Q&A pairs from text using API.
        
        Args:
            text: Source text
            num_questions: Number of questions to generate
            language: Language for generation
            question_type: Type of questions to generate
            is_question_paper: Whether the text is from a question paper
            
        Returns:
            API response with Q&A pairs
        """
        try:
            logger.info(f"🎯 Generating {num_questions} questions from text")
            
            # Single endpoint expects event=mcq_question; for raw text we pass as form field
            files = None
            request_fields = {
                'text': text,
                'question_number': str(num_questions) if num_questions else 'optimal',
                'language': LANGUAGE_MAPPING.get(language, language),
                'question_type': QUESTION_TYPE_MAPPING.get(question_type, question_type)
            }
            response = self._make_request(
                'single',
                data=request_fields,
                files=files,
                query={'event': 'mcq_question'},
                use_multipart=False
            )
            
            if response['success']:
                logger.info(f"✅ Questions generated successfully")
            else:
                logger.error(f"❌ Question generation failed: {response.get('error', 'Unknown error')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': ERROR_MESSAGES.get('generation_failed', 'Question generation failed')
            }
    
    # Auto generation is covered by passing question_number='optimal' on the same endpoint
    
    def evaluate_short_answer(self, exam_id: str, user_id: str, q_id: str, 
                             question: str, user_answer: str) -> Dict[str, Any]:
        """
        Evaluate a single short answer question using API.
        
        Args:
            exam_id: Unique exam identifier
            user_id: User identifier
            q_id: Question identifier
            question: The question text
            user_answer: User's answer to evaluate
            
        Returns:
            API response with evaluation results
        """
        try:
            logger.info(f"🎯 Evaluating short answer for question {q_id}")
            
            request_data = {
                'exam_id': exam_id,
                'user_id': user_id,
                'q_id': q_id,
                'question': question,
                'user_answer': user_answer,
                'max_score': SHORT_QUESTION_CONFIG['max_score_per_question'],
                'evaluation_criteria': SHORT_QUESTION_CONFIG['evaluation_criteria']
            }
            
            response = self._make_request(
                'single',
                data=request_data,
                query={'event': SHORT_QUESTION_CONFIG['evaluation_endpoint']},
                use_multipart=False
            )
            
            if response['success']:
                logger.info(f"✅ Short answer evaluation completed for question {q_id}")
            else:
                logger.error(f"❌ Short answer evaluation failed for question {q_id}: {response.get('error', 'Unknown error')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error evaluating short answer for question {q_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': ERROR_MESSAGES.get('evaluation_failed', 'Answer evaluation failed')
            }
    
    def analyze_document(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze document type and metadata using API.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            API response with document analysis
        """
        try:
            logger.info(f"🔍 Analyzing document: {file_path}")
            
            # Prepare file data
            file_data = self._prepare_file_data(file_path)
            
            # Prepare request data
            request_data = {
                'file': file_data,
                'options': {
                    'detect_language': True,
                    'detect_question_paper': True,
                    'extract_metadata': True,
                    'analyze_structure': True
                }
            }
            
            # Make API call
            response = self._make_request('analyze_document', data=request_data)
            
            if response['success']:
                logger.info(f"✅ Document analysis complete: {file_path}")
            else:
                logger.error(f"❌ Document analysis failed: {response.get('error', 'Unknown error')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error analyzing document: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': ERROR_MESSAGES.get('api_error', 'Document analysis failed')
            }
    
    def detect_question_paper(self, file_path: str) -> Dict[str, Any]:
        """
        Detect if document is a question paper using API.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            API response with detection result
        """
        try:
            logger.info(f"📋 Detecting question paper: {file_path}")
            
            # Prepare file data
            file_data = self._prepare_file_data(file_path)
            
            # Prepare request data
            request_data = {
                'file': file_data,
                'options': {
                    'confidence_threshold': 0.7,
                    'analyze_structure': True
                }
            }
            
            # Make API call
            response = self._make_request('detect_question_paper', data=request_data)
            
            if response['success']:
                logger.info(f"✅ Question paper detection complete: {file_path}")
            else:
                logger.error(f"❌ Question paper detection failed: {response.get('error', 'Unknown error')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error detecting question paper: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': ERROR_MESSAGES.get('api_error', 'Question paper detection failed')
            }
