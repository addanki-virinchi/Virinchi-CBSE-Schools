#!/usr/bin/env python3
"""
Test Next Button - Quick test of the specific next button clicking
"""

import undetected_chromedriver as uc
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_next_button():
    """Test the specific next button clicking functionality"""
    driver = None
    try:
        print("🚀 TESTING NEXT BUTTON FUNCTIONALITY")
        print("="*50)

        # Setup Chrome
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        
        driver = uc.Chrome(options=options, version_main=138)
        driver.maximize_window()
        driver.implicitly_wait(3)
        
        # Navigate through portal (abbreviated)
        print("1. Navigating to portal...")
        driver.get("https://udiseplus.gov.in/#/en/home")
        time.sleep(2)
        
        # Visit Portal
        visit_portal_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Visit Portal')]"))
        )
        visit_portal_btn.click()
        time.sleep(2)
        
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(1)
        
        # Advance Search
        advance_search_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='advanceSearch']"))
        )
        advance_search_btn.click()
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "select.form-select.select"))
        )
        
        # Quick state/district selection
        print("2. Selecting state and district...")
        state_select = driver.find_element(By.CSS_SELECTOR, "select.form-select.select")
        state_options = state_select.find_elements(By.TAG_NAME, "option")[1:]
        
        # Select first state
        first_state_value = state_options[0].get_attribute("value")
        state_select_obj = Select(state_select)
        state_select_obj.select_by_value(first_state_value)
        time.sleep(1)
        
        # Select first district
        select_elements = driver.find_elements(By.CSS_SELECTOR, "select.form-select.select")
        district_select = select_elements[1]
        district_options = district_select.find_elements(By.TAG_NAME, "option")[1:]
        
        first_district_value = district_options[0].get_attribute("value")
        district_select_obj = Select(district_select)
        district_select_obj.select_by_value(first_district_value)
        time.sleep(1)
        
        # Search
        search_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Search')]"))
        )
        search_button.click()
        time.sleep(3)
        
        print("3. Testing next button detection and clicking...")
        
        # Test different selectors
        selectors_to_test = [
            ".nextBtn",
            "a.nextBtn", 
            "li a.nextBtn",
            "[class*='nextBtn']"
        ]
        
        for selector in selectors_to_test:
            try:
                buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"   Selector '{selector}': Found {len(buttons)} elements")
                
                if buttons:
                    button = buttons[0]
                    print(f"      - Enabled: {button.is_enabled()}")
                    print(f"      - Displayed: {button.is_displayed()}")
                    print(f"      - Text: '{button.text.strip()}'")
                    print(f"      - Tag: {button.tag_name}")
                    print(f"      - Classes: {button.get_attribute('class')}")
                    
                    # Get the HTML structure
                    html = button.get_attribute('outerHTML')
                    print(f"      - HTML: {html[:100]}...")
                    
            except Exception as e:
                print(f"   Selector '{selector}': Error - {e}")
        
        # Test actual clicking
        print("\n4. Testing actual next button clicking...")
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, "a.nextBtn")
            
            if next_button.is_enabled() and next_button.is_displayed():
                print("   ✅ Next button found and clickable")
                
                # Test regular click
                print("   Testing regular click...")
                start_time = time.time()
                next_button.click()
                click_time = time.time() - start_time
                print(f"   ✅ Regular click completed in {click_time:.3f}s")
                
                time.sleep(2)
                
                # Check if page changed
                new_elements = driver.find_elements(By.CSS_SELECTOR, ".accordion-body")
                print(f"   📄 Found {len(new_elements)} elements after click")
                
                # Test JavaScript click on next page (if available)
                try:
                    next_button2 = driver.find_element(By.CSS_SELECTOR, "a.nextBtn")
                    if next_button2.is_enabled() and next_button2.is_displayed():
                        print("   Testing JavaScript click...")
                        start_time = time.time()
                        driver.execute_script("arguments[0].click();", next_button2)
                        js_click_time = time.time() - start_time
                        print(f"   ✅ JavaScript click completed in {js_click_time:.3f}s")
                        
                        time.sleep(2)
                        new_elements2 = driver.find_elements(By.CSS_SELECTOR, ".accordion-body")
                        print(f"   📄 Found {len(new_elements2)} elements after JS click")
                        
                        # Performance comparison
                        print(f"\n   ⏱️ PERFORMANCE COMPARISON:")
                        print(f"      Regular click: {click_time:.3f}s")
                        print(f"      JavaScript click: {js_click_time:.3f}s")
                        
                        if js_click_time < click_time:
                            print(f"      ✅ JavaScript click is {((click_time - js_click_time) / click_time * 100):.1f}% faster")
                        else:
                            print(f"      ✅ Regular click is {((js_click_time - click_time) / js_click_time * 100):.1f}% faster")
                            
                except NoSuchElementException:
                    print("   📄 No more pages available for JS click test")
                    
            else:
                print("   📄 Next button not clickable - may be last page")
                
        except NoSuchElementException:
            print("   📄 Next button not found - may be last page")
        except Exception as e:
            print(f"   ❌ Error testing next button: {e}")
        
        print("\n" + "="*50)
        print("🎉 NEXT BUTTON TEST COMPLETED!")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        
    finally:
        if driver:
            input("\nPress Enter to close browser...")
            driver.quit()

if __name__ == "__main__":
    test_next_button()
