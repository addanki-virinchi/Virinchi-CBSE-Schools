#!/usr/bin/env python3
"""
Phase 1 State-wise Scraper - Modified to create separate CSV files for each state
with data segregation based on know_more_links availability
"""

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
# Removed unused import for performance
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import json
import re
import undetected_chromedriver as uc
import logging
from datetime import datetime
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StatewiseSchoolScraper:
    def __init__(self):
        self.driver = None
        self.current_state = None
        self.current_district = None
        
        # State-wise data storage
        self.state_schools_with_links = {}  # Schools WITH know_more_links
        self.state_schools_no_links = {}    # Schools WITHOUT know_more_links
        
    def setup_driver(self):
        """Initialize the Chrome browser driver with optimized performance settings"""
        try:
            # Setup Chrome options for optimal performance and reliability
            options = uc.ChromeOptions()

            # Core stability options
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-blink-features=AutomationControlled")

            # Performance optimizations (balanced for speed and functionality)
            options.add_argument("--disable-images")  # Speed optimization
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-backgrounding-occluded-windows")

            # Memory and resource optimizations
            options.add_argument("--memory-pressure-off")
            options.add_argument("--max_old_space_size=4096")

            # Initialize Chrome driver
            self.driver = uc.Chrome(options=options, version_main=138)
            self.driver.maximize_window()

            # Balanced timeouts for reliability and speed
            self.driver.implicitly_wait(5)  # Balanced from 3 for stability
            self.driver.set_page_load_timeout(20)  # Balanced from 15 for stability

            logger.info("✅ Chrome browser driver initialized with optimized settings")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Chrome driver: {e}")
            logger.error("Please ensure Chrome browser is installed and updated")
            raise

    def navigate_to_portal(self, max_retries=3):
        """Navigate to the UDISE Plus portal and access advance search with retry mechanism"""
        for attempt in range(max_retries):
            try:
                logger.info(f"🌐 Navigating to UDISE Plus portal... (attempt {attempt + 1}/{max_retries})")
                self.driver.get("https://udiseplus.gov.in/#/en/home")
                time.sleep(3)  # Slightly increased for connection stability

                # Click on Visit Portal with optimized selector
                logger.info("🔍 Looking for Visit Portal button...")
                visit_portal_btn = WebDriverWait(self.driver, 10).until(  # Increased for stability
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Visit Portal')]"))
                )
                visit_portal_btn.click()
                logger.info("✅ Clicked Visit Portal button")
                time.sleep(3)  # Increased for stability

                # Switch to new tab if opened
                if len(self.driver.window_handles) > 1:
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    logger.info("🔄 Switched to new tab")
                    time.sleep(2)  # Increased for stability

                # Click on Advance Search with optimized approach
                logger.info("🔍 Looking for Advance Search button...")
                advance_search_btn = WebDriverWait(self.driver, 10).until(  # Increased for stability
                    EC.element_to_be_clickable((By.XPATH, "//a[@id='advanceSearch']"))
                )
                advance_search_btn.click()
                logger.info("✅ Clicked Advance Search button")

                # Optimized wait for page load - use explicit wait instead of sleep
                logger.info("⏳ Waiting for advance search page to load...")
                WebDriverWait(self.driver, 15).until(  # Increased for stability
                    EC.presence_of_element_located((By.CSS_SELECTOR, "select.form-select.select"))
                )
                logger.info("✅ Advance search page loaded successfully")
                return True

            except Exception as e:
                logger.error(f"❌ Failed to navigate to portal (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"⏳ Retrying navigation in 15 seconds...")
                    time.sleep(15)
                    # Refresh the page before retry
                    try:
                        self.driver.refresh()
                        time.sleep(5)
                    except:
                        pass
                else:
                    logger.error("❌ All navigation attempts failed")
                    return False

        return False

    def extract_states_data(self):
        """Extract all states data from dropdown using optimized approach"""
        try:
            logger.info("🔍 Looking for state dropdown...")

            # Wait for state dropdown to be present and populated
            state_select = WebDriverWait(self.driver, 8).until(  # Reduced from 15
                EC.presence_of_element_located((By.CSS_SELECTOR, "select.form-select.select"))
            )
            logger.info("✅ Found state dropdown")

            # Minimal wait for options to populate
            time.sleep(1)  # Reduced from 3

            # Get all state options
            state_options = state_select.find_elements(By.TAG_NAME, "option")
            logger.info(f"📋 Found {len(state_options)} total options in state dropdown")

            if len(state_options) <= 1:
                logger.error("❌ State dropdown appears to be empty or not loaded")
                return []

            # Skip the first "Select State" option
            state_options = state_options[1:]
            states = []

            for i, option in enumerate(state_options):
                try:
                    state_value = option.get_attribute("value")
                    state_text = option.text.strip()

                    if state_value and state_text:
                        try:
                            # Parse JSON state data (this is how the working version does it)
                            state_data = json.loads(state_value)
                            states.append(state_data)
                            logger.info(f"✅ Added state {i+1}: {state_data['stateName']}")
                        except json.JSONDecodeError:
                            logger.warning(f"⚠️ Failed to parse state data for '{state_text}': {state_value[:100]}...")
                            # Try to create a basic state data structure
                            states.append({
                                'stateId': state_value,
                                'stateName': state_text
                            })
                except Exception as option_error:
                    logger.warning(f"⚠️ Error processing state option: {option_error}")
                    continue

            logger.info(f"✅ Extracted {len(states)} valid states")
            return states

        except Exception as e:
            logger.error(f"❌ Failed to extract states: {e}")
            # Try to get page source for debugging
            try:
                current_url = self.driver.current_url
                page_title = self.driver.title
                logger.error(f"Current URL: {current_url}")
                logger.error(f"Page title: {page_title}")
            except:
                pass
            return []

    def select_state(self, state_data):
        """Select a specific state from the dropdown using robust method from Schools.py"""
        try:
            self.current_state = state_data
            logger.info(f"🔄 Selecting state: {state_data['stateName']}")

            state_select_element = self.driver.find_element(By.CSS_SELECTOR, "select.form-select.select")
            state_select = Select(state_select_element)

            # Try multiple methods to select the state (exact copy from working Schools.py)
            success = False

            # Method 1: Try exact JSON match
            try:
                state_value = json.dumps(state_data, separators=(',', ':'))
                state_select.select_by_value(state_value)
                success = True
                logger.info(f"✅ Selected state by exact JSON: {state_data['stateName']}")
            except:
                pass

            # Method 2: Try JSON with different formatting
            if not success:
                try:
                    state_value = json.dumps(state_data)
                    state_select.select_by_value(state_value)
                    success = True
                    logger.info(f"✅ Selected state by formatted JSON: {state_data['stateName']}")
                except:
                    pass

            # Method 3: Try selecting by visible text
            if not success:
                try:
                    state_select.select_by_visible_text(state_data['stateName'])
                    success = True
                    logger.info(f"✅ Selected state by visible text: {state_data['stateName']}")
                except:
                    pass

            # Method 4: Try finding option by state name in value
            if not success:
                try:
                    options = state_select_element.find_elements(By.TAG_NAME, "option")
                    for option in options:
                        option_value = option.get_attribute("value")
                        if option_value and state_data['stateName'] in option_value:
                            option.click()
                            success = True
                            logger.info(f"✅ Selected state by name match: {state_data['stateName']}")
                            break
                except:
                    pass

            # Method 5: Try finding option by partial text match
            if not success:
                try:
                    options = state_select_element.find_elements(By.TAG_NAME, "option")
                    for option in options:
                        option_text = option.text.strip().upper()
                        state_name = state_data['stateName'].upper()
                        if state_name in option_text or option_text in state_name:
                            option.click()
                            success = True
                            logger.info(f"✅ Selected state by partial match: {state_data['stateName']} -> {option.text}")
                            break
                except:
                    pass

            if not success:
                # Log available options for debugging
                options = state_select_element.find_elements(By.TAG_NAME, "option")
                logger.error(f"❌ Failed to select state. Available options:")
                for i, option in enumerate(options[:5]):  # Show first 5
                    logger.error(f"  Option {i}: text='{option.text}', value='{option.get_attribute('value')[:100]}...'")
                raise Exception(f"Could not select state {state_data['stateName']} using any method")

            time.sleep(1)  # Reduced wait for districts to load
            return True

        except Exception as e:
            logger.error(f"❌ Failed to select state {state_data['stateName']}: {e}")
            return False

    def extract_districts_data(self):
        """Extract districts data for the currently selected state (FIXED version)"""
        try:
            # Validate current_state
            if not self.current_state:
                logger.error("❌ current_state is None")
                return []

            if not isinstance(self.current_state, dict):
                logger.error(f"❌ current_state is not a dict: {type(self.current_state)} = {self.current_state}")
                return []

            if 'stateName' not in self.current_state:
                logger.error(f"❌ current_state missing stateName: {self.current_state}")
                return []

            logger.info(f"🔍 Extracting districts for {self.current_state['stateName']}...")

            # Optimized wait for district dropdown to be populated
            time.sleep(2)  # Reduced from 5

            # Find all select elements and get the district one (usually the second one)
            select_elements = self.driver.find_elements(By.CSS_SELECTOR, "select.form-select.select")

            if len(select_elements) < 2:
                logger.warning("❌ District dropdown not found")
                return []

            district_select = select_elements[1]  # Second select is usually districts
            district_options = district_select.find_elements(By.TAG_NAME, "option")[1:]  # Skip "Select District"

            districts_data = []
            for option in district_options:
                district_value = option.get_attribute("value")
                district_text = option.text.strip()

                if district_value and district_text:
                    # Check if it's JSON format or simple value
                    try:
                        # Try to parse as JSON first
                        district_data = json.loads(district_value)
                        # Validate that district_data is a dictionary
                        if isinstance(district_data, dict) and 'districtName' in district_data:
                            districts_data.append(district_data)
                            logger.info(f"✅ Found district (JSON): {district_data['districtName']}")
                        else:
                            logger.warning(f"⚠️ Invalid JSON district data: {district_data}")
                    except (json.JSONDecodeError, TypeError, KeyError) as e:
                        # If not JSON, create a simple district data structure
                        try:
                            district_data = {
                                'districtId': district_value,
                                'districtName': district_text,
                                'stateId': self.current_state['stateId'] if self.current_state and 'stateId' in self.current_state else 0,
                                'udiseDistrictCode': district_value
                            }
                            districts_data.append(district_data)
                            logger.info(f"✅ Found district (simple): {district_text} (ID: {district_value})")
                        except Exception as inner_e:
                            logger.error(f"❌ Failed to create district data: {inner_e}")
                            continue
                else:
                    logger.warning(f"⚠️ Empty district option: text='{district_text}', value='{district_value}'")

            logger.info(f"✅ Extracted {len(districts_data)} districts for {self.current_state['stateName']}")
            return districts_data

        except Exception as e:
            logger.error(f"❌ Failed to extract districts data: {e}")
            return []

    def select_district(self, district_data):
        """Select a specific district from the dropdown (exact copy from Schools.py)"""
        try:
            self.current_district = district_data
            logger.info(f"🔄 Selecting district: {district_data['districtName']}")

            # Minimal wait for district dropdown to populate
            time.sleep(1)  # Reduced from 3

            select_elements = self.driver.find_elements(By.CSS_SELECTOR, "select.form-select.select")

            if len(select_elements) < 2:
                raise Exception("District dropdown not found")

            district_select_element = select_elements[1]
            district_select = Select(district_select_element)

            # Try multiple methods to select the district
            success = False

            # Method 1: Try selecting by district ID (simple value)
            try:
                district_id = str(district_data['districtId'])
                district_select.select_by_value(district_id)
                success = True
                logger.info(f"✅ Selected district by ID: {district_data['districtName']} (ID: {district_id})")
            except Exception as e:
                logger.debug(f"Method 1 failed: {e}")
                pass

            # Method 2: Try exact JSON match (for backward compatibility)
            if not success:
                try:
                    district_value = json.dumps(district_data, separators=(',', ':'))
                    district_select.select_by_value(district_value)
                    success = True
                    logger.info(f"✅ Selected district by exact JSON: {district_data['districtName']}")
                except Exception as e:
                    logger.debug(f"Method 2 failed: {e}")
                    pass

            # Method 3: Try selecting by visible text
            if not success:
                try:
                    district_select.select_by_visible_text(district_data['districtName'])
                    success = True
                    logger.info(f"✅ Selected district by visible text: {district_data['districtName']}")
                except Exception as e:
                    logger.debug(f"Method 3 failed: {e}")
                    pass

            # Method 4: Try JSON with different formatting
            if not success:
                try:
                    district_value = json.dumps(district_data)
                    district_select.select_by_value(district_value)
                    success = True
                    logger.info(f"✅ Selected district by formatted JSON: {district_data['districtName']}")
                except Exception as e:
                    logger.debug(f"Method 4 failed: {e}")
                    pass

            # Method 5: Try finding option by partial text match
            if not success:
                try:
                    options = district_select_element.find_elements(By.TAG_NAME, "option")
                    for option in options:
                        option_text = option.text.strip().upper()
                        district_name = district_data['districtName'].upper()
                        if district_name in option_text or option_text in district_name:
                            option.click()
                            success = True
                            logger.info(f"✅ Selected district by partial match: {district_data['districtName']} -> {option.text}")
                            break
                except Exception as e:
                    logger.debug(f"Method 5 failed: {e}")
                    pass

            if not success:
                # Log available options for debugging
                options = district_select_element.find_elements(By.TAG_NAME, "option")
                logger.error(f"❌ Failed to select district. Available options:")
                for i, option in enumerate(options[:5]):  # Show first 5
                    logger.error(f"  Option {i}: text='{option.text}', value='{option.get_attribute('value')[:100]}...'")
                raise Exception(f"Could not select district {district_data['districtName']} using any method")

            time.sleep(1)  # Reduced from 2
            return True

        except Exception as e:
            logger.error(f"❌ Failed to select district {district_data['districtName']}: {e}")
            return False

    def click_search_button(self):
        """Click the search button with viewport scrolling and improved error handling"""
        try:
            # Try multiple selectors for the search button
            search_selectors = [
                "button.purpleBtn",  # New selector based on your HTML
                "//button[contains(text(),'Search')]",  # Original text-based
                "//button[contains(@class,'purpleBtn')]",  # XPath for purpleBtn class
                "button[class*='purpleBtn']",  # CSS for purpleBtn class
                "//button[normalize-space()='Search']"  # Normalized text search
            ]

            search_button = None
            working_selector = None

            for selector in search_selectors:
                try:
                    if selector.startswith("//") or selector.startswith("("):
                        # XPath selector
                        search_button = WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                    else:
                        # CSS selector
                        search_button = WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                    working_selector = selector
                    break
                except:
                    continue

            if not search_button:
                logger.error("❌ Search button not found with any selector")
                return False

            # CRITICAL FIX: Scroll element into view before clicking
            try:
                # Scroll to the element to ensure it's in viewport
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", search_button)
                time.sleep(1)  # Wait for scroll to complete

                # Verify element is now clickable
                WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(search_button)
                )

                # Try clicking with JavaScript if regular click fails
                try:
                    search_button.click()
                    logger.info(f"✅ Clicked search button using selector: {working_selector}")
                except Exception as click_error:
                    logger.warning(f"⚠️ Regular click failed, trying JavaScript click: {click_error}")
                    # Fallback to JavaScript click
                    self.driver.execute_script("arguments[0].click();", search_button)
                    logger.info(f"✅ Clicked search button with JavaScript using selector: {working_selector}")

            except Exception as scroll_error:
                logger.error(f"❌ Failed to scroll to or click search button: {scroll_error}")
                return False

            # Wait for results to load with better debugging
            logger.info("⏳ Waiting for search results to load...")

            # Try multiple selectors for results
            result_found = False
            selectors_to_try = [
                ".accordion-body",
                ".accordion-item",
                "[class*='accordion']",
                ".card-body",
                ".result-item",
                "table tbody tr",
                ".school-item"
            ]

            for selector in selectors_to_try:
                try:
                    WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.info(f"✅ Found {len(elements)} result elements with selector: {selector}")
                        result_found = True
                        break
                except:
                    continue

            if not result_found:
                logger.warning("⚠️ No results found with any selector - checking page content")
                # Debug: Check what's actually on the page
                page_text = self.driver.page_source[:2000]  # First 2000 chars
                logger.info(f"Page content preview: {page_text}")

                # Check for common "no results" messages
                if "No records found" in page_text or "No data available" in page_text:
                    logger.info("📄 No schools found for this district")
                else:
                    logger.warning("⚠️ Results may not have loaded properly")

                time.sleep(2)  # Give more time for results to load

            return True

        except Exception as e:
            logger.error(f"❌ Failed to click search button: {e}")
            return False

    def extract_single_school_data(self, school_element):
        """ULTRA-FAST extraction of ALL required fields (PERFORMANCE OPTIMIZED)"""
        try:
            # Pre-create base data structure
            school_data = {
                'state': self.current_state['stateName'],
                'state_id': self.current_state['stateId'],
                'district': self.current_district['districtName'],
                'district_id': self.current_district['districtId'],
                'extraction_date': datetime.now().isoformat()
            }

            # ULTRA-FAST: Single bulk text extraction + optimized regex patterns
            element_html = school_element.get_attribute('innerHTML')
            element_text = school_element.text

            # PERFORMANCE CRITICAL: Use compiled regex patterns for maximum speed
            # Extract all fields in single pass using optimized regex

            # 1. UDISE Code - fast regex extraction
            udise_match = re.search(r'class="udiseCode"[^>]*>([^<]+)', element_html)
            school_data['udise_code'] = udise_match.group(1).strip() if udise_match else 'N/A'

            # 2. Operational Status - fast regex extraction
            status_match = re.search(r'class="OperationalStatus"[^>]*>([^<]+)', element_html)
            school_data['operational_status'] = status_match.group(1).strip() if status_match else 'N/A'

            # 3. School Name - from h4 tag (CRITICAL FIX)
            name_match = re.search(r'<h4[^>]*class="[^"]*custom-word-break[^"]*"[^>]*>([^<]+)', element_html)
            if not name_match:
                name_match = re.search(r'<h4[^>]*>([^<]+)', element_html)
            school_data['school_name'] = name_match.group(1).strip() if name_match else 'N/A'

            # 4. Know More Link - CRITICAL for Phase 2 (extract early for performance)
            link_match = re.search(r'class="[^"]*blueBtn[^"]*"[^>]*href="([^"]+)"', element_html)
            if link_match:
                relative_link = link_match.group(1)
                if relative_link.startswith("#/"):
                    school_data['know_more_link'] = f"https://kys.udiseplus.gov.in/{relative_link}"
                else:
                    school_data['know_more_link'] = relative_link
            else:
                school_data['know_more_link'] = 'N/A'

            # ULTRA-FAST: Bulk field extraction using optimized string operations
            # Pre-compile field patterns for maximum speed
            field_patterns = {
                'edu_district': r'Edu\.\s*District[:\s]*([^\n]+)',
                'edu_block': r'Edu\.\s*Block[:\s]*([^\n]+)',
                'academic_year': r'Academic\s*Year[:\s]*([^\n]+)',
                'school_category': r'School\s*Category[:\s]*([^\n]+)',
                'school_management': r'School\s*Management[:\s]*([^\n]+)',
                'class_range': r'Class[:\s]*([^\n]+)',
                'school_type': r'School\s*Type[:\s]*([^\n]+)',
                'school_location': r'School\s*Location[:\s]*([^\n]+)',
                'address': r'Address[:\s]*([^\n]+)',
                'pin_code': r'PIN\s*Code[:\s]*([^\n]+)'
            }

            # Extract all fields in single pass
            for field_name, pattern in field_patterns.items():
                match = re.search(pattern, element_text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip().replace(':', '').strip()
                    school_data[field_name] = value if value else 'N/A'
                else:
                    school_data[field_name] = 'N/A'

            # Last Modified Time - fast regex extraction
            modified_match = re.search(r'class="lastModifiedTime"[^>]*>([^<]+)', element_html)
            school_data['last_modified'] = modified_match.group(1).strip() if modified_match else 'N/A'

            return school_data

        except:
            # ULTRA-FAST: Minimal error handling for maximum speed
            return None

    def extract_schools_from_current_page(self):
        """Extract schools data from the current page with multiple selector attempts"""
        try:
            # Try multiple selectors to find school elements
            selectors_to_try = [
                ".accordion-body",
                ".accordion-item",
                "[class*='accordion']",
                ".card-body",
                ".result-item",
                "table tbody tr",
                ".school-item"
            ]

            school_elements = []
            working_selector = None

            for selector in selectors_to_try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    school_elements = elements
                    working_selector = selector
                    logger.info(f"✅ Found {len(elements)} school elements with selector: {selector}")
                    break

            if not school_elements:
                logger.warning("⚠️ No school elements found with any selector")
                # Debug: Check page content
                page_text = self.driver.page_source[:1000]
                if "No records found" in page_text or "No data available" in page_text:
                    logger.info("📄 Confirmed: No schools in this district")
                else:
                    logger.warning("⚠️ Page may not have loaded properly")
                return []

            # Process all schools
            schools_data = []
            for school_element in school_elements:
                school_data = self.extract_single_school_data(school_element)
                if school_data:
                    schools_data.append(school_data)

            logger.info(f"Extracted {len(schools_data)} schools from current page using selector: {working_selector}")
            return schools_data

        except Exception as e:
            logger.error(f"Error extracting schools from page: {e}")
            return []

    def extract_schools_basic_data(self):
        """Extract basic schools data from search results with pagination"""
        try:
            schools_data = []
            page_number = 1
            max_pages = 100  # Safety limit to prevent infinite loops

            while page_number <= max_pages:
                logger.info(f"📄 Processing page {page_number}")

                # ULTRA-FAST: Minimal wait for page to load
                if page_number > 1:
                    time.sleep(0.2)  # Reduced from 0.5 second

                # Extract schools from current page
                logger.info(f"   🔍 Extracting schools from page {page_number}...")
                page_schools = self.extract_schools_from_current_page()
                schools_data.extend(page_schools)
                logger.info(f"   ✅ Extracted {len(page_schools)} schools from page {page_number}")
                logger.info(f"   📊 Total schools so far: {len(schools_data)}")

                # Try to go to next page
                logger.info(f"   🔄 Checking for next page after page {page_number}...")
                if not self.click_next_page():
                    logger.info(f"📄 No more pages available after page {page_number}")
                    break

                page_number += 1
                # ULTRA-FAST: Minimal wait for next page to load
                time.sleep(0.3)  # Reduced from 0.8 seconds

            if page_number > max_pages:
                logger.warning(f"⚠️ Reached maximum page limit ({max_pages}) - stopping pagination")

            logger.info(f"Total schools extracted: {len(schools_data)}")
            return schools_data

        except Exception as e:
            logger.error(f"Failed to extract schools data: {e}")
            return []

    def click_next_page(self):
        """Click next page button if available and not disabled"""
        try:
            # Find next button using primary selector
            next_buttons = self.driver.find_elements(By.CSS_SELECTOR, "a.nextBtn")

            if not next_buttons:
                logger.debug("No next button found")
                return False

            next_button = next_buttons[0]

            # Check if button is displayed
            if not next_button.is_displayed():
                logger.debug("Next button not displayed")
                return False

            # CRITICAL FIX: Check if the parent <li> element has disabled class
            try:
                parent_li = next_button.find_element(By.XPATH, "..")
                parent_classes = parent_li.get_attribute("class") or ""

                # Check if parent li has disabled class
                if "disabled" in parent_classes.lower():
                    logger.info("📄 Next button is disabled (parent li has disabled class) - no more pages")
                    return False

            except:
                # If we can't check parent, continue with other checks
                pass

            # Check if the anchor itself has disabled class or attribute
            button_classes = next_button.get_attribute("class") or ""
            if "disabled" in button_classes.lower():
                logger.info("📄 Next button is disabled (has disabled class) - no more pages")
                return False

            # Check for disabled attribute
            if next_button.get_attribute("disabled"):
                logger.info("📄 Next button has disabled attribute - no more pages")
                return False

            # Check if button is enabled (basic Selenium check)
            if not next_button.is_enabled():
                logger.info("📄 Next button is not enabled - no more pages")
                return False

            # Button appears to be clickable - try to click
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

    def reset_search_filters(self):
        """Reset any search filters to ensure we get all schools for the district"""
        try:
            logger.info("🔄 Resetting search filters...")

            # Look for any filter dropdowns or checkboxes that might limit results
            filter_selectors = [
                "select[name*='filter']",
                "select[name*='category']",
                "select[name*='type']",
                "input[type='checkbox']:checked"
            ]

            for selector in filter_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.tag_name == 'select':
                            # Reset select to first option (usually "All" or default)
                            select_obj = Select(element)
                            if len(select_obj.options) > 0:
                                select_obj.select_by_index(0)
                                logger.debug(f"   Reset select filter: {selector}")
                        elif element.tag_name == 'input' and element.get_attribute('type') == 'checkbox':
                            # Uncheck any checked filters
                            if element.is_selected():
                                element.click()
                                logger.debug(f"   Unchecked filter: {selector}")
                except Exception as e:
                    logger.debug(f"   Error resetting filter {selector}: {e}")
                    continue

            # Brief wait for filter reset to take effect
            time.sleep(0.5)
            logger.info("✅ Search filters reset")
            return True

        except Exception as e:
            logger.debug(f"Error resetting search filters: {e}")
            return False

    def segregate_schools_by_links(self, schools_data, state_name):
        """Segregate schools based on know_more_links availability"""
        schools_with_links = []
        schools_no_links = []

        for school in schools_data:
            if school.get('know_more_link', 'N/A') != 'N/A' and school.get('know_more_link', '').strip():
                schools_with_links.append(school)
            else:
                schools_no_links.append(school)

        logger.info(f"State {state_name}: {len(schools_with_links)} schools WITH links, {len(schools_no_links)} schools WITHOUT links")

        return schools_with_links, schools_no_links

    def save_state_data_to_csv(self, state_name):
        """Save consolidated state data to single CSV file with link availability status"""
        try:
            # Clean state name for filename
            clean_state = state_name.replace(' ', '_').replace('&', 'and').replace('/', '_').upper()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Create consolidated data with link availability status
            all_state_schools = []

            # Add schools WITH know_more_links
            if state_name in self.state_schools_with_links and self.state_schools_with_links[state_name]:
                for school in self.state_schools_with_links[state_name]:
                    school_copy = school.copy()
                    school_copy['has_know_more_link'] = True
                    school_copy['phase2_ready'] = True
                    all_state_schools.append(school_copy)

            # Add schools WITHOUT know_more_links
            if state_name in self.state_schools_no_links and self.state_schools_no_links[state_name]:
                for school in self.state_schools_no_links[state_name]:
                    school_copy = school.copy()
                    school_copy['has_know_more_link'] = False
                    school_copy['phase2_ready'] = False
                    all_state_schools.append(school_copy)

            # Create consolidated filename following new convention
            consolidated_filename = f"{clean_state}_phase1_complete_{timestamp}.csv"

            if all_state_schools:
                df_consolidated = pd.DataFrame(all_state_schools)

                # Reorder columns to put status columns first for easy filtering
                cols = df_consolidated.columns.tolist()
                status_cols = ['has_know_more_link', 'phase2_ready']
                other_cols = [col for col in cols if col not in status_cols]
                df_consolidated = df_consolidated[status_cols + other_cols]

                df_consolidated.to_csv(consolidated_filename, index=False)
            else:
                # Create empty CSV with proper headers even when no schools found
                empty_data = {
                    'has_know_more_link': [],
                    'phase2_ready': [],
                    'state': [],
                    'state_id': [],
                    'district': [],
                    'district_id': [],
                    'udise_code': [],
                    'school_name': [],
                    'know_more_link': [],
                    'extraction_date': []
                }
                df_empty = pd.DataFrame(empty_data)
                df_empty.to_csv(consolidated_filename, index=False)
                logger.info(f"✅ Created empty CSV file (no schools found): {consolidated_filename}")

            with_links_count = len(self.state_schools_with_links.get(state_name, []))
            no_links_count = len(self.state_schools_no_links.get(state_name, []))

            logger.info(f"✅ Saved consolidated Phase 1 data to: {consolidated_filename}")
            logger.info(f"   📊 Total schools: {len(all_state_schools)}")
            logger.info(f"   🔗 With links (Phase 2 ready): {with_links_count}")
            logger.info(f"   📋 Without links (reference only): {no_links_count}")

            return True

        except Exception as e:
            logger.error(f"Failed to save consolidated state data for {state_name}: {e}")
            return False

    def run_statewise_scraping(self, target_states=None, max_districts_per_state=None):
        """Main function to run state-wise scraping with data segregation"""
        try:
            self.setup_driver()
            self.navigate_to_portal()

            # Minimal wait for page to fully load
            logger.info("Waiting for page to fully load...")
            time.sleep(1)  # Reduced from 5

            # Extract all states
            states = self.extract_states_data()

            if not states:
                logger.error("No states extracted. Cannot proceed.")
                return

            # Filter states if target_states specified
            if target_states:
                if isinstance(target_states, str):
                    target_states = [target_states]
                states = [state for state in states if state['stateName'] in target_states]
                logger.info(f"Filtered to target states: {[s['stateName'] for s in states]}")

            total_states = len(states)
            logger.info(f"🎯 Processing {total_states} states")

            for state_index, state in enumerate(states, 1):
                state_name = state['stateName']
                logger.info(f"\n{'='*80}")
                logger.info(f"🏛️ PROCESSING STATE {state_index}/{total_states}: {state_name}")
                logger.info(f"{'='*80}")

                try:
                    # Initialize state data storage
                    self.state_schools_with_links[state_name] = []
                    self.state_schools_no_links[state_name] = []

                    # Select state
                    self.select_state(state)

                    # Get districts for this state
                    districts = self.extract_districts_data()

                    if max_districts_per_state:
                        districts = districts[:max_districts_per_state]
                        logger.info(f"Limited to first {max_districts_per_state} districts for testing")

                    total_districts = len(districts)
                    logger.info(f"📍 Found {total_districts} districts in {state_name}")

                    for district_index, district in enumerate(districts, 1):
                        district_name = district['districtName']
                        logger.info(f"\n🏘️ Processing district {district_index}/{total_districts}: {district_name}")

                        try:
                            # Select district
                            self.select_district(district)

                            # Click search
                            if self.click_search_button():
                                # Extract basic schools data with pagination
                                district_schools_data = self.extract_schools_basic_data()

                                if district_schools_data:
                                    # Segregate schools by know_more_links availability
                                    schools_with_links, schools_no_links = self.segregate_schools_by_links(
                                        district_schools_data, state_name
                                    )

                                    # Add to state collections
                                    self.state_schools_with_links[state_name].extend(schools_with_links)
                                    self.state_schools_no_links[state_name].extend(schools_no_links)

                                    logger.info(f"✅ Completed {district_name}: {len(district_schools_data)} schools total")
                                    logger.info(f"   📊 {len(schools_with_links)} with links, {len(schools_no_links)} without links")
                                else:
                                    logger.warning(f"⚠️ No schools found for {district_name}")

                            # Minimal delay between districts
                            time.sleep(0.2)  # Reduced from 0.5

                        except Exception as e:
                            logger.error(f"❌ Failed to process district {district_name}: {e}")
                            continue

                    # Save state data to CSV files
                    logger.info(f"\n💾 Saving data for state: {state_name}")
                    self.save_state_data_to_csv(state_name)

                    # Show state summary
                    total_with_links = len(self.state_schools_with_links[state_name])
                    total_no_links = len(self.state_schools_no_links[state_name])
                    total_schools = total_with_links + total_no_links

                    logger.info(f"\n📊 STATE SUMMARY - {state_name}:")
                    logger.info(f"   🏫 Total schools: {total_schools}")
                    logger.info(f"   🔗 Schools with links (Phase 2 ready): {total_with_links}")
                    logger.info(f"   📋 Schools without links (reference only): {total_no_links}")
                    logger.info(f"   📈 Phase 2 coverage: {(total_with_links/total_schools)*100:.1f}%" if total_schools > 0 else "   📈 Phase 2 coverage: 0%")

                except Exception as e:
                    logger.error(f"❌ Failed to process state {state_name}: {e}")
                    continue

            # Final summary
            self.show_final_summary()

        except Exception as e:
            logger.error(f"❌ State-wise scraping process failed: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("🔒 Driver closed")

    def process_single_state(self, target_state):
        """Process a single state (for sequential processing)"""
        try:
            logger.info(f"🎯 Processing single state: {target_state['stateName']}")

            # Set current state
            self.current_state = target_state

            # Select the state
            if not self.select_state(target_state):
                logger.error(f"Failed to select state: {target_state['stateName']}")
                return False

            # Extract districts for this state
            districts = self.extract_districts_data()
            if not districts:
                logger.warning(f"No districts found for {target_state['stateName']}")
                self.save_state_data_to_csv(target_state['stateName'])
                return True

            # Process all districts in this state
            for i, district in enumerate(districts, 1):
                try:
                    logger.info(f"\n🏘️ Processing district {i}/{len(districts)}: {district['districtName']}")

                    # Set current district
                    self.current_district = district

                    # Select district, reset filters, click search, and extract schools
                    if self.select_district(district):
                        # CRITICAL FIX: Reset all filters to ensure we get all schools
                        self.reset_search_filters()

                        # Click search button after selecting district with retry mechanism
                        search_success = False
                        for search_attempt in range(3):  # Try up to 3 times
                            if self.click_search_button():
                                search_success = True
                                break
                            else:
                                logger.warning(f"Search button click failed (attempt {search_attempt + 1}/3) for district: {district['districtName']}")
                                if search_attempt < 2:  # Don't wait after last attempt
                                    time.sleep(2)  # Wait before retry

                        if search_success:
                            schools_data = self.extract_schools_basic_data()
                        else:
                            logger.error(f"❌ Failed to click search button after 3 attempts for district: {district['districtName']}")
                            schools_data = []

                        # Categorize schools
                        for school in schools_data:
                            if school.get('know_more_link') and school['know_more_link'] != 'N/A':
                                if target_state['stateName'] not in self.state_schools_with_links:
                                    self.state_schools_with_links[target_state['stateName']] = []
                                self.state_schools_with_links[target_state['stateName']].append(school)
                            else:
                                if target_state['stateName'] not in self.state_schools_no_links:
                                    self.state_schools_no_links[target_state['stateName']] = []
                                self.state_schools_no_links[target_state['stateName']].append(school)

                        with_links = len(self.state_schools_with_links.get(target_state['stateName'], []))
                        without_links = len(self.state_schools_no_links.get(target_state['stateName'], []))

                        logger.info(f"✅ Completed {district['districtName']}: {len(schools_data)} schools total")
                        logger.info(f"   📊 {with_links} with links, {without_links} without links")

                        # Brief delay between districts
                        time.sleep(0.2)
                    else:
                        logger.warning(f"Failed to select district: {district['districtName']}")

                except Exception as e:
                    logger.error(f"Error processing district {district['districtName']}: {e}")
                    continue

            # Save state data
            self.save_state_data_to_csv(target_state['stateName'])

            # Show state summary
            with_links_count = len(self.state_schools_with_links.get(target_state['stateName'], []))
            no_links_count = len(self.state_schools_no_links.get(target_state['stateName'], []))
            total_count = with_links_count + no_links_count

            logger.info(f"\n📊 STATE SUMMARY - {target_state['stateName']}:")
            logger.info(f"   🏫 Total schools: {total_count}")
            logger.info(f"   🔗 Schools with links (Phase 2 ready): {with_links_count}")
            logger.info(f"   📋 Schools without links (reference only): {no_links_count}")
            if total_count > 0:
                logger.info(f"   📈 Phase 2 coverage: {with_links_count/total_count*100:.0f}%")

            return True

        except Exception as e:
            logger.error(f"Error processing single state {target_state['stateName']}: {e}")
            return False

    def show_final_summary(self):
        """Show final summary of all processed states"""
        print(f"\n{'='*100}")
        print("🎯 FINAL SUMMARY - STATE-WISE SCRAPING COMPLETED")
        print(f"{'='*100}")

        total_states_processed = len(self.state_schools_with_links)
        total_schools_with_links = sum(len(schools) for schools in self.state_schools_with_links.values())
        total_schools_no_links = sum(len(schools) for schools in self.state_schools_no_links.values())
        total_schools = total_schools_with_links + total_schools_no_links

        print(f"📊 OVERALL STATISTICS:")
        print(f"   🏛️ States processed: {total_states_processed}")
        print(f"   🏫 Total schools extracted: {total_schools}")
        print(f"   🔗 Schools with know_more_links: {total_schools_with_links}")
        print(f"   📋 Schools without know_more_links: {total_schools_no_links}")
        print(f"   📈 Phase 2 readiness: {(total_schools_with_links/total_schools)*100:.1f}%" if total_schools > 0 else "   📈 Phase 2 readiness: 0%")

        print(f"\n📁 FILES CREATED:")
        for state_name in self.state_schools_with_links.keys():
            clean_state = state_name.replace(' ', '_').replace('&', 'and').replace('/', '_').upper()
            with_links_count = len(self.state_schools_with_links[state_name])
            no_links_count = len(self.state_schools_no_links[state_name])

            print(f"   🏛️ {state_name}:")
            if with_links_count > 0:
                print(f"      ✅ {clean_state}_with_links_[timestamp].csv ({with_links_count} schools)")
            if no_links_count > 0:
                print(f"      📋 {clean_state}_no_links_[timestamp].csv ({no_links_count} schools)")
            print(f"      📊 {clean_state}_complete_[timestamp].csv ({with_links_count + no_links_count} schools)")

        print(f"\n🚀 NEXT STEPS:")
        print(f"   1. Use {clean_state}_with_links_[timestamp].csv files for Phase 2 processing")
        print(f"   2. Run Phase 2 batch processor on each state file")
        print(f"   3. {clean_state}_no_links_[timestamp].csv files are for reference only")

        print(f"{'='*100}")

# Main execution
if __name__ == "__main__":
    scraper = StatewiseSchoolScraper()

    # Configuration options
    print("🚀 STATE-WISE SCHOOL SCRAPER")
    print("Creates separate CSV files for each state with data segregation")
    print()

    # Get user preferences
    choice = input("Select option:\n1. Process ALL states\n2. Process specific states\n3. Test mode (limited districts)\nEnter choice (1-3): ").strip()

    if choice == "1":
        # Process all states
        scraper.run_statewise_scraping()
    elif choice == "2":
        # Process specific states
        target_states_input = input("Enter state names (comma-separated): ").strip()
        target_states = [state.strip() for state in target_states_input.split(',') if state.strip()]
        scraper.run_statewise_scraping(target_states=target_states)
    elif choice == "3":
        # Test mode
        target_states_input = input("Enter state names for testing (comma-separated): ").strip()
        target_states = [state.strip() for state in target_states_input.split(',') if state.strip()]
        max_districts = int(input("Enter max districts per state (default 2): ").strip() or "2")
        scraper.run_statewise_scraping(target_states=target_states, max_districts_per_state=max_districts)
    else:
        print("Invalid choice. Running test mode with default settings.")
        scraper.run_statewise_scraping(target_states=["ANDAMAN & NICOBAR ISLANDS"], max_districts_per_state=2)

    print("\n✅ State-wise scraping completed!")
