#!/usr/bin/env python3
"""
Test Pagination Performance - Quick test of pagination functionality
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

def test_pagination_performance():
    """Test pagination performance with a state that has multiple pages"""
    driver = None
    try:
        print("🚀 TESTING PAGINATION PERFORMANCE")
        print("="*50)

        # Setup Chrome with performance optimizations
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-images")
        
        driver = uc.Chrome(options=options, version_main=138)
        driver.maximize_window()
        driver.implicitly_wait(3)
        driver.set_page_load_timeout(15)
        
        # Navigate to portal
        print("\n1. Navigating to portal...")
        driver.get("https://udiseplus.gov.in/#/en/home")
        time.sleep(2)
        
        # Click Visit Portal
        visit_portal_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Visit Portal')]"))
        )
        visit_portal_btn.click()
        time.sleep(2)
        
        # Switch to new tab
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(1)
        
        # Click Advance Search
        advance_search_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@id='advanceSearch']"))
        )
        advance_search_btn.click()
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "select.form-select.select"))
        )
        print("   ✅ Portal navigation completed")
        
        # Select a state with many schools (e.g., UTTAR PRADESH)
        print("\n2. Selecting state with many schools...")
        state_select = driver.find_element(By.CSS_SELECTOR, "select.form-select.select")
        state_options = state_select.find_elements(By.TAG_NAME, "option")[1:]
        
        # Find UTTAR PRADESH or another large state
        target_state = None
        for option in state_options:
            state_value = option.get_attribute("value")
            state_data = json.loads(state_value)
            if state_data['stateName'] in ['UTTAR PRADESH', 'MAHARASHTRA', 'BIHAR', 'WEST BENGAL']:
                target_state = state_data
                print(f"   Selected state: {state_data['stateName']}")
                state_select_obj = Select(state_select)
                state_select_obj.select_by_value(state_value)
                time.sleep(1)
                break
        
        if not target_state:
            print("   Using first available state")
            first_state_value = state_options[0].get_attribute("value")
            target_state = json.loads(first_state_value)
            state_select_obj = Select(state_select)
            state_select_obj.select_by_value(first_state_value)
            time.sleep(1)
        
        # Select first district
        print("\n3. Selecting first district...")
        select_elements = driver.find_elements(By.CSS_SELECTOR, "select.form-select.select")
        if len(select_elements) >= 2:
            district_select = select_elements[1]
            district_options = district_select.find_elements(By.TAG_NAME, "option")[1:]
            
            if district_options:
                first_district_value = district_options[0].get_attribute("value")
                first_district_data = json.loads(first_district_value)
                print(f"   Selected district: {first_district_data['districtName']}")
                
                district_select_obj = Select(district_select)
                district_select_obj.select_by_value(first_district_value)
                time.sleep(1)
                
                # Click search
                print("\n4. Clicking search and testing pagination...")
                search_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Search')]"))
                )
                search_button.click()
                time.sleep(3)
                
                # Test pagination performance
                print("\n5. TESTING PAGINATION PERFORMANCE:")
                print("="*40)
                
                page_number = 1
                total_schools = 0
                pagination_times = []
                
                while page_number <= 3:  # Test first 3 pages max
                    start_time = time.time()
                    
                    print(f"\n   📄 Processing page {page_number}...")
                    
                    # Count schools on current page
                    school_elements = driver.find_elements(By.CSS_SELECTOR, ".accordion-body")
                    page_schools = len(school_elements)
                    total_schools += page_schools
                    print(f"      Found {page_schools} schools on page {page_number}")
                    
                    # Try to click next page
                    try:
                        next_button = driver.find_element(By.CSS_SELECTOR, ".nextBtn")
                        
                        if next_button.is_enabled() and next_button.is_displayed():
                            click_start = time.time()
                            next_button.click()
                            click_time = time.time() - click_start
                            
                            print(f"      ✅ Clicked next button in {click_time:.2f}s")
                            
                            # Wait for next page
                            time.sleep(1.5)
                            
                            page_time = time.time() - start_time
                            pagination_times.append(page_time)
                            print(f"      ⏱️ Total page processing time: {page_time:.2f}s")
                            
                            page_number += 1
                        else:
                            print(f"      📄 Next button disabled - reached last page")
                            break
                            
                    except NoSuchElementException:
                        print(f"      📄 Next button not found - reached last page")
                        break
                    except Exception as e:
                        print(f"      ❌ Pagination error: {e}")
                        break
                
                # Performance summary
                print(f"\n6. PAGINATION PERFORMANCE SUMMARY:")
                print("="*40)
                print(f"   📊 Total pages processed: {page_number}")
                print(f"   🏫 Total schools found: {total_schools}")
                
                if pagination_times:
                    avg_time = sum(pagination_times) / len(pagination_times)
                    max_time = max(pagination_times)
                    min_time = min(pagination_times)
                    
                    print(f"   ⏱️ Average page time: {avg_time:.2f}s")
                    print(f"   ⏱️ Fastest page: {min_time:.2f}s")
                    print(f"   ⏱️ Slowest page: {max_time:.2f}s")
                    
                    if avg_time < 3.0:
                        print(f"   ✅ EXCELLENT: Pagination is fast (< 3s per page)")
                    elif avg_time < 5.0:
                        print(f"   ✅ GOOD: Pagination is acceptable (< 5s per page)")
                    else:
                        print(f"   ⚠️ SLOW: Pagination needs optimization (> 5s per page)")
                
        print("\n" + "="*50)
        print("🎉 PAGINATION PERFORMANCE TEST COMPLETED!")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        
    finally:
        if driver:
            input("\nPress Enter to close browser...")
            driver.quit()

if __name__ == "__main__":
    test_pagination_performance()
