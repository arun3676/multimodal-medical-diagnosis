#!/usr/bin/env python3
"""
Test script to verify AI consistency and detect if the system is actually analyzing images
or just returning cached/fallback results.
"""

import os
import sys
import time
import hashlib
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.vision_analyzer_gemini import GeminiImageAnalyzer
from app.core.diagnosis_generator import MedicalDiagnosisGenerator

def calculate_image_hash(image_path):
    """Calculate SHA-256 hash of image file."""
    with open(image_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def test_ai_consistency():
    """Test if AI is actually analyzing different images."""
    
    print("🔍 Testing AI Consistency and Image Analysis")
    print("=" * 50)
    
    # Initialize analyzers
    try:
        image_analyzer = GeminiImageAnalyzer()
        diagnosis_generator = MedicalDiagnosisGenerator()
        print("✅ Analyzers initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize analyzers: {e}")
        return
    
    # Find test images in current directory
    test_images = []
    image_extensions = ['.png', '.jpg', '.jpeg', '.webp']
    
    for ext in image_extensions:
        test_images.extend(Path('.').glob(f'*{ext}'))
        test_images.extend(Path('.').glob(f'*{ext.upper()}'))
    
    if not test_images:
        print("❌ No test images found in current directory")
        print("Please place some medical images (PNG, JPG, JPEG, WebP) in this directory")
        return
    
    print(f"📁 Found {len(test_images)} test images")
    
    results = []
    
    for i, image_path in enumerate(test_images, 1):
        print(f"\n🔬 Testing Image {i}/{len(test_images)}: {image_path.name}")
        print("-" * 40)
        
        try:
            # Calculate image hash
            image_hash = calculate_image_hash(image_path)
            print(f"📊 Image Hash: {image_hash[:16]}...")
            
            # Analyze image
            print("🤖 Analyzing image with Gemini...")
            start_time = time.time()
            
            analysis_results = image_analyzer.analyze_medical_image(str(image_path))
            
            analysis_time = time.time() - start_time
            print(f"⏱️  Analysis time: {analysis_time:.2f}s")
            
            # Extract key information
            analysis_text = analysis_results.get('analysis_text', '')
            is_medical = analysis_results.get('is_medical_image', False)
            
            print(f"📋 Medical Image: {is_medical}")
            print(f"📝 Analysis Length: {len(analysis_text)} characters")
            
            # Show first 200 characters of analysis
            preview = analysis_text[:200] + "..." if len(analysis_text) > 200 else analysis_text
            print(f"🔍 Analysis Preview: {preview}")
            
            # Generate diagnosis
            print("🏥 Generating diagnosis...")
            diagnosis_results = diagnosis_generator.generate_diagnosis(analysis_results)
            
            diagnosis_text = diagnosis_results.get('diagnosis', '')
            confidence = diagnosis_results.get('confidence_score', 0)
            
            print(f"📊 Confidence Score: {confidence}")
            print(f"📄 Diagnosis Length: {len(diagnosis_text)} characters")
            
            # Show first 200 characters of diagnosis
            diagnosis_preview = diagnosis_text[:200] + "..." if len(diagnosis_text) > 200 else diagnosis_text
            print(f"🏥 Diagnosis Preview: {diagnosis_preview}")
            
            # Store results
            results.append({
                'image_name': image_path.name,
                'image_hash': image_hash,
                'analysis_text': analysis_text,
                'diagnosis_text': diagnosis_text,
                'confidence': confidence,
                'analysis_time': analysis_time,
                'is_medical': is_medical
            })
            
            print("✅ Analysis completed")
            
        except Exception as e:
            print(f"❌ Error analyzing {image_path.name}: {e}")
            continue
    
    # Analyze results for consistency issues
    print(f"\n📊 CONSISTENCY ANALYSIS")
    print("=" * 50)
    
    if len(results) < 2:
        print("⚠️  Need at least 2 images to test consistency")
        return
    
    # Check for identical analyses
    analysis_texts = [r['analysis_text'] for r in results]
    diagnosis_texts = [r['diagnosis_text'] for r in results]
    
    # Check if all analyses are identical
    if len(set(analysis_texts)) == 1:
        print("🚨 CRITICAL ISSUE: All Gemini analyses are identical!")
        print("   This suggests the AI is not actually analyzing the images")
    else:
        print("✅ Gemini analyses are different - AI is analyzing images")
    
    # Check if all diagnoses are identical
    if len(set(diagnosis_texts)) == 1:
        print("🚨 CRITICAL ISSUE: All diagnoses are identical!")
        print("   This suggests the diagnosis generator is using fallback/cached results")
    else:
        print("✅ Diagnoses are different - system is working correctly")
    
    # Check for OpenAI API issues
    openai_failures = sum(1 for r in results if "fallback" in r['diagnosis_text'].lower())
    if openai_failures > 0:
        print(f"⚠️  {openai_failures}/{len(results)} analyses used fallback (OpenAI API issues)")
    
    # Show detailed comparison
    print(f"\n📋 DETAILED COMPARISON")
    print("=" * 50)
    
    for i, result in enumerate(results):
        print(f"\n🖼️  Image {i+1}: {result['image_name']}")
        print(f"   Hash: {result['image_hash'][:16]}...")
        print(f"   Medical: {result['is_medical']}")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Analysis Time: {result['analysis_time']:.2f}s")
        print(f"   Analysis Length: {len(result['analysis_text'])} chars")
        print(f"   Diagnosis Length: {len(result['diagnosis_text'])} chars")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS")
    print("=" * 50)
    
    if len(set(analysis_texts)) == 1:
        print("🔧 ACTION NEEDED: Check Gemini API configuration and prompts")
        print("   - Verify GEMINI_API_KEY is correct")
        print("   - Check if API is returning cached responses")
        print("   - Review the analysis prompt in vision_analyzer_gemini.py")
    
    if len(set(diagnosis_texts)) == 1:
        print("🔧 ACTION NEEDED: Check OpenAI API and fallback logic")
        print("   - Verify OPENAI_API_KEY is correct")
        print("   - Check OpenAI API quota/limits")
        print("   - Review fallback diagnosis logic in diagnosis_generator.py")
    
    if openai_failures > 0:
        print("🔧 ACTION NEEDED: Fix OpenAI API issues")
        print("   - Check API key validity")
        print("   - Verify account has sufficient credits")
        print("   - Consider upgrading fallback logic")
    
    if len(set(analysis_texts)) > 1 and len(set(diagnosis_texts)) > 1:
        print("✅ System appears to be working correctly!")
        print("   - Different images produce different analyses")
        print("   - AI is actually analyzing image content")

if __name__ == "__main__":
    test_ai_consistency() 