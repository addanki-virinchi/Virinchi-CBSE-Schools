#!/usr/bin/env python3
"""
School Scraper Phase 2 - Detailed Data Extraction
Clean implementation for extracting detailed school data from individual school pages.
Processes schools with "Know More" links from Phase 1 CSV files.
"""

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
from datetime import datetime
import os
import re
import undetected_chromedriver as uc

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SchoolScraperPhase2:
    def __init__(self):
        self.driver = None
        self.processed_count = 0
        self.success_count = 0
        self.fail_count = 0
        
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
            
            # Initialize driver
            self.driver = uc.Chrome(options=options)
            self.driver.set_page_load_timeout(30)
            logger.info("✅ Chrome driver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup driver: {e}")
            return False
    
    def load_phase1_csv(self, csv_file):
        """Load Phase 1 CSV file and filter schools with links"""
        try:
            df = pd.read_csv(csv_file)
            logger.info(f"📁 Loaded {len(df)} records from {csv_file}")
            
            # Filter schools with valid know_more_links
            schools_with_links = df[
                (df['know_more_link'].notna()) & 
                (df['know_more_link'] != 'N/A') & 
                (df['know_more_link'].str.contains('schooldetail', na=False))
            ].copy()
            
            logger.info(f"🎯 Found {len(schools_with_links)} schools ready for Phase 2")
            return schools_with_links
            
        except Exception as e:
            logger.error(f"❌ Failed to load CSV file: {e}")
            return pd.DataFrame()
    
    def navigate_to_school_page(self, url, max_retries=2):
        """Navigate to school detail page with immediate refresh"""
        for attempt in range(max_retries):
            try:
                logger.info(f"🌐 Navigating to: {url}")
                
                # Clear cookies and navigate
                self.driver.delete_all_cookies()
                self.driver.get(url)
                
                # IMMEDIATELY refresh the page to ensure fresh data
                logger.info("🔄 Refreshing page for fresh data...")
                self.driver.refresh()
                time.sleep(3)  # Wait for refresh to complete
                
                # Wait for page to fully load
                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                
                # Verify we're on the correct page
                current_url = self.driver.current_url
                if "schooldetail" in current_url:
                    logger.info("✅ Successfully navigated to school detail page")
                    return True
                else:
                    logger.warning(f"⚠️ Unexpected URL: {current_url}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    
            except Exception as e:
                logger.error(f"❌ Navigation failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)
                    
        return False
    
    def extract_detailed_data(self, basic_school_data):
        """Extract detailed data from school page"""
        try:
            # Initialize detailed data with basic info
            detailed_data = {
                # Basic info from Phase 1
                'state_name': basic_school_data.get('state_name', 'N/A'),
                'district_name': basic_school_data.get('district_name', 'N/A'),
                'school_name': basic_school_data.get('school_name', 'N/A'),
                'udise_code': basic_school_data.get('udise_code', 'N/A'),
                'know_more_link': basic_school_data.get('know_more_link', 'N/A'),
                
                # Detailed data to extract
                'detail_school_name': 'N/A',
                'academic_year': 'N/A',
                'location_detail': 'N/A',
                'school_category_detail': 'N/A',
                'school_type_detail': 'N/A',
                'class_from': 'N/A',
                'class_to': 'N/A',
                'year_of_establishment': 'N/A',
                'management_detail': 'N/A',
                
                # Student enrollment data
                'total_students': 'N/A',
                'total_boys': 'N/A',
                'total_girls': 'N/A',
                
                # Teacher data
                'total_teachers': 'N/A',
                'male_teachers': 'N/A',
                'female_teachers': 'N/A',
                
                # Additional details
                'affiliation_board': 'N/A',
                'recognition_status': 'N/A'
            }
            
            # Get page source for regex extraction
            page_source = self.driver.page_source
            
            # Extract school name from detail page
            try:
                school_name_selectors = [
                    "h1", "h2.school-name", ".school-title", 
                    "//h1[contains(@class,'school')]", "//h2[contains(@class,'school')]"
                ]
                
                for selector in school_name_selectors:
                    try:
                        if selector.startswith("//"):
                            elem = self.driver.find_element(By.XPATH, selector)
                        else:
                            elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        
                        if elem and elem.text.strip():
                            detailed_data['detail_school_name'] = elem.text.strip()
                            break
                    except:
                        continue
            except:
                pass
            
            # Extract student enrollment data from H3Value elements
            try:
                h3_elements = self.driver.find_elements(By.CSS_SELECTOR, "p.H3Value")
                logger.debug(f"Found {len(h3_elements)} H3Value elements")
                
                # First 3 H3Value elements are typically student data
                if len(h3_elements) >= 3:
                    student_keys = ['total_students', 'total_boys', 'total_girls']
                    for i, key in enumerate(student_keys):
                        try:
                            value = h3_elements[i].text.strip()
                            if value and (value.isdigit() or value == '0'):
                                detailed_data[key] = value
                        except:
                            pass
                
                # Next 3 H3Value elements are typically teacher data
                if len(h3_elements) >= 6:
                    teacher_keys = ['total_teachers', 'male_teachers', 'female_teachers']
                    for i, key in enumerate(teacher_keys):
                        try:
                            value = h3_elements[i + 3].text.strip()
                            if value and (value.isdigit() or value == '0'):
                                detailed_data[key] = value
                        except:
                            pass
                            
            except Exception as e:
                logger.debug(f"H3Value extraction failed: {e}")
            
            # Extract basic details using regex patterns
            try:
                # Academic Year
                academic_year_match = re.search(r'Academic Year[:\s]*<span[^>]*>([^<]+)', page_source)
                if academic_year_match:
                    detailed_data['academic_year'] = academic_year_match.group(1).strip()
                
                # Location
                location_match = re.search(r'Location</p></div><div[^>]*class="blueCol">([^<]+)', page_source)
                if location_match:
                    detailed_data['location_detail'] = location_match.group(1).strip()
                
                # School Category
                category_match = re.search(r'School Category</p></div><div[^>]*class="blueCol">([^<]+)', page_source)
                if category_match:
                    detailed_data['school_category_detail'] = category_match.group(1).strip()
                
                # School Type
                type_match = re.search(r'School Type</p></div><div[^>]*class="blueCol">([^<]+)', page_source)
                if type_match:
                    detailed_data['school_type_detail'] = type_match.group(1).strip()
                
                # Class From/To
                class_from_match = re.search(r'Class From</p></div><div[^>]*class="blueCol">([^<]+)', page_source)
                if class_from_match:
                    detailed_data['class_from'] = class_from_match.group(1).strip()
                
                class_to_match = re.search(r'Class To</p></div><div[^>]*class="blueCol">([^<]+)', page_source)
                if class_to_match:
                    detailed_data['class_to'] = class_to_match.group(1).strip()
                
                # Year of Establishment
                year_match = re.search(r'Year of Establishment</p></div><div[^>]*class="blueCol">([^<]+)', page_source)
                if year_match:
                    detailed_data['year_of_establishment'] = year_match.group(1).strip()
                
            except Exception as e:
                logger.debug(f"Regex extraction failed: {e}")
            
            return detailed_data
            
        except Exception as e:
            logger.error(f"❌ Failed to extract detailed data: {e}")
            return None

    def process_single_school(self, school_data):
        """Process a single school for detailed data extraction"""
        try:
            school_name = school_data.get('school_name', 'Unknown')
            url = school_data.get('know_more_link', '')

            logger.info(f"🏫 Processing: {school_name}")

            # Navigate to school page
            if not self.navigate_to_school_page(url):
                logger.error(f"❌ Failed to navigate to {school_name}")
                self.fail_count += 1
                return None

            # Extract detailed data
            detailed_data = self.extract_detailed_data(school_data)

            if detailed_data:
                # Validate that we got meaningful data
                if (detailed_data['total_students'] != 'N/A' or
                    detailed_data['total_teachers'] != 'N/A' or
                    detailed_data['detail_school_name'] != 'N/A'):

                    logger.info(f"✅ Success: Students={detailed_data['total_students']}, Teachers={detailed_data['total_teachers']}")
                    self.success_count += 1
                    return detailed_data
                else:
                    logger.warning(f"⚠️ No meaningful data extracted for {school_name}")
                    self.fail_count += 1
                    return None
            else:
                logger.error(f"❌ Failed to extract data for {school_name}")
                self.fail_count += 1
                return None

        except Exception as e:
            logger.error(f"❌ Error processing school: {e}")
            self.fail_count += 1
            return None

    def save_detailed_data_to_csv(self, detailed_schools_data, state_name):
        """Save detailed schools data to CSV file"""
        try:
            if not detailed_schools_data:
                logger.warning(f"No detailed data to save for {state_name}")
                return None

            # Create DataFrame
            df = pd.DataFrame(detailed_schools_data)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_state_name = state_name.replace(' ', '_').replace('&', 'AND')
            filename = f"{clean_state_name}_phase2_detailed_{timestamp}.csv"

            # Save to CSV
            df.to_csv(filename, index=False)

            logger.info(f"✅ Saved {len(df)} detailed school records to {filename}")
            return filename

        except Exception as e:
            logger.error(f"❌ Failed to save detailed CSV: {e}")
            return None

    def process_phase1_csv_file(self, csv_file, batch_size=50):
        """Process a Phase 1 CSV file for detailed data extraction"""
        try:
            logger.info(f"\n{'='*80}")
            logger.info(f"🚀 STARTING PHASE 2 PROCESSING")
            logger.info(f"📁 Input file: {csv_file}")
            logger.info(f"{'='*80}")

            # Extract state name from filename
            state_name = "Unknown_State"
            if "_phase1_complete_" in csv_file:
                state_name = csv_file.split("_phase1_complete_")[0]

            # Setup driver
            if not self.setup_driver():
                return False

            # Load Phase 1 data
            schools_to_process = self.load_phase1_csv(csv_file)

            if len(schools_to_process) == 0:
                logger.info("✅ No schools ready for Phase 2 processing")
                self.driver.quit()
                return True

            # Reset counters
            self.processed_count = 0
            self.success_count = 0
            self.fail_count = 0

            detailed_schools_data = []
            total_schools = len(schools_to_process)

            logger.info(f"🎯 Processing {total_schools} schools in batches of {batch_size}")

            # Process schools in batches
            for i in range(0, total_schools, batch_size):
                batch_end = min(i + batch_size, total_schools)
                batch_schools = schools_to_process.iloc[i:batch_end]

                logger.info(f"\n📦 Processing batch {i//batch_size + 1}: Schools {i+1}-{batch_end}")

                for idx, school in batch_schools.iterrows():
                    self.processed_count += 1

                    logger.info(f"\n🔄 [{self.processed_count}/{total_schools}] Processing school...")

                    # Process single school
                    detailed_data = self.process_single_school(school.to_dict())

                    if detailed_data:
                        detailed_schools_data.append(detailed_data)

                    # Brief pause between schools
                    time.sleep(0.5)

                # Longer pause between batches
                if batch_end < total_schools:
                    logger.info(f"⏸️ Batch complete. Pausing before next batch...")
                    time.sleep(2)

            # Save detailed data
            csv_filename = self.save_detailed_data_to_csv(detailed_schools_data, state_name)

            # Cleanup
            self.driver.quit()

            # Final summary
            logger.info(f"\n🎉 PHASE 2 PROCESSING COMPLETE")
            logger.info(f"📊 Total processed: {self.processed_count}")
            logger.info(f"✅ Successful extractions: {self.success_count}")
            logger.info(f"❌ Failed extractions: {self.fail_count}")
            logger.info(f"📁 Output file: {csv_filename}")

            return csv_filename

        except Exception as e:
            logger.error(f"❌ Error in Phase 2 processing: {e}")
            try:
                self.driver.quit()
            except:
                pass
            return False

if __name__ == "__main__":
    scraper = SchoolScraperPhase2()

    print("🚀 SCHOOL SCRAPER PHASE 2 - DETAILED DATA EXTRACTION")
    print("Processes schools with 'Know More' links from Phase 1 CSV files")
    print()

    # Find available Phase 1 CSV files
    available_files = []
    for f in os.listdir('.'):
        if f.endswith('.csv') and 'phase1_complete' in f:
            available_files.append(f)

    if not available_files:
        print("❌ No Phase 1 CSV files found!")
        print("Looking for files with 'phase1_complete' in filename")
    else:
        print("📁 Available Phase 1 files:")
        for i, f in enumerate(available_files, 1):
            print(f"   {i}. {f}")

        try:
            choice = int(input(f"\nSelect file (1-{len(available_files)}): ")) - 1
            if 0 <= choice < len(available_files):
                selected_file = available_files[choice]

                batch_size = input("Enter batch size (default 50): ").strip()
                batch_size = int(batch_size) if batch_size.isdigit() else 50

                result = scraper.process_phase1_csv_file(selected_file, batch_size)

                if result:
                    print(f"\n✅ SUCCESS! Phase 2 complete")
                    print(f"📁 Detailed data saved to: {result}")
                else:
                    print(f"\n❌ FAILED to process {selected_file}")
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
