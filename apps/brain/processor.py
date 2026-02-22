"""
API-based Document Processor for Sisimpur Brain Engine.

This module provides a simplified document processing pipeline using external APIs.
"""

import logging
import json
import os
import time
from django.utils import timezone
from typing import Dict, Any, Optional, List
from pathlib import Path
from django.core.files.storage import default_storage
from django.conf import settings

from .provider import APIService
from .models import ProcessingJob, QuestionAnswer

logger = logging.getLogger("sisimpur.brain.api_processor")


class APIDocumentProcessor:
    """API-based document processor for the Sisimpur Brain system"""
    
    def __init__(self, language: str = "auto"):
        """
        Initialize the API document processor.
        
        Args:
            language: Language for processing ('auto', 'english', 'bengali')
        """
        self.language = language
        self.api_service = APIService()
        logger.info(f"Initialized APIDocumentProcessor with language: {language}")
    
    def process_document(self, file_path: str, num_questions: Optional[int] = None, 
                        question_type: str = 'MULTIPLECHOICE') -> str:
        """
        Process a document and generate Q&A pairs using API.
        
        Args:
            file_path: Path to the document file
            num_questions: Number of questions to generate (optional)
            question_type: Type of questions to generate
            
        Returns:
            Path to the output JSON file containing Q&A pairs
        """
        try:
            logger.info(f"🚀 Starting API document processing for: {file_path}")
            
            # Use single API endpoint (event=mcq_question) for document processing
            response = self.api_service.process_document(
                file_path=file_path,
                num_questions=num_questions or 5,
                language=self.language,
                question_type=question_type
            )
            
            if not response['success']:
                raise Exception(f"API processing failed: {response.get('error', 'Unknown error')}")
            
            # Extract Q&A pairs from API response
            api_data = response['data']
            qa_pairs = self._extract_qa_pairs(api_data)
            
            if not qa_pairs:
                raise Exception("No Q&A pairs generated from API response")
            
            # Save results to file
            output_file = self._save_qa_pairs(qa_pairs, file_path)
            
            logger.info(f"✅ API document processing completed. Output saved to: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"❌ Error in API document processing: {e}")
            raise
    
    def process_text(self, text: str, num_questions: Optional[int] = None, 
                    source_name: str = "raw_text", question_type: str = 'MULTIPLECHOICE') -> str:
        """
        Process raw text and generate Q&A pairs using API.
        
        Args:
            text: Raw text to process
            num_questions: Number of questions to generate (optional)
            source_name: Name to use for the source in output
            question_type: Type of questions to generate
            
        Returns:
            Path to the output JSON file containing Q&A pairs
        """
        try:
            logger.info(f"🚀 Starting API text processing for: {source_name}")
            
            if not text.strip():
                raise ValueError("No text provided for processing")
            
            # Use single endpoint for question generation (question_number=optimal when None)
            response = self.api_service.generate_questions(
                text=text,
                num_questions=num_questions or 0,
                language=self.language,
                question_type=question_type,
                is_question_paper=False
            )
            
            if not response['success']:
                raise Exception(f"API question generation failed: {response.get('error', 'Unknown error')}")
            
            # Extract Q&A pairs from API response
            api_data = response['data']
            qa_pairs = self._extract_qa_pairs(api_data)
            
            if not qa_pairs:
                raise Exception("No Q&A pairs generated from API response")
            
            # Save results to file
            output_file = self._save_qa_pairs(qa_pairs, source_name)
            
            logger.info(f"✅ API text processing completed. Output saved to: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"❌ Error in API text processing: {e}")
            raise
    
    def _extract_qa_pairs(self, api_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract Q&A pairs from API response data.
        
        Args:
            api_data: API response data
            
        Returns:
            List of Q&A pairs
        """
        try:
            qa_pairs = []

            # Unwrap common n8n response shapes if they slip past the service normalization
            # e.g. { "output": { "success": true, "data": { "questions": [...] } } }
            if isinstance(api_data, dict) and 'output' in api_data and isinstance(api_data.get('output'), dict):
                output = api_data.get('output') or {}
                if isinstance(output.get('data'), dict):
                    api_data = output.get('data') or {}
                else:
                    api_data = output
            
            # Handle different API response formats
            if 'questions' in api_data:
                questions = api_data['questions']
            elif 'qa_pairs' in api_data:
                questions = api_data['qa_pairs']
            elif 'results' in api_data and 'questions' in api_data['results']:
                questions = api_data['results']['questions']
            else:
                # Try to find questions in the data structure
                questions = []
                for key, value in api_data.items():
                    if isinstance(value, list) and value and isinstance(value[0], dict):
                        if 'question' in value[0] or 'q' in value[0]:
                            questions = value
                            break
            
            # Process each question
            for item in questions:
                qa_pair = {
                    'question': item.get('question', item.get('q', '')),
                    'answer': item.get('answer', item.get('a', '')),
                    'question_type': item.get('question_type', 'MULTIPLECHOICE'),
                    'options': item.get('options', []),
                    'correct_option': item.get('correct_option', ''),
                    'confidence_score': item.get('confidence_score', 0.0),
                    'explanation': item.get('explanation', ''),
                    'difficulty': item.get('difficulty', 'medium'),
                    'topic': item.get('topic', ''),
                    'metadata': item.get('metadata', {})
                }
                
                # Ensure required fields are present
                if not qa_pair['question']:
                    logger.warning("Skipping question with empty question text")
                    continue
                
                qa_pairs.append(qa_pair)
            
            logger.info(f"📊 Extracted {len(qa_pairs)} Q&A pairs from API response")
            return qa_pairs
            
        except Exception as e:
            logger.error(f"Error extracting Q&A pairs from API response: {e}")
            return []
    
    def _save_qa_pairs(self, qa_pairs: List[Dict[str, Any]], source_name: str) -> str:
        """
        Save Q&A pairs to JSON file.
        
        Args:
            qa_pairs: List of Q&A pairs
            source_name: Source name for the file
            
        Returns:
            Path to the saved JSON file
        """
        try:
            # Prepare output data
            output_data = {
                'source': source_name,
                'language': self.language,
                'total_questions': len(qa_pairs),
                'generated_at': timezone.now().isoformat(),
                'questions': qa_pairs
            }
            
            # Create output directory if it doesn't exist
            output_dir = os.path.join(settings.MEDIA_ROOT, 'brain', 'qa_outputs')
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename
            safe_source_name = "".join(c for c in source_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_source_name}_qa_{int(time.time())}.json"
            output_path = os.path.join(output_dir, filename)
            
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Q&A pairs saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving Q&A pairs: {e}")
            raise
    
    def process_with_job(self, job: ProcessingJob) -> Dict[str, Any]:
        """
        Process document using a ProcessingJob instance.
        
        Args:
            job: ProcessingJob instance
            
        Returns:
            Processing result
        """
        try:
            logger.info(f"🔄 Processing job {job.id}: {job.document_name}")
            
            # Update job status
            job.status = 'processing'
            job.save()
            
            # Process based on document type
            if job.document_type == 'text':
                # Process raw text
                if not job.extracted_text_file:
                    raise Exception("No text content available for processing")
                
                # Read text content
                with open(job.extracted_text_file.path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
                
                output_file = self.process_text(
                    text=text_content,
                    num_questions=job.num_questions,
                    source_name=job.document_name,
                    question_type=job.question_type
                )
            else:
                # Process document file
                if not job.document_file:
                    raise Exception("No document file available for processing")
                
                output_file = self.process_document(
                    file_path=job.document_file.path,
                    num_questions=job.num_questions,
                    question_type=job.question_type
                )
            
            # Load generated Q&A pairs
            with open(output_file, 'r', encoding='utf-8') as f:
                qa_data = json.load(f)
            
            # Save Q&A pairs to database
            qa_count = 0
            for qa_item in qa_data.get('questions', []):
                QuestionAnswer.objects.create(
                    job=job,
                    question=qa_item.get('question', ''),
                    answer=qa_item.get('answer', ''),
                    question_type=qa_item.get('question_type', job.question_type),
                    options=qa_item.get('options', []),
                    correct_option=qa_item.get('correct_option', ''),
                    confidence_score=qa_item.get('confidence_score')
                )
                qa_count += 1
            
            # Update job with results
            relative_output_path = os.path.relpath(output_file, settings.MEDIA_ROOT)
            # Assigning relative path is sufficient for FileField; ensure it matches upload_to convention
            job.output_file.name = relative_output_path
            job.mark_completed()
            
            logger.info(f"✅ Job {job.id} completed successfully with {qa_count} Q&A pairs")
            
            return {
                'success': True,
                'qa_count': qa_count,
                'output_file': output_file,
                'message': f'Successfully generated {qa_count} questions'
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing job {job.id}: {e}")
            job.mark_failed(str(e))
            return {
                'success': False,
                'error': str(e),
                'message': f'Processing failed: {str(e)}'
            }
