#!/usr/bin/env python3
"""
Test script to verify that different images produce different analysis results.
"""

import requests
import os
import json

def test_different_images():
    """Test that different images produce different analysis results."""
    
    # Test images
    test_images = [
        "00000001_000.png",
        "00009232_004.png", 
        "00001336_000.png"
    ]
    
    print("🔬 Testing Different Image Analysis")
    print("=" * 50)
    
    results = []
    
    for i, image_file in enumerate(test_images, 1):
        if not os.path.exists(image_file):
            print(f"❌ Image {image_file} not found, skipping...")
            continue
            
        print(f"\n📋 Test {i}: {image_file}")
        print("-" * 30)
        
        try:
            # Prepare the request
            with open(image_file, 'rb') as f:
                files = {'xray_image': (image_file, f, 'image/png')}
                data = {'symptoms': ''}
                
                # Send request
                response = requests.post(
                    'http://127.0.0.1:5000/api/analyze',
                    files=files,
                    data=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get('success'):
                        diagnosis = result.get('diagnosis', '')
                        
                        # Extract key information
                        finding = "Unknown"
                        confidence = "Unknown"
                        
                        # Look for finding in the diagnosis text
                        if "SUMMARY TABLE" in diagnosis:
                            # Extract from summary table
                            lines = diagnosis.split('\n')
                            for line in lines:
                                if '|' in line and '%' in line:
                                    parts = [p.strip() for p in line.split('|')]
                                    if len(parts) >= 4:
                                        finding = parts[1] if parts[1] else "Unknown"
                                        confidence = parts[2] if parts[2] else "Unknown"
                                        break
                        
                        print(f"✅ Analysis successful")
                        print(f"📊 Finding: {finding}")
                        print(f"🎯 Confidence: {confidence}")
                        print(f"⏱️  Processing time: {result.get('processing_time', 'Unknown')}")
                        
                        results.append({
                            'image': image_file,
                            'finding': finding,
                            'confidence': confidence,
                            'diagnosis_preview': diagnosis[:200] + "..." if len(diagnosis) > 200 else diagnosis
                        })
                        
                    else:
                        print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
                        
                else:
                    print(f"❌ HTTP Error: {response.status_code}")
                    print(f"Response: {response.text}")
                    
        except Exception as e:
            print(f"❌ Error testing {image_file}: {str(e)}")
    
    # Compare results
    print("\n" + "=" * 50)
    print("📊 COMPARISON RESULTS")
    print("=" * 50)
    
    if len(results) >= 2:
        print("✅ Multiple images analyzed successfully!")
        
        # Check if findings are different
        findings = [r['finding'] for r in results]
        unique_findings = set(findings)
        
        if len(unique_findings) > 1:
            print("🎉 SUCCESS: Different images produced different findings!")
            print(f"📋 Unique findings: {len(unique_findings)}")
            for finding in unique_findings:
                print(f"   • {finding}")
        else:
            print("⚠️  WARNING: All images produced the same finding")
            print(f"📋 Finding: {findings[0]}")
            
        # Show detailed results
        print("\n📋 DETAILED RESULTS:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['image']}")
            print(f"   Finding: {result['finding']}")
            print(f"   Confidence: {result['confidence']}")
            
    else:
        print("❌ Not enough successful analyses to compare")
        
    return results

if __name__ == "__main__":
    test_different_images() 