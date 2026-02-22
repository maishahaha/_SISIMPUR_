import os
import json
import tempfile
from django.test import TestCase, override_settings
from django.utils import timezone
from apps.brain.processor import APIDocumentProcessor


class APIDocumentProcessorTests(TestCase):
    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_save_qa_pairs_creates_file_with_iso_timestamp(self):
        processor = APIDocumentProcessor(language="english")
        qa_pairs = [
            {
                'question': 'What is 2+2?',
                'answer': '4',
                'question_type': 'MULTIPLECHOICE',
                'options': ['A) 3', 'B) 4'],
                'correct_option': 'B',
                'confidence_score': 0.95
            }
        ]
        output_path = processor._save_qa_pairs(qa_pairs, 'sample_doc')
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertIn('generated_at', data)
        # Basic ISO 8601 check
        self.assertTrue('T' in data['generated_at'])
        self.assertEqual(data['total_questions'], 1)

    def test_extract_qa_pairs_handles_varied_formats(self):
        processor = APIDocumentProcessor()
        # Format with 'questions'
        api_data_1 = {'questions': [{'question': 'Q1', 'answer': 'A1'}]}
        # Format with 'qa_pairs'
        api_data_2 = {'qa_pairs': [{'q': 'Q2', 'a': 'A2'}]}
        # Nested results format
        api_data_3 = {'results': {'questions': [{'question': 'Q3', 'answer': 'A3'}]}}
        # Fallback discovery
        api_data_4 = {'misc': [{'question': 'Q4', 'answer': 'A4'}]}
        # n8n output wrapper dict format
        api_data_5 = {'output': {'success': True, 'data': {'questions': [{'question': 'Q5', 'answer': 'A5'}]}}}
        self.assertEqual(len(processor._extract_qa_pairs(api_data_1)), 1)
        self.assertEqual(len(processor._extract_qa_pairs(api_data_2)), 1)
        self.assertEqual(len(processor._extract_qa_pairs(api_data_3)), 1)
        self.assertEqual(len(processor._extract_qa_pairs(api_data_4)), 1)
        self.assertEqual(len(processor._extract_qa_pairs(api_data_5)), 1)
