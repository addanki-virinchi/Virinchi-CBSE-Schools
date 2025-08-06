#!/usr/bin/env python3
"""
School Scraper Phase 1 - Basic Data Extraction
Clean implementation for extracting basic school data with pagination support.
Processes ALL districts in a state before moving to Phase 2.
"""

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import logging
from datetime import datetime
import os
import undetected_chromedriver as uc

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SchoolScraperPhase1:
    def __init__(self):
        self.driver = None
        self.current_state = None
        self.current_district = None
        self.all_schools_data = []
        
    def setup_driver(self):
        """Initialize Chrome browser driver with ultra-fast settings"""
        try:
            options = uc.ChromeOptions()
            # Performance optimizations
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-images")  # Speed optimization
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-javascript")  # Speed optimization
            options.add_argument("--disable-css")  # Speed optimization
            
            # Initialize driver
            self.driver = uc.Chrome(options=options)
            self.driver.set_page_load_timeout(30)
            logger.info("✅ Chrome driver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup driver: {e}")
            return False
    
    def navigate_to_portal(self, max_retries=3):
        """Navigate to UDISE Plus portal with retry mechanism"""
        for attempt in range(max_retries):
            try:
                logger.info(f"🌐 Navigating to portal (attempt {attempt + 1}/{max_retries})")
                self.driver.get("https://udiseplus.gov.in/#/en/home")
                time.sleep(3)
                
                # Click Visit Portal
                visit_portal_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Visit Portal')]"))
                )
                visit_portal_btn.click()
                time.sleep(3)
                
                # Switch to new tab if opened
                if len(self.driver.window_handles) > 1:
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    time.sleep(2)
                
                # Click Advance Search
                advance_search_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[@id='advanceSearch']"))
                )
                advance_search_btn.click()
                
                # Wait for page to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "select.form-select.select"))
                )
                
                logger.info("✅ Successfully navigated to portal")
                return True
                
            except Exception as e:
                logger.error(f"❌ Navigation failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(15)
                    try:
                        self.driver.refresh()
                        time.sleep(5)
                    except:
                        pass
                        
        return False
    
    def extract_states_data(self):
        """Extract all available states from dropdown"""
        try:
            state_select_element = self.driver.find_element(By.CSS_SELECTOR, "select.form-select.select")
            state_select = Select(state_select_element)
            
            states = []
            for option in state_select.options[1:]:  # Skip first option (placeholder)
                try:
                    state_data = json.loads(option.get_attribute('value'))
                    states.append(state_data)
                except:
                    continue
                    
            logger.info(f"✅ Extracted {len(states)} states")
            return states
            
        except Exception as e:
            logger.error(f"❌ Failed to extract states: {e}")
            return []
    
    def select_state(self, state_data):
        """Select a specific state from dropdown"""
        try:
            self.current_state = state_data
            logger.info(f"🔄 Selecting state: {state_data['stateName']}")
            
            state_select_element = self.driver.find_element(By.CSS_SELECTOR, "select.form-select.select")
            state_select = Select(state_select_element)
            
            # Try exact JSON match
            try:
                state_value = json.dumps(state_data, separators=(',', ':'))
                state_select.select_by_value(state_value)
                logger.info(f"✅ Selected state: {state_data['stateName']}")
                time.sleep(2)  # Wait for districts to load
                return True
            except Exception as e:
                logger.error(f"❌ Failed to select state: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error in select_state: {e}")
            return False
    
    def extract_districts_data(self):
        """Extract all districts for the selected state"""
        try:
            time.sleep(2)  # Wait for districts to populate
            
            select_elements = self.driver.find_elements(By.CSS_SELECTOR, "select.form-select.select")
            if len(select_elements) < 2:
                raise Exception("District dropdown not found")
                
            district_select = Select(select_elements[1])
            
            districts = []
            for option in district_select.options[1:]:  # Skip placeholder
                try:
                    district_data = json.loads(option.get_attribute('value'))
                    districts.append(district_data)
                except:
                    continue
                    
            logger.info(f"✅ Found {len(districts)} districts")
            return districts
            
        except Exception as e:
            logger.error(f"❌ Failed to extract districts: {e}")
            return []
    
    def select_district(self, district_data):
        """Select a specific district from dropdown"""
        try:
            self.current_district = district_data
            logger.info(f"🔄 Selecting district: {district_data['districtName']}")
            
            time.sleep(1)  # Wait for dropdown
            select_elements = self.driver.find_elements(By.CSS_SELECTOR, "select.form-select.select")
            
            if len(select_elements) < 2:
                raise Exception("District dropdown not found")
                
            district_select = Select(select_elements[1])
            
            # Try exact JSON match
            try:
                district_value = json.dumps(district_data, separators=(',', ':'))
                district_select.select_by_value(district_value)
                logger.info(f"✅ Selected district: {district_data['districtName']}")
                time.sleep(1)
                return True
            except Exception as e:
                logger.error(f"❌ Failed to select district: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error in select_district: {e}")
            return False
    
    def reset_search_filters(self):
        """Reset all search filters to ensure we get all schools"""
        try:
            # Reset Category dropdown
            try:
                category_selects = self.driver.find_elements(By.CSS_SELECTOR, "select")
                for select_elem in category_selects:
                    select_obj = Select(select_elem)
                    if len(select_obj.options) > 0 and "Category" in select_obj.options[0].text:
                        select_obj.select_by_index(0)  # Select first option (usually "All")
                        break
            except:
                pass
                
            # Reset Management dropdown
            try:
                management_selects = self.driver.find_elements(By.CSS_SELECTOR, "select")
                for select_elem in management_selects:
                    select_obj = Select(select_elem)
                    if len(select_obj.options) > 0 and "Management" in select_obj.options[0].text:
                        select_obj.select_by_index(0)  # Select first option (usually "All")
                        break
            except:
                pass
                
            logger.debug("✅ Reset search filters")
            
        except Exception as e:
            logger.debug(f"Filter reset failed: {e}")
    
    def click_search_button(self):
        """Click search button with multiple selector attempts"""
        try:
            search_selectors = [
                "button.purpleBtn",
                "//button[contains(text(),'Search')]",
                "//button[contains(@class,'purpleBtn')]",
                "button[class*='purpleBtn']"
            ]
            
            for selector in search_selectors:
                try:
                    if selector.startswith("//"):
                        button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    # Scroll to button and click
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
                    time.sleep(0.5)
                    button.click()
                    
                    logger.info(f"✅ Clicked search button using: {selector}")
                    time.sleep(2)  # Wait for results
                    return True
                    
                except:
                    continue
                    
            logger.error("❌ Failed to find/click search button")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error clicking search button: {e}")
            return False

    def extract_schools_from_current_page(self):
        """Extract schools data from current page"""
        try:
            # Try multiple selectors to find school elements
            selectors_to_try = [
                ".accordion-body",
                ".accordion-item",
                "[class*='accordion']",
                ".card-body",
                ".result-item",
                "table tbody tr"
            ]

            school_elements = []
            working_selector = None

            for selector in selectors_to_try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    school_elements = elements
                    working_selector = selector
                    break

            if not school_elements:
                logger.warning("No school elements found on page")
                return []

            # Extract data from each school element
            schools_data = []
            for school_element in school_elements:
                school_data = self.extract_single_school_data(school_element)
                if school_data:
                    schools_data.append(school_data)

            logger.info(f"Extracted {len(schools_data)} schools from page using: {working_selector}")
            return schools_data

        except Exception as e:
            logger.error(f"Error extracting schools from page: {e}")
            return []

    def extract_single_school_data(self, school_element):
        """Extract data from a single school element"""
        try:
            school_data = {
                'state_name': self.current_state['stateName'] if self.current_state else 'N/A',
                'district_name': self.current_district['districtName'] if self.current_district else 'N/A',
                'school_name': 'N/A',
                'udise_code': 'N/A',
                'location': 'N/A',
                'school_category': 'N/A',
                'school_type': 'N/A',
                'know_more_link': 'N/A'
            }

            # Extract school name
            try:
                name_selectors = ["h5", ".school-name", "strong", ".title"]
                for selector in name_selectors:
                    name_elem = school_element.find_element(By.CSS_SELECTOR, selector)
                    if name_elem and name_elem.text.strip():
                        school_data['school_name'] = name_elem.text.strip()
                        break
            except:
                pass

            # Extract UDISE code
            try:
                text_content = school_element.text
                import re
                udise_match = re.search(r'UDISE[:\s]*(\d+)', text_content, re.IGNORECASE)
                if udise_match:
                    school_data['udise_code'] = udise_match.group(1)
            except:
                pass

            # Extract location
            try:
                location_selectors = [".location", ".address", "p"]
                for selector in location_selectors:
                    location_elem = school_element.find_element(By.CSS_SELECTOR, selector)
                    if location_elem and location_elem.text.strip():
                        school_data['location'] = location_elem.text.strip()
                        break
            except:
                pass

            # Extract Know More link
            try:
                link_elem = school_element.find_element(By.CSS_SELECTOR, "a[href*='schooldetail']")
                if link_elem:
                    school_data['know_more_link'] = link_elem.get_attribute('href')
            except:
                pass

            return school_data

        except Exception as e:
            logger.debug(f"Error extracting single school data: {e}")
            return None

    def click_next_page(self):
        """Click next page button if available and not disabled"""
        try:
            # Find next button
            next_buttons = self.driver.find_elements(By.CSS_SELECTOR, "a.nextBtn")

            if not next_buttons:
                return False

            next_button = next_buttons[0]

            # Check if button is displayed
            if not next_button.is_displayed():
                return False

            # Check if parent <li> has disabled class
            try:
                parent_li = next_button.find_element(By.XPATH, "..")
                parent_classes = parent_li.get_attribute("class") or ""
                if "disabled" in parent_classes.lower():
                    logger.info("📄 Next button disabled - no more pages")
                    return False
            except:
                pass

            # Check if button itself has disabled class
            button_classes = next_button.get_attribute("class") or ""
            if "disabled" in button_classes.lower():
                logger.info("📄 Next button disabled - no more pages")
                return False

            # Check for disabled attribute
            if next_button.get_attribute("disabled"):
                logger.info("📄 Next button has disabled attribute - no more pages")
                return False

            # Check if button is enabled
            if not next_button.is_enabled():
                logger.info("📄 Next button not enabled - no more pages")
                return False

            # Click the button
            try:
                next_button.click()
                logger.info("✅ Clicked next page")
                return True
            except Exception as click_error:
                logger.warning(f"Failed to click next button: {click_error}")
                return False

        except Exception as e:
            logger.debug(f"Error in click_next_page: {e}")
            return False

    def extract_schools_with_pagination(self):
        """Extract schools data with pagination support"""
        try:
            all_schools = []
            page_number = 1
            max_pages = 100  # Safety limit

            while page_number <= max_pages:
                logger.info(f"📄 Processing page {page_number}")

                # Wait for page to load
                if page_number > 1:
                    time.sleep(0.2)

                # Extract schools from current page
                page_schools = self.extract_schools_from_current_page()
                all_schools.extend(page_schools)
                logger.info(f"   ✅ Extracted {len(page_schools)} schools from page {page_number}")
                logger.info(f"   📊 Total schools so far: {len(all_schools)}")

                # Try to go to next page
                if not self.click_next_page():
                    logger.info(f"📄 No more pages after page {page_number}")
                    break

                page_number += 1
                time.sleep(0.3)  # Wait for next page to load

            if page_number > max_pages:
                logger.warning(f"⚠️ Reached maximum page limit ({max_pages})")

            logger.info(f"Total schools extracted: {len(all_schools)}")
            return all_schools

        except Exception as e:
            logger.error(f"Failed to extract schools with pagination: {e}")
            return []

    def save_state_data_to_csv(self, state_name):
        """Save all schools data for a state to CSV file"""
        try:
            if not self.all_schools_data:
                logger.warning(f"No data to save for {state_name}")
                return None

            # Create DataFrame
            df = pd.DataFrame(self.all_schools_data)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_state_name = state_name.replace(' ', '_').replace('&', 'AND')
            filename = f"{clean_state_name}_phase1_complete_{timestamp}.csv"

            # Save to CSV
            df.to_csv(filename, index=False)

            # Count schools with links for Phase 2
            schools_with_links = df[
                (df['know_more_link'].notna()) &
                (df['know_more_link'] != 'N/A') &
                (df['know_more_link'].str.contains('schooldetail', na=False))
            ]

            logger.info(f"✅ Saved {len(df)} schools to {filename}")
            logger.info(f"   📊 {len(schools_with_links)} schools ready for Phase 2")

            return filename

        except Exception as e:
            logger.error(f"❌ Failed to save CSV: {e}")
            return None

    def process_single_state(self, state_name):
        """Process a single state completely"""
        try:
            logger.info(f"\n{'='*80}")
            logger.info(f"🏛️ PROCESSING STATE: {state_name}")
            logger.info(f"{'='*80}")

            # Setup driver and navigate
            if not self.setup_driver():
                return False

            if not self.navigate_to_portal():
                return False

            # Extract states and find target state
            states = self.extract_states_data()
            target_state = None
            for state in states:
                if state['stateName'] == state_name:
                    target_state = state
                    break

            if not target_state:
                logger.error(f"❌ State '{state_name}' not found")
                return False

            # Select state
            if not self.select_state(target_state):
                return False

            # Get districts
            districts = self.extract_districts_data()
            if not districts:
                logger.error(f"❌ No districts found for {state_name}")
                return False

            logger.info(f"📍 Found {len(districts)} districts to process")

            # Process each district
            self.all_schools_data = []  # Reset data for this state

            for district_index, district in enumerate(districts, 1):
                district_name = district['districtName']
                logger.info(f"\n🏘️ Processing district {district_index}/{len(districts)}: {district_name}")

                try:
                    # Select district
                    if self.select_district(district):
                        # Reset filters to get all schools
                        self.reset_search_filters()

                        # Click search with retry
                        search_success = False
                        for attempt in range(3):
                            if self.click_search_button():
                                search_success = True
                                break
                            else:
                                logger.warning(f"Search failed (attempt {attempt + 1}/3)")
                                if attempt < 2:
                                    time.sleep(2)

                        if search_success:
                            # Extract schools with pagination
                            district_schools = self.extract_schools_with_pagination()
                            self.all_schools_data.extend(district_schools)

                            logger.info(f"✅ Completed {district_name}: {len(district_schools)} schools")
                        else:
                            logger.error(f"❌ Failed to search in {district_name}")
                    else:
                        logger.error(f"❌ Failed to select district: {district_name}")

                except Exception as e:
                    logger.error(f"❌ Error processing district {district_name}: {e}")
                    continue

            # Save all data for this state
            csv_filename = self.save_state_data_to_csv(state_name)

            # Cleanup
            self.driver.quit()

            if csv_filename:
                logger.info(f"\n🎉 STATE PROCESSING COMPLETE: {state_name}")
                logger.info(f"📁 Data saved to: {csv_filename}")
                logger.info(f"📊 Total schools extracted: {len(self.all_schools_data)}")
                return csv_filename
            else:
                return False

        except Exception as e:
            logger.error(f"❌ Error processing state {state_name}: {e}")
            try:
                self.driver.quit()
            except:
                pass
            return False

if __name__ == "__main__":
    scraper = SchoolScraperPhase1()

    print("🚀 SCHOOL SCRAPER PHASE 1 - BASIC DATA EXTRACTION")
    print("Extracts basic school data with pagination for entire states")
    print()

    state_name = input("Enter state name to process: ").strip()

    if state_name:
        result = scraper.process_single_state(state_name)
        if result:
            print(f"\n✅ SUCCESS! Phase 1 complete for {state_name}")
            print(f"📁 CSV file created: {result}")
            print(f"\n🔄 Ready for Phase 2 processing!")
        else:
            print(f"\n❌ FAILED to process {state_name}")
    else:
        print("❌ No state name provided")
