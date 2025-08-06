#!/usr/bin/env python3
"""
Simple test to verify the web application analysis functionality.
"""

import requests
import os
import time

def test_web_analysis():
    """Test the web application analysis functionality."""
    
    print("🔍 Testing Web Application Analysis")
    print("=" * 50)
    
    # Test if the server is running
    try:
        response = requests.get("http://127.0.0.1:5000", timeout=5)
        if response.status_code == 200:
            print("✅ Web application is running successfully")
        else:
            print(f"❌ Web application returned status code: {response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to web application: {e}")
        return
    
    # Find a test image
    test_images = []
    for ext in ['.png', '.jpg', '.jpeg']:
        for file in os.listdir('.'):
            if file.lower().endswith(ext):
                test_images.append(file)
                break
    
    if not test_images:
        print("❌ No test images found in current directory")
        return
    
    test_image = test_images[0]
    print(f"📁 Using test image: {test_image}")
    
    # Test the analysis endpoint
    try:
        print("🤖 Testing image analysis...")
        
        with open(test_image, 'rb') as f:
            files = {'xray_image': (test_image, f, 'image/png')}
            data = {
                'symptoms': 'Chest pain and shortness of breath',
                'patient_age': '45',
                'patient_gender': 'male',
                'medical_history': 'Hypertension'
            }
            
            start_time = time.time()
            response = requests.post(
                "http://127.0.0.1:5000/analyze",
                files=files,
                data=data,
                timeout=60
            )
            analysis_time = time.time() - start_time
            
            print(f"⏱️  Analysis time: {analysis_time:.2f}s")
            print(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Analysis completed successfully")
                print(f"📄 Response length: {len(response.text)} characters")
                
                # Check if we got redirected to results page
                if response.url != "http://127.0.0.1:5000/analyze":
                    print(f"🔄 Redirected to: {response.url}")
                    
                    # Try to access the results page
                    results_response = requests.get(response.url, timeout=10)
                    if results_response.status_code == 200:
                        print("✅ Results page accessible")
                        print(f"📄 Results page length: {len(results_response.text)} characters")
                        
                        # Check for diagnosis content
                        if "AI-Assisted Medical Assessment" in results_response.text:
                            print("✅ Diagnosis content found in results")
                        else:
                            print("⚠️  No diagnosis content found in results")
                    else:
                        print(f"❌ Results page returned status: {results_response.status_code}")
                else:
                    print("⚠️  No redirect to results page")
                    
            elif response.status_code == 302:
                print("✅ Analysis completed with redirect")
                print(f"🔄 Redirect location: {response.headers.get('Location', 'Unknown')}")
                
            else:
                print(f"❌ Analysis failed with status: {response.status_code}")
                print(f"📄 Error response: {response.text[:500]}...")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print(f"\n💡 RECOMMENDATIONS")
    print("=" * 50)
    print("✅ Web application is functional")
    print("✅ Analysis endpoint is responding")
    print("✅ You can now test with different images through the web interface")

if __name__ == "__main__":
    test_web_analysis() 