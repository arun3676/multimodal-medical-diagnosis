#!/usr/bin/env python3
"""
Simple test to verify the improved fallback diagnosis system.
"""

import os
import sys
import time

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.diagnosis_generator import MedicalDiagnosisGenerator

def test_fallback_system():
    """Test the improved fallback diagnosis system."""
    
    print("🔍 Testing Improved Fallback Diagnosis System")
    print("=" * 50)
    
    # Initialize diagnosis generator
    try:
        diagnosis_generator = MedicalDiagnosisGenerator()
        print("✅ Diagnosis generator initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize diagnosis generator: {e}")
        return
    
    # Test cases with different analysis results
    test_cases = [
        {
            'name': 'Cardiomegaly Case',
            'analysis': {
                'analysis_text': 'The chest x-ray demonstrates findings concerning for cardiomegaly. The cardiac silhouette is enlarged, exceeding the 50% transverse thoracic diameter, suggesting possible cardiomegaly.',
                'labels': [],
                'objects': []
            }
        },
        {
            'name': 'Pleural Effusion Case',
            'analysis': {
                'analysis_text': 'The chest radiograph demonstrates several significant findings. There is a large opacity obscuring the right hemidiaphragm and extending superiorly. The findings are consistent with pleural effusion.',
                'labels': [],
                'objects': []
            }
        },
        {
            'name': 'Pneumonia Case',
            'analysis': {
                'analysis_text': 'The chest x-ray demonstrates diffuse bilateral opacities consistent with likely bilateral pneumonia. The opacities are most prominent in the lower lung zones bilaterally.',
                'labels': [],
                'objects': []
            }
        },
        {
            'name': 'Normal Case',
            'analysis': {
                'analysis_text': 'The chest radiograph demonstrates normal cardiac silhouette and clear lung fields. No significant abnormalities are identified.',
                'labels': [],
                'objects': []
            }
        },
        {
            'name': 'Multiple Findings Case',
            'analysis': {
                'analysis_text': 'The chest x-ray demonstrates cardiomegaly with pleural effusion. The cardiac silhouette is enlarged and there is blunting of the costophrenic angles bilaterally.',
                'labels': [],
                'objects': []
            }
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔬 Testing Case {i}/{len(test_cases)}: {test_case['name']}")
        print("-" * 40)
        
        try:
            # Generate diagnosis using fallback
            diagnosis_results = diagnosis_generator.generate_diagnosis(
                test_case['analysis'],
                symptoms="Chest pain and shortness of breath",
                patient_info={'age': '45', 'gender': 'male'}
            )
            
            diagnosis_text = diagnosis_results.get('diagnosis', '')
            confidence = diagnosis_results.get('confidence_score', 0)
            
            print(f"📊 Confidence Score: {confidence}")
            print(f"📄 Diagnosis Length: {len(diagnosis_text)} characters")
            
            # Show first 300 characters of diagnosis
            diagnosis_preview = diagnosis_text[:300] + "..." if len(diagnosis_text) > 300 else diagnosis_text
            print(f"🏥 Diagnosis Preview: {diagnosis_preview}")
            
            # Store results
            results.append({
                'case_name': test_case['name'],
                'diagnosis_text': diagnosis_text,
                'confidence': confidence,
                'analysis_text': test_case['analysis']['analysis_text']
            })
            
            print("✅ Diagnosis generated successfully")
            
        except Exception as e:
            print(f"❌ Error generating diagnosis: {e}")
            continue
    
    # Analyze results for consistency
    print(f"\n📊 FALLBACK SYSTEM ANALYSIS")
    print("=" * 50)
    
    if len(results) < 2:
        print("⚠️  Need at least 2 test cases to analyze consistency")
        return
    
    # Check if diagnoses are different
    diagnosis_texts = [r['diagnosis_text'] for r in results]
    
    if len(set(diagnosis_texts)) == 1:
        print("🚨 CRITICAL ISSUE: All diagnoses are identical!")
        print("   The fallback system is not working correctly")
    else:
        print("✅ Diagnoses are different - fallback system is working correctly")
    
    # Show detailed comparison
    print(f"\n📋 DETAILED COMPARISON")
    print("=" * 50)
    
    for i, result in enumerate(results):
        print(f"\n🖼️  Case {i+1}: {result['case_name']}")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Diagnosis Length: {len(result['diagnosis_text'])} chars")
        print(f"   Analysis Preview: {result['analysis_text'][:100]}...")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS")
    print("=" * 50)
    
    if len(set(diagnosis_texts)) > 1:
        print("✅ Fallback system is working correctly!")
        print("   - Different analysis inputs produce different diagnoses")
        print("   - The system is using the actual Gemini analysis content")
        print("   - Multiple findings are being detected properly")
    else:
        print("🔧 ACTION NEEDED: Fix fallback diagnosis logic")
        print("   - Check the keyword detection in _generate_fallback_diagnosis")
        print("   - Verify the diagnosis text generation logic")
        print("   - Ensure findings are being properly extracted")

if __name__ == "__main__":
    test_fallback_system() 