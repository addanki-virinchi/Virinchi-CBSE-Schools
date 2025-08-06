#!/usr/bin/env python3
"""
Phase 2 Focused Processor - Extracts ONLY specific fields for improved speed and reliability
Focuses on: Student Data, Teacher Data, Affiliation Board Sec, Affiliation Board HSec
"""

import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging
from datetime import datetime
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FocusedPhase2Processor:
    def __init__(self):
        self.driver = None
        self.processed_count = 0
        self.success_count = 0
        self.fail_count = 0
        self.extracted_signatures = set()  # For duplicate detection
        
    def setup_driver(self):
        """Initialize Chrome browser driver with optimized settings"""
        try:
            # Setup Chrome options
            options = uc.ChromeOptions()

            # Optimize for speed and stability
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-blink-features=AutomationControlled")

            self.driver = uc.Chrome(options=options)
            self.driver.maximize_window()
            self.driver.implicitly_wait(5)
            self.driver.set_page_load_timeout(20)

            logger.info("✅ Chrome browser driver initialized for focused extraction")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Chrome driver: {e}")
            logger.error("Please ensure Chrome browser is installed")
            raise
    
    def navigate_and_extract(self, school_url, school_name, expected_id):
        """Navigate to school and extract ONLY the 4 focused data categories"""
        max_attempts = 2
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"🌐 Attempt {attempt + 1}: {school_name} (ID: {expected_id})")
                
                # Clear browser state for fresh navigation
                if attempt > 0:
                    self.driver.delete_all_cookies()
                    time.sleep(1)
                
                # Navigate to school page
                self.driver.get(school_url)
                
                # Wait for page load
                initial_wait = 5 + (attempt * 2)  # 5s, 7s for retries
                time.sleep(initial_wait)
                
                # Verify navigation success
                current_url = self.driver.current_url
                if expected_id not in current_url or "schooldetail" not in current_url:
                    logger.warning(f"⚠️ Navigation issue: {current_url}")
                    if attempt < max_attempts - 1:
                        continue
                    return None
                
                # Wait for content to load
                try:
                    WebDriverWait(self.driver, 12).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "p.H3Value"))
                    )
                    time.sleep(3)  # Additional stabilization
                except TimeoutException:
                    logger.warning(f"⚠️ Content loading timeout")
                    if attempt < max_attempts - 1:
                        continue
                    return None
                
                # Extract comprehensive data including school name
                data = self.extract_comprehensive_data()

                # Verify data quality
                if self.is_valid_comprehensive_data(data):
                    signature = self.create_comprehensive_signature(data)
                    
                    # Check for duplicates
                    if signature in self.extracted_signatures:
                        logger.warning(f"⚠️ Duplicate data detected for {school_name}")
                        if attempt < max_attempts - 1:
                            logger.info(f"🔄 Refreshing and retrying...")
                            self.driver.refresh()
                            time.sleep(4)
                            continue
                        else:
                            return None
                    
                    # Success - add to extracted signatures
                    self.extracted_signatures.add(signature)
                    logger.info(f"✅ Success: Students={data['total_students']}, Teachers={data['total_teachers']}")
                    return data
                else:
                    logger.warning(f"⚠️ Invalid focused data extracted")
                    if attempt < max_attempts - 1:
                        continue
                
            except Exception as e:
                logger.error(f"❌ Extraction error (attempt {attempt + 1}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    continue
        
        return None
    
    def extract_comprehensive_data(self):
        """Extract ALL comprehensive data fields including school name from detail page"""
        data = {
            # School Name (from detail page HTML)
            'detail_school_name': 'N/A',

            # Student Data
            'total_students': 'N/A',
            'total_boys': 'N/A',
            'total_girls': 'N/A',

            # Teacher Data
            'total_teachers': 'N/A',
            'male_teachers': 'N/A',
            'female_teachers': 'N/A',

            # Basic Details (Comprehensive)
            'location_detail': 'N/A',
            'school_category_detail': 'N/A',
            'class_from': 'N/A',
            'class_to': 'N/A',
            'school_type_detail': 'N/A',
            'year_of_establishment': 'N/A',
            'national_management': 'N/A',
            'state_management': 'N/A',
            'affiliation_board_sec': 'N/A',
            'affiliation_board_hsec': 'N/A',

            # Additional Details
            'academic_year_detail': 'N/A',
            'school_code': 'N/A',
            'village_name': 'N/A',
            'cluster_name': 'N/A',
            'block_name': 'N/A',
            'district_name': 'N/A',
            'pin_code_detail': 'N/A'
        }
        
        try:
            # STEP 1: Extract School Name from detail page
            try:
                school_name_element = self.driver.find_element(By.CSS_SELECTOR, "h3.custom-word-break.schoolNameCSS.mb-2")
                detail_school_name = school_name_element.text.strip()
                if detail_school_name:
                    data['detail_school_name'] = detail_school_name
                    logger.info(f"🏫 School name: {detail_school_name}")
            except Exception as e:
                logger.debug(f"School name extraction failed: {e}")
                # Try alternative selectors
                try:
                    alt_name_element = self.driver.find_element(By.CSS_SELECTOR, "h3.schoolNameCSS")
                    detail_school_name = alt_name_element.text.strip()
                    if detail_school_name:
                        data['detail_school_name'] = detail_school_name
                        logger.info(f"🏫 School name (alt): {detail_school_name}")
                except:
                    logger.debug("Alternative school name extraction also failed")

            # STEP 2: Extract Student and Teacher Data from H3Value elements
            h3_elements = self.driver.find_elements(By.CSS_SELECTOR, "p.H3Value")
            logger.info(f"📊 Found {len(h3_elements)} H3Value elements")

            # Extract student data (first 3 H3Value elements)
            if len(h3_elements) >= 3:
                for i, key in enumerate(['total_students', 'total_boys', 'total_girls']):
                    value = h3_elements[i].text.strip()
                    if value and (value.isdigit() or value == '0'):
                        data[key] = value
                        logger.debug(f"Student data - {key}: {value}")

            # Extract teacher data (next 3 H3Value elements)
            if len(h3_elements) >= 6:
                for i, key in enumerate(['total_teachers', 'male_teachers', 'female_teachers']):
                    value = h3_elements[i + 3].text.strip()
                    if value and (value.isdigit() or value == '0'):
                        data[key] = value
                        logger.debug(f"Teacher data - {key}: {value}")

            # STEP 3: Extract Comprehensive Basic Details
            try:
                basic_section = self.driver.find_element(By.XPATH, "//h2[contains(text(), 'Basic Details')]/parent::*")

                # Extract all basic details using blueCol elements
                basic_fields_map = {
                    'Location': 'location_detail',
                    'School Category': 'school_category_detail',
                    'Class From': 'class_from',
                    'Class To': 'class_to',
                    'School Type': 'school_type_detail',
                    'Year of Establishment': 'year_of_establishment',
                    'National Management': 'national_management',
                    'State Management': 'state_management',
                    'Affiliation Board Sec.': 'affiliation_board_sec',
                    'Affiliation Board HSec.': 'affiliation_board_hsec'
                }

                for field_text, field_key in basic_fields_map.items():
                    try:
                        field_elem = basic_section.find_element(By.XPATH, f".//p[contains(text(), '{field_text}')]/../../following-sibling::div[@class='blueCol']")
                        field_value = field_elem.text.strip()
                        if field_value and field_value not in ['NA', 'N/A', '']:
                            data[field_key] = field_value
                            logger.debug(f"{field_text}: {field_value}")
                    except:
                        logger.debug(f"{field_text}: Not found")
                        continue

            except Exception as e:
                logger.debug(f"Basic Details section not found: {e}")

            # STEP 4: Extract Additional Details (if available)
            try:
                # Look for additional information sections
                additional_fields = {
                    'Academic Year': 'academic_year_detail',
                    'School Code': 'school_code',
                    'Village': 'village_name',
                    'Cluster': 'cluster_name',
                    'Block': 'block_name',
                    'District': 'district_name',
                    'PIN Code': 'pin_code_detail'
                }

                for field_text, field_key in additional_fields.items():
                    try:
                        # Try multiple possible selectors
                        field_elem = None
                        selectors = [
                            f"//span[contains(text(), '{field_text}')]/following-sibling::span",
                            f"//p[contains(text(), '{field_text}')]/following-sibling::p",
                            f"//div[contains(text(), '{field_text}')]/following-sibling::div"
                        ]

                        for selector in selectors:
                            try:
                                field_elem = self.driver.find_element(By.XPATH, selector)
                                break
                            except:
                                continue

                        if field_elem:
                            field_value = field_elem.text.strip()
                            if field_value and field_value not in ['NA', 'N/A', '']:
                                data[field_key] = field_value
                                logger.debug(f"{field_text}: {field_value}")

                    except:
                        continue

            except Exception as e:
                logger.debug(f"Additional details extraction failed: {e}")

            # Log extraction summary
            extracted_fields = len([v for v in data.values() if v != 'N/A'])
            total_fields = len(data)
            logger.info(f"📈 Extracted {extracted_fields}/{total_fields} comprehensive fields")

        except Exception as e:
            logger.error(f"❌ Comprehensive extraction failed: {e}")
        
        return data
    
    def is_valid_comprehensive_data(self, data):
        """Check if extracted comprehensive data is valid"""
        # At least one student or teacher field should be valid
        key_fields = ['total_students', 'total_teachers']
        for field in key_fields:
            value = data.get(field, 'N/A')
            if value != 'N/A' and str(value).isdigit():
                return True

        # Or at least school name should be extracted
        if data.get('detail_school_name', 'N/A') != 'N/A':
            return True

        return False

    def create_comprehensive_signature(self, data):
        """Create unique signature for duplicate detection (comprehensive data)"""
        return f"{data.get('total_students', 'N/A')}_{data.get('total_boys', 'N/A')}_{data.get('total_girls', 'N/A')}_{data.get('total_teachers', 'N/A')}_{data.get('detail_school_name', 'N/A')}"
    
    def process_state_file(self, csv_file, batch_size=30, start_index=0):
        """Process schools from state-wise CSV file"""
        try:
            # Load data
            df = pd.read_csv(csv_file)
            logger.info(f"📁 Loaded {len(df)} records from {csv_file}")
            
            # Filter schools that need processing (must have know_more_link)
            schools_to_process = df[
                (df['know_more_link'].notna()) & 
                (df['know_more_link'] != 'N/A') & 
                (df['know_more_link'].str.contains('schooldetail', na=False))
            ].copy()
            
            logger.info(f"🎯 Found {len(schools_to_process)} schools with valid links")
            
            if len(schools_to_process) == 0:
                logger.info("✅ No schools with valid links found!")
                return
            
            # Process in batches
            end_index = min(start_index + batch_size, len(schools_to_process))
            batch = schools_to_process.iloc[start_index:end_index]
            
            logger.info(f"🔄 Processing batch: {start_index + 1} to {end_index} ({len(batch)} schools)")
            
            # Initialize comprehensive columns if not present
            comprehensive_columns = [
                'detail_school_name',
                'total_students', 'total_boys', 'total_girls',
                'total_teachers', 'male_teachers', 'female_teachers',
                'location_detail', 'school_category_detail', 'class_from', 'class_to',
                'school_type_detail', 'year_of_establishment', 'national_management', 'state_management',
                'affiliation_board_sec', 'affiliation_board_hsec',
                'academic_year_detail', 'school_code', 'village_name', 'cluster_name',
                'block_name', 'district_name', 'pin_code_detail',
                'extraction_status'
            ]

            for col in comprehensive_columns:
                if col not in df.columns:
                    df[col] = 'N/A'
            
            # Setup driver
            self.setup_driver()
            
            # Process each school in batch
            for i, (idx, school) in enumerate(batch.iterrows(), 1):
                school_name = school.get('school_name', f'School_{i}')
                school_url = school.get('know_more_link', '')
                expected_id = school_url.split('/')[-2] if '/' in school_url else 'unknown'
                
                logger.info(f"🏫 {start_index + i}/{end_index}: {school_name}")
                
                # Extract focused data
                extracted_data = self.navigate_and_extract(school_url, school_name, expected_id)
                
                if extracted_data:
                    # Update DataFrame with extracted focused data
                    for key, value in extracted_data.items():
                        df.at[idx, key] = value
                    df.at[idx, 'extraction_status'] = 'SUCCESS'
                    self.success_count += 1
                else:
                    df.at[idx, 'extraction_status'] = 'FAILED'
                    self.fail_count += 1
                
                self.processed_count += 1
                
                # Save progress every 10 schools
                if i % 10 == 0:
                    self.save_progress(df, csv_file)
                    success_rate = (self.success_count / self.processed_count) * 100
                    logger.info(f"📊 Progress: {i}/{len(batch)} ({success_rate:.1f}% success)")
                
                # Minimal delay between schools
                time.sleep(0.5)
            
            # Final save
            self.save_progress(df, csv_file)
            self.show_batch_summary(start_index, end_index, len(schools_to_process))
            
        except Exception as e:
            logger.error(f"❌ Batch processing failed: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("🔒 Browser closed")

    def save_progress(self, df, original_file):
        """Save progress to output file"""
        try:
            # Create output filename
            if '_with_links_' in original_file:
                output_file = original_file.replace('_with_links_', '_with_details_')
            else:
                output_file = original_file.replace('.csv', '_with_details.csv')

            df.to_csv(output_file, index=False)
            logger.info(f"💾 Progress saved to: {output_file}")

            # Create timestamped backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = output_file.replace('.csv', f'_backup_{timestamp}.csv')
            df.to_csv(backup_file, index=False)
            logger.debug(f"💾 Backup created: {backup_file}")

        except Exception as e:
            logger.error(f"❌ Failed to save progress: {e}")

    def show_batch_summary(self, start_index, end_index, total_remaining):
        """Show comprehensive batch processing summary"""
        print(f"\n{'='*80}")
        print("🎯 COMPREHENSIVE PHASE 2 BATCH SUMMARY")
        print(f"{'='*80}")
        print(f"📊 Batch processed: {start_index + 1} to {end_index}")
        print(f"✅ Successful extractions: {self.success_count}")
        print(f"❌ Failed extractions: {self.fail_count}")

        if self.processed_count > 0:
            success_rate = (self.success_count / self.processed_count) * 100
            print(f"📈 Success rate: {success_rate:.1f}%")

        print(f"\n📊 COMPREHENSIVE DATA EXTRACTED:")
        print(f"   🏫 School Name: From detail page HTML")
        print(f"   🎓 Student Data: Total, Boys, Girls breakdown")
        print(f"   👨‍🏫 Teacher Data: Total, Male, Female breakdown")
        print(f"   📍 Location Details: Location, Category, Type")
        print(f"   📅 Establishment: Year, Management details")
        print(f"   🏛️ Affiliation Boards: Secondary & Higher Secondary")
        print(f"   📋 Additional Info: Academic year, codes, addresses")

        remaining = total_remaining - end_index
        if remaining > 0:
            print(f"\n📋 REMAINING WORK:")
            print(f"   {remaining} schools still need processing")
            print(f"   Recommended next batch: {end_index} to {min(end_index + 30, total_remaining)}")
        else:
            print(f"\n🎉 ALL SCHOOLS IN BATCH PROCESSED!")

        print(f"{'='*80}")

def main():
    """Main function for comprehensive Phase 2 processing"""
    print("🚀 COMPREHENSIVE PHASE 2 PROCESSOR")
    print("Extracts: School Name + Student Data + Teacher Data + Location Details + Affiliation Boards + All Other Fields")
    print("Uses Brave Browser for enhanced privacy and performance")
    print()

    # Check for available state files
    available_files = []
    for f in os.listdir('.'):
        if f.endswith('.csv') and ('_with_links_' in f or 'ANDAMAN' in f):
            available_files.append(f)

    if not available_files:
        print("❌ No suitable CSV files found!")
        print("Looking for files with '_with_links_' in filename or state-wise files")
        return

    print("📁 Available files:")
    for i, f in enumerate(available_files, 1):
        print(f"   {i}. {f}")

    # Get user selection
    try:
        choice = int(input(f"\nSelect file (1-{len(available_files)}): ").strip())
        if 1 <= choice <= len(available_files):
            csv_file = available_files[choice - 1]
        else:
            print("Invalid choice, using first file")
            csv_file = available_files[0]
    except ValueError:
        print("Invalid input, using first file")
        csv_file = available_files[0]

    print(f"📁 Selected file: {csv_file}")

    # Get batch preferences
    try:
        batch_size = input("Enter batch size (default 30): ").strip()
        batch_size = int(batch_size) if batch_size else 30

        start_index = input("Enter start index (default 0): ").strip()
        start_index = int(start_index) if start_index else 0

    except ValueError:
        batch_size = 30
        start_index = 0

    print(f"⚡ Processing {batch_size} schools starting from index {start_index}")
    print(f"🎯 Comprehensive extraction: School Name + All Detail Fields + Brave Browser")

    try:
        processor = FocusedPhase2Processor()
        processor.process_state_file(csv_file, batch_size=batch_size, start_index=start_index)
    except Exception as e:
        print(f"❌ Critical error: {e}")
        print("Please check the logs above for details")

if __name__ == "__main__":
    main()
