#!/usr/bin/env python3
"""
Simple test script - bypasses syntax error and tests with local images
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_local_images():
    """Test with any local images in the project directory"""
    print("🔬 Testing Local Images")
    print("=" * 50)
    
    # Look for any image files in the project root
    image_extensions = ['.png', '.jpg', '.jpeg', '.webp']
    local_images = []
    
    for ext in image_extensions:
        local_images.extend(Path('.').glob(f'*{ext}'))
    
    if not local_images:
        print("❌ No local images found.")
        print("📁 Please add some test images to the project directory.")
        print("💡 You can download X-ray images from:")
        print("   - https://github.com/ieee8023/covid-chestxray-dataset")
        print("   - https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia")
        return
    
    print(f"📁 Found {len(local_images)} local images")
    
    for img_path in local_images[:3]:  # Test max 3 images
        print(f"\n📋 Testing: {img_path.name}")
        
        try:
            # Import here to avoid syntax error
            from app.core.vision_analyzer_gemini import GeminiImageAnalyzer
            from app.core.diagnosis_generator import MedicalDiagnosisGenerator
            
            analyzer = GeminiImageAnalyzer()
            generator = MedicalDiagnosisGenerator()
            
            # Analyze image
            print("🔍 Analyzing...")
            analysis = analyzer.analyze_medical_image(str(img_path), "chest_xray")
            
            # Generate diagnosis
            print("📊 Generating diagnosis...")
            diagnosis = generator.generate_diagnosis(analysis, symptoms="")
            
            print("📊 Results:")
            print("-" * 50)
            print(diagnosis['diagnosis'])
            print("-" * 50)
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            print("💡 This might be due to API issues or syntax errors")
        
        print()

if __name__ == "__main__":
    test_local_images()
    print("\n✅ Test complete!") 