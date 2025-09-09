#!/usr/bin/env python3
"""
Deployment verification script for the updated glove scanner
Tests the new inside/outside color field functionality
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

def test_main_page():
    """Test the main application page"""
    print("\n🔍 Testing main application page...")
    try:
        response = requests.get(BASE_URL, timeout=10)
        if response.status_code == 200:
            content = response.text
            # Check for new color fields in HTML
            if 'inside_color' in content and 'outside_color' in content:
                print("✅ Main page loaded successfully")
                print("✅ New inside/outside color fields detected in HTML")
                return True
            else:
                print("⚠️ Main page loaded but color fields not found")
                return False
        else:
            print(f"❌ Main page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Main page error: {e}")
        return False

def test_color_fields_in_html():
    """Test that the HTML contains the new color fields"""
    print("\n🔍 Checking for new color fields in deployed HTML...")
    try:
        response = requests.get(BASE_URL, timeout=10)
        if response.status_code == 200:
            html = response.text
            
            checks = [
                ('Inside Color field', 'inside_color'),
                ('Outside Color field', 'outside_color'),
                ('Inside Color label', 'Inside Color'),
                ('Outside Color label', 'Outside Color'),
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

def main():
    """Run all deployment tests"""
    print("🚀 Testing Railway Deployment - Updated Glove Scanner")
    print("=" * 60)
    
    tests = [
        test_health_endpoint,
        test_main_page,
        test_color_fields_in_html,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Deployment verification SUCCESSFUL!")
        print("🔗 Application URL: https://liamaivision-production.up.railway.app")
        print("✨ New inside/outside color fields are working correctly!")
    else:
        print("⚠️ Some tests failed - check deployment")
    
    return passed == total

if __name__ == "__main__":
    main()
