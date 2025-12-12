import os
import json
import subprocess
import requests
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE_DIR, "Jsons", "accounts.json")

def load_accounts():
  
    if not os.path.exists(ACCOUNTS_FILE):
        return []
    try:
        with open(ACCOUNTS_FILE, 'r') as f:
            data = json.load(f)
            return [data] if isinstance(data, dict) else data
    except Exception as e:
        print(f"Error loading accounts: {e}")
        return []

def get_account(username):
    
    for acc in load_accounts():
        if acc.get('username', '').lower() == username.lower():
            return acc
    return None

def normalize_cookie(raw):
   
    if not raw: 
        return ""
    s = str(raw).strip()
   
    if ".ROBLOSECURITY=" in s:
        s = s.split(".ROBLOSECURITY=", 1)[1].split(";", 1)[0]
    if "ROBLOSECURITY=" in s:
        s = s.split("ROBLOSECURITY=", 1)[1].split(";", 1)[0]
   
    if s.startswith("_|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items.|_"):
        s = s  
    return s.strip().strip('"').strip("'")

def validate_cookie(cookie):
    
    try:
        headers = {
            'Cookie': f'.ROBLOSECURITY={cookie}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
       
        response = requests.get(
            'https://users.roblox.com/v1/users/authenticated',
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            username = data.get('name', 'Unknown')
            user_id = data.get('id', 'Unknown')
            print(f"✓ Cookie is VALID - Logged in as: {username} (ID: {user_id})")
            return True, username
        else:
            print(f"✗ Cookie validation failed - Status: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False, None
            
    except Exception as e:
        print(f"✗ Error validating cookie: {e}")
        return False, None

def get_auth_ticket(cookie):
   
    try:
        headers = {
            'Cookie': f'.ROBLOSECURITY={cookie}',
            'Referer': 'https://www.roblox.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json'
        }
        
        
        csrf_response = requests.post(
            'https://auth.roblox.com/v1/authentication-ticket',
            headers=headers
        )
        
        csrf_token = csrf_response.headers.get('x-csrf-token')
        
        if csrf_token:
            print(f"✓ CSRF token obtained")
            headers['x-csrf-token'] = csrf_token
            
            
            response = requests.post(
                'https://auth.roblox.com/v1/authentication-ticket',
                headers=headers
            )
            
            auth_ticket = response.headers.get('rbx-authentication-ticket')
            
            if auth_ticket:
                print(f"✓ Auth ticket obtained: {auth_ticket[:20]}...")
                return auth_ticket
            else:
                print(f"✗ Failed to get auth ticket. Status: {response.status_code}")
                print(f"  Response: {response.text[:200]}")
                return None
        else:
           
            auth_ticket = csrf_response.headers.get('rbx-authentication-ticket')
            if auth_ticket:
                print(f"✓ Auth ticket obtained directly: {auth_ticket[:20]}...")
                return auth_ticket
            else:
                print(f"✗ No CSRF token or auth ticket received")
                return None
            
    except Exception as e:
        print(f"✗ Error getting auth ticket: {e}")
        return None

def launch_roblox_direct(place_id, auth_ticket, job_id=None):
    
    try:
        timestamp = int(time.time() * 1000)
        
        
        if job_id:
           
            base_url = f"https://assetgame.roblox.com/game/PlaceLauncher.ashx?request=RequestGameJob&browserTrackerId={timestamp}&placeId={place_id}&gameId={job_id}&isPlayTogetherGame=false"
        else:
            
            base_url = f"https://assetgame.roblox.com/game/PlaceLauncher.ashx?request=RequestGame&browserTrackerId={timestamp}&placeId={place_id}&isPlayTogetherGame=false"
        
     
        import urllib.parse
        encoded_url = urllib.parse.quote(base_url, safe='')
        
    
        launch_url = f"roblox-player:1+launchmode:play+gameinfo:{auth_ticket}+launchtime:{timestamp}+placelauncherurl:{encoded_url}+browsertrackerid:{timestamp}+robloxLocale:en_us+gameLocale:en_us+channel:"
        
        print(f"Launching Roblox...")
        
   
        subprocess.Popen(['cmd', '/c', 'start', '', launch_url], shell=True)
        
        print("✓ Roblox launch command sent!")
        return True
        
    except Exception as e:
        print(f"✗ Error launching Roblox: {e}")
        return False

def launch_with_account(username, place_id=None, job_id=None):
  
    print(f"\n{'='*50}")
    print(f"LAUNCHING ROBLOX FOR: {username}")
    print(f"{'='*50}")
    
    
    acc = get_account(username)
    if not acc:
        print(f"✗ User '{username}' not found in accounts.json")
        return False, f"User '{username}' not found"
    
   
    cookie = normalize_cookie(acc.get('cookie') or acc.get('password'))
    if not cookie:
        print("✗ No cookie found for account")
        return False, "No cookie found"
    
    print(f"✓ Cookie loaded (length: {len(cookie)} chars)")
    print(f"  First 30 chars: {cookie[:30]}...")
    

    print("\nValidating cookie...")
    is_valid, actual_username = validate_cookie(cookie)
    
    if not is_valid:
        print("\n" + "="*50)
        print("✗ COOKIE IS INVALID OR EXPIRED!")
        print("="*50)
        print("\nHow to get a new cookie:")
        print("1. Open Roblox.com in your browser")
        print("2. Log in to your account")
        print("3. Press F12 to open Developer Tools")
        print("4. Go to 'Application' tab (Chrome) or 'Storage' tab (Firefox)")
        print("5. Click 'Cookies' → 'https://www.roblox.com'")
        print("6. Find '.ROBLOSECURITY' cookie")
        print("7. Copy the entire VALUE (starts with '_|WARNING:-DO...')")
        print("8. Update your accounts.json file")
        print("="*50 + "\n")
        return False, "Cookie is invalid - please update it"

    if not place_id:
        print("✗ Place ID is required")
        return False, "Place ID required"
    
    print(f"✓ Target Place ID: {place_id}")
    if job_id:
        print(f"✓ Target Job ID: {job_id}")
    

    print("\nGetting authentication ticket...")
    auth_ticket = get_auth_ticket(cookie)
    
    if not auth_ticket:
        print("✗ Failed to get authentication ticket")
        return False, "Failed to get auth ticket"
    
  
    print("\nLaunching Roblox client...")
    success = launch_roblox_direct(place_id, auth_ticket, job_id)
    
    if success:
        print(f"\n{'='*50}")
        print("✓ SUCCESS! Roblox should be launching now...")
        print(f"{'='*50}\n")
        return True, f"Launched for {username} - Place: {place_id}"
    else:
        print("\n✗ Failed to launch Roblox")
        return False, "Launch failed"

def launch_game(place_id, job_id=None, username=None):
   
    if not place_id:
        return False, "Place ID required"
    
    if not username:
        accs = load_accounts()
        username = accs[0].get('username') if accs else None
    
    if not username:
        return False, "No username provided or no accounts found"
    
    return launch_with_account(username, place_id, job_id)


class RobloxMiniBrowser:
    launch_with_account = staticmethod(launch_with_account)
    launch_game = staticmethod(launch_game)
    get_account_by_username = staticmethod(get_account)
    _load_accounts = staticmethod(load_accounts)

class RobloxLauncher:

    
    @staticmethod
    def launch_with_account(username, place_id=None, job_id=None):
        return launch_with_account(username, place_id, job_id)
    
    @staticmethod
    def launch_game(place_id, job_id=None, username=None):
        return launch_game(place_id, job_id, username)
    
    @staticmethod
    def get_accounts():
        return load_accounts()
    
    @staticmethod
    def list_accounts():
        return [a.get('username', 'Unknown') for a in load_accounts()]
    
    @staticmethod
    def get_account_by_username(username):
        return get_account(username)