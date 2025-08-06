#!/usr/bin/env python3
"""
Sequential State Processor - Unified Phase 1 + Phase 2 Workflow
Single entry point for complete state-by-state processing

This script processes states sequentially:
1. Run Phase 1 (basic data extraction) for entire state
2. Immediately run Phase 2 (detailed data extraction) on schools with know_more_links
3. Move to next state only after both phases are complete

Usage: python sequential_process_state.py
"""

import os
import time
import logging
import pandas as pd
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json
import re
import glob

# Google Sheets integration
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError as e:
    GOOGLE_SHEETS_AVAILABLE = False
    gspread = None
    Credentials = None
    logging.warning(f"Google Sheets packages not available: {e}. Install with: pip install gspread google-auth")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Google Sheets Configuration
GOOGLE_SHEETS_ENABLED = True
GOOGLE_SHEET_NAME = "Know your School Database"
SERVICE_ACCOUNT_FILE = "credentials.json"

class GoogleSheetsUploader:
    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self.authenticated = False

    def authenticate(self):
        """Authenticate with Google Sheets using service account"""
        try:
            if not GOOGLE_SHEETS_AVAILABLE:
                logger.warning("⚠️ Google Sheets packages not available")
                return False

            if not os.path.exists(SERVICE_ACCOUNT_FILE):
                logger.error(f"❌ Service account file not found: {SERVICE_ACCOUNT_FILE}")
                return False

            # Define the scope
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]

            # Authenticate using service account
            credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
            self.client = gspread.authorize(credentials)

            # Open the spreadsheet
            self.spreadsheet = self.client.open(GOOGLE_SHEET_NAME)

            self.authenticated = True
            logger.info(f"✅ Successfully authenticated with Google Sheets: {GOOGLE_SHEET_NAME}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to authenticate with Google Sheets: {e}")
            return False

    def create_or_get_worksheet(self, state_name):
        """Create or get worksheet for the state"""
        try:
            if not self.authenticated:
                return None

            # Clean state name for worksheet
            worksheet_name = state_name.replace(' ', '_').replace('&', 'and').upper()

            try:
                # Try to get existing worksheet
                worksheet = self.spreadsheet.worksheet(worksheet_name)
                logger.info(f"📋 Found existing worksheet: {worksheet_name}")
                return worksheet
            except gspread.WorksheetNotFound:
                # Create new worksheet
                worksheet = self.spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=50)
                logger.info(f"📋 Created new worksheet: {worksheet_name}")
                return worksheet

        except Exception as e:
            logger.error(f"❌ Error creating/getting worksheet for {state_name}: {e}")
            return None

    def upload_phase2_data(self, csv_file, state_name):
        """Upload Phase 2 data to Google Sheets"""
        try:
            if not self.authenticated:
                logger.warning("⚠️ Not authenticated with Google Sheets")
                return False

            if not os.path.exists(csv_file):
                logger.error(f"❌ CSV file not found: {csv_file}")
                return False

            # Read CSV data
            df = pd.read_csv(csv_file)
            if len(df) == 0:
                logger.warning(f"⚠️ No data in CSV file: {csv_file}")
                return True  # Not an error, just no data

            # Handle NaN values that cause JSON compliance issues
            logger.info(f"📊 Processing {len(df)} rows for upload...")
            df = df.fillna('N/A')  # Replace NaN with 'N/A'

            # Convert numeric columns to strings to avoid float precision issues
            for col in df.columns:
                if df[col].dtype in ['float64', 'int64']:
                    df[col] = df[col].astype(str)

            # Get or create worksheet
            worksheet = self.create_or_get_worksheet(state_name)
            if not worksheet:
                return False

            # Check if worksheet is empty (add headers)
            if len(worksheet.get_all_values()) == 0:
                # Add headers
                headers = df.columns.tolist()
                worksheet.append_row(headers)
                logger.info(f"📋 Added headers to worksheet: {state_name}")

            # Convert DataFrame to list of lists for upload
            data_rows = df.values.tolist()

            # Ensure all values are strings to avoid JSON issues
            clean_data_rows = []
            for row in data_rows:
                clean_row = [str(cell) if cell is not None else 'N/A' for cell in row]
                clean_data_rows.append(clean_row)

            data_rows = clean_data_rows

            # Upload data in batches to avoid API limits
            batch_size = 100
            total_rows = len(data_rows)

            for i in range(0, total_rows, batch_size):
                batch = data_rows[i:i + batch_size]
                worksheet.append_rows(batch)
                logger.info(f"📤 Uploaded batch {i//batch_size + 1}: {len(batch)} rows to {state_name}")

                # Brief pause to respect API limits
                time.sleep(1)

            logger.info(f"✅ Successfully uploaded {total_rows} rows to Google Sheets: {state_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to upload data to Google Sheets for {state_name}: {e}")
            return False

