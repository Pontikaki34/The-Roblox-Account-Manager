import os
import sys
import time
import logging
import json
import tempfile
import shutil
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium not available - install with: pip install selenium webdriver-manager")


class RobloxLogin:
    
    
    PROFILE_DIR = os.path.join(os.getcwd(), "chrome_profiles")
    
    def __init__(self):
       
        self.driver = None
        self.wait = None
        os.makedirs(self.PROFILE_DIR, exist_ok=True)
    
    @staticmethod
    def get_profile_path(username):
       
        safe_username = "".join(c for c in username if c.isalnum() or c in ('_', '-'))
        return os.path.join(RobloxLogin.PROFILE_DIR, f"profile_{safe_username}")
    
    def setup_driver(self, username, headless=True):
       
        if not SELENIUM_AVAILABLE:
            logger.error("Selenium not installed")
            return None
        
        try:
            profile_path = self.get_profile_path(username)
            os.makedirs(profile_path, exist_ok=True)
            
            chrome_options = Options()
            chrome_options.add_argument(f'--user-data-dir={profile_path}')
            chrome_options.add_argument('--profile-directory=Default')
            
            if headless:
                chrome_options.add_argument('--headless=new')
                chrome_options.add_argument('--disable-gpu')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
          
            chrome_options.add_experimental_option('prefs', {
                'protocol_handler.allowed_origin_protocol_pairs': {
                    'https://www.roblox.com': {'roblox': True, 'roblox-player': True}
                }
            })
            
            import warnings
            warnings.filterwarnings('ignore')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            
            logger.info(f"Chrome driver setup complete for user: {username}")
            return self.driver
            
        except Exception as e:
            logger.error(f"Failed to setup driver: {e}")
            return None
    
    def is_logged_in(self):

        if not self.driver:
            return False
        
        try:
            self.driver.get("https://www.roblox.com/home")
            time.sleep(2)
            current_url = self.driver.current_url.lower()
            
          
            if "login" in current_url:
                return False
            
          
            try:
                self.driver.find_element(By.ID, "navbar-user-info")
                logger.info("User is logged in (found navbar)")
                return True
            except NoSuchElementException:
                pass
            
          
            logged_in = "home" in current_url or "discover" in current_url
            logger.info(f"Login check: {logged_in} (URL: {current_url})")
            return logged_in
            
        except Exception as e:
            logger.debug(f"Login check failed: {e}")
            return False
    
    def login_with_cookie(self, username, cookie):
       
        try:
            if not self.driver:
                self.setup_driver(username, headless=True)
            
            if not self.driver:
                return False
            
            logger.info(f"Logging in with cookie for: {username}")
            
            
            self.driver.get("https://www.roblox.com")
            time.sleep(2)
            
            
            cookie_dict = {
                'name': '.ROBLOSECURITY',
                'value': cookie,
                'domain': '.roblox.com',
                'path': '/',
                'secure': True,
                'httpOnly': True
            }
            
            self.driver.add_cookie(cookie_dict)
            logger.info("Cookie added to session")
            
           
            self.driver.refresh()
            time.sleep(3)
            
           
            if self.is_logged_in():
                logger.info(f"Successfully logged in as: {username}")
                return True
            else:
                logger.warning("Cookie login failed - cookie may be invalid")
                return False
            
        except Exception as e:
            logger.error(f"Cookie login failed: {e}")
            return False
    
    def login_with_credentials(self, username, password):
       
        try:
            if not self.driver:
                self.setup_driver(username, headless=False)  
            
            if not self.driver:
                return False
            
            logger.info(f"Logging in with credentials: {username}")
            
         
            self.driver.get("https://www.roblox.com/login")
            time.sleep(3)
          
            try:
                username_field = self.wait.until(
                    EC.presence_of_element_located((By.ID, "login-username"))
                )
                username_field.clear()
                username_field.send_keys(username)
                time.sleep(0.5)
            except TimeoutException:
                logger.error("Username field not found")
                return False
            
          
            try:
                password_field = self.driver.find_element(By.ID, "login-password")
                password_field.clear()
                password_field.send_keys(password)
                time.sleep(0.5)
            except NoSuchElementException:
                logger.error("Password field not found")
                return False
            
            try:
                login_button = self.driver.find_element(By.ID, "login-button")
                login_button.click()
                time.sleep(5)
            except NoSuchElementException:
                logger.error("Login button not found")
                return False
            
            max_wait = 30
            elapsed = 0
            
            while elapsed < max_wait:
                current_url = self.driver.current_url.lower()
                
                if "two-step" in current_url or "2sv" in current_url:
                    logger.error("Account has 2FA enabled - not supported")
                    return False
                

                if any(x in current_url for x in ["home", "discover"]):
                    logger.info("Login successful!")
                    return True
                
                time.sleep(2)
                elapsed += 2
 
            current_url = self.driver.current_url.lower()
            if "login" in current_url:
                logger.error("Login failed - check credentials")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Credential login failed: {e}")
            return False
    
    def get_current_cookie(self):
     
        try:
            if not self.driver:
                return None
            
            cookies = self.driver.get_cookies()
            for cookie in cookies:
                if cookie['name'] == '.ROBLOSECURITY':
                    logger.info("Cookie extracted from session")
                    return cookie['value']
            
            logger.warning("No .ROBLOSECURITY cookie found")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cookie: {e}")
            return None
    
    def logout(self):
       
        try:
            if self.driver:
                self.driver.get("https://www.roblox.com/logout")
                time.sleep(2)
                logger.info("Logged out")
        except Exception as e:
            logger.error(f"Logout failed: {e}")
    
    def delete_session(self, username):
       
        profile_path = self.get_profile_path(username)
        
        try:
            if os.path.exists(profile_path):
                shutil.rmtree(profile_path)
                logger.info(f"Session deleted for: {username}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
        
        return False
    
    def close(self):
       
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
                logger.info("Driver closed")
        except Exception as e:
            logger.error(f"Error closing driver: {e}")
    
    def __del__(self):
       
        self.close()



if __name__ == "__main__":
    print("\n" + "="*70)
    print("              ROBLOX LOGIN MODULE TEST")
    print("="*70 + "\n")
    
    if not SELENIUM_AVAILABLE:
        print("❌ Selenium not installed!")
        print("Run: pip install selenium webdriver-manager")
        sys.exit(1)
    

    username = input("Enter Roblox username: ").strip()
    
    login_mgr = RobloxLogin()
    
    try:
   
        print("\n⚙️  Setting up browser...")
        if not login_mgr.setup_driver(username, headless=False):
            print("❌ Failed to setup browser")
            sys.exit(1)
     
        print("🔍 Checking for existing session...")
        if login_mgr.is_logged_in():
            print("✅ Already logged in!")
        else:
            print("🔐 Not logged in")
            
            choice = input("\nLogin method:\n1. Cookie\n2. Password\nChoice: ").strip()
            
            if choice == "1":
                cookie = input("Enter .ROBLOSECURITY cookie: ").strip()
                if login_mgr.login_with_cookie(username, cookie):
                    print("✅ Cookie login successful!")
                else:
                    print("❌ Cookie login failed")
            
            elif choice == "2":
                import getpass
                password = getpass.getpass("Enter password: ")
                if login_mgr.login_with_credentials(username, password):
                    print("✅ Password login successful!")
                    
               
                    cookie = login_mgr.get_current_cookie()
                    if cookie:
                        print(f"\n🔑 Cookie extracted (save this!):\n{cookie[:50]}...")
                else:
                    print("❌ Password login failed")
        
        input("\nPress Enter to close...")
        
    finally:
        login_mgr.close()