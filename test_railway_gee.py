#!/usr/bin/env python3
"""
Test GEE initialization on Railway production
Check: environment variables, credentials, GEE connection
"""

import requests
import json
import sys

# Production URL
RAILWAY_URL = "https://aurora-githubpages-production.up.railway.app"
API_PREFIX = "/api"

def test_gee_diagnostics():
    """Test GEE diagnostics endpoint"""
    url = f"{RAILWAY_URL}{API_PREFIX}/gee/diagnostics"
    print(f"\n🧪 Testing GEE Diagnostics Endpoint")
    print(f"   URL: {url}")
    print(f"   {'='*70}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"\n✅ Diagnostics Response:")
        print(json.dumps(data, indent=2))
        
        # Check critical fields
        print(f"\n📊 Status Check:")
        print(f"   GEE_JSON_CONTENT env: {data.get('gee_json_content_env', '?')}")
        print(f"   GEE initialized flag: {data.get('gee_initialized_flag', '?')}")
        print(f"   GEE fetcher available: {data.get('gee_fetcher_available', '?')}")
        
        if data.get('credentials_file_exists'):
            print(f"   Service Account: {data.get('service_account_email', '?')}")
            print(f"   Project ID: {data.get('project_id', '?')}")
        
        if data.get('gee_connection_test'):
            print(f"   GEE Connection Test: {data.get('gee_connection_test', '?')}")
            if data.get('gee_test_error'):
                print(f"   GEE Test Error: {data.get('gee_test_error', '?')}")
        
        return data
        
    except Exception as e:
        print(f"❌ Error testing GEE diagnostics:")
        print(f"   {str(e)}")
        return None

def test_health_check():
    """Test backend health check"""
    url = f"{RAILWAY_URL}{API_PREFIX}/system/health"
    print(f"\n🧪 Testing Health Check Endpoint")
    print(f"   URL: {url}")
    print(f"   {'='*70}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"\n✅ Health Response:")
        print(json.dumps(data, indent=2))
        return data
        
    except Exception as e:
        print(f"❌ Error testing health check:")
        print(f"   {str(e)}")
        return None

def test_satellite_data():
    """Test satellite data endpoint"""
    url = f"{RAILWAY_URL}{API_PREFIX}/satellite-data"
    print(f"\n🧪 Testing Satellite Data Endpoint")
    print(f"   URL: {url}")
    print(f"   {'='*70}")
    
    payload = {
        "latitude": 9.15,
        "longitude": -1.5,
        "date_start": "2024-01-01",
        "date_end": "2024-12-31"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"\n✅ Satellite Data Response:")
        print(json.dumps(data, indent=2)[:500])  # Truncate for readability
        
        if "error" in data:
            print(f"\n⚠️  Error returned: {data.get('error', '?')}")
        else:
            print(f"\n✅ Real data returned!")
        
        return data
        
    except Exception as e:
        print(f"❌ Error testing satellite data:")
        print(f"   {str(e)}")
        return None

def main():
    print(f"\n{'='*70}")
    print(f"🚀 Aurora OSI - Railway GEE Integration Test")
    print(f"{'='*70}")
    
    # Test health first
    health = test_health_check()
    
    # Test GEE diagnostics
    diagnostics = test_gee_diagnostics()
    
    # Test satellite data
    satellite = test_satellite_data()
    
    # Summary
    print(f"\n{'='*70}")
    print(f"📋 Test Summary:")
    print(f"{'='*70}")
    
    if health:
        print(f"✅ Backend health: OK")
    else:
        print(f"❌ Backend health: FAILED")
    
    if diagnostics:
        if diagnostics.get('gee_json_content_env') == 'PRESENT':
            print(f"✅ GEE_JSON_CONTENT env var: SET")
        else:
            print(f"❌ GEE_JSON_CONTENT env var: NOT SET - Add to Railway Variables!")
        
        if diagnostics.get('gee_initialized_flag'):
            print(f"✅ GEE initialized: YES")
        else:
            print(f"❌ GEE initialized: NO - Check Railway logs for errors")
        
        if diagnostics.get('gee_fetcher_available'):
            print(f"✅ GEE fetcher: AVAILABLE")
        else:
            print(f"❌ GEE fetcher: NOT AVAILABLE")
    else:
        print(f"❌ Diagnostics: FAILED")
    
    if satellite:
        if "error" in satellite:
            print(f"❌ Satellite data: ERROR - {satellite.get('error', '?')[:100]}")
        else:
            print(f"✅ Satellite data: SUCCESS - Real data returned")
    else:
        print(f"❌ Satellite data: FAILED")
    
    print(f"\n{'='*70}")
    print(f"💡 Next Steps:")
    print(f"   1. If GEE_JSON_CONTENT not set: Add it to Railway Variables")
    print(f"   2. If GEE not initialized: Check Railway logs for decode errors")
    print(f"   3. If satellite data fails: Run this script again after restarting")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