class SequentialStateProcessor:
    def __init__(self):
        self.driver = None
        self.current_state = None
        self.current_district = None

        # Processing statistics
        self.processed_states = []
        self.failed_states = []
        self.total_schools_phase1 = 0
        self.total_schools_phase2 = 0
        self.successful_extractions = 0
        self.start_time = None

        # State-wise data storage for Phase 1
        self.state_schools_with_links = {}
        self.state_schools_no_links = {}

        # Phase 2 settings
        self.phase2_batch_size = 25  # Smaller batches for sequential processing

        # Google Sheets integration
        self.sheets_uploader = None
        if GOOGLE_SHEETS_ENABLED:
            self.sheets_uploader = GoogleSheetsUploader()
        
    def setup_driver(self, phase="Phase1"):
        """Initialize Chrome browser driver optimized for the specified phase"""
        try:
            logger.info(f"🔧 Setting up Chrome driver for {phase}...")
            
            # Setup Chrome options optimized for each phase
            options = uc.ChromeOptions()
            
            # Core stability options
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-blink-features=AutomationControlled")
            
            # Performance optimizations
            options.add_argument("--disable-images")  # Speed optimization
            options.add_argument("--disable-plugins")
            options.add_argument("--memory-pressure-off")
            options.add_argument("--max_old_space_size=4096")
            
            # Phase-specific optimizations
            if phase == "Phase1":
                # Phase 1: Optimize for pagination and basic extraction
                options.add_argument("--disable-background-timer-throttling")
                options.add_argument("--disable-renderer-backgrounding")
                options.add_argument("--disable-backgrounding-occluded-windows")
                
            # Note: Keep JavaScript enabled for Phase 2 dynamic content
            
            self.driver = uc.Chrome(options=options, version_main=138)
            self.driver.maximize_window()
            
            # Phase-specific timeouts
            if phase == "Phase1":
                self.driver.implicitly_wait(5)
                self.driver.set_page_load_timeout(20)
            else:  # Phase2
                self.driver.implicitly_wait(5)
                self.driver.set_page_load_timeout(25)
            
            logger.info(f"✅ Chrome driver initialized for {phase}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup Chrome driver for {phase}: {e}")
            return False
    
    def close_driver(self):
        """Safely close the Chrome driver"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                logger.info("🔒 Chrome driver closed")
        except Exception as e:
            logger.debug(f"Error closing driver: {e}")
    
    def get_available_states(self):
        """Get list of available states from the portal"""
        try:
            logger.info("🌐 Connecting to UDISE Plus portal to get available states...")
            
            # Setup driver for state extraction
            if not self.setup_driver("Phase1"):
                return []
            
            # Navigate to portal
            if not self.navigate_to_portal():
                return []
            
            # Extract states
            states = self.extract_states_data()
            
            # Close driver after getting states
            self.close_driver()
            
            return states
            
        except Exception as e:
            logger.error(f"❌ Failed to get available states: {e}")
            self.close_driver()
            return []
    
    def navigate_to_portal(self, max_retries=3):
        """Navigate to the UDISE Plus portal and access advance search"""
        for attempt in range(max_retries):
            try:
                logger.info(f"🌐 Navigating to UDISE Plus portal... (attempt {attempt + 1}/{max_retries})")
                self.driver.get("https://udiseplus.gov.in/#/en/home")
                time.sleep(3)

                # Click on Visit Portal
                logger.info("🔍 Looking for Visit Portal button...")
                visit_portal_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Visit Portal')]"))
                )
                visit_portal_btn.click()
                logger.info("✅ Clicked Visit Portal button")
                time.sleep(3)

                # Switch to new tab if opened
                if len(self.driver.window_handles) > 1:
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    logger.info("🔄 Switched to new tab")
                    time.sleep(2)

                # Click on Advance Search
                logger.info("🔍 Looking for Advance Search button...")
                advance_search_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[@id='advanceSearch']"))
                )
                advance_search_btn.click()
                logger.info("✅ Clicked Advance Search button")

                # Wait for page to load
                logger.info("⏳ Waiting for advance search page to load...")
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "select.form-select.select"))
                )
                logger.info("✅ Advance search page loaded successfully")
                return True

            except Exception as e:
                logger.error(f"❌ Failed to navigate to portal (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"⏳ Retrying navigation in 15 seconds...")
                    time.sleep(15)
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
        """Extract all states data from dropdown"""
        try:
            logger.info("🔍 Extracting available states...")

            # Wait for state dropdown
            state_select = WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "select.form-select.select"))
            )
            logger.info("✅ Found state dropdown")

            time.sleep(1)  # Wait for options to populate

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
                            # Parse JSON state data
                            state_data = json.loads(state_value)
                            states.append(state_data)
                            logger.info(f"✅ Added state {i+1}: {state_data['stateName']}")
                        except json.JSONDecodeError:
                            logger.warning(f"⚠️ Failed to parse state data for '{state_text}'")
                            # Create basic state data structure
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
            return []
    
    def process_single_state_complete(self, state_data):
        """Process a single state completely (Phase 1 + Phase 2)"""
        try:
            state_name = state_data['stateName']
            logger.info(f"\n{'='*100}")
            logger.info(f"🏛️ PROCESSING STATE: {state_name}")
            logger.info(f"{'='*100}")
            
            # Phase 1: Extract basic school data for the entire state
            logger.info(f"📋 PHASE 1: Extracting basic school data for {state_name}")
            phase1_success, phase1_file = self.run_phase1_for_state(state_data)
            
            if not phase1_success:
                logger.error(f"❌ Phase 1 failed for {state_name}, skipping Phase 2")
                self.failed_states.append(state_name)
                return False
            
            # Phase 2: Process schools with know_more_links
            logger.info(f"\n🔍 PHASE 2: Processing detailed data for {state_name}")
            phase2_success = self.run_phase2_for_state(state_name, phase1_file)
            
            if phase2_success:
                logger.info(f"✅ COMPLETED: Both phases successful for {state_name}")
                self.processed_states.append(state_name)
                return True
            else:
                logger.warning(f"⚠️ PARTIAL: Phase 1 successful, Phase 2 had issues for {state_name}")
                self.processed_states.append(state_name)  # Still count as processed
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to process state {state_name}: {e}")
            self.failed_states.append(state_name)
            return False
    
    def show_state_selection_menu(self, states):
        """Show interactive state selection menu"""
        print(f"\n🏛️ SEQUENTIAL STATE PROCESSOR")
        print("="*60)
        print("Available processing options:")
        print()
        print("1. Process ALL states sequentially")
        print("2. Process specific states")
        print("3. Test mode (single small state)")
        print("4. Show available states")
        print("5. Exit")
        print()
        
        while True:
            choice = input("Select option (1-5): ").strip()
            
            if choice == "1":
                return states
            elif choice == "2":
                return self.select_specific_states(states)
            elif choice == "3":
                # Find a small state for testing
                test_states = [s for s in states if s['stateName'] in ['ANDAMAN & NICOBAR ISLANDS', 'LAKSHADWEEP', 'CHANDIGARH']]
                if test_states:
                    return [test_states[0]]
                else:
                    return [states[0]]  # Fallback to first state
            elif choice == "4":
                self.show_available_states(states)
                continue
            elif choice == "5":
                return []
            else:
                print("Invalid choice. Please select 1-5.")
    
    def select_specific_states(self, states):
        """Allow user to select specific states"""
        print(f"\n📋 Available states:")
        for i, state in enumerate(states, 1):
            print(f"   {i:2d}. {state['stateName']}")
        
        print(f"\nEnter state numbers (comma-separated) or state names:")
        print(f"Examples: '1,5,10' or 'TAMIL NADU,KERALA'")
        
        selection = input("Your selection: ").strip()
        
        if not selection:
            return []
        
        selected_states = []
        
        # Try parsing as numbers first
        try:
            numbers = [int(x.strip()) for x in selection.split(',')]
            for num in numbers:
                if 1 <= num <= len(states):
                    selected_states.append(states[num - 1])
                else:
                    print(f"⚠️ Invalid state number: {num}")
        except ValueError:
            # Parse as state names
            names = [x.strip().upper() for x in selection.split(',')]
            for name in names:
                found = False
                for state in states:
                    if name in state['stateName'].upper():
                        selected_states.append(state)
                        found = True
                        break
                if not found:
                    print(f"⚠️ State not found: {name}")
        
        if selected_states:
            print(f"\n✅ Selected {len(selected_states)} states:")
            for state in selected_states:
                print(f"   - {state['stateName']}")
        
        return selected_states
    
    def show_available_states(self, states):
        """Display all available states"""
        print(f"\n📋 Available states ({len(states)} total):")
        for i, state in enumerate(states, 1):
            print(f"   {i:2d}. {state['stateName']}")
        print()

    def run_phase1_for_state(self, state_data):
        """Run Phase 1 (basic data extraction) for a single state"""
        try:
            state_name = state_data['stateName']
            logger.info(f"🚀 Starting Phase 1 for {state_name}")

            # Setup driver for Phase 1
            if not self.setup_driver("Phase1"):
                return False, None

            # Navigate to portal
            if not self.navigate_to_portal():
                self.close_driver()
                return False, None

            # Initialize state data storage
            self.state_schools_with_links[state_name] = []
            self.state_schools_no_links[state_name] = []
            self.current_state = state_data

            # Select the state
            if not self.select_state(state_data):
                logger.error(f"Failed to select state: {state_name}")
                self.close_driver()
                return False, None

            # Extract districts for this state
            districts = self.extract_districts_data()
            if not districts:
                logger.warning(f"No districts found for {state_name}")
                # Still save empty data
                output_file = self.save_phase1_state_data(state_name)
                self.close_driver()
                return True, output_file

            logger.info(f"📍 Found {len(districts)} districts in {state_name}")

            # Process all districts in this state
            for i, district in enumerate(districts, 1):
                try:
                    logger.info(f"\n🏘️ Processing district {i}/{len(districts)}: {district['districtName']}")

                    self.current_district = district

                    # Select district and extract schools
                    if self.select_district(district):
                        # Reset filters and click search
                        self.reset_search_filters()

                        if self.click_search_button():
                            # ENHANCEMENT: Set pagination to 100 results per page for efficiency
                            self.set_pagination_to_100()
                            schools_data = self.extract_schools_basic_data()

                            # Categorize schools by know_more_links availability
                            for school in schools_data:
                                if school.get('know_more_link') and school['know_more_link'] != 'N/A':
                                    self.state_schools_with_links[state_name].append(school)
                                else:
                                    self.state_schools_no_links[state_name].append(school)

                            with_links = len(self.state_schools_with_links[state_name])
                            without_links = len(self.state_schools_no_links[state_name])

                            logger.info(f"✅ Completed {district['districtName']}: {len(schools_data)} schools")
                            logger.info(f"   📊 Running totals - With links: {with_links}, Without links: {without_links}")
                        else:
                            logger.warning(f"Failed to search for district: {district['districtName']}")
                    else:
                        logger.warning(f"Failed to select district: {district['districtName']}")

                    # Brief delay between districts
                    time.sleep(0.3)

                except Exception as e:
                    logger.error(f"Error processing district {district['districtName']}: {e}")
                    continue

            # Save Phase 1 data for this state
            output_file = self.save_phase1_state_data(state_name)

            # Update statistics
            total_schools = len(self.state_schools_with_links[state_name]) + len(self.state_schools_no_links[state_name])
            self.total_schools_phase1 += total_schools

            # Show state summary
            with_links_count = len(self.state_schools_with_links[state_name])
            no_links_count = len(self.state_schools_no_links[state_name])

            logger.info(f"\n📊 PHASE 1 SUMMARY - {state_name}:")
            logger.info(f"   🏫 Total schools: {total_schools}")
            logger.info(f"   🔗 Schools with links (Phase 2 ready): {with_links_count}")
            logger.info(f"   📋 Schools without links (reference only): {no_links_count}")
            if total_schools > 0:
                logger.info(f"   📈 Phase 2 coverage: {with_links_count/total_schools*100:.1f}%")

            # Close driver after Phase 1
            self.close_driver()

            return True, output_file

        except Exception as e:
            logger.error(f"❌ Phase 1 failed for {state_name}: {e}")
            self.close_driver()
            return False, None

    def select_state(self, state_data):
        """Select a specific state from the dropdown"""
        try:
            logger.info(f"🔄 Selecting state: {state_data['stateName']}")

            state_select_element = self.driver.find_element(By.CSS_SELECTOR, "select.form-select.select")
            state_select = Select(state_select_element)

            # Try multiple methods to select the state
            success = False

            # Method 1: Try exact JSON match
            try:
                state_value = json.dumps(state_data, separators=(',', ':'))
                state_select.select_by_value(state_value)
                success = True
                logger.info(f"✅ Selected state by exact JSON: {state_data['stateName']}")
            except:
                pass

            # Method 2: Try selecting by visible text
            if not success:
                try:
                    state_select.select_by_visible_text(state_data['stateName'])
                    success = True
                    logger.info(f"✅ Selected state by visible text: {state_data['stateName']}")
                except:
                    pass

            # Method 3: Try finding option by partial text match
            if not success:
                try:
                    options = state_select_element.find_elements(By.TAG_NAME, "option")
                    for option in options:
                        option_text = option.text.strip().upper()
                        state_name = state_data['stateName'].upper()
                        if state_name in option_text or option_text in state_name:
                            option.click()
                            success = True
                            logger.info(f"✅ Selected state by partial match: {state_data['stateName']}")
                            break
                except:
                    pass

            if not success:
                logger.error(f"❌ Failed to select state {state_data['stateName']}")
                return False

            time.sleep(1)  # Wait for districts to load
            return True

        except Exception as e:
            logger.error(f"❌ Failed to select state {state_data['stateName']}: {e}")
            return False

    def extract_districts_data(self):
        """Extract districts data for the currently selected state"""
        try:
            if not self.current_state:
                logger.error("❌ current_state is None")
                return []

            logger.info(f"🔍 Extracting districts for {self.current_state['stateName']}...")
            time.sleep(2)  # Wait for district dropdown to populate

            # Find district dropdown (usually the second select element)
            select_elements = self.driver.find_elements(By.CSS_SELECTOR, "select.form-select.select")

            if len(select_elements) < 2:
                logger.warning("❌ District dropdown not found")
                return []

            district_select = select_elements[1]
            district_options = district_select.find_elements(By.TAG_NAME, "option")[1:]  # Skip "Select District"

            districts_data = []
            for option in district_options:
                district_value = option.get_attribute("value")
                district_text = option.text.strip()

                if district_value and district_text:
                    try:
                        # Try to parse as JSON first
                        district_data = json.loads(district_value)
                        if isinstance(district_data, dict) and 'districtName' in district_data:
                            districts_data.append(district_data)
                            logger.info(f"✅ Found district (JSON): {district_data['districtName']}")
                        else:
                            logger.warning(f"⚠️ Invalid JSON district data: {district_data}")
                    except (json.JSONDecodeError, TypeError, KeyError):
                        # Create simple district data structure
                        district_data = {
                            'districtId': district_value,
                            'districtName': district_text,
                            'stateId': self.current_state.get('stateId', 0),
                            'udiseDistrictCode': district_value
                        }
                        districts_data.append(district_data)
                        logger.info(f"✅ Found district (simple): {district_text}")

            logger.info(f"✅ Extracted {len(districts_data)} districts for {self.current_state['stateName']}")
            return districts_data

        except Exception as e:
            logger.error(f"❌ Failed to extract districts data: {e}")
            return []

    def select_district(self, district_data):
        """Select a specific district from the dropdown"""
        try:
            logger.info(f"🔄 Selecting district: {district_data['districtName']}")
            time.sleep(1)

            select_elements = self.driver.find_elements(By.CSS_SELECTOR, "select.form-select.select")

            if len(select_elements) < 2:
                raise Exception("District dropdown not found")

            district_select_element = select_elements[1]
            district_select = Select(district_select_element)

            # Try multiple methods to select the district
            success = False

            # Method 1: Try selecting by district ID
            try:
                district_id = str(district_data['districtId'])
                district_select.select_by_value(district_id)
                success = True
                logger.info(f"✅ Selected district by ID: {district_data['districtName']}")
            except:
                pass

            # Method 2: Try selecting by visible text
            if not success:
                try:
                    district_select.select_by_visible_text(district_data['districtName'])
                    success = True
                    logger.info(f"✅ Selected district by visible text: {district_data['districtName']}")
                except:
                    pass

            # Method 3: Try partial text match
            if not success:
                try:
                    options = district_select_element.find_elements(By.TAG_NAME, "option")
                    for option in options:
                        option_text = option.text.strip().upper()
                        district_name = district_data['districtName'].upper()
                        if district_name in option_text or option_text in district_name:
                            option.click()
                            success = True
                            logger.info(f"✅ Selected district by partial match: {district_data['districtName']}")
                            break
                except:
                    pass

            if not success:
                logger.error(f"❌ Failed to select district {district_data['districtName']}")
                return False

            time.sleep(1)
            return True

        except Exception as e:
            logger.error(f"❌ Failed to select district {district_data['districtName']}: {e}")
            return False

    def reset_search_filters(self):
        """Reset any search filters to ensure we get all schools for the district"""
        try:
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
                            select_obj = Select(element)
                            if len(select_obj.options) > 0:
                                select_obj.select_by_index(0)
                        elif element.tag_name == 'input' and element.get_attribute('type') == 'checkbox':
                            if element.is_selected():
                                element.click()
                except:
                    continue

            time.sleep(0.5)
            return True

        except Exception as e:
            logger.debug(f"Error resetting search filters: {e}")
            return False

    def click_search_button(self):
        """Click the search button with viewport scrolling"""
        try:
            # Try multiple selectors for the search button
            search_selectors = [
                "button.purpleBtn",
                "//button[contains(text(),'Search')]",
                "//button[contains(@class,'purpleBtn')]",
                "button[class*='purpleBtn']"
            ]

            search_button = None
            for selector in search_selectors:
                try:
                    if selector.startswith("//"):
                        search_button = WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                    else:
                        search_button = WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                    break
                except:
                    continue

            if not search_button:
                logger.error("❌ Search button not found")
                return False

            # Scroll to element and click
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", search_button)
            time.sleep(1)

            try:
                search_button.click()
                logger.info("✅ Clicked search button")
            except:
                # Fallback to JavaScript click
                self.driver.execute_script("arguments[0].click();", search_button)
                logger.info("✅ Clicked search button with JavaScript")

            # Wait for results to load
            time.sleep(2)
            return True

        except Exception as e:
            logger.error(f"❌ Failed to click search button: {e}")
            return False

    def set_pagination_to_100(self):
        """Set pagination to 100 results per page for improved efficiency"""
        try:
            logger.info("🔧 Setting pagination to 100 results per page...")

            # Wait for pagination dropdown to be available
            time.sleep(1)

            # Find the pagination dropdown with the specific selector
            pagination_select = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "select.form-select.w11110"))
            )

            # Create Select object and change to 100 results per page
            from selenium.webdriver.support.ui import Select
            select_obj = Select(pagination_select)

            # Select the option with value="100"
            select_obj.select_by_value("100")

            logger.info("✅ Successfully set pagination to 100 results per page")

            # Brief wait for the page to update with new pagination
            time.sleep(1)
            return True

        except Exception as e:
            logger.debug(f"⚠️ Could not set pagination to 100 (continuing with default): {e}")
            # Continue with default pagination if this fails
            return False

    def extract_schools_basic_data(self):
        """Extract schools data from search results with pagination"""
        try:
            schools_data = []
            page_number = 1
            max_pages = 100  # Safety limit

            while page_number <= max_pages:
                logger.info(f"📄 Processing page {page_number}")

                # Wait for page to load if not first page
                if page_number > 1:
                    time.sleep(1)  # Increased wait time for page transitions

                # Extract schools from current page
                page_schools = self.extract_schools_from_current_page()
                schools_data.extend(page_schools)
                logger.info(f"   ✅ Extracted {len(page_schools)} schools from page {page_number}")

                # Check if we got any schools on this page
                if len(page_schools) == 0:
                    logger.warning(f"   ⚠️ No schools found on page {page_number}, stopping pagination")
                    break

                # Show running total
                logger.info(f"   📊 Running total: {len(schools_data)} schools")

                # Try to go to next page
                logger.debug(f"   🔍 Checking for next page after page {page_number}...")
                next_page_available = self.click_next_page()

                if not next_page_available:
                    logger.info(f"📄 No more pages available after page {page_number}")
                    break

                page_number += 1

                # Longer wait after successful page navigation
                time.sleep(1.5)

            logger.info(f"✅ Pagination complete: {len(schools_data)} total schools extracted across {page_number} pages")
            return schools_data

        except Exception as e:
            logger.error(f"Failed to extract schools data: {e}")
            return []

    def extract_schools_from_current_page(self):
        """Extract schools data from the current page with optimized single scroll"""
        try:
            # Wait for page to stabilize
            time.sleep(1)

            # Single efficient scroll to load all content
            logger.debug("   📜 Loading all schools with single scroll...")
            self.driver.execute_script("""
                // Scroll to bottom to trigger any lazy loading
                window.scrollTo(0, document.body.scrollHeight);
            """)
            time.sleep(1)

            # Scroll back to top for extraction
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)

            # Try multiple selectors to find school elements
            selectors_to_try = [
                ".accordion-body",      # Original accordion format
                ".accordion-item",      # Alternative accordion format
                "[class*='accordion']", # Any accordion class
                ".card-body",          # Card format
                "tbody tr",            # Table rows
                "tr.ng-star-inserted", # Angular table rows
                ".table tr",           # Bootstrap table rows
                "[class*='school']",   # Any school-related class
                ".list-group-item",    # List format
                "[class*='result']"    # Result items
            ]

            school_elements = []
            used_selector = None

            for selector in selectors_to_try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    # Filter out header rows and empty elements
                    valid_elements = []
                    for elem in elements:
                        try:
                            text = elem.text.strip()
                            if text and len(text) > 10:  # Must have substantial content
                                valid_elements.append(elem)
                        except:
                            continue

                    if valid_elements:
                        school_elements = valid_elements
                        used_selector = selector
                        logger.debug(f"   ✅ Found {len(school_elements)} schools with selector: {selector}")
                        break

            if not school_elements:
                logger.warning("   ⚠️ No school elements found with any selector")
                return []

            # Process all schools
            schools_data = []
            logger.debug(f"   🔍 Processing {len(school_elements)} school elements...")

            for i, school_element in enumerate(school_elements):
                try:
                    school_data = self.extract_single_school_data(school_element)
                    if school_data:
                        schools_data.append(school_data)
                        logger.debug(f"   ✅ Extracted school {len(schools_data)}: {school_data.get('school_name', 'Unknown')}")
                    else:
                        logger.debug(f"   ⚠️ No data extracted from element {i+1}")

                except Exception as e:
                    logger.debug(f"   ❌ Error processing school element {i+1}: {e}")
                    continue

            logger.info(f"   📊 Successfully extracted {len(schools_data)} schools using selector: {used_selector}")
            return schools_data

        except Exception as e:
            logger.error(f"Error extracting schools from page: {e}")
            return []

    def extract_single_school_data(self, school_element):
        """Extract data from a single school element"""
        try:
            # Pre-create base data structure
            school_data = {
                'state': self.current_state['stateName'],
                'state_id': self.current_state.get('stateId', ''),
                'district': self.current_district['districtName'],
                'district_id': self.current_district.get('districtId', ''),
                'extraction_date': datetime.now().isoformat()
            }

            # Get element HTML and text for extraction
            element_html = school_element.get_attribute('innerHTML')
            element_text = school_element.text

            # Extract UDISE Code
            udise_match = re.search(r'class="udiseCode"[^>]*>([^<]+)', element_html)
            school_data['udise_code'] = udise_match.group(1).strip() if udise_match else 'N/A'

            # Extract School Name
            name_match = re.search(r'<h4[^>]*class="[^"]*custom-word-break[^"]*"[^>]*>([^<]+)', element_html)
            if not name_match:
                name_match = re.search(r'<h4[^>]*>([^<]+)', element_html)
            school_data['school_name'] = name_match.group(1).strip() if name_match else 'N/A'

            # Extract Know More Link (critical for Phase 2)
            link_match = re.search(r'class="[^"]*blueBtn[^"]*"[^>]*href="([^"]+)"', element_html)
            if link_match:
                relative_link = link_match.group(1)
                if relative_link.startswith("#/"):
                    school_data['know_more_link'] = f"https://kys.udiseplus.gov.in/{relative_link}"
                else:
                    school_data['know_more_link'] = relative_link
            else:
                school_data['know_more_link'] = 'N/A'

            # Extract other basic fields using regex patterns
            field_patterns = {
                'operational_status': r'class="OperationalStatus"[^>]*>([^<]+)',
                'school_category': r'School\s*Category[:\s]*([^\n]+)',
                'school_management': r'School\s*Management[:\s]*([^\n]+)',
                'school_type': r'School\s*Type[:\s]*([^\n]+)',
                'school_location': r'School\s*Location[:\s]*([^\n]+)',
                'address': r'Address[:\s]*([^\n]+)',
                'pin_code': r'PIN\s*Code[:\s]*([^\n]+)'
            }

            for field_name, pattern in field_patterns.items():
                match = re.search(pattern, element_text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip().replace(':', '').strip()
                    school_data[field_name] = value if value else 'N/A'
                else:
                    school_data[field_name] = 'N/A'

            return school_data

        except:
            return None

    def click_next_page(self):
        """Click next page button if available and not disabled using proper selectors"""
        try:
            # Wait for page to stabilize
            time.sleep(1)

            # Use specific selector for next button based on the HTML structure
            # <li class=""><a class="nextBtn">Next</a></li> - enabled
            # <li class="disabled"><a class="nextBtn">Next</a></li> - disabled

            try:
                # Find the next button and its parent li
                next_button = self.driver.find_element(By.CSS_SELECTOR, "a.nextBtn")
                parent_li = next_button.find_element(By.XPATH, "..")

                # Check parent li classes
                parent_classes = parent_li.get_attribute("class") or ""
                button_text = next_button.text.strip()

                logger.info(f"   🔍 Found next button: '{button_text}'")
                logger.info(f"   📋 Parent <li> classes: '{parent_classes}'")

                # Check if parent li has 'disabled' class
                if "disabled" in parent_classes.lower():
                    logger.info("   🛑 Next button is disabled (parent li has 'disabled' class)")
                    return False
                else:
                    logger.info("   ✅ Next button is enabled (parent li does not have 'disabled' class)")

            except Exception as e:
                logger.info(f"   ❌ Could not find next button: {e}")
                return False

            if not next_button.is_displayed():
                logger.info("   ❌ Next button not displayed")
                return False

            # Get current page info for debugging
            try:
                page_info_selectors = [
                    ".pagination-info", ".page-info", "[class*='showing']",
                    "[class*='page']", ".pagination", "[class*='result']"
                ]
                for selector in page_info_selectors:
                    page_info = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if page_info:
                        info_text = page_info[0].text.strip()
                        if info_text and len(info_text) > 5:
                            logger.info(f"   📊 Page info ({selector}): {info_text}")
                            break
            except:
                pass

            # DEBUG: Show pagination HTML structure
            try:
                pagination_container = self.driver.find_elements(By.CSS_SELECTOR, ".pagination, [class*='page'], ul.pagination")
                if pagination_container:
                    container = pagination_container[0]
                    html_snippet = container.get_attribute('outerHTML')[:500]  # First 500 chars
                    logger.info(f"   🔍 Pagination HTML: {html_snippet}...")
            except:
                pass

            # Check if button is disabled - focus on parent <li> class
            is_disabled = False

            # Primary Check: Parent <li> element disabled class (most reliable)
            try:
                parent_li = next_button.find_element(By.XPATH, "..")
                parent_classes = parent_li.get_attribute("class") or ""
                parent_tag = parent_li.tag_name.lower()

                logger.info(f"   🔍 Parent element: <{parent_tag} class='{parent_classes}'>")

                if "disabled" in parent_classes.lower():
                    logger.info(f"   ❌ Parent <li> has disabled class: '{parent_classes}'")
                    is_disabled = True
                else:
                    logger.info(f"   ✅ Parent <li> is NOT disabled: '{parent_classes}'")

            except Exception as e:
                logger.warning(f"   ⚠️ Could not check parent element: {e}")

            # Secondary Check: Button disabled class
            button_classes = next_button.get_attribute("class") or ""
            if "disabled" in button_classes.lower():
                logger.info(f"   ❌ Button has disabled class: '{button_classes}'")
                is_disabled = True

            # Tertiary Check: Disabled attribute
            if next_button.get_attribute("disabled"):
                logger.info("   ❌ Button has disabled attribute")
                is_disabled = True

            # Final Check: Button enabled state
            if not next_button.is_enabled():
                logger.info("   ❌ Button is not enabled")
                is_disabled = True

            if is_disabled:
                logger.info("   🛑 Next button is disabled - no more pages available")
                return False
            else:
                logger.info("   ✅ Next button is enabled - proceeding to click")

            # Click the next button with simple, clean approach
            try:
                logger.info("   🖱️ Clicking next button...")

                # Simple JavaScript click (most reliable for Angular apps)
                self.driver.execute_script("arguments[0].click();", next_button)
                print("clicked next button")

                # Wait for page to change
                time.sleep(3)

                # Verify page actually changed by checking pagination info
                page_changed = False
                try:
                    # Check pagination info for page change
                    page_info = self.driver.find_elements(By.CSS_SELECTOR, ".pagination, [class*='showing']")
                    if page_info:
                        info_text = page_info[0].text.strip()
                        logger.info(f"   📊 Pagination after click: {info_text}")

                        # Check for page 2+ indicators
                        if any(indicator in info_text for indicator in ["101 to", "201 to", "301 to"]):
                            logger.info(f"   ✅ Successfully moved to next page")
                            page_changed = True
                        elif "Showing 1 to" in info_text:
                            logger.warning(f"   ⚠️ Still on page 1 - click may have failed")
                        else:
                            logger.info(f"   📊 Page status unclear: {info_text}")
                except:
                    logger.warning("   ⚠️ Could not check pagination status")

                # If no clear change detected, wait a bit more and check again
                if not page_changed:
                    logger.info("   ⏳ Waiting for page transition to complete...")
                    time.sleep(2)

                    try:
                        final_page_info = self.driver.find_elements(By.CSS_SELECTOR, ".pagination, [class*='showing']")
                        if final_page_info:
                            final_info_text = final_page_info[0].text.strip()
                            if any(indicator in final_info_text for indicator in ["101 to", "201 to", "301 to"]):
                                logger.info(f"   ✅ Page transition completed: {final_info_text}")
                                page_changed = True
                            else:
                                logger.warning(f"   ❌ Page didn't change: {final_info_text}")
                    except:
                        logger.error("   ❌ Could not verify page change")

                    if not page_changed:
                        return False

                logger.info("   ✅ Successfully clicked next button and page changed")
                return True

            except Exception as click_error:
                logger.error(f"   ❌ Failed to click next button: {click_error}")

                # FALLBACK: Try to find and click any pagination element that might work
                logger.info("   🔄 Trying fallback pagination methods...")
                try:
                    # Look for any clickable element with page numbers
                    page_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='page'], .pagination a, .page-link")
                    for link in page_links:
                        link_text = link.text.strip()
                        if link_text.isdigit() and int(link_text) > 1:
                            logger.info(f"   🔄 Trying to click page number: {link_text}")
                            link.click()
                            print(f"clicked page {link_text}")
                            time.sleep(3)
                            return True
                except:
                    pass

                return False

        except Exception as e:
            logger.debug(f"Error in click_next_page: {e}")
            return False

    def save_phase1_state_data(self, state_name):
        """Save Phase 1 data for the state to CSV file"""
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

            # Create filename
            filename = f"{clean_state}_phase1_complete_{timestamp}.csv"

            if all_state_schools:
                df = pd.DataFrame(all_state_schools)

                # Reorder columns to put status columns first
                cols = df.columns.tolist()
                status_cols = ['has_know_more_link', 'phase2_ready']
                other_cols = [col for col in cols if col not in status_cols]
                df = df[status_cols + other_cols]

                df.to_csv(filename, index=False)
            else:
                # Create empty CSV with proper headers
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
                df_empty.to_csv(filename, index=False)

            logger.info(f"✅ Saved Phase 1 data to: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Failed to save Phase 1 data for {state_name}: {e}")
            return None

    def run_phase2_for_state(self, state_name, phase1_file):
        """Run Phase 2 (detailed data extraction) for schools with know_more_links"""
        try:
            logger.info(f"🚀 Starting Phase 2 for {state_name}")

            if not phase1_file or not os.path.exists(phase1_file):
                logger.error(f"Phase 1 file not found: {phase1_file}")
                return False

            # Load Phase 1 data
            df = pd.read_csv(phase1_file)
            logger.info(f"📊 Loaded {len(df)} total records from Phase 1")

            # Filter schools ready for Phase 2
            phase2_schools = self.filter_phase2_ready_schools(df)

            if len(phase2_schools) == 0:
                logger.info("✅ No schools ready for Phase 2 processing")
                return True

            logger.info(f"🎯 Processing {len(phase2_schools)} schools for Phase 2")

            # Setup driver for Phase 2
            if not self.setup_driver("Phase2"):
                return False

            # Process schools in batches and collect all results
            total_batches = (len(phase2_schools) + self.phase2_batch_size - 1) // self.phase2_batch_size
            successful_extractions = 0
            all_phase2_results = []  # Collect all results for single CSV

            for batch_num in range(total_batches):
                start_idx = batch_num * self.phase2_batch_size
                end_idx = min(start_idx + self.phase2_batch_size, len(phase2_schools))

                batch = phase2_schools.iloc[start_idx:end_idx]
                logger.info(f"🔄 Processing batch {batch_num + 1}/{total_batches}: schools {start_idx + 1}-{end_idx}")

                # Process batch and collect results
                batch_results, batch_success = self.process_phase2_batch_consolidated(batch, state_name, batch_num + 1)
                successful_extractions += batch_success
                all_phase2_results.extend(batch_results)  # Add to consolidated results

                # Brief pause between batches
                time.sleep(1)

            # Save all Phase 2 results in a single consolidated CSV file
            if all_phase2_results:
                csv_filename = self.save_phase2_consolidated_results(all_phase2_results, state_name)

                # Upload to Google Sheets if enabled
                if GOOGLE_SHEETS_ENABLED and csv_filename:
                    self.upload_to_google_sheets(csv_filename, state_name)

            # Close driver after Phase 2
            self.close_driver()

            # Update statistics
            self.total_schools_phase2 += len(phase2_schools)
            self.successful_extractions += successful_extractions

            success_rate = (successful_extractions / len(phase2_schools)) * 100 if len(phase2_schools) > 0 else 0

            logger.info(f"\n📊 PHASE 2 SUMMARY - {state_name}:")
            logger.info(f"   🏫 Schools processed: {len(phase2_schools)}")
            logger.info(f"   ✅ Successful extractions: {successful_extractions}")
            logger.info(f"   📈 Success rate: {success_rate:.1f}%")

            return success_rate >= 50  # Consider successful if at least 50% success rate

        except Exception as e:
            logger.error(f"❌ Phase 2 failed for {state_name}: {e}")
            self.close_driver()
            return False

    def filter_phase2_ready_schools(self, df):
        """Filter schools that are ready for Phase 2 processing"""
        try:
            # Check for new consolidated format
            if 'phase2_ready' in df.columns:
                phase2_schools = df[df['phase2_ready'] == True].copy()
                logger.info(f"   📊 Found {len(phase2_schools)} Phase 2 ready schools (new format)")
            elif 'has_know_more_link' in df.columns:
                phase2_schools = df[df['has_know_more_link'] == True].copy()
                logger.info(f"   📊 Found {len(phase2_schools)} schools with know_more_links")
            else:
                # Legacy format
                phase2_schools = df[df['know_more_link'].notna() & (df['know_more_link'] != 'N/A')].copy()
                logger.info(f"   📊 Found {len(phase2_schools)} schools with valid know_more_links (legacy format)")

            return phase2_schools

        except Exception as e:
            logger.error(f"❌ Error filtering Phase 2 ready schools: {e}")
            return pd.DataFrame()

    def process_phase2_batch(self, batch, state_name, batch_num):
        """Process a batch of schools for Phase 2"""
        try:
            batch_results = []
            successful_count = 0

            for idx, school in batch.iterrows():
                try:
                    logger.info(f"   🔍 Processing school {idx + 1}: {school.get('school_name', 'Unknown')}")

                    # Extract detailed data
                    extracted_data = self.extract_phase2_data(school['know_more_link'])

                    if extracted_data and extracted_data.get('extraction_status') in ['SUCCESS', 'PARTIAL']:
                        # Combine original and extracted data
                        combined_data = school.to_dict()
                        combined_data.update(extracted_data)
                        batch_results.append(combined_data)
                        successful_count += 1

                        logger.info(f"   ✅ Success: Students={extracted_data.get('total_students', 'N/A')}, Teachers={extracted_data.get('total_teachers', 'N/A')}")
                    else:
                        logger.warning(f"   ⚠️ Failed to extract detailed data")

                    # Brief pause between schools
                    time.sleep(0.5)

                except Exception as e:
                    logger.warning(f"   ❌ Error processing school: {e}")
                    continue

            # Save batch results
            if batch_results:
                self.save_phase2_batch_results(batch_results, state_name, batch_num)

            logger.info(f"   📊 Batch {batch_num} completed: {successful_count}/{len(batch)} successful")
            return successful_count

        except Exception as e:
            logger.error(f"❌ Error processing Phase 2 batch: {e}")
            return 0

    def process_phase2_batch_consolidated(self, batch, state_name, batch_num):
        """Process a batch of schools for Phase 2 and return results for consolidated saving"""
        try:
            batch_results = []
            successful_count = 0

            for idx, school in batch.iterrows():
                try:
                    logger.info(f"   🔍 Processing school {idx + 1}: {school.get('school_name', 'Unknown')}")

                    # Extract detailed data
                    extracted_data = self.extract_phase2_data(school['know_more_link'])

                    if extracted_data and extracted_data.get('extraction_status') in ['SUCCESS', 'PARTIAL']:
                        # Combine original and extracted data
                        combined_data = school.to_dict()
                        combined_data.update(extracted_data)
                        batch_results.append(combined_data)
                        successful_count += 1

                        logger.info(f"   ✅ Success: Students={extracted_data.get('total_students', 'N/A')}, Teachers={extracted_data.get('total_teachers', 'N/A')}")
                    else:
                        logger.warning(f"   ⚠️ Failed to extract detailed data")

                    # Brief pause between schools
                    time.sleep(0.5)

                except Exception as e:
                    logger.warning(f"   ❌ Error processing school: {e}")
                    continue

            logger.info(f"   📊 Batch {batch_num} completed: {successful_count}/{len(batch)} successful")
            return batch_results, successful_count

        except Exception as e:
            logger.error(f"❌ Error processing Phase 2 batch: {e}")
            return [], 0

    def save_phase2_consolidated_results(self, all_results, state_name):
        """Save all Phase 2 results in a single consolidated CSV file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_state = state_name.replace(' ', '_').replace('&', 'and').replace('/', '_').upper()

            # Create consolidated filename similar to Phase 1
            filename = f"{clean_state}_phase2_complete_{timestamp}.csv"

            if all_results:
                df = pd.DataFrame(all_results)
                df.to_csv(filename, index=False)
                logger.info(f"✅ Saved consolidated Phase 2 data to: {filename}")
                logger.info(f"   💾 Total records: {len(all_results)}")
            else:
                # Create empty CSV with proper headers if no results
                empty_data = {
                    'has_know_more_link': [],
                    'phase2_ready': [],
                    'state': [],
                    'district': [],
                    'school_name': [],
                    'detail_school_name': [],
                    'total_students': [],
                    'total_teachers': [],
                    'affiliation_board_sec': [],
                    'affiliation_board_hsec': [],
                    'extraction_status': []
                }
                df_empty = pd.DataFrame(empty_data)
                df_empty.to_csv(filename, index=False)
                logger.info(f"✅ Created empty Phase 2 file: {filename}")

            return filename  # Return filename for Google Sheets upload

        except Exception as e:
            logger.error(f"❌ Error saving consolidated Phase 2 data for {state_name}: {e}")
            return None

    def upload_to_google_sheets(self, csv_filename, state_name):
        """Upload Phase 2 data to Google Sheets"""
        try:
            if not self.sheets_uploader:
                logger.warning("⚠️ Google Sheets uploader not initialized")
                return False

            # Authenticate if not already done
            if not self.sheets_uploader.authenticated:
                logger.info("🔐 Authenticating with Google Sheets...")
                if not self.sheets_uploader.authenticate():
                    logger.error("❌ Failed to authenticate with Google Sheets")
                    return False

            # Upload data
            logger.info(f"📤 Uploading {state_name} data to Google Sheets...")
            success = self.sheets_uploader.upload_phase2_data(csv_filename, state_name)

            if success:
                logger.info(f"✅ Successfully uploaded {state_name} to Google Sheets")
            else:
                logger.error(f"❌ Failed to upload {state_name} to Google Sheets")

            return success

        except Exception as e:
            logger.error(f"❌ Error uploading to Google Sheets for {state_name}: {e}")
            return False

    def extract_phase2_data(self, url, max_retries=2):
        """Extract comprehensive data from school detail page with immediate browser refresh"""
        for attempt in range(max_retries):
            try:
                logger.debug(f"   🌐 Navigating to: {url}")

                # IMMEDIATE BROWSER REFRESH as requested
                try:
                    # Step 1: Navigate to the URL
                    self.driver.get(url)

                    # Step 2: IMMEDIATE REFRESH
                    logger.debug(f"   🔄 Performing IMMEDIATE browser refresh...")
                    self.driver.refresh()

                    # Step 3: Wait for refresh to complete
                    time.sleep(3)

                    # Step 4: Verify page is loaded
                    WebDriverWait(self.driver, 10).until(
                        lambda driver: driver.execute_script("return document.readyState") == "complete"
                    )

                    time.sleep(2)  # Additional wait for dynamic content

                except Exception as e:
                    logger.debug(f"   ❌ Navigation/refresh error: {e}")
                    if attempt < max_retries - 1:
                        continue
                    return None

                # Initialize comprehensive data structure
                data = {
                    'detail_school_name': 'N/A',
                    'source_url': url,
                    'extraction_timestamp': datetime.now().isoformat(),

                    # Basic Details from .innerPad div with .schoolInfoCol elements
                    'academic_year': 'N/A',
                    'location': 'N/A',
                    'school_category': 'N/A',
                    'class_from': 'N/A',
                    'class_to': 'N/A',
                    'class_range': 'N/A',
                    'school_type': 'N/A',
                    'year_of_establishment': 'N/A',
                    'affiliation_board_sec': 'N/A',
                    'affiliation_board_hsec': 'N/A',

                    # Student Enrollment from .bg-white div with .H3Value elements
                    'total_students': 'N/A',
                    'total_boys': 'N/A',
                    'total_girls': 'N/A',

                    # Teacher data from similar HTML structures
                    'total_teachers': 'N/A',
                    'male_teachers': 'N/A',
                    'female_teachers': 'N/A'
                }

                # Get page content
                page_text = self.driver.page_source

                # EXTRACT DATA FROM SPECIFIC HTML STRUCTURES

                # 1. Basic Details from .innerPad div with .schoolInfoCol elements
                try:
                    basic_details_elements = self.driver.find_elements(By.CSS_SELECTOR, ".innerPad .schoolInfoCol")
                    if basic_details_elements:
                        for element in basic_details_elements:
                            try:
                                element_text = element.text.strip()
                                if "Academic Year" in element_text:
                                    data['academic_year'] = self.extract_value_from_element_text(element_text, "Academic Year")
                                elif "Location" in element_text:
                                    data['location'] = self.extract_value_from_element_text(element_text, "Location")
                                elif "School Category" in element_text:
                                    data['school_category'] = self.extract_value_from_element_text(element_text, "School Category")
                                elif "School Type" in element_text:
                                    data['school_type'] = self.extract_value_from_element_text(element_text, "School Type")
                            except:
                                continue
                except:
                    pass

                # ENHANCEMENT: Extract Affiliation Board fields from specific HTML structure
                try:
                    # Extract Affiliation Board Sec. - targeting the exact structure
                    # <div class="schoolInfoCol"><div class="title"><p class="fw-600">Affiliation Board Sec.</p></div><div class="blueCol"><span>1-CBSE</span></div></div>
                    affiliation_sec_elements = self.driver.find_elements(By.XPATH,
                        "//div[contains(@class,'schoolInfoCol')]//div[@class='title']/p[@class='fw-600' and contains(text(), 'Affiliation Board Sec.')]/../../div[contains(@class,'blueCol')]//span")
                    if affiliation_sec_elements:
                        for element in affiliation_sec_elements:
                            try:
                                value = element.text.strip()
                                if value and value.upper() not in ['N/A', 'NA', '']:
                                    data['affiliation_board_sec'] = value
                                    logger.debug(f"   Found Affiliation Board Sec: {value}")
                                    break
                            except:
                                continue

                    # Extract Affiliation Board HSec. - targeting the exact structure
                    affiliation_hsec_elements = self.driver.find_elements(By.XPATH,
                        "//div[contains(@class,'schoolInfoCol')]//div[@class='title']/p[@class='fw-600' and contains(text(), 'Affiliation Board HSec.')]/../../div[contains(@class,'blueCol')]//span")
                    if affiliation_hsec_elements:
                        for element in affiliation_hsec_elements:
                            try:
                                value = element.text.strip()
                                if value and value.upper() not in ['N/A', 'NA', '']:
                                    data['affiliation_board_hsec'] = value
                                    logger.debug(f"   Found Affiliation Board HSec: {value}")
                                    break
                            except:
                                continue

                    # Fallback: Try alternative extraction methods for affiliation boards
                    if data['affiliation_board_sec'] == 'N/A' or data['affiliation_board_hsec'] == 'N/A':
                        # Try regex patterns on page text to catch formats like "1-CBSE" or "NA"
                        if data['affiliation_board_sec'] == 'N/A':
                            # Look for patterns like: Affiliation Board Sec.</p></div><div class="blueCol"><span>1-CBSE</span>
                            sec_patterns = [
                                r'Affiliation Board Sec\.[^>]*>[^<]*</[^>]*>[^<]*<[^>]*>[^<]*<[^>]*>([^<]+)',
                                r'Affiliation Board Sec\.[:\s]*([^\n<]+)',
                                r'Affiliation Board Sec\.</p></div><div[^>]*><span[^>]*>([^<]+)</span>'
                            ]
                            for pattern in sec_patterns:
                                sec_match = re.search(pattern, page_text, re.IGNORECASE)
                                if sec_match:
                                    value = sec_match.group(1).strip()
                                    if value and value.upper() not in ['N/A', 'NA', '']:
                                        data['affiliation_board_sec'] = value
                                        logger.debug(f"   Found Affiliation Board Sec (regex): {value}")
                                        break

                        if data['affiliation_board_hsec'] == 'N/A':
                            # Look for patterns like: Affiliation Board HSec.</p></div><div class="blueCol"><span>NA</span>
                            hsec_patterns = [
                                r'Affiliation Board HSec\.[^>]*>[^<]*</[^>]*>[^<]*<[^>]*>[^<]*<[^>]*>([^<]+)',
                                r'Affiliation Board HSec\.[:\s]*([^\n<]+)',
                                r'Affiliation Board HSec\.</p></div><div[^>]*><span[^>]*>([^<]+)</span>'
                            ]
                            for pattern in hsec_patterns:
                                hsec_match = re.search(pattern, page_text, re.IGNORECASE)
                                if hsec_match:
                                    value = hsec_match.group(1).strip()
                                    if value and value.upper() not in ['N/A', 'NA', '']:
                                        data['affiliation_board_hsec'] = value
                                        logger.debug(f"   Found Affiliation Board HSec (regex): {value}")
                                        break

                except Exception as e:
                    logger.debug(f"   Error extracting affiliation board data: {e}")

                # 2. Student Enrollment from .bg-white div with .H3Value elements
                try:
                    h3_value_elements = self.driver.find_elements(By.CSS_SELECTOR, ".bg-white .H3Value")
                    if h3_value_elements:
                        for element in h3_value_elements:
                            try:
                                parent = element.find_element(By.XPATH, "..")
                                parent_text = parent.text.strip().lower()
                                value = element.text.strip()

                                if value.isdigit():
                                    if "total students" in parent_text:
                                        data['total_students'] = value
                                    elif "boys" in parent_text and "total" not in parent_text:
                                        data['total_boys'] = value
                                    elif "girls" in parent_text:
                                        data['total_girls'] = value
                            except:
                                continue
                except:
                    pass

                # 3. Teacher data from similar HTML structures
                try:
                    all_h3_elements = self.driver.find_elements(By.CSS_SELECTOR, ".H3Value")
                    for element in all_h3_elements:
                        try:
                            parent = element.find_element(By.XPATH, "..")
                            parent_text = parent.text.strip().lower()
                            value = element.text.strip()

                            if value.isdigit():
                                if "total teachers" in parent_text:
                                    data['total_teachers'] = value
                                elif "male" in parent_text and ("teacher" in parent_text or data['total_teachers'] != 'N/A'):
                                    data['male_teachers'] = value
                                elif "female" in parent_text and ("teacher" in parent_text or data['total_teachers'] != 'N/A'):
                                    data['female_teachers'] = value
                        except:
                            continue
                except:
                    pass

                # 4. School Name extraction
                try:
                    page_title = self.driver.title
                    if page_title and page_title != "Know Your School":
                        data['detail_school_name'] = page_title.replace("Know Your School", "").strip()

                    if data['detail_school_name'] == 'N/A':
                        # Try to find from page elements
                        name_elements = self.driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3")
                        for element in name_elements:
                            text = element.text.strip()
                            if text and len(text) > 5 and len(text) < 200:
                                if not any(skip in text.lower() for skip in ['know your school', 'udise', 'dashboard']):
                                    data['detail_school_name'] = text
                                    break
                except:
                    pass

                # Validation and status
                critical_fields = 0
                if data['total_students'] != 'N/A':
                    critical_fields += 1
                if data['total_teachers'] != 'N/A':
                    critical_fields += 1

                data['extraction_status'] = 'SUCCESS' if critical_fields >= 2 else 'PARTIAL' if critical_fields >= 1 else 'FAILED'
                data['critical_fields_extracted'] = critical_fields

                return data

            except Exception as e:
                logger.debug(f"   ⚠️ Failed to extract data (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    return None

        return None

    def extract_value_from_element_text(self, element_text, field_name):
        """Helper method to extract value from element text"""
        try:
            lines = element_text.split('\n')
            for i, line in enumerate(lines):
                if field_name.lower() in line.lower():
                    if ':' in line:
                        value = line.split(':', 1)[1].strip()
                        if value:
                            return value
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and not any(keyword in next_line.lower() for keyword in ['class', 'school', 'year', 'type', 'category']):
                            return next_line
            return 'N/A'
        except:
            return 'N/A'

    def save_phase2_batch_results(self, results, state_name, batch_num):
        """Save Phase 2 batch results to CSV"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_state = state_name.replace(' ', '_').replace('&', 'and').replace('/', '_').upper()

            filename = f"{clean_state}_phase2_batch{batch_num}_{timestamp}.csv"

            df = pd.DataFrame(results)
            df.to_csv(filename, index=False)

            logger.info(f"   💾 Saved {len(results)} records to: {filename}")

        except Exception as e:
            logger.error(f"❌ Error saving Phase 2 batch results: {e}")

    def run_sequential_processing(self):
        """Main method to run sequential state processing"""
        try:
            self.start_time = time.time()

            logger.info("🚀 SEQUENTIAL STATE PROCESSOR")
            logger.info("="*80)
            logger.info("Unified Phase 1 + Phase 2 workflow")
            logger.info("Processing states sequentially with complete Phase 1 + Phase 2 for each state")
            logger.info("="*80)

            # Get available states
            logger.info("📋 Getting available states from UDISE Plus portal...")
            states = self.get_available_states()

            if not states:
                logger.error("❌ No states available. Cannot proceed.")
                return

            logger.info(f"✅ Found {len(states)} available states")

            # Show state selection menu
            selected_states = self.show_state_selection_menu(states)

            if not selected_states:
                logger.info("👋 No states selected. Exiting.")
                return

            logger.info(f"\n🎯 Starting sequential processing of {len(selected_states)} states")
            logger.info("Each state will be completely processed (Phase 1 + Phase 2) before moving to the next")

            # Process each state sequentially
            for i, state in enumerate(selected_states, 1):
                try:
                    logger.info(f"\n{'='*100}")
                    logger.info(f"🏛️ PROCESSING STATE {i}/{len(selected_states)}: {state['stateName']}")
                    logger.info(f"{'='*100}")

                    state_start_time = time.time()

                    # Process state completely (Phase 1 + Phase 2)
                    success = self.process_single_state_complete(state)

                    state_time = time.time() - state_start_time

                    if success:
                        logger.info(f"✅ COMPLETED {state['stateName']} in {state_time:.1f} seconds")
                    else:
                        logger.error(f"❌ FAILED {state['stateName']} after {state_time:.1f} seconds")

                    # Brief pause between states
                    if i < len(selected_states):
                        logger.info("⏳ Brief pause before next state...")
                        time.sleep(3)

                except Exception as e:
                    logger.error(f"❌ Critical error processing {state['stateName']}: {e}")
                    continue

            # Show final summary
            self.show_final_summary()

        except Exception as e:
            logger.error(f"❌ Critical error in sequential processing: {e}")
        finally:
            self.close_driver()

    def show_final_summary(self):
        """Show final processing summary"""
        try:
            total_time = time.time() - self.start_time if self.start_time else 0

            logger.info(f"\n{'='*100}")
            logger.info("🎯 SEQUENTIAL PROCESSING COMPLETED")
            logger.info(f"{'='*100}")

            logger.info(f"⏱️ TIMING:")
            logger.info(f"   Total processing time: {total_time/60:.1f} minutes")

            logger.info(f"\n📊 OVERALL STATISTICS:")
            logger.info(f"   🏛️ States successfully processed: {len(self.processed_states)}")
            logger.info(f"   ❌ States failed: {len(self.failed_states)}")
            logger.info(f"   🏫 Total schools Phase 1: {self.total_schools_phase1}")
            logger.info(f"   🔍 Total schools Phase 2: {self.total_schools_phase2}")
            logger.info(f"   ✅ Successful Phase 2 extractions: {self.successful_extractions}")

            if self.total_schools_phase2 > 0:
                success_rate = (self.successful_extractions / self.total_schools_phase2) * 100
                logger.info(f"   📈 Phase 2 success rate: {success_rate:.1f}%")

            if self.processed_states:
                logger.info(f"\n✅ SUCCESSFULLY PROCESSED STATES:")
                for state in self.processed_states:
                    logger.info(f"   - {state}")

            if self.failed_states:
                logger.info(f"\n❌ FAILED STATES:")
                for state in self.failed_states:
                    logger.info(f"   - {state}")

            logger.info(f"\n📁 OUTPUT FILES:")
            logger.info(f"   Phase 1: *_phase1_complete_*.csv")
            logger.info(f"   Phase 2: *_phase2_batch*_*.csv")

            logger.info(f"\n🎉 Sequential processing complete!")
            logger.info(f"{'='*100}")

        except Exception as e:
            logger.error(f"Error showing final summary: {e}")

def main():
    """Main function"""
    print("🚀 SEQUENTIAL STATE PROCESSOR")
    print("Unified Phase 1 + Phase 2 workflow for complete state processing")
    print("Each state is fully processed (both phases) before moving to the next")
    print()

    try:
        processor = SequentialStateProcessor()
        processor.run_sequential_processing()
    except KeyboardInterrupt:
        print("\n⚠️ Processing interrupted by user")
        print("Any completed states have been saved")
    except Exception as e:
        print(f"❌ Critical error: {e}")
        print("Please check the logs above for details")

if __name__ == "__main__":
    main()
