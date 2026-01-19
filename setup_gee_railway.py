#!/usr/bin/env python3
"""
Aurora OSI - Deploy GEE Credentials to Railway
Converts GEE JSON to Railway-compatible environment variable
"""

import os
import sys
import json
import base64
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
            return result.stdout
    except Exception as e:
        return ""


def verify_json_content(json_content: str) -> tuple[bool, dict]:
    """Verify that the JSON content is valid GEE credentials"""
    try:
        creds = json.loads(json_content)
        
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        for field in required_fields:
            if field not in creds:
                print_error(f"Missing field: {field}")
                return False, {}
        
        print_success(f"Credentials are valid")
        print_info(f"Service Account: {creds['client_email']}")
        print_info(f"Project ID: {creds['project_id']}")
        return True, creds
        
    except json.JSONDecodeError:
        print_error(f"Invalid JSON format")
        return False, {}
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False, {}


def main():
    """Main flow"""
    print_header("Deploy GEE to Railway")
    
    print_info("This will prepare your GEE credentials for Railway deployment")
    
    # Step 1: Get credentials
    print_step(1, "Get GEE Credentials from Clipboard")
    print_info("Reading from clipboard...")
    json_content = get_clipboard_content()
    
    if not json_content.strip():
        print_error("Clipboard is empty!")
        print_info("Copy your GEE JSON service key and try again")
        sys.exit(1)
    
    # Step 2: Verify
    print_step(2, "Verify Credentials")
    is_valid, creds = verify_json_content(json_content)
    
    if not is_valid:
        print_error("Invalid credentials")
        sys.exit(1)
    
    # Step 3: Prepare for Railway
    print_step(3, "Prepare for Railway Deployment")
    
    # Create a temporary credentials file
    temp_creds_path = Path.home() / '.aurora_temp_gee.json'
    with open(temp_creds_path, 'w') as f:
        f.write(json_content)
    
    print_success("Created temporary credentials file")
    
    # Step 4: Show railway configuration
    print_step(4, "Configure Railway")
    
    print_info("\n📌 OPTION 1: Via Railway Dashboard (Web UI)")
    print_info("1. Go to https://railway.app/dashboard")
    print_info("2. Select your Aurora OSI backend project")
    print_info("3. Click 'Variables' tab")
    print_info("4. Add new variable:")
    print_info("   Key: GEE_CREDENTIALS")
    print_info(f"   Value: /app/gee-credentials.json")
    print_info("5. In same tab, also add:")
    print_info("   Key: GEE_JSON_CONTENT")
    
    # Encode for safety
    encoded = base64.b64encode(json_content.encode()).decode()
    
    print_info(f"   Value: {encoded[:80]}...")
    print_info("6. Deploy")
    
    print_info("\n📌 OPTION 2: Via railway.toml (Code)")
    print_info("Add to your railway.toml:")
    print_info(f"""
[variables]
GEE_CREDENTIALS = "/app/gee-credentials.json"
GEE_JSON_CONTENT = "{encoded}"
""")
    
    print_info("\n📌 OPTION 3: Via Environment File")
    print_info(f"Save this to .env.railway:")
    
    # Write to file
    env_file = Path.home() / 'Desktop' / 'railway_env.txt'
    with open(env_file, 'w') as f:
        f.write(f"GEE_CREDENTIALS=/app/gee-credentials.json\n")
        f.write(f"GEE_JSON_CONTENT={encoded}\n")
    
    print_info(f"✓ Saved to: {env_file}")
    
    # Step 5: Show backend update needed
    print_step(5, "Backend Update Needed")
    
    print_info("Your backend.main needs to handle the encoded GEE JSON.")
    print_info("Add this to backend/main.py:")
    
    code = '''
# At the top of main.py, add:
import base64

# Update GEE initialization:
@app.on_event("startup")
async def startup_gee():
    """Initialize GEE from Railway environment variable"""
    try:
        # Try reading from environment
        gee_json_content = os.getenv("GEE_JSON_CONTENT")
        if gee_json_content:
            # Decode base64
            gee_json_str = base64.b64decode(gee_json_content).decode()
            # Write to temp file
            import tempfile
            temp_dir = tempfile.gettempdir()
            creds_path = os.path.join(temp_dir, "gee-credentials.json")
            with open(creds_path, 'w') as f:
                f.write(gee_json_str)
            os.environ["GEE_CREDENTIALS"] = creds_path
            logger.info("✓ GEE credentials initialized from Railway env")
    except Exception as e:
        logger.warning(f"GEE initialization: {str(e)}")
'''
    
    print_info(code)
    
    # Step 6: Deploy
    print_step(6, "Deploy to Railway")
    
    print_info("1. Configure variables in Railway dashboard (Option 1 above)")
    print_info("2. Or add to railway.toml and push")
    print_info("3. Railway will automatically redeploy")
    print_info("4. Check logs to verify GEE initialization")
    
    # Final
    print_header("Next Steps")
    print_success("Ready to deploy GEE to Railway!")
    print_info("\n1. Set GEE_JSON_CONTENT environment variable on Railway")
    print_info("2. Update backend/main.py with startup_gee() function")
    print_info("3. Deploy: git push railway main")
    print_info("4. Check Railway logs for GEE initialization")
    print_info("5. Try MissionControl scan - should work now!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled")
        sys.exit(0)
    except Exception as e:
        print_error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
