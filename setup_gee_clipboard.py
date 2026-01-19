#!/usr/bin/env python3
"""
Aurora OSI - GEE Setup via Clipboard
Reads GEE credentials directly from clipboard (simplest method)
"""

import os
import sys
import json
from pathlib import Path


def print_header(text: str):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_step(num: int, text: str):
    print(f"\n[Step {num}] {text}")


def print_success(text: str):
    print(f"✓ {text}")


def print_error(text: str):
    print(f"❌ {text}")


def print_info(text: str):
    print(f"ℹ️  {text}")


def get_clipboard_content() -> str:
    """Get content from system clipboard"""
    try:
        if os.name == 'nt':  # Windows
            import subprocess
            result = subprocess.run(
                ['powershell', '-Command', 'Get-Clipboard'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        else:  # Linux/Mac
            import subprocess
            result = subprocess.run(
                ['xclip', '-selection', 'clipboard', '-o'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout
            # Fallback for Mac
            result = subprocess.run(
                ['pbpaste'],
                capture_output=True,
                text=True
            )
            return result.stdout
    except Exception as e:
        print_error(f"Could not read clipboard: {str(e)}")
        return ""


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
    """Save credentials to a secure location"""
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
        # Windows: Use setx to set permanent environment variable
        if os.name == 'nt':
            os.system(f'setx GEE_CREDENTIALS "{creds_path}"')
            print_success(f"Environment variable set permanently")
            print_info(f"(Restart PowerShell to apply changes)")
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
        print_info("Testing GEE initialization...")
        response = requests.post(
            "http://localhost:8000/gee/initialize",
            json={},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print_success("✓ GEE initialization successful!")
                return True
            else:
                print_error(f"GEE initialization failed: {result.get('error')}")
                return False
        else:
            print_error(f"API returned status {response.status_code}")
            print_info("Make sure backend is running")
            return False
            
    except Exception as e:
        print_error(f"Could not connect to backend")
        print_info("Make sure backend is running: python -m uvicorn backend.main:app --reload")
        return False


def test_sentinel2_fetch():
    """Test Sentinel-2 data fetching"""
    try:
        import requests
    except ImportError:
        return False
    
    try:
        # Test with Busunu, Ghana coordinates
        payload = {
            "latitude": 9.15,
            "longitude": -1.5,
            "radius_m": 5000,
            "max_cloud_cover": 0.3
        }
        
        print_info("Fetching Sentinel-2 data for Busunu, Ghana...")
        
        response = requests.post(
            "http://localhost:8000/gee/sentinel2",
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                data = result.get("data", {})
                print_success(f"✓ Sentinel-2 data fetched!")
                print_info(f"  Bands: {', '.join(list(data.get('bands', {}).keys())[:3])}...")
                metadata = data.get("metadata", {})
                if metadata.get('acquisition_date'):
                    print_info(f"  Date: {metadata.get('acquisition_date')}")
                print_info(f"  Cloud: {metadata.get('cloud_coverage')*100:.1f}%")
                return True
            else:
                print_error(f"Satellite fetch failed: {result.get('error')}")
                return False
        else:
            print_error(f"API error: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Test error: {str(e)}")
        return False


def main():
    """Main setup flow"""
    print_header("Aurora OSI - GEE Setup (Clipboard)")
    
    print_info("Reading GEE credentials from your clipboard...")
    json_content = get_clipboard_content()
    
    if not json_content.strip():
        print_error("Clipboard is empty!")
        print_info("1. Copy your GEE JSON service key to clipboard")
        print_info("2. Run this script again")
        sys.exit(1)
    
    # Step 1: Verify JSON
    print_step(1, "Verify Credentials")
    is_valid, creds = verify_json_content(json_content)
    
    if not is_valid:
        print_error("Invalid or malformed JSON in clipboard")
        sys.exit(1)
    
    # Step 2: Save securely
    print_step(2, "Save Credentials Securely")
    creds_path = save_credentials_securely(json_content)
    
    if not creds_path:
        print_error("Failed to save credentials")
        sys.exit(1)
    
    # Step 3: Set environment variable
    print_step(3, "Configure Environment Variable")
    if not set_environment_variable(creds_path):
        print_error("Failed to set environment variable")
        sys.exit(1)
    
    # Step 4: Test authentication
    print_step(4, "Test GEE Authentication")
    test_gee_initialization()
    
    # Step 5: Optional test
    print_step(5, "Test Satellite Data (Optional)")
    response = input("\nTest Sentinel-2 fetch? (y/n): ").strip().lower()
    
    if response == 'y':
        test_sentinel2_fetch()
    
    # Final summary
    print_header("✓ Setup Complete!")
    print_success("Aurora OSI GEE is now configured")
    print_info(f"\nCredentials: {creds_path}")
    print_info(f"Service Account: {creds.get('client_email')}")
    print_info("\nWhat to do next:")
    print_info("1. Restart your backend server")
    print_info("2. Close and reopen PowerShell (to load environment variable)")
    print_info("3. Go back to MissionControl")
    print_info("4. Try scanning again - real satellite data will be fetched!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled")
        sys.exit(0)
    except Exception as e:
        print_error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
