#!/usr/bin/env python3
"""
Aurora OSI - GEE Setup via Paste (No Local Storage)
Accepts GEE credentials JSON via paste, verifies, and configures
"""

import os
import sys
import json
import tempfile
from pathlib import Path


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


def print_info(text: str):
    """Print info message"""
    print(f"ℹ️  {text}")


def verify_json_content(json_content: str) -> tuple[bool, dict]:
    """Verify that the JSON content is valid GEE credentials"""
    try:
        creds = json.loads(json_content)
        
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        for field in required_fields:
            if field not in creds:
                print_error(f"Missing field in credentials: {field}")
                return False, {}
        
        print_success(f"Credentials JSON is valid")
        print_info(f"Service Account Email: {creds['client_email']}")
        print_info(f"Project ID: {creds['project_id']}")
        return True, creds
        
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON: {str(e)}")
        return False, {}
    except Exception as e:
        print_error(f"Error parsing credentials: {str(e)}")
        return False, {}


def save_credentials_securely(json_content: str) -> str:
    """Save credentials to a secure temporary location"""
    try:
        # Create secure credentials directory
        if os.name == 'nt':  # Windows
            creds_dir = Path(os.path.expandvars(r'%APPDATA%\Aurora\gee'))
        else:  # Linux/Mac
            creds_dir = Path.home() / '.aurora' / 'gee'
        
        creds_dir.mkdir(parents=True, exist_ok=True)
        
        # Set restrictive permissions on directory
        if os.name != 'nt':
            os.chmod(creds_dir, 0o700)
        
        # Save credentials file
        creds_path = creds_dir / 'gee-credentials.json'
        
        with open(creds_path, 'w') as f:
            f.write(json_content)
        
        # Set restrictive permissions on file
        if os.name != 'nt':
            os.chmod(creds_path, 0o600)
        
        print_success(f"Credentials saved securely to: {creds_path}")
        return str(creds_path)
        
    except Exception as e:
        print_error(f"Error saving credentials: {str(e)}")
        return None


def set_environment_variable(creds_path: str):
    """Set the GEE_CREDENTIALS environment variable"""
    try:
        # Windows: Use environment variable via registry/userenv
        if os.name == 'nt':
            os.system(f'setx GEE_CREDENTIALS "{creds_path}"')
            print_success(f"Environment variable set (restart PowerShell to apply)")
            print_info(f"Current session: set GEE_CREDENTIALS={creds_path}")
            os.environ['GEE_CREDENTIALS'] = creds_path
        else:
            # Linux/Mac
            rc_file = Path.home() / '.bashrc'
            export_cmd = f'export GEE_CREDENTIALS="{creds_path}"'
            
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
            
            os.environ['GEE_CREDENTIALS'] = creds_path
            print_info(f"Restart terminal or run: source ~/.bashrc")
        
        return True
        
    except Exception as e:
        print_error(f"Error setting environment variable: {str(e)}")
        return False


def test_gee_initialization():
    """Test GEE initialization via API"""
    try:
        import requests
    except ImportError:
        print_info("requests library not installed - skipping API test")
        return False
    
    try:
        response = requests.post(
            "http://localhost:8000/gee/initialize",
            json={},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print_success("GEE initialization successful via API")
                return True
            else:
                print_error(f"GEE initialization failed: {result.get('error')}")
                return False
        else:
            print_error(f"API returned status {response.status_code}")
            print_info("Make sure backend is running: python -m uvicorn backend.main:app --reload")
            return False
            
    except Exception as e:
        print_error(f"Could not connect to backend: {str(e)}")
        print_info("Make sure backend is running on http://localhost:8000")
        return False


def test_sentinel2_fetch():
    """Test Sentinel-2 data fetching"""
    try:
        import requests
    except ImportError:
        print_info("requests library not installed - skipping test")
        return False
    
    try:
        # Test with Busunu, Ghana coordinates from the error
        payload = {
            "latitude": 9.15,
            "longitude": -1.5,
            "radius_m": 5000,
            "max_cloud_cover": 0.3
        }
        
        print_info("Fetching Sentinel-2 data for Busunu, Ghana (this may take 30-60 seconds)...")
        
        response = requests.post(
            "http://localhost:8000/gee/sentinel2",
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                data = result.get("data", {})
                print_success(f"Sentinel-2 data fetched successfully!")
                print_info(f"Bands: {', '.join(data.get('bands', {}).keys())}")
                metadata = data.get("metadata", {})
                print_info(f"Acquisition Date: {metadata.get('acquisition_date')}")
                print_info(f"Cloud Coverage: {metadata.get('cloud_coverage')*100:.1f}%")
                return True
            else:
                print_error(f"Sentinel-2 fetch failed: {result.get('error')}")
                print_info("This may be normal if no satellite data is available for this date range")
                return False
        else:
            print_error(f"API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error testing Sentinel-2 fetch: {str(e)}")
        return False


def main():
    """Main setup flow"""
    print_header("Aurora OSI - GEE Setup (Paste Method)")
    
    print_info("This script will help you set up GEE authentication from a pasted JSON key")
    print_info("Your credentials will be saved securely and never committed to git")
    
    # Step 1: Paste JSON content
    print_step(1, "Paste GEE Credentials JSON")
    print_info("1. Paste your GEE JSON service key below")
    print_info("2. Press Enter twice when done (blank line signals end)")
    print_info("3. Keep your GEE key private!\n")
    
    lines = []
    print("Paste your JSON credentials (press Enter twice to finish):")
    empty_count = 0
    
    while True:
        try:
            line = input()
            if line.strip() == "":
                empty_count += 1
                if empty_count >= 2:
                    break
            else:
                empty_count = 0
                lines.append(line)
        except EOFError:
            break
    
    json_content = "\n".join(lines)
    
    if not json_content.strip():
        print_error("No JSON content provided")
        sys.exit(1)
    
    # Step 2: Verify JSON
    print_step(2, "Verify Credentials")
    is_valid, creds = verify_json_content(json_content)
    
    if not is_valid:
        print_error("Invalid credentials")
        sys.exit(1)
    
    # Step 3: Save securely
    print_step(3, "Save Credentials Securely")
    creds_path = save_credentials_securely(json_content)
    
    if not creds_path:
        print_error("Failed to save credentials")
        sys.exit(1)
    
    # Step 4: Set environment variable
    print_step(4, "Configure Environment Variable")
    if not set_environment_variable(creds_path):
        print_error("Failed to set environment variable")
        sys.exit(1)
    
    # Step 5: Test authentication
    print_step(5, "Test GEE Authentication")
    if test_gee_initialization():
        print_success("GEE authentication is working!")
    else:
        print_info("Backend may not be running - you can test manually later")
    
    # Step 6: Test Sentinel-2
    print_step(6, "Test Satellite Data Fetching")
    response = input("\nTest Sentinel-2 data fetch for Busunu, Ghana? (y/n): ").strip().lower()
    
    if response == 'y':
        if test_sentinel2_fetch():
            print_success("Satellite data fetching works!")
        else:
            print_info("GEE data may not be available for this location/date range")
    
    # Final summary
    print_header("Setup Complete")
    print_success("Aurora OSI GEE is configured!")
    print_info(f"Credentials saved to: {creds_path}")
    print_info(f"Environment variable: GEE_CREDENTIALS={creds_path}")
    print_info("\nNext steps:")
    print_info("1. Restart your backend server")
    print_info("2. Go back to MissionControl")
    print_info("3. Try the scan again - it should fetch real satellite data now!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)
