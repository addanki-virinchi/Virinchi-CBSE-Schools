import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import undetected_chromedriver as uc
import logging
from datetime import datetime
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SchoolDataScraper:
    def __init__(self):
        self.driver = None
        self.all_schools_data = []
        self.states_data = []
        self.current_state = None
        self.current_district = None

    def setup_driver(self):
        """Initialize the Chrome browser driver"""
        try:
            # Setup Chrome options
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-blink-features=AutomationControlled")

            self.driver = uc.Chrome(options=options)
            self.driver.maximize_window()
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(30)
            logger.info("✅ Chrome browser driver initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Chrome driver: {e}")
            logger.error("Please ensure Chrome browser is installed")
            raise

    def navigate_to_portal(self):
        """Navigate to the UDISE Plus portal and access advance search"""
        try:
            logger.info("🌐 Navigating to UDISE Plus portal...")
            self.driver.get("https://udiseplus.gov.in/#/en/home")
            time.sleep(5)

            # Click on Visit Portal with multiple selector attempts
            logger.info("🔍 Looking for Visit Portal button...")
            visit_portal_selectors = [
                "//a[contains(text(),'Visit Portal')]",
                "//a[contains(@href, 'portal')]",
                "//button[contains(text(),'Visit Portal')]",
                "//div[contains(text(),'Visit Portal')]"
            ]

            visit_portal_btn = None
            for selector in visit_portal_selectors:
                try:
                    visit_portal_btn = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    logger.info(f"✅ Found Visit Portal button with selector: {selector}")
                    break
                except TimeoutException:
                    continue

            if visit_portal_btn:
                visit_portal_btn.click()
                logger.info("✅ Clicked Visit Portal button")
                time.sleep(5)
            else:
                logger.error("❌ Visit Portal button not found")
                raise Exception("Visit Portal button not found")

            # Switch to new tab if opened
            if len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                logger.info("🔄 Switched to new tab")
                time.sleep(3)

            # Click on Advance Search with multiple selector attempts
            logger.info("🔍 Looking for Advance Search button...")
            advance_search_selectors = [
                "//a[@id='advanceSearch']",
                "//a[contains(text(),'Advance Search')]",
                "//a[contains(text(),'Advanced Search')]",
                "//button[contains(text(),'Advance Search')]",
                "//div[contains(text(),'Advance Search')]"
            ]

            advance_search_btn = None
            for selector in advance_search_selectors:
                try:
                    advance_search_btn = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    logger.info(f"✅ Found Advance Search button with selector: {selector}")
                    break
                except TimeoutException:
                    continue

            if advance_search_btn:
                # Scroll to element and click
                self.driver.execute_script("arguments[0].scrollIntoView(true);", advance_search_btn)
                time.sleep(1)
                advance_search_btn.click()
                logger.info("✅ Clicked Advance Search button")
                time.sleep(5)
            else:
                logger.error("❌ Advance Search button not found")
                raise Exception("Advance Search button not found")

        except Exception as e:
            logger.error(f"❌ Failed to navigate to portal: {e}")
            raise

    def debug_dropdown_state(self):
        """Debug method to check dropdown state"""
        try:
            select_elements = self.driver.find_elements(By.CSS_SELECTOR, "select.form-select.select")
            logger.info(f"Found {len(select_elements)} select elements")

            for i, select_element in enumerate(select_elements):
                options = select_element.find_elements(By.TAG_NAME, "option")
                logger.info(f"Select {i}: {len(options)} options")

                # Show first few options
                for j, option in enumerate(options[:3]):
                    logger.info(f"  Option {j}: text='{option.text}', value='{option.get_attribute('value')[:50]}...'")

        except Exception as e:
            logger.error(f"Debug dropdown failed: {e}")

    def extract_states_data(self):
        """Extract all states data from the dropdown"""
        try:
            # Debug dropdown state first
            self.debug_dropdown_state()

            # Wait for state dropdown to be present and populated
            logger.info("Waiting for state dropdown to load...")
            state_select = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "select.form-select.select"))
            )

            # Wait a bit more for options to populate
            time.sleep(3)

            # Get all state options (skip the first "Select State" option)
            state_options = state_select.find_elements(By.TAG_NAME, "option")
            logger.info(f"Found {len(state_options)} total options in state dropdown")

            if len(state_options) <= 1:
                logger.error("State dropdown appears to be empty or not loaded")
                raise Exception("State dropdown not properly loaded")

            # Skip the first "Select State" option
            state_options = state_options[1:]

            for i, option in enumerate(state_options):
                state_value = option.get_attribute("value")
                state_text = option.text.strip()

                if state_value and state_text:
                    try:
                        state_data = json.loads(state_value)
                        self.states_data.append(state_data)
                        logger.info(f"Added state {i+1}: {state_data['stateName']}")
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse state data for '{state_text}': {state_value[:100]}...")
                        # Try to create a basic state data structure
                        state_data = {
                            'stateName': state_text,
                            'stateId': i + 100,  # Fallback ID
                            'udiseStateCode': f"{i+1:02d}"
                        }
                        self.states_data.append(state_data)
                        logger.info(f"Added state {i+1} with fallback data: {state_text}")
                else:
                    logger.warning(f"Empty state option found: text='{state_text}', value='{state_value}'")

            logger.info(f"Total states extracted: {len(self.states_data)}")

            if len(self.states_data) == 0:
                raise Exception("No states were extracted from dropdown")

            return self.states_data

        except Exception as e:
            logger.error(f"Failed to extract states data: {e}")
            raise

    def select_state(self, state_data):
        """Select a specific state from the dropdown"""
        try:
            self.current_state = state_data
            state_select_element = self.driver.find_element(By.CSS_SELECTOR, "select.form-select.select")
            state_select = Select(state_select_element)

            # Try multiple methods to select the state
            success = False

            # Method 1: Try exact JSON match
            try:
                state_value = json.dumps(state_data, separators=(',', ':'))
                state_select.select_by_value(state_value)
                success = True
                logger.info(f"Selected state by exact JSON: {state_data['stateName']}")
            except:
                pass

            # Method 2: Try JSON with different formatting
            if not success:
                try:
                    state_value = json.dumps(state_data)
                    state_select.select_by_value(state_value)
                    success = True
                    logger.info(f"Selected state by formatted JSON: {state_data['stateName']}")
                except:
                    pass

            # Method 3: Try selecting by visible text
            if not success:
                try:
                    state_select.select_by_visible_text(state_data['stateName'])
                    success = True
                    logger.info(f"Selected state by visible text: {state_data['stateName']}")
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
                            logger.info(f"Selected state by name match: {state_data['stateName']}")
                            break
                except:
                    pass

            # Method 5: Try clicking the option directly
            if not success:
                try:
                    options = state_select_element.find_elements(By.TAG_NAME, "option")
                    for option in options:
                        if option.text.strip() == state_data['stateName']:
                            option.click()
                            success = True
                            logger.info(f"Selected state by direct click: {state_data['stateName']}")
                            break
                except:
                    pass

            if not success:
                # Log available options for debugging
                options = state_select_element.find_elements(By.TAG_NAME, "option")
                logger.error(f"Failed to select state. Available options:")
                for i, option in enumerate(options[:5]):  # Show first 5
                    logger.error(f"  Option {i}: text='{option.text}', value='{option.get_attribute('value')[:100]}...'")
                raise Exception(f"Could not select state {state_data['stateName']} using any method")

            time.sleep(3)  # Wait for districts to load

        except Exception as e:
            logger.error(f"Failed to select state {state_data['stateName']}: {e}")
            raise

    def extract_districts_data(self):
        """Extract districts data for the currently selected state"""
        try:
            # Wait for district dropdown to be populated
            time.sleep(5)

            # Find all select elements and get the district one (usually the second one)
            select_elements = self.driver.find_elements(By.CSS_SELECTOR, "select.form-select.select")

            if len(select_elements) < 2:
                logger.warning("District dropdown not found")
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
                        districts_data.append(district_data)
                        logger.info(f"Found district (JSON): {district_data['districtName']}")
                    except json.JSONDecodeError:
                        # If not JSON, create a simple district data structure
                        district_data = {
                            'districtId': district_value,
                            'districtName': district_text,
                            'stateId': self.current_state.get('stateId', 0),
                            'udiseDistrictCode': district_value
                        }
                        districts_data.append(district_data)
                        logger.info(f"Found district (simple): {district_text} (ID: {district_value})")
                else:
                    logger.warning(f"Empty district option: text='{district_text}', value='{district_value}'")

            logger.info(f"Total districts found for {self.current_state['stateName']}: {len(districts_data)}")
            return districts_data

        except Exception as e:
            logger.error(f"Failed to extract districts data: {e}")
            return []

    def select_district(self, district_data):
        """Select a specific district from the dropdown"""
        try:
            self.current_district = district_data

            # Wait a bit more for district dropdown to populate
            time.sleep(3)

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
                logger.info(f"Selected district by ID: {district_data['districtName']} (ID: {district_id})")
            except Exception as e:
                logger.debug(f"Method 1 failed: {e}")
                pass

            # Method 2: Try exact JSON match (for backward compatibility)
            if not success:
                try:
                    district_value = json.dumps(district_data, separators=(',', ':'))
                    district_select.select_by_value(district_value)
                    success = True
                    logger.info(f"Selected district by exact JSON: {district_data['districtName']}")
                except Exception as e:
                    logger.debug(f"Method 2 failed: {e}")
                    pass

            # Method 3: Try selecting by visible text
            if not success:
                try:
                    district_select.select_by_visible_text(district_data['districtName'])
                    success = True
                    logger.info(f"Selected district by visible text: {district_data['districtName']}")
                except Exception as e:
                    logger.debug(f"Method 3 failed: {e}")
                    pass

            # Method 4: Try finding option by exact text match
            if not success:
                try:
                    options = district_select_element.find_elements(By.TAG_NAME, "option")
                    for option in options:
                        if option.text.strip().upper() == district_data['districtName'].upper():
                            option.click()
                            success = True
                            logger.info(f"Selected district by text match: {district_data['districtName']}")
                            break
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
                            logger.info(f"Selected district by partial match: {district_data['districtName']} -> {option.text}")
                            break
                except Exception as e:
                    logger.debug(f"Method 5 failed: {e}")
                    pass

            if not success:
                # Log available options for debugging
                options = district_select_element.find_elements(By.TAG_NAME, "option")
                logger.error(f"Failed to select district '{district_data['districtName']}'. Available options:")
                for i, option in enumerate(options[:10]):  # Show first 10
                    logger.error(f"  Option {i}: text='{option.text}', value='{option.get_attribute('value')}'")
                raise Exception(f"Could not select district {district_data['districtName']} using any method")

            time.sleep(2)

        except Exception as e:
            logger.error(f"Failed to select district {district_data['districtName']}: {e}")
            raise

    def click_search_button(self):
        """Click the search button to load schools data"""
        try:
            # Look for search button - it might have different selectors
            search_button_selectors = [
                "//button[contains(text(),'Search')]",
                "//input[@type='submit']",
                "//button[@type='submit']",
                "//a[contains(@class, 'search')]",
                "//button[contains(@class, 'search')]"
            ]

            search_button = None
            for selector in search_button_selectors:
                try:
                    search_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except TimeoutException:
                    continue

            if search_button:
                search_button.click()
                logger.info("Clicked search button")
                time.sleep(5)  # Wait for results to load
                return True
            else:
                logger.warning("Search button not found")
                return False

        except Exception as e:
            logger.error(f"Failed to click search button: {e}")
            return False

    def extract_schools_basic_data(self):
        """Extract basic schools data from search results with pagination"""
        try:
            schools_data = []
            page_number = 1

            while True:
                logger.info(f"Processing page {page_number} for {self.current_state['stateName']} - {self.current_district['districtName']}")

                # Wait for results to load
                time.sleep(3)

                # Extract schools from current page
                page_schools = self.extract_schools_from_current_page()
                schools_data.extend(page_schools)

                # Check for next button and click if exists
                if not self.click_next_page():
                    logger.info(f"No more pages. Processed {page_number} pages total.")
                    break

                page_number += 1
                time.sleep(2)  # Wait between page clicks

            logger.info(f"Extracted {len(schools_data)} schools total for {self.current_state['stateName']} - {self.current_district['districtName']}")
            return schools_data

        except Exception as e:
            logger.error(f"Failed to extract schools data: {e}")
            return []

    def extract_schools_from_current_page(self):
        """Extract schools data from the current page"""
        try:
            schools_data = []

            # Look for accordion items containing school data
            school_elements = self.driver.find_elements(By.CSS_SELECTOR, ".accordion-body")

            if not school_elements:
                # Try alternative selectors
                school_elements = self.driver.find_elements(By.CSS_SELECTOR, "[class*='accordion']")

            for school_element in school_elements:
                try:
                    school_data = self.extract_single_school_data(school_element)
                    if school_data:
                        schools_data.append(school_data)
                except Exception as e:
                    logger.warning(f"Failed to extract data from one school element: {e}")
                    continue

            logger.info(f"Extracted {len(schools_data)} schools from current page")
            return schools_data

        except Exception as e:
            logger.error(f"Failed to extract schools from current page: {e}")
            return []

    def extract_single_school_data(self, school_element):
        """Extract data from a single school element"""
        try:
            school_data = {
                'state': self.current_state['stateName'],
                'state_id': self.current_state['stateId'],
                'district': self.current_district['districtName'],
                'district_id': self.current_district['districtId'],
                'extraction_date': datetime.now().isoformat()
            }

            # Extract UDISE Code
            try:
                udise_element = school_element.find_element(By.CSS_SELECTOR, ".udiseCode")
                school_data['udise_code'] = udise_element.text.strip()
            except NoSuchElementException:
                school_data['udise_code'] = 'N/A'

            # Extract Operational Status
            try:
                status_element = school_element.find_element(By.CSS_SELECTOR, ".OperationalStatus")
                school_data['operational_status'] = status_element.text.strip()
            except NoSuchElementException:
                school_data['operational_status'] = 'N/A'

            # Extract School Name
            try:
                name_element = school_element.find_element(By.CSS_SELECTOR, "h4")
                school_data['school_name'] = name_element.text.strip()
            except NoSuchElementException:
                school_data['school_name'] = 'N/A'

            # Extract Educational District and Block
            try:
                edu_district_element = school_element.find_element(By.XPATH, ".//span[contains(text(), 'Edu. District')]/following-sibling::span")
                school_data['edu_district'] = edu_district_element.text.strip()
            except NoSuchElementException:
                school_data['edu_district'] = 'N/A'

            try:
                edu_block_element = school_element.find_element(By.XPATH, ".//span[contains(text(), 'Edu. Block')]/following-sibling::span")
                school_data['edu_block'] = edu_block_element.text.strip()
            except NoSuchElementException:
                school_data['edu_block'] = 'N/A'

            # Extract Academic Year
            try:
                academic_year_element = school_element.find_element(By.XPATH, ".//span[contains(text(), 'Academic Year')]/following-sibling::span")
                school_data['academic_year'] = academic_year_element.text.strip()
            except NoSuchElementException:
                school_data['academic_year'] = 'N/A'

            # Extract School Category
            try:
                category_element = school_element.find_element(By.XPATH, ".//span[contains(text(), 'School Category')]/following-sibling::span")
                school_data['school_category'] = category_element.text.strip()
            except NoSuchElementException:
                school_data['school_category'] = 'N/A'

            # Extract School Management
            try:
                management_element = school_element.find_element(By.XPATH, ".//span[contains(text(), 'School Management')]/following-sibling::span")
                school_data['school_management'] = management_element.text.strip()
            except NoSuchElementException:
                school_data['school_management'] = 'N/A'

            # Extract Class Range
            try:
                class_element = school_element.find_element(By.XPATH, ".//span[contains(text(), 'Class')]/following-sibling::span")
                school_data['class_range'] = class_element.text.strip()
            except NoSuchElementException:
                school_data['class_range'] = 'N/A'

            # Extract School Type
            try:
                type_element = school_element.find_element(By.XPATH, ".//span[contains(text(), 'School Type')]/following-sibling::span")
                school_data['school_type'] = type_element.text.strip()
            except NoSuchElementException:
                school_data['school_type'] = 'N/A'

            # Extract School Location
            try:
                location_element = school_element.find_element(By.XPATH, ".//span[contains(text(), 'School Location')]/following-sibling::span")
                school_data['school_location'] = location_element.text.strip()
            except NoSuchElementException:
                school_data['school_location'] = 'N/A'

            # Extract Address
            try:
                address_element = school_element.find_element(By.XPATH, ".//span[contains(text(), 'Address')]/following-sibling::span")
                school_data['address'] = address_element.text.strip()
            except NoSuchElementException:
                school_data['address'] = 'N/A'

            # Extract PIN Code
            try:
                pin_element = school_element.find_element(By.XPATH, ".//span[contains(text(), 'PIN Code')]/following-sibling::span")
                school_data['pin_code'] = pin_element.text.strip()
            except NoSuchElementException:
                school_data['pin_code'] = 'N/A'

            # Extract Last Modified Time
            try:
                modified_element = school_element.find_element(By.CSS_SELECTOR, ".lastModifiedTime:last-child")
                school_data['last_modified'] = modified_element.text.strip()
            except NoSuchElementException:
                school_data['last_modified'] = 'N/A'

            # Extract Know More Link (MOST IMPORTANT)
            try:
                know_more_element = school_element.find_element(By.CSS_SELECTOR, ".blueBtn")
                relative_link = know_more_element.get_attribute("href")
                if relative_link:
                    # Convert to full URL
                    if relative_link.startswith("#/"):
                        full_url = f"https://kys.udiseplus.gov.in/{relative_link}"
                    else:
                        full_url = relative_link
                    school_data['know_more_link'] = full_url
                else:
                    school_data['know_more_link'] = 'N/A'
            except NoSuchElementException:
                school_data['know_more_link'] = 'N/A'

            return school_data

        except Exception as e:
            logger.error(f"Failed to extract single school data: {e}")
            return None

    def click_next_page(self):
        """Click next page button if available"""
        try:
            # Look for next button
            next_button = self.driver.find_element(By.CSS_SELECTOR, ".nextBtn")

            # Check if button is enabled/clickable
            if next_button.is_enabled() and next_button.is_displayed():
                next_button.click()
                logger.info("Clicked next page button")
                return True
            else:
                logger.info("Next button not available or disabled")
                return False

        except NoSuchElementException:
            logger.info("Next button not found - reached last page")
            return False
        except Exception as e:
            logger.warning(f"Error clicking next button: {e}")
            return False

    def save_district_data_to_csv(self, data, state_name, district_name):
        """Save district data to CSV with state and district in filename"""
        try:
            if not data:
                logger.warning("No data to save for this district")
                return None

            # Clean state and district names for filename
            clean_state = state_name.replace(' ', '_').replace('&', 'and').replace('/', '_')
            clean_district = district_name.replace(' ', '_').replace('&', 'and').replace('/', '_')

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"schools_basic_{clean_state}_{clean_district}_{timestamp}.csv"

            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            logger.info(f"District data saved to {filename}")
            logger.info(f"Records saved: {len(data)}")

            return filename

        except Exception as e:
            logger.error(f"Failed to save district data: {e}")
            return None

    def save_data_to_csv(self, filename=None):
        """Save all collected data to CSV"""
        try:
            if not self.all_schools_data:
                logger.warning("No data to save")
                return

            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"schools_basic_complete_{timestamp}.csv"

            df = pd.DataFrame(self.all_schools_data)
            df.to_csv(filename, index=False)
            logger.info(f"Complete data saved to {filename}")
            logger.info(f"Total records saved: {len(self.all_schools_data)}")

        except Exception as e:
            logger.error(f"Failed to save data: {e}")

    def run_phase1_basic_scraping(self, max_states=None, max_districts_per_state=None):
        """Phase 1: Extract basic school data and know more links"""
        try:
            self.setup_driver()
            self.navigate_to_portal()

            # Add extra wait for page to fully load
            logger.info("Waiting for page to fully load...")
            time.sleep(5)

            # Extract all states
            states = self.extract_states_data()

            if not states:
                logger.error("No states extracted. Cannot proceed.")
                return

            if max_states:
                states = states[:max_states]
                logger.info(f"Limited to first {max_states} states for testing")

            total_states = len(states)

            for state_index, state in enumerate(states, 1):
                logger.info(f"Processing state {state_index}/{total_states}: {state['stateName']}")

                try:
                    # Select state
                    self.select_state(state)

                    # Get districts for this state
                    districts = self.extract_districts_data()

                    if max_districts_per_state:
                        districts = districts[:max_districts_per_state]
                        logger.info(f"Limited to first {max_districts_per_state} districts for testing")

                    total_districts = len(districts)

                    for district_index, district in enumerate(districts, 1):
                        logger.info(f"Processing district {district_index}/{total_districts}: {district['districtName']}")

                        try:
                            # Select district
                            self.select_district(district)

                            # Click search
                            if self.click_search_button():
                                # Extract basic schools data with pagination
                                district_schools_data = self.extract_schools_basic_data()

                                # Save district data immediately
                                if district_schools_data:
                                    self.save_district_data_to_csv(
                                        district_schools_data,
                                        state['stateName'],
                                        district['districtName']
                                    )

                                    # Add to overall collection
                                    self.all_schools_data.extend(district_schools_data)

                                    logger.info(f"Completed district {district['districtName']}: {len(district_schools_data)} schools")
                                else:
                                    logger.warning(f"No schools found for {district['districtName']}")

                            # Small delay between districts
                            time.sleep(2)

                        except Exception as e:
                            logger.error(f"Failed to process district {district['districtName']}: {e}")
                            continue

                except Exception as e:
                    logger.error(f"Failed to process state {state['stateName']}: {e}")
                    continue

            # Save final consolidated results
            self.save_data_to_csv()

        except Exception as e:
            logger.error(f"Phase 1 scraping process failed: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Driver closed")

    def run_full_scraping(self, max_states=None, max_districts_per_state=None):
        """Backward compatibility - runs Phase 1 basic scraping"""
        logger.info("Running Phase 1: Basic school data extraction")
        self.run_phase1_basic_scraping(max_states, max_districts_per_state)

# Main execution
if __name__ == "__main__":
    scraper = SchoolDataScraper()

    # For testing, limit to first 2 states and 2 districts per state
    # Remove these limits for full scraping
    scraper.run_full_scraping(max_states=2, max_districts_per_state=2)

    print(f"Scraping completed. Total schools extracted: {len(scraper.all_schools_data)}")
