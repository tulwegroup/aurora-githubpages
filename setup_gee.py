#!/usr/bin/env python3
"""
Aurora OSI - GEE Setup Helper Script
Automates Google Earth Engine credential setup and testing
"""

import os
import sys
import json
from pathlib import Path
import subprocess


def print_header(text: str):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_step(num: int, text: str):
    """Print a numbered step"""
    print(f"\n[Step {num}] {text}")


def print_success(text: str):
    """Print success message"""
    print(f"✓ {text}")


def print_error(text: str):
    """Print error message"""
    print(f"❌ {text}")


def print_warning(text: str):
    """Print warning message"""
    print(f"⚠️  {text}")


def print_info(text: str):
    """Print info message"""
    print(f"ℹ️  {text}")


def verify_credentials_file(creds_path: str) -> bool:
    """Verify that the credentials file exists and is valid JSON"""
    if not Path(creds_path).exists():
        print_error(f"File not found: {creds_path}")
        return False
    
    try:
        with open(creds_path, 'r') as f:
            creds = json.load(f)
        
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        for field in required_fields:
            if field not in creds:
                print_error(f"Missing field in credentials: {field}")
                return False
        
        print_success(f"Credentials file is valid")
        print_info(f"Service Account Email: {creds['client_email']}")
        print_info(f"Project ID: {creds['project_id']}")
        return True
        
    except json.JSONDecodeError:
        print_error("Credentials file is not valid JSON")
        return False
    except Exception as e:
        print_error(f"Error reading credentials: {str(e)}")
        return False


def set_environment_variable(creds_path: str):
    """Set the GEE_CREDENTIALS environment variable"""
    # Determine shell and rc file
    shell = os.environ.get('SHELL', '/bin/bash')
    
    if 'bash' in shell:
        rc_file = Path.home() / '.bashrc'
        export_cmd = f'export GEE_CREDENTIALS="{creds_path}"'
    elif 'zsh' in shell:
        rc_file = Path.home() / '.zshrc'
        export_cmd = f'export GEE_CREDENTIALS="{creds_path}"'
    else:
        print_warning(f"Unknown shell: {shell}")
        print_info(f"Add this to your shell rc file:")
        print_info(f'export GEE_CREDENTIALS="{creds_path}"')
        return False
    
    # Add to rc file if not already present
    if rc_file.exists():
        with open(rc_file, 'r') as f:
            content = f.read()
        
        if 'GEE_CREDENTIALS' not in content:
            with open(rc_file, 'a') as f:
                f.write(f'\n# Aurora OSI GEE Credentials\n{export_cmd}\n')
            print_success(f"Added to {rc_file}")
    else:
        with open(rc_file, 'w') as f:
            f.write(f'# Aurora OSI GEE Credentials\n{export_cmd}\n')
        print_success(f"Created {rc_file}")
    
    # Set in current session
    os.environ['GEE_CREDENTIALS'] = creds_path
    print_info(f"Environment variable set for current session")
    
    return True


def test_backend_connection(backend_url: str = "http://localhost:8000") -> bool:
    """Test connection to Aurora OSI backend"""
    try:
        import requests
    except ImportError:
        print_warning("requests library not installed")
        print_info("Install with: pip install requests")
        return False
    
    try:
        response = requests.get(f"{backend_url}/docs", timeout=5)
        if response.status_code == 200:
            print_success(f"Backend is running at {backend_url}")
            return True
        else:
            print_error(f"Backend returned status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Could not connect to backend: {str(e)}")
        print_info(f"Make sure the backend is running with: python -m uvicorn backend.main:app --reload")
        return False


