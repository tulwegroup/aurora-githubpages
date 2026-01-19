#!/usr/bin/env python3
"""
Test GEE with different locations and dates to find available data
"""

import requests
import json

RAILWAY_URL = "https://aurora-githubpages-production.up.railway.app"
API_PREFIX = "/api"

def test_satellite_data(lat, lon, start_date, end_date, location_name):
    """Test satellite data for specific location and dates"""
    url = f"{RAILWAY_URL}{API_PREFIX}/satellite-data"
    
    payload = {
        "latitude": lat,
        "longitude": lon,
        "date_start": start_date,
        "date_end": end_date
    }
    
    print(f"\n🧪 Testing: {location_name}")
    print(f"   Coords: ({lat}, {lon}), Dates: {start_date} to {end_date}")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        
        if "error" in data:
            print(f"   ❌ {data.get('error', '?')[:100]}")
            return False
        else:
            bands = len(data.get('bands', []))
            print(f"   ✅ SUCCESS - {bands} bands returned!")
            return True
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:80]}")
        return False

def main():
    print(f"\n{'='*70}")
    print(f"🧪 Testing Sentinel-2 Data Availability")
    print(f"{'='*70}")
    
    # Test various locations and dates
    tests = [
        # Original location but different dates
        (9.15, -1.5, "2023-06-01", "2023-08-31", "Busunu Ghana (Jun-Aug 2023)"),
        (9.15, -1.5, "2023-01-01", "2023-03-31", "Busunu Ghana (Jan-Mar 2023)"),
        
        # Different African locations with more likely coverage
        (-9.5, 27.8, "2023-06-01", "2023-08-31", "Zimbabwe (Jun-Aug 2023)"),
        (-10.5, 33.5, "2023-06-01", "2023-08-31", "Tanzania (Jun-Aug 2023)"),
        (1.0, 35.0, "2023-06-01", "2023-08-31", "Kenya (Jun-Aug 2023)"),
        
        # Recent dates with high cloud probability in tropics
        (9.15, -1.5, "2025-12-01", "2025-12-31", "Busunu Ghana (Dec 2025)"),
    ]
    
    success_count = 0
    for lat, lon, start, end, name in tests:
        if test_satellite_data(lat, lon, start, end, name):
            success_count += 1
    
    print(f"\n{'='*70}")
    print(f"📊 Results: {success_count}/{len(tests)} locations returned data")
    print(f"{'='*70}\n")
    
    if success_count == 0:
        print("💡 Possible reasons for no data:")
        print("   1. Busunu, Ghana location is in tropics with high cloud cover")
        print("   2. Sentinel-2 may not have coverage for this specific location")
        print("   3. Need to extend date range or try different locations")
        print("   4. GEE API might be filtering out low-quality/cloudy scenes")
    elif success_count > 0:
        print(f"✅ Found {success_count} locations with available Sentinel-2 data!")
        print("💡 Solution options:")
        print("   1. Use a location that returns data (see successful tests above)")
        print("   2. Extend date range to find less cloudy acquisitions")
        print("   3. Implement cloud filtering and scene selection in GEE fetcher")
    
    print()

if __name__ == "__main__":
    main()
