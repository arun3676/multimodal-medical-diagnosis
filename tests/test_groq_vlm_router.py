import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.groq_vlm_router import GroqVLMRouter


@pytest.fixture
def router():
    """A GroqVLMRouter instance for testing."""
    # Mock environment variables to avoid needing actual API keys
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test_openai_key',
        'GOOGLE_API_KEY': 'test_google_key',
        'GROQ_API_KEY': 'test_groq_key'
    }):
        # Mock the http_client
        mock_http_client = MagicMock()
        # Instantiate the router
        router = GroqVLMRouter(http_client=mock_http_client)
        yield router


def test_normalize_vlm_response_openai_structure(router):
    """Test normalizing a response that looks like it came from OpenAI."""
    raw_result = {
        'provider': 'openai',
        'model': 'gpt-4-vision-preview',
        'is_medical_image': True,
        'image_type': 'chest_xray',
        'provided_symptoms': 'cough and fever',
        'overall_impression': 'The X-ray shows evidence of consolidation.',
        'patient_friendly_summary': 'There are signs of pneumonia in your lungs.',
        'urgency': 'urgent',
        'confidence_score': 0.92,
        'critical_findings': [
            {
                'term': 'Consolidation',
                'status': 'present',
                'severity': 'moderate',
                'confidence': 0.90,
                'radiology_summary': 'Area of consolidation in the right lower lobe.',
                'plain_language_summary': 'There is a dense area in the lower part of your right lung.'
            }
        ],
        'priority_recommendations': [
            {
                'urgency': 'urgent',
                'category': 'Clinical',
                'rationale': 'Start antibiotics immediately.',
                'follow_up_timeline': 'Within 24 hours'
            }
        ]
    }

    normalized = router._normalize_vlm_response(raw_result)

    # Assertions
    assert normalized['provider'] == 'openai'
    assert normalized['urgency'] == 'urgent'
    assert normalized['confidence_score'] == 92  # Converted to percentage
    assert len(normalized['findings']) == 1
    
    finding = normalized['findings'][0]
    assert finding['term'] == 'Consolidation'
    assert finding['status'] == 'present'
    assert finding['category'] == 'LUNGS'
    assert finding['confidence'] == 90
    assert finding['severity'] == 'moderate'
    
    assert len(normalized['recommendations']) == 1
    recommendation = normalized['recommendations'][0]
    assert recommendation['priority'] == 'URGENT'
    assert recommendation['text'] == 'Start antibiotics immediately.'
    assert recommendation['timeline'] == 'Within 24 hours'
    
    assert 'Overall Impression:' in normalized['diagnosis']
    assert 'Patient-Friendly Summary:' in normalized['diagnosis']


def test_normalize_vlm_response_gemini_structure(router):
    """Test normalizing a response that looks like it came from Gemini."""
    raw_result = {
        'provider': 'google',
        'model': 'gemini-pro-vision',
        'is_medical_image': True,
        'image_type': 'chest_xray',
        'provided_symptoms': '',
        'diagnosis': 'No acute cardiopulmonary abnormality.',
        'urgency': 'routine',
        'confidence_score': 88,  # Already a percentage
        'findings': [
            {
                'term': 'Pleural Effusion',
                'status': 'absent',
                'severity': 'none',
                'confidence': 0.95,
                'radiology_summary': 'No pleural effusion identified.',
                'plain_language_summary': 'There is no fluid around the lungs.'
            }
        ],
        'recommendations': [
            'No specific action required.'
        ]
    }

    normalized = router._normalize_vlm_response(raw_result)

    # Assertions
    assert normalized['provider'] == 'google'
    assert normalized['urgency'] == 'routine'
    assert normalized['confidence_score'] == 88
    assert len(normalized['findings']) == 1
    
    finding = normalized['findings'][0]
    assert finding['term'] == 'Pleural Effusion'
    assert finding['status'] == 'absent'
    assert finding['confidence'] == 95  # Converted from 0.95
    assert finding['severity'] == 'normal'
    
    assert len(normalized['recommendations']) == 1
    recommendation = normalized['recommendations'][0]
    assert recommendation['priority'] == 'MEDIUM'
    assert recommendation['text'] == 'No specific action required.'


def test_normalize_vlm_response_empty_findings(router):
    """Test normalizing a response with no findings."""
    raw_result = {
        'provider': 'openai',
        'model': 'gpt-4-vision-preview',
        'is_medical_image': True,
        'image_type': 'chest_xray',
        'provided_symptoms': '',
        'overall_impression': 'Study is normal.',
        'urgency': 'routine',
        'confidence_score': 0.99,
        'critical_findings': []
    }

    normalized = router._normalize_vlm_response(raw_result)

    assert normalized['provider'] == 'openai'
    assert len(normalized['findings']) == 0
    assert len(normalized['recommendations']) == 0
    assert 'Study is normal.' in normalized['diagnosis']


def test_normalize_vlm_response_invalid_input(router):
    """Test normalizing a non-dictionary or malformed response."""
    # Test with a string instead of a dict
    normalized = router._normalize_vlm_response("this is not a dict")
    assert normalized['provider'] == 'unknown'
    assert normalized['confidence_score'] == 0
    assert 'Unable to parse' in normalized['diagnosis']

    # Test with a completely empty dict
    normalized = router._normalize_vlm_response({})
    assert normalized['provider'] == 'unknown'
    assert normalized['urgency'] == 'routine'
    assert normalized['confidence_score'] == 0
