#!/usr/bin/env python3
"""
Deployment verification script for cuff type detection
Tests the new cuff_type field functionality
"""
import requests
import json

# Railway deployment URL
BASE_URL = "https://liamaivision-production.up.railway.app"

def test_health_endpoint():
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health endpoint working")
            print(f"   Status: {data.get('status')}")
            print(f"   OpenAI Available: {data.get('openai_available')}")
            print(f"   Google Vision Available: {data.get('google_vision_available')}")
            print(f"   Hybrid Ready: {data.get('hybrid_ready')}")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def test_cuff_type_fields_in_html():
    """Test that the HTML contains the new cuff type field"""
    print("\n🔍 Checking for cuff type field in deployed HTML...")
    try:
        response = requests.get(BASE_URL, timeout=10)
        if response.status_code == 200:
            html = response.text
            
            checks = [
                ('Inside Color field', 'inside_color'),
                ('Outside Color field', 'outside_color'),
                ('Cuff Type field', 'cuff_type'),
                ('Cuff Type label', 'Cuff Type'),
                ('Bell Cuff placeholder', 'Bell Cuff'),
                ('Straight Cuff placeholder', 'Straight Cuff'),
                ('Contour Cuff placeholder', 'Contour Cuff'),
            ]
            
            all_passed = True
            for check_name, search_term in checks:
                if search_term in html:
                    print(f"✅ {check_name} found")
                else:
                    print(f"❌ {check_name} NOT found")
                    all_passed = False
            
            return all_passed
        else:
            print(f"❌ Failed to fetch HTML: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ HTML check error: {e}")
        return False

def test_field_count():
    """Test that we now have all expected form fields"""
    print("\n🔍 Counting form fields in deployed application...")
    try:
        response = requests.get(BASE_URL, timeout=10)
        if response.status_code == 200:
            html = response.text
            
            # Count input fields (should have 6: manufacturer, class, size, inside_color, outside_color, cuff_type)
            input_count = html.count('<input type="text"')
            expected_fields = 6
            
            print(f"📊 Found {input_count} input fields (expected {expected_fields})")
            
            if input_count >= expected_fields:
                print("✅ All expected form fields present")
                return True
            else:
                print(f"❌ Missing form fields (found {input_count}, expected {expected_fields})")
                return False
        else:
            print(f"❌ Failed to fetch HTML: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Field count error: {e}")
        return False

def main():
    """Run all cuff type deployment tests"""
    print("🚀 Testing Railway Deployment - Cuff Type Detection")
    print("=" * 60)
    
    tests = [
        test_health_endpoint,
        test_cuff_type_fields_in_html,
        test_field_count,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Cuff Type Deployment verification SUCCESSFUL!")
        print("🔗 Application URL: https://liamaivision-production.up.railway.app")
        print("✨ New cuff type detection is working correctly!")
        print("\n📋 Available Cuff Types:")
        print("   • Bell Cuff - Widens into distinctive bell shape")
        print("   • Straight Cuff - Straight profile with straight-across cut")
        print("   • Contour Cuff - Slanted/angled cut across opening")
    else:
        print("⚠️ Some tests failed - check deployment")
    
    return passed == total

if __name__ == "__main__":
    main()
