#!/usr/bin/env python3
"""
Test script to validate the safety check implementation.
This script tests the body region mismatch detection.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.vision_analyzer_gemini import GeminiImageAnalyzer

def test_safety_check():
    """Test the safety check with a mock shoulder image."""
    
    print("🔍 Testing Safety Check Implementation...")
    print("=" * 50)
    
    # Initialize the analyzer
    analyzer = GeminiImageAnalyzer()
    
    # Test 1: Simulate a shoulder image file path with chest request
    print("\n📋 TEST 1: Shoulder image with chest request")
    print("-" * 40)
    
    # Use a real image file but simulate it's a shoulder by naming it
    # We'll copy an existing image to a shoulder-named file temporarily
    mock_shoulder_path = "test-shoulder-annotated-x-rays-2.jpg"
    
    # Copy an existing image to create our test file
    import shutil
    if os.path.exists("COVID-00001.jpg"):
        shutil.copy("COVID-00001.jpg", mock_shoulder_path)
        print(f"Created test file: {mock_shoulder_path}")
    else:
        print("No source image found for test")
    
    try:
        # This should trigger the forced override and safety check
        result = analyzer.analyze_medical_image(mock_shoulder_path, 'chest_xray')
        
        print(f"Result error: {result.get('error', 'None')}")
        print(f"Error message: {result.get('error_message', 'None')}")
        print(f"Detected type: {result.get('detected_type', 'None')}")
        print(f"Requested type: {result.get('requested_type', 'None')}")
        
        # Check if safety gate fired
        if result.get('error') == 'BODY_REGION_MISMATCH':
            print("✅ SUCCESS: Safety check fired correctly!")
            print("✅ Analysis was blocked as expected")
            return True
        else:
            print("❌ FAILURE: Safety check did not fire!")
            print("❌ Analysis proceeded when it should have been blocked")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Exception occurred: {str(e)}")
        return False
    finally:
        # Clean up test file
        if os.path.exists(mock_shoulder_path):
            os.remove(mock_shoulder_path)
            print("Cleaned up test file")

def test_normal_flow():
    """Test normal flow with auto-detect."""
    
    print("\n📋 TEST 2: Auto-detect mode (should work normally)")
    print("-" * 40)
    
    analyzer = GeminiImageAnalyzer()
    mock_path = "COVID-00001.jpg"  # Use existing image
    
    try:
        # This should work normally with auto-detect
        result = analyzer.analyze_medical_image(mock_path, 'auto_detect')
        
        print(f"Result error: {result.get('error', 'None')}")
        print(f"Detected type: {result.get('detected_type', 'None')}")
        
        # Auto-detect should not trigger mismatch error
        if result.get('error') == 'BODY_REGION_MISMATCH':
            print("❌ FAILURE: Auto-detect triggered mismatch error!")
            return False
        else:
            print("✅ SUCCESS: Auto-detect worked normally")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: Exception occurred: {str(e)}")
        return False

if __name__ == "__main__":
    print("🩺 Safety Check Validation Test")
    print("Testing body region mismatch detection...")
    
    test1_passed = test_safety_check()
    test2_passed = test_normal_flow()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"Test 1 (Safety Check): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 (Auto-detect): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED! Safety check is working correctly.")
    else:
        print("\n🚨 SOME TESTS FAILED! Safety check needs debugging.")
    
    print("=" * 50)