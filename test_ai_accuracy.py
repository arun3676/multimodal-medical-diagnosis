#!/usr/bin/env python3
"""
Test script to evaluate AI accuracy on the provided chest X-ray image.
This will analyze the image and compare AI findings with actual radiographic findings.
"""

import os
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent / 'app'))

from app.core.vision_analyzer_gemini import GeminiImageAnalyzer
from app.core.diagnosis_generator import MedicalDiagnosisGenerator

def test_ai_accuracy():
    """Test the AI's accuracy on the provided chest X-ray."""
    
    # Initialize analyzers
    image_analyzer = GeminiImageAnalyzer()
    diagnosis_generator = MedicalDiagnosisGenerator()
    
    # Find the image file (assuming it's in the current directory)
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
    
    print(f"🔍 Testing AI accuracy on image: {image_path}")
    print("=" * 80)
    
    try:
        # Step 1: Analyze the image with Gemini
        print("📊 Step 1: Performing image analysis...")
        analysis_results = image_analyzer.analyze_medical_image(image_path, 'chest_xray')
        
        print(f"✅ Analysis completed")
        print(f"   - Is medical image: {analysis_results.get('is_medical_image', False)}")
        print(f"   - Quality rating: {analysis_results.get('quality_metrics', {}).get('quality_rating', 'Unknown')}")
        print(f"   - Labels detected: {len(analysis_results.get('labels', []))}")
        print(f"   - Objects detected: {len(analysis_results.get('objects', []))}")
        
        # Step 2: Generate diagnosis
        print("\n📋 Step 2: Generating diagnosis...")
        diagnosis_results = diagnosis_generator.generate_diagnosis(analysis_results, "")
        
        print(f"✅ Diagnosis generated")
        print(f"   - Confidence score: {diagnosis_results.get('confidence_score', 0):.2f}")
        
        # Step 3: Extract key findings from AI analysis
        print("\n🔍 Step 3: Extracting AI findings...")
        analysis_text = analysis_results.get('analysis_text', '')
        labels = analysis_results.get('labels', [])
        
        print("AI Analysis Text (first 500 chars):")
        print("-" * 40)
        print(analysis_text[:500] + "..." if len(analysis_text) > 500 else analysis_text)
        print("-" * 40)
        
        print("\nTop AI Detected Labels:")
        for i, label in enumerate(labels[:10], 1):
            print(f"   {i}. {label['description']} ({label['score']:.1%})")
        
        # Step 4: Compare with actual findings
        print("\n" + "=" * 80)
        print("🎯 ACCURACY ASSESSMENT")
        print("=" * 80)
        
        # Actual findings from the image description
        actual_findings = [
            "Bilateral diffuse reticular/reticulonodular opacities",
            "Cardiomegaly (enlarged heart)", 
            "Blunting of right costophrenic angle (small pleural effusion)",
            "Multiple medical devices (CVC, ECG leads)",
            "Elevated right hemidiaphragm"
        ]
        
        # AI findings from the diagnosis
        ai_findings = diagnosis_results.get('diagnosis', '')
        
        print("📋 ACTUAL FINDINGS (from image description):")
        for i, finding in enumerate(actual_findings, 1):
            print(f"   {i}. {finding}")
        
        print("\n🤖 AI REPORTED FINDINGS:")
        print("-" * 40)
        print(ai_findings)
        print("-" * 40)
        
        # Check for key discrepancies
        print("\n🔍 ACCURACY ANALYSIS:")
        
        # Check if AI reported "normal" when there are obvious abnormalities
        if "normal" in ai_findings.lower() and "chest x-ray" in ai_findings.lower():
            print("❌ CRITICAL ERROR: AI reported 'Normal chest X-ray'")
            print("   → ACTUAL: Multiple significant abnormalities present")
            print("   → This is a FALSE NEGATIVE - AI missed critical findings")
            
            # Check for specific missed findings
            missed_findings = []
            if "cardiomegaly" not in ai_findings.lower() and "heart" not in ai_findings.lower():
                missed_findings.append("Cardiomegaly")
            if "effusion" not in ai_findings.lower() and "pleural" not in ai_findings.lower():
                missed_findings.append("Pleural effusion")
            if "opacity" not in ai_findings.lower() and "consolidation" not in ai_findings.lower():
                missed_findings.append("Lung opacities")
            
            if missed_findings:
                print(f"   → MISSED FINDINGS: {', '.join(missed_findings)}")
        
        # Check if AI detected any of the actual findings
        detected_findings = []
        for finding in actual_findings:
            finding_lower = finding.lower()
            if any(term in ai_findings.lower() for term in finding_lower.split()):
                detected_findings.append(finding)
        
        if detected_findings:
            print(f"✅ CORRECTLY DETECTED: {len(detected_findings)} findings")
            for finding in detected_findings:
                print(f"   → {finding}")
        else:
            print("❌ NO ACTUAL FINDINGS DETECTED")
        
        # Overall assessment
        print("\n📊 OVERALL ASSESSMENT:")
        accuracy_score = len(detected_findings) / len(actual_findings) if actual_findings else 0
        print(f"   Accuracy: {accuracy_score:.1%} ({len(detected_findings)}/{len(actual_findings)} findings detected)")
        
        if accuracy_score < 0.5:
            print("   ❌ POOR ACCURACY: AI missed majority of significant findings")
        elif accuracy_score < 0.8:
            print("   ⚠️ MODERATE ACCURACY: AI detected some findings but missed others")
        else:
            print("   ✅ GOOD ACCURACY: AI detected most significant findings")
        
        # Check for false positives
        if "normal" in ai_findings.lower() and len(actual_findings) > 0:
            print("   ❌ FALSE NEGATIVE: AI reported normal when abnormalities present")
        
        print("\n" + "=" * 80)
        print("🎯 CONCLUSION")
        print("=" * 80)
        
        if "normal" in ai_findings.lower() and len(actual_findings) > 0:
            print("❌ FAIL: AI is providing FALSE NEGATIVE results")
            print("   This is dangerous for medical applications as it could miss")
            print("   critical findings that require immediate medical attention.")
        else:
            print("✅ PASS: AI detected some abnormalities")
            print("   However, accuracy needs improvement for clinical use.")
        
        print("\n💡 RECOMMENDATIONS:")
        print("   1. AI model needs retraining on abnormal chest X-rays")
        print("   2. Implement stricter validation for 'normal' classifications")
        print("   3. Add confidence thresholds for critical findings")
        print("   4. Consider ensemble methods for improved accuracy")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_accuracy() 