def test_gee_initialization(backend_url: str = "http://localhost:8000", creds_path: str = None) -> bool:
    """Test GEE initialization via API"""
    try:
        import requests
    except ImportError:
        print_warning("requests library not installed")
        return False
    
    try:
        payload = {}
        if creds_path:
            payload["credentials_path"] = creds_path
        
        response = requests.post(
            f"{backend_url}/gee/initialize",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print_success("GEE initialization successful")
                return True
            else:
                print_error(f"GEE initialization failed: {result.get('error')}")
                return False
        else:
            print_error(f"API returned status {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Error testing GEE initialization: {str(e)}")
        return False


def test_sentinel2_fetch(
    backend_url: str = "http://localhost:8000",
    latitude: float = 40.7128,
    longitude: float = -74.0060
) -> bool:
    """Test Sentinel-2 data fetching"""
    try:
        import requests
    except ImportError:
        print_warning("requests library not installed")
        return False
    
    try:
        payload = {
            "latitude": latitude,
            "longitude": longitude,
            "radius_m": 5000,
            "max_cloud_cover": 0.3
        }
        
        response = requests.post(
            f"{backend_url}/gee/sentinel2",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                data = result.get("data", {})
                print_success(f"Sentinel-2 data fetched successfully")
                print_info(f"Bands: {', '.join(data.get('bands', {}).keys())}")
                metadata = data.get("metadata", {})
                print_info(f"Acquisition Date: {metadata.get('acquisition_date')}")
                print_info(f"Cloud Coverage: {metadata.get('cloud_coverage')*100:.1f}%")
                return True
            else:
                print_error(f"Sentinel-2 fetch failed: {result.get('error')}")
                return False
        else:
            print_error(f"API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error fetching Sentinel-2 data: {str(e)}")
        return False


def main():
    """Main setup flow"""
    print_header("Aurora OSI - Google Earth Engine Setup")
    
    print_info("This script will help you set up GEE authentication for Aurora OSI")
    
    # Step 1: Locate credentials file
    print_step(1, "Locate GEE Credentials File")
    creds_path = input("\nEnter path to GEE credentials JSON file (or press Enter to skip): ").strip()
    
    if not creds_path:
        print_warning("Skipping credentials verification")
        creds_path = None
    else:
        # Expand home directory
        creds_path = os.path.expanduser(creds_path)
        
        if not verify_credentials_file(creds_path):
            print_error("Invalid credentials file")
            sys.exit(1)
    
    # Step 2: Set environment variable
    if creds_path:
        print_step(2, "Set Environment Variable")
        response = input("\nAdd GEE_CREDENTIALS to shell rc file? (y/n): ").strip().lower()
        
        if response == 'y':
            if set_environment_variable(creds_path):
                print_success("Environment variable configured")
                print_info("Restart your terminal or run: source ~/.bashrc")
            else:
                print_warning("Could not set environment variable")
    
    # Step 3: Test backend connection
    print_step(3, "Test Backend Connection")
    backend_url = input("\nBackend URL (default: http://localhost:8000): ").strip()
    backend_url = backend_url or "http://localhost:8000"
    
    if not test_backend_connection(backend_url):
        print_warning("Backend is not running")
        print_info("You can start it with: cd backend && python -m uvicorn main:app --reload")
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            sys.exit(0)
    
    # Step 4: Test GEE initialization
    print_step(4, "Test GEE Initialization")
    response = input("\nTest GEE initialization? (y/n): ").strip().lower()
    
    if response == 'y':
        if test_gee_initialization(backend_url, creds_path):
            print_success("GEE is ready to use")
            
            # Step 5: Test Sentinel-2 fetching
            print_step(5, "Test Sentinel-2 Data Fetching")
            response = input("\nFetch sample Sentinel-2 data? (y/n): ").strip().lower()
            
            if response == 'y':
                latitude = input("Enter latitude (default: 40.7128): ").strip()
                latitude = float(latitude) if latitude else 40.7128
                
                longitude = input("Enter longitude (default: -74.0060): ").strip()
                longitude = float(longitude) if longitude else -74.0060
                
                print_info("Fetching Sentinel-2 data (this may take a minute)...")
                if test_sentinel2_fetch(backend_url, latitude, longitude):
                    print_success("Sentinel-2 data fetching works!")
                else:
                    print_warning("Could not fetch Sentinel-2 data")
        else:
            print_error("GEE initialization failed")
            print_info("Check that:")
            print_info("  1. GEE credentials file is correct")
            print_info("  2. Service account is registered with Earth Engine")
            print_info("  3. GEE_CREDENTIALS environment variable is set correctly")
    
    # Final summary
    print_header("Setup Complete")
    print_success("Aurora OSI GEE setup is complete!")
    print_info("\nNext steps:")
    print_info("1. Test the GEE endpoints with sample coordinates")
    print_info("2. Integrate GEE data with MissionControl scans")
    print_info("3. Configure visualization to show satellite imagery")
    print_info("\nFor more information, see: GEE_SETUP_GUIDE.md")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)
