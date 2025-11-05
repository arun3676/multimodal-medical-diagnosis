import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.vision_classifier import analyze_xray_for_pneumonia


@pytest.fixture
def mock_classifier():
    """A mock classifier instance to simulate model predictions."""
    with patch('app.core.vision_classifier.get_classifier') as mock_get_classifier:
        classifier_instance = MagicMock()
        classifier_instance.is_ready.return_value = True
        mock_get_classifier.return_value = classifier_instance
        yield classifier_instance


def test_analyze_xray_for_pneumonia_pneumonia_detected(mock_classifier):
    """Test that the structured output is correct for a PNEUMONIA prediction."""
    # Configure the mock to return a PNEUMONIA prediction
    mock_classifier.predict.return_value = {
        'success': True,
        'prediction': 'PNEUMONIA',
        'confidence': 0.95,
        'probabilities': {'NORMAL': 0.05, 'PNEUMONIA': 0.95}
    }

    # Call the function with a dummy image path
    result = analyze_xray_for_pneumonia('dummy_path.jpg')

    # Assertions
    assert result['success'] is True
    assert result['provider'] == 'fine_tuned_model'
    assert result['is_medical_image'] is True
    assert 'PNEUMONIA DETECTED' in result['diagnosis']
    assert result['urgency'] == 'urgent'
    assert len(result['findings']) == 1
    
    finding = result['findings'][0]
    assert finding['term'] == 'Pneumonia'
    assert finding['status'] == 'present'
    assert finding['category'] == 'LUNGS'
    assert finding['confidence'] == 95
    assert finding['severity'] == 'urgent'
    
    assert len(result['recommendations']) == 2
    assert "Clinical correlation recommended" in result['recommendations']


def test_analyze_xray_for_pneumonia_normal_study(mock_classifier):
    """Test that the structured output is correct for a NORMAL prediction."""
    # Configure the mock to return a NORMAL prediction
    mock_classifier.predict.return_value = {
        'success': True,
        'prediction': 'NORMAL',
        'confidence': 0.98,
        'probabilities': {'NORMAL': 0.98, 'PNEUMONIA': 0.02}
    }

    # Call the function with a dummy image path
    result = analyze_xray_for_pneumonia('dummy_path.jpg')

    # Assertions
    assert result['success'] is True
    assert result['provider'] == 'fine_tuned_model'
    assert result['is_medical_image'] is True
    assert 'NO EVIDENCE OF PNEUMONIA' in result['diagnosis']
    assert result['urgency'] == 'routine'
    assert len(result['findings']) == 1
    
    finding = result['findings'][0]
    assert finding['term'] == 'Pneumonia'
    assert finding['status'] == 'absent'
    assert finding['category'] == 'LUNGS'
    assert finding['confidence'] == 98
    assert finding['severity'] == 'normal'
    
    assert len(result['recommendations']) == 2
    assert "No immediate follow-up required" in result['recommendations']


def test_analyze_xray_for_pneumonia_model_not_ready():
    """Test the case where the fine-tuned model is not loaded."""
    with patch('app.core.vision_classifier.get_classifier') as mock_get_classifier:
        classifier_instance = MagicMock()
        classifier_instance.is_ready.return_value = False
        mock_get_classifier.return_value = classifier_instance

        result = analyze_xray_for_pneumonia('dummy_path.jpg')

        assert result['success'] is False
        assert 'not available' in result['error']
        assert result['provider'] == 'fine_tuned_model'
        assert result['is_medical_image'] is False
        assert result['confidence_score'] == 0.0


def test_analyze_xray_for_pneumonia_prediction_fails(mock_classifier):
    """Test the case where the model prediction itself fails."""
    # Configure the mock to return a failure
    mock_classifier.predict.return_value = {
        'success': False,
        'error': 'Model prediction failed'
    }

    result = analyze_xray_for_pneumonia('dummy_path.jpg')

    assert result['success'] is False
    assert result['error'] == 'Model prediction failed'
    assert result['provider'] == 'fine_tuned_model'
    assert result['is_medical_image'] is False
    assert result['confidence_score'] == 0.0
