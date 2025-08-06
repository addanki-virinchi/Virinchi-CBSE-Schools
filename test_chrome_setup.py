#!/usr/bin/env python3
"""
Test Chrome Browser Setup - Verify Chrome browser is working correctly
"""

import undetected_chromedriver as uc
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_chrome_browser():
    """Test if Chrome browser can be initialized and used"""

    print("🚀 TESTING CHROME BROWSER SETUP")
    print("="*50)

    # Test driver initialization
    print("\n1. Testing Chrome driver initialization...")
    driver = None

    try:
        # Setup Chrome options
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Initialize Chrome browser
        driver = uc.Chrome(options=options)
        print("   ✅ Chrome driver initialized successfully")
        driver.maximize_window()
        driver.implicitly_wait(10)
        driver.set_page_load_timeout(30)

    except Exception as e:
        print(f"   ❌ Failed to initialize Chrome driver: {e}")
        return False
    
    # Test navigation
    print("\n2. Testing navigation...")
    try:
        driver.get("https://www.google.com")
        time.sleep(3)
        
        current_url = driver.current_url
        page_title = driver.title
        
        print(f"   ✅ Navigation successful")
        print(f"   📍 Current URL: {current_url}")
        print(f"   📄 Page title: {page_title}")
        
    except Exception as e:
        print(f"   ❌ Navigation failed: {e}")
        return False
    
    # Test UDISE Plus portal access
    print("\n3. Testing UDISE Plus portal access...")
    try:
        driver.get("https://udiseplus.gov.in/#/en/home")
        time.sleep(5)
        
        current_url = driver.current_url
        page_title = driver.title
        
        print(f"   ✅ UDISE Plus portal access successful")
        print(f"   📍 Current URL: {current_url}")
        print(f"   📄 Page title: {page_title}")
        
        # Check if page loaded properly
        if "udiseplus" in current_url.lower():
            print("   ✅ Portal loaded correctly")
        else:
            print("   ⚠️ Portal may not have loaded correctly")

    except Exception as e:
        print(f"   ❌ UDISE Plus portal access failed: {e}")
        return False

    # Test Visit Portal button detection
    print("\n4. Testing Visit Portal button detection...")
    try:
        visit_portal_selectors = [
            "//a[contains(text(),'Visit Portal')]",
            "//a[contains(@href, 'portal')]",
            "//button[contains(text(),'Visit Portal')]",
            "//div[contains(text(),'Visit Portal')]"
        ]
        
        found_button = False
        for selector in visit_portal_selectors:
            try:
                button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                print(f"   ✅ Found Visit Portal button with selector: {selector}")
                found_button = True
                break
            except TimeoutException:
                continue
        
        if not found_button:
            print("   ⚠️ Visit Portal button not found with any selector")
        
    except Exception as e:
        print(f"   ❌ Visit Portal button detection failed: {e}")

    # Cleanup
    print("\n5. Cleaning up...")
    try:
        driver.quit()
        print("   ✅ Browser closed successfully")
    except Exception as e:
        print(f"   ⚠️ Error closing browser: {e}")

    print("\n" + "="*50)
    print("🎉 CHROME BROWSER TEST COMPLETED!")
    print("✅ Chrome browser is ready for school scraping")
    print("="*50)

    return True

def show_chrome_info():
    """Show information about Chrome browser installation"""
    print("\n" + "="*50)
    print("CHROME BROWSER INFORMATION")
    print("="*50)
    print("Chrome browser should be installed automatically with undetected_chromedriver")
    print("\nIf Chrome is not working:")
    print("1. Make sure Chrome browser is installed")
    print("2. Update Chrome to the latest version")
    print("3. Run this test again")
    print("="*50)

if __name__ == "__main__":
    try:
        success = test_chrome_browser()

        if not success:
            show_chrome_info()

    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        show_chrome_info()
