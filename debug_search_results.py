#!/usr/bin/env python3
"""
Debug Search Results - Test what happens after clicking search button
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

def debug_search_results():
    """Debug the search results page structure"""
    driver = None
    try:
        print("🚀 DEBUGGING SEARCH RESULTS")
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
        driver.set_page_load_timeout(15)
        
        # Navigate to portal
        print("\n1. Navigating to UDISE Plus portal...")
        driver.get("https://udiseplus.gov.in/#/en/home")
        time.sleep(2)
        
        # Click Visit Portal
        print("2. Clicking Visit Portal...")
        visit_portal_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Visit Portal')]"))
        )
        visit_portal_btn.click()
        time.sleep(2)
        
        # Switch to new tab
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            print("   ✅ Switched to new tab")
            time.sleep(1)
        
        # Click Advance Search
        print("3. Clicking Advance Search...")
        advance_search_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='advanceSearch']"))
        )
        advance_search_btn.click()
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "select.form-select.select"))
        )
        print("   ✅ Advance search page loaded")
        
        # Select first state
        print("4. Selecting first state...")
        state_select = driver.find_element(By.CSS_SELECTOR, "select.form-select.select")
        state_options = state_select.find_elements(By.TAG_NAME, "option")[1:]  # Skip first
        
        if state_options:
            first_state_value = state_options[0].get_attribute("value")
            first_state_data = json.loads(first_state_value)
            print(f"   Selected state: {first_state_data['stateName']}")
            
            state_select_obj = Select(state_select)
            state_select_obj.select_by_value(first_state_value)
            time.sleep(2)
            
            # Select first district
            print("5. Selecting first district...")
            select_elements = driver.find_elements(By.CSS_SELECTOR, "select.form-select.select")
            if len(select_elements) >= 2:
                district_select = select_elements[1]
                district_options = district_select.find_elements(By.TAG_NAME, "option")[1:]  # Skip first
                
                if district_options:
                    first_district_value = district_options[0].get_attribute("value")
                    first_district_data = json.loads(first_district_value)
                    print(f"   Selected district: {first_district_data['districtName']}")
                    
                    district_select_obj = Select(district_select)
                    district_select_obj.select_by_value(first_district_value)
                    time.sleep(1)
                    
                    # Click search
                    print("6. Clicking search button...")
                    search_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Search')]"))
                    )
                    search_button.click()
                    print("   ✅ Search button clicked")
                    
                    # Wait for results
                    print("7. Waiting for results to load...")
                    time.sleep(5)
                    
                    # Debug page structure
                    print("\n8. DEBUGGING PAGE STRUCTURE:")
                    print("="*50)
                    
                    # Check for different possible containers
                    containers_to_check = [
                        ".accordion-item",
                        ".accordion-body", 
                        ".accordion",
                        "[class*='accordion']",
                        ".card",
                        ".school-item",
                        "table tbody tr",
                        ".result-item",
                        ".list-group-item"
                    ]
                    
                    for container in containers_to_check:
                        try:
                            elements = driver.find_elements(By.CSS_SELECTOR, container)
                            print(f"   {container}: {len(elements)} elements found")
                            
                            if elements and len(elements) > 0:
                                print(f"      First element HTML preview:")
                                first_element_html = elements[0].get_attribute('outerHTML')[:200]
                                print(f"      {first_element_html}...")
                                
                        except Exception as e:
                            print(f"   {container}: Error - {e}")
                    
                    # Check for pagination
                    print("\n9. CHECKING PAGINATION:")
                    print("="*30)
                    
                    pagination_selectors = [
                        ".nextBtn",
                        ".next",
                        "[class*='next']",
                        ".pagination .next",
                        "button[aria-label*='next']",
                        "a[aria-label*='next']"
                    ]
                    
                    for selector in pagination_selectors:
                        try:
                            elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            print(f"   {selector}: {len(elements)} elements found")
                            
                            if elements:
                                for i, elem in enumerate(elements):
                                    is_enabled = elem.is_enabled()
                                    is_displayed = elem.is_displayed()
                                    text = elem.text.strip()
                                    print(f"      Element {i}: enabled={is_enabled}, displayed={is_displayed}, text='{text}'")
                                    
                        except Exception as e:
                            print(f"   {selector}: Error - {e}")
                    
                    # Check page source for clues
                    print("\n10. PAGE SOURCE ANALYSIS:")
                    print("="*30)
                    page_source = driver.page_source
                    
                    keywords_to_check = [
                        "accordion",
                        "school",
                        "udise",
                        "next",
                        "pagination",
                        "result",
                        "No records found",
                        "No data available"
                    ]
                    
                    for keyword in keywords_to_check:
                        count = page_source.lower().count(keyword.lower())
                        print(f"   '{keyword}': appears {count} times in page source")
                    
                    print(f"\n   Page title: {driver.title}")
                    print(f"   Current URL: {driver.current_url}")
                    
                    # Save page source for manual inspection
                    with open("debug_page_source.html", "w", encoding="utf-8") as f:
                        f.write(page_source)
                    print("   ✅ Page source saved to debug_page_source.html")
                    
        print("\n" + "="*50)
        print("🎉 DEBUG COMPLETED!")
        print("Check the output above and debug_page_source.html for clues")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Debug failed: {e}")
        
    finally:
        if driver:
            input("\nPress Enter to close browser...")
            driver.quit()

if __name__ == "__main__":
    debug_search_results()
