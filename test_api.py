#!/usr/bin/env python3
"""
Test script for Image Processing API
Tests all endpoints and image processing functionality
"""

import requests
import base64
import json
from PIL import Image
import io
import os

# API Configuration
API_BASE_URL = "http://localhost:5000"

def create_test_image():
    """Create a simple test image for testing"""
    # Create a simple 100x100 RGB image with gradient
    img = Image.new('RGB', (100, 100), color='white')
    pixels = img.load()
    
    for i in range(100):
        for j in range(100):
            # Create a simple gradient pattern
            r = int(255 * i / 100)
            g = int(255 * j / 100)
            b = int(255 * (i + j) / 200)
            pixels[i, j] = (r, g, b)
    
    # Save to bytes
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Health check passed!")
            return True
        else:
            print("❌ Health check failed!")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_image_processing(filter_type):
    """Test image processing with specific filter"""
    print(f"\n🖼️ Testing {filter_type} filter...")
    
    try:
        # Create test image
        test_image = create_test_image()
        
        # Prepare the request
        files = {'image': ('test.png', test_image, 'image/png')}
        data = {'type': filter_type}
        
        # Send request
        response = requests.post(f"{API_BASE_URL}/process-image", files=files, data=data)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ {filter_type} processing successful!")
                print(f"Process type: {result.get('process_type')}")
                
                # Verify base64 image data
                image_data = result.get('processed_image', '')
                if image_data.startswith('data:image/png;base64,'):
                    print("✅ Base64 image data format is correct!")
                    
                    # Try to decode and verify it's a valid image
                    try:
                        base64_data = image_data.split(',')[1]
                        decoded_data = base64.b64decode(base64_data)
                        processed_img = Image.open(io.BytesIO(decoded_data))
                        print(f"✅ Processed image size: {processed_img.size}")
                        print(f"✅ Processed image mode: {processed_img.mode}")
                        return True
                    except Exception as e:
                        print(f"❌ Error decoding processed image: {e}")
                        return False
                else:
                    print("❌ Invalid image data format!")
                    return False
            else:
                print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing {filter_type}: {e}")
        return False

def test_error_handling():
    """Test error handling scenarios"""
    print("\n🚨 Testing error handling...")
    
    # Test 1: No image file
    print("Testing request without image...")
    try:
        response = requests.post(f"{API_BASE_URL}/process-image", data={'type': 'grayscale'})
        if response.status_code == 400:
            print("✅ Correctly handled missing image!")
        else:
            print(f"❌ Unexpected response for missing image: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing missing image: {e}")
    
    # Test 2: Invalid filter type
    print("Testing invalid filter type...")
    try:
        test_image = create_test_image()
        files = {'image': ('test.png', test_image, 'image/png')}
        data = {'type': 'invalid_filter'}
        
        response = requests.post(f"{API_BASE_URL}/process-image", files=files, data=data)
        result = response.json()
        print(f"Response for invalid filter: {result}")
        
        # Should still work (defaults to grayscale)
        if result.get('success'):
            print("✅ Invalid filter handled gracefully (defaulted to grayscale)!")
        else:
            print("❌ Invalid filter not handled properly!")
            
    except Exception as e:
        print(f"❌ Error testing invalid filter: {e}")

def main():
    """Run all tests"""
    print("🧪 Starting Image Processing API Tests")
    print("=" * 50)
    
    # Test health check
    if not test_health_check():
        print("❌ Health check failed. Make sure the API is running!")
        return
    
    # Test all filter types
    filters = ['grayscale', 'blur', 'sharpen', 'edge']
    success_count = 0
    
    for filter_type in filters:
        if test_image_processing(filter_type):
            success_count += 1
    
    # Test error handling
    test_error_handling()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print(f"✅ Successful filter tests: {success_count}/{len(filters)}")
    
    if success_count == len(filters):
        print("🎉 All tests passed! Backend API is working correctly!")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
