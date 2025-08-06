#!/usr/bin/env python3
"""
Simple validation script for testing public X-ray URLs
Memory-efficient: downloads one image at a time, processes, then deletes
"""
import tempfile
import requests
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Working test URLs (simpler, more reliable)
TEST_URLS = {
    "Normal": "https://raw.githubusercontent.com/ieee8023/covid-chestxray-dataset/master/images/1-s2.0-S0140673620303706-fx1_lrg.jpg",
    "COVID": "https://raw.githubusercontent.com/ieee8023/covid-chestxray-dataset/master/images/1-s2.0-S0140673620303706-fx2_lrg.jpg",
    "Pneumonia": "https://raw.githubusercontent.com/ieee8023/covid-chestxray-dataset/master/images/1-s2.0-S0140673620303706-fx3_lrg.jpg"
}

def download_and_test():
    """Download each image, test it, then delete it immediately"""
    print("🔬 Testing X-ray Analysis Pipeline")
    print("=" * 50)
    
    for name, url in TEST_URLS.items():
        print(f"\n📋 Testing: {name}")
        print(f"🔗 URL: {url}")
        
        try:
            # Download image to temp file
            print("⬇️  Downloading...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name
            
            print(f"✅ Downloaded ({len(response.content)} bytes)")
            
            # Test the analysis pipeline
            print("🔍 Analyzing...")
            try:
                from app.core.vision_analyzer_gemini import GeminiImageAnalyzer
                from app.core.diagnosis_generator import MedicalDiagnosisGenerator
                
                analyzer = GeminiImageAnalyzer()
                generator = MedicalDiagnosisGenerator()
                
                # Analyze image
                analysis = analyzer.analyze_medical_image(tmp_path, "chest_xray")
                
                # Generate diagnosis
                diagnosis = generator.generate_diagnosis(analysis, symptoms="")
                
                print("📊 Results:")
                print("-" * 30)
                print(diagnosis['diagnosis'][:500] + "..." if len(diagnosis['diagnosis']) > 500 else diagnosis['diagnosis'])
                print("-" * 30)
                
            except Exception as e:
                print(f"❌ Analysis failed: {e}")
            
            # Clean up temp file immediately
            os.unlink(tmp_path)
            print("🗑️  Cleaned up temp file")
            
        except requests.RequestException as e:
            print(f"❌ Download failed: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()

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
        print("❌ No local images found. Please add some test images to the project directory.")
        return
    
    print(f"📁 Found {len(local_images)} local images")
    
    for img_path in local_images[:3]:  # Test max 3 images
        print(f"\n📋 Testing: {img_path.name}")
        
        try:
            from app.core.vision_analyzer_gemini import GeminiImageAnalyzer
            from app.core.diagnosis_generator import MedicalDiagnosisGenerator
            
            analyzer = GeminiImageAnalyzer()
            generator = MedicalDiagnosisGenerator()
            
            # Analyze image
            analysis = analyzer.analyze_medical_image(str(img_path), "chest_xray")
            
            # Generate diagnosis
            diagnosis = generator.generate_diagnosis(analysis, symptoms="")
            
            print("📊 Results:")
            print("-" * 30)
            print(diagnosis['diagnosis'][:500] + "..." if len(diagnosis['diagnosis']) > 500 else diagnosis['diagnosis'])
            print("-" * 30)
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
        
        print()

if __name__ == "__main__":
    print("Choose test mode:")
    print("1. Test with online URLs")
    print("2. Test with local images")
    print("3. Both")
    
    choice = input("Enter choice (1/2/3): ").strip()
    
    if choice == "1":
        download_and_test()
    elif choice == "2":
        test_local_images()
    elif choice == "3":
        download_and_test()
        test_local_images()
    else:
        print("Invalid choice. Running both tests...")
        download_and_test()
        test_local_images()
    
    print("\n✅ Validation complete!") 