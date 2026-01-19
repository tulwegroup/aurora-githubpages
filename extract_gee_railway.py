import json
import base64
from pathlib import Path

# Read the GEE credentials from local storage
creds_path = Path(r'C:\Users\gh\AppData\Roaming\Aurora\gee\gee-credentials.json')

if creds_path.exists():
    with open(creds_path, 'r') as f:
        json_content = f.read()
    
    # Parse and verify
    creds = json.loads(json_content)
    print('✓ GEE Credentials Found')
    print(f'  Service Account: {creds.get("client_email")}')
    print(f'  Project ID: {creds.get("project_id")}')
    
    # Encode for Railway
    encoded = base64.b64encode(json_content.encode()).decode()
    
    print('\n' + '='*70)
    print('RAILWAY CONFIGURATION')
    print('='*70)
    print('\n1. Go to https://railway.app/dashboard')
    print('2. Select your Aurora OSI backend project')
    print('3. Click "Variables" tab')
    print('4. Add these environment variables:\n')
    print('Variable 1:')
    print('  Key: GEE_JSON_CONTENT')
    print(f'  Value: {encoded}\n')
    print('5. Deploy and restart backend')
    
    # Save to file
    output_file = Path.home() / 'Desktop' / 'railway_gee_config.txt'
    with open(output_file, 'w') as f:
        f.write(f'GEE_JSON_CONTENT={encoded}\n')
    print(f'\n✓ Saved to: {output_file}')
else:
    print('❌ GEE credentials file not found')
