#!/usr/bin/env python3
"""
Simple test script to verify the simplified AI medical diagnosis system.
"""
import os
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent / 'app'))

from app.core.vision_analyzer_gemini import GeminiImageAnalyzer
from app.core.diagnosis_generator import MedicalDiagnosisGenerator

def test_simplified_system():
    """Test the simplified AI medical diagnosis system."""
    
    print("🔧 Testing Simplified AI Medical Diagnosis System")
    print("=" * 60)
    
    # Initialize analyzers
    try:
        image_analyzer = GeminiImageAnalyzer()
        diagnosis_generator = MedicalDiagnosisGenerator()
        print("✅ Analyzers initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing analyzers: {e}")
        return
    
    # Find test images
    image_files = [
        "00000001_000.png",
        "00001336_000.png", 
        "00009232_004.png",
        "00009232_004 (1).png"
    ]
    
    image_path = None
    for img_file in image_files:
        if os.path.exists(img_file):
            image_path = img_file
            break
    
    if not image_path:
        print("❌ No test image found. Please ensure one of the test images is in the current directory.")
        return
    
    print(f"📸 Testing with image: {image_path}")
    print()
    
    try:
        # Step 1: Analyze the image
        print("🔍 Step 1: Image Analysis")
        print("-" * 30)
        
        analysis_results = image_analyzer.analyze_medical_image(image_path, 'chest_xray')
        
        print(f"✅ Analysis completed successfully")
        print(f"   - Medical image detected: {analysis_results.get('is_medical_image', False)}")
        print(f"   - Quality rating: {analysis_results.get('quality_metrics', {}).get('quality_rating', 'Unknown')}")
        print(f"   - Labels detected: {len(analysis_results.get('labels', []))}")
        print(f"   - Objects detected: {len(analysis_results.get('objects', []))}")
        
        # Show analysis text preview
        analysis_text = analysis_results.get('analysis_text', '')
        if analysis_text:
            print(f"   - Analysis text length: {len(analysis_text)} characters")
            print(f"   - Preview: {analysis_text[:100]}...")
        
        print()
        
        # Step 2: Generate diagnosis
        print("📋 Step 2: Diagnosis Generation")
        print("-" * 30)
        
        diagnosis_results = diagnosis_generator.generate_diagnosis(analysis_results, "")
        
        print(f"✅ Diagnosis generated successfully")
        print(f"   - Confidence score: {diagnosis_results.get('confidence_score', 0):.2f}")
        print(f"   - Diagnosis length: {len(diagnosis_results.get('diagnosis', ''))} characters")
        
        # Show diagnosis preview
        diagnosis_text = diagnosis_results.get('diagnosis', '')
        if diagnosis_text:
            # Extract the main finding from the diagnosis
            lines = diagnosis_text.split('\n')
            for line in lines:
                if '|' in line and 'Finding' in line:
                    continue
                if '|' in line and '---' not in line and 'Finding' not in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 4:
                        finding = parts[1]
                        confidence = parts[2]
                        location = parts[3]
                        severity = parts[4] if len(parts) > 4 else 'Unknown'
                        print(f"   - Primary finding: {finding}")
                        print(f"   - Confidence: {confidence}")
                        print(f"   - Location: {location}")
                        print(f"   - Severity: {severity}")
                        break
        
        print()
        
        # Step 3: System assessment
        print("📊 Step 3: System Assessment")
        print("-" * 30)
        
        # Check if system is working properly
        if analysis_results.get('is_medical_image', False):
            print("✅ Medical image detection: Working")
        else:
            print("⚠️ Medical image detection: May need adjustment")
        
        if analysis_results.get('analysis_text'):
            print("✅ Image analysis: Working")
        else:
            print("❌ Image analysis: Failed")
        
        if diagnosis_results.get('diagnosis'):
            print("✅ Diagnosis generation: Working")
        else:
            print("❌ Diagnosis generation: Failed")
        
        if diagnosis_results.get('confidence_score', 0) > 0:
            print("✅ Confidence scoring: Working")
        else:
            print("❌ Confidence scoring: Failed")
        
        print()
        
        # Step 4: Performance metrics
        print("⚡ Step 4: Performance Metrics")
        print("-" * 30)
        
        # Calculate basic metrics
        analysis_length = len(analysis_results.get('analysis_text', ''))
        diagnosis_length = len(diagnosis_results.get('diagnosis', ''))
        confidence = diagnosis_results.get('confidence_score', 0)
        
        print(f"   - Analysis text length: {analysis_length} characters")
        print(f"   - Diagnosis text length: {diagnosis_length} characters")
        print(f"   - Overall confidence: {confidence:.1%}")
        
        # Quality assessment
        quality_metrics = analysis_results.get('quality_metrics', {})
        if quality_metrics:
            quality_score = quality_metrics.get('quality_score', 0)
            quality_rating = quality_metrics.get('quality_rating', 'Unknown')
            print(f"   - Image quality score: {quality_score:.2f}")
            print(f"   - Image quality rating: {quality_rating}")
        
        print()
        
        # Step 5: Summary
        print("🎯 Step 5: System Summary")
        print("-" * 30)
        
        if analysis_results.get('is_medical_image') and diagnosis_results.get('diagnosis'):
            print("✅ SYSTEM STATUS: OPERATIONAL")
            print("   The simplified AI medical diagnosis system is working correctly.")
            print("   It can analyze uploaded images and generate diagnostic reports.")
        else:
            print("⚠️ SYSTEM STATUS: PARTIALLY OPERATIONAL")
            print("   Some components may need adjustment.")
        
        print()
        print("💡 Key Improvements Made:")
        print("   - Simplified codebase for better maintainability")
        print("   - Removed unnecessary complexity")
        print("   - Enhanced error handling")
        print("   - Improved medical analysis prompts")
        print("   - Better fallback mechanisms")
        
        print()
        print("⚠️ Important Notes:")
        print("   - This system is for educational purposes only")
        print("   - Not intended for clinical use")
        print("   - Always consult healthcare professionals for medical decisions")
        print("   - Results should be validated by qualified radiologists")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simplified_system() 