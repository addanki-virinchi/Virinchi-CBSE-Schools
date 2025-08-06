#!/usr/bin/env python3
"""
Phase 2 Automated Processor - Fully automated processing of Phase 1 CSV files
- Automatically reads Phase 1 CSV files
- Processes ALL schools with know_more_links
- No user interaction required
- Optimized for large-scale batch processing
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
import glob
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutomatedPhase2Processor:
    def __init__(self):
        self.driver = None
        self.processed_count = 0
        self.success_count = 0
        self.fail_count = 0
        self.extracted_signatures = set()  # For duplicate detection
        self.optimal_batch_size = 50  # Optimized batch size for automation

    def extract_value_from_element_text(self, element_text, field_name):
        """Helper method to extract value from element text"""
        try:
            # Split by newlines and look for the field
            lines = element_text.split('\n')
            for i, line in enumerate(lines):
                if field_name.lower() in line.lower():
                    # Value might be on the same line or next line
                    if ':' in line:
                        value = line.split(':', 1)[1].strip()
                        if value:
                            return value
                    # Check next line
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and not any(keyword in next_line.lower() for keyword in ['class', 'school', 'year', 'type', 'category']):
                            return next_line
            return 'N/A'
        except Exception:
            return 'N/A'
        
    def setup_driver(self):
        """Initialize Chrome browser driver with optimized settings for Phase 2 processing"""
        try:
            # Setup Chrome options for Phase 2 data extraction
            options = uc.ChromeOptions()

            # Core stability options
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-blink-features=AutomationControlled")

            # Performance optimizations (KEEP JavaScript enabled for dynamic content)
            options.add_argument("--disable-images")  # Speed optimization
            options.add_argument("--disable-plugins")  # Speed optimization
            # NOTE: JavaScript is ENABLED for proper page functionality

            # Memory and resource optimizations
            options.add_argument("--memory-pressure-off")
            options.add_argument("--max_old_space_size=4096")

            self.driver = uc.Chrome(options=options)
            self.driver.maximize_window()

            # Balanced timeouts for Phase 2 processing
            self.driver.implicitly_wait(5)  # Increased for dynamic content
            self.driver.set_page_load_timeout(25)  # Increased for detailed pages

            logger.info("✅ Chrome browser driver initialized for Phase 2 automated processing")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Chrome driver: {e}")
            logger.error("Please ensure Chrome browser is installed and updated")
            raise

    def find_phase1_csv_files(self):
        """Find all Phase 1 CSV files automatically"""
        try:
            # Look for Phase 1 CSV files with the new naming convention
            pattern = "*_phase1_complete_*.csv"
            csv_files = glob.glob(pattern)
            
            if not csv_files:
                # Fallback: look for old naming convention
                pattern = "*_with_links_*.csv"
                csv_files = glob.glob(pattern)
                logger.info("Using legacy Phase 1 files (with_links format)")
            
            if not csv_files:
                logger.error("❌ No Phase 1 CSV files found!")
                return []
            
            # Sort files by state name for consistent processing order
            csv_files.sort()
            logger.info(f"✅ Found {len(csv_files)} Phase 1 CSV files")
            
            return csv_files
            
        except Exception as e:
            logger.error(f"❌ Error finding Phase 1 CSV files: {e}")
            return []

    def extract_state_name_from_filename(self, filename):
        """Extract state name from CSV filename"""
        try:
            # Remove path and extension
            basename = os.path.basename(filename)
            
            # Extract state name from different naming patterns
            if "_phase1_complete_" in basename:
                state_name = basename.split("_phase1_complete_")[0]
            elif "_with_links_" in basename:
                state_name = basename.split("_with_links_")[0]
            else:
                state_name = basename.split("_")[0]
            
            # Convert back to readable format
            state_name = state_name.replace("_", " ").replace("and", "&")
            return state_name
            
        except Exception as e:
            logger.error(f"❌ Error extracting state name from {filename}: {e}")
            return "UNKNOWN_STATE"

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
                # Legacy format: assume all schools in with_links files are ready
                phase2_schools = df[df['know_more_link'].notna() & (df['know_more_link'] != 'N/A')].copy()
                logger.info(f"   📊 Found {len(phase2_schools)} schools with valid know_more_links (legacy format)")
            
            return phase2_schools
            
        except Exception as e:
            logger.error(f"❌ Error filtering Phase 2 ready schools: {e}")
            return pd.DataFrame()

    def extract_focused_data(self, url, max_retries=2):
        """Extract comprehensive data from school detail page with immediate browser refresh"""
        for attempt in range(max_retries):
            try:
                logger.info(f"🌐 Navigating to school detail page: {url}")

                # IMMEDIATE BROWSER REFRESH: Navigate and immediately refresh
                try:
                    # Step 1: Navigate to the URL
                    self.driver.get(url)
                    logger.info(f"   📍 Initial navigation completed")

                    # Step 2: IMMEDIATE REFRESH as requested
                    logger.info(f"   🔄 Performing IMMEDIATE browser refresh...")
                    self.driver.refresh()

                    # Step 3: Wait for refresh to complete
                    time.sleep(4)  # Increased wait for refresh completion

                    # Step 4: Verify page is loaded
                    WebDriverWait(self.driver, 10).until(
                        lambda driver: driver.execute_script("return document.readyState") == "complete"
                    )

                    # Step 5: Additional wait for dynamic content
                    time.sleep(2)

                    logger.info(f"   ✅ Page refreshed and loaded successfully")
                    logger.info(f"   📍 Final URL: {self.driver.current_url}")
                    logger.info(f"   📄 Page title: {self.driver.title}")

                except Exception as e:
                    logger.error(f"   ❌ Navigation/refresh error: {e}")
                    if attempt < max_retries - 1:
                        continue
                    return None

                # Initialize comprehensive data structure for all extracted fields
                data = {
                    # School identification
                    'detail_school_name': 'N/A',
                    'source_url': url,
                    'extraction_timestamp': datetime.now().isoformat(),

                    # Basic Details section (.innerPad div with .schoolInfoCol elements)
                    'academic_year': 'N/A',
                    'location': 'N/A',
                    'school_category': 'N/A',
                    'class_from': 'N/A',
                    'class_to': 'N/A',
                    'class_range': 'N/A',
                    'school_type': 'N/A',
                    'year_of_establishment': 'N/A',
                    'national_management': 'N/A',
                    'state_management': 'N/A',
                    'affiliation_board_sec': 'N/A',
                    'affiliation_board_hsec': 'N/A',

                    # Student Enrollment section (.bg-white div with .H3Value elements)
                    'total_students': 'N/A',
                    'total_boys': 'N/A',
                    'total_girls': 'N/A',
                    'enrollment_class_range': 'N/A',

                    # Teacher section (similar structure with Total Teachers/Male/Female)
                    'total_teachers': 'N/A',
                    'male_teachers': 'N/A',
                    'female_teachers': 'N/A'
                }

                # Get page content for extraction
                page_text = self.driver.page_source

                # Extract school ID for verification
                import re
                url_school_id = re.search(r'/(\d+)/\d+$', url)
                expected_school_id = url_school_id.group(1) if url_school_id else "unknown"

                logger.info(f"   📄 Expected school ID: {expected_school_id}")
                logger.info(f"   📄 Page content length: {len(page_text)} characters")

                # Verify we're on the correct page
                if expected_school_id not in page_text and expected_school_id != "unknown":
                    logger.warning(f"   ⚠️ School ID {expected_school_id} not found in page content")
                    # Continue with extraction anyway, but mark as potential issue
                    data['detail_school_name'] = f"POTENTIAL_ISSUE_{expected_school_id}"

                # EXTRACT DATA FROM SPECIFIC HTML STRUCTURES AS REQUESTED

                # 1. BASIC DETAILS SECTION - Extract from .innerPad div with .schoolInfoCol elements
                try:
                    logger.info(f"   📋 Extracting Basic Details from .innerPad div...")

                    # Try to find Basic Details section using Selenium elements first
                    try:
                        basic_details_elements = self.driver.find_elements(By.CSS_SELECTOR, ".innerPad .schoolInfoCol")
                        if basic_details_elements:
                            logger.info(f"   Found {len(basic_details_elements)} basic detail elements")

                            for element in basic_details_elements:
                                try:
                                    element_text = element.text.strip()
                                    if "Academic Year" in element_text:
                                        data['academic_year'] = self.extract_value_from_element_text(element_text, "Academic Year")
                                    elif "Location" in element_text:
                                        data['location'] = self.extract_value_from_element_text(element_text, "Location")
                                    elif "School Category" in element_text:
                                        data['school_category'] = self.extract_value_from_element_text(element_text, "School Category")
                                    elif "Class From" in element_text:
                                        data['class_from'] = self.extract_value_from_element_text(element_text, "Class From")
                                    elif "Class To" in element_text:
                                        data['class_to'] = self.extract_value_from_element_text(element_text, "Class To")
                                    elif "School Type" in element_text:
                                        data['school_type'] = self.extract_value_from_element_text(element_text, "School Type")
                                    elif "Year of Establishment" in element_text:
                                        data['year_of_establishment'] = self.extract_value_from_element_text(element_text, "Year of Establishment")
                                except Exception as e:
                                    logger.debug(f"   Error processing basic detail element: {e}")
                                    continue
                    except Exception as e:
                        logger.debug(f"   Error finding basic details elements: {e}")

                    # Fallback: Use regex patterns for basic details
                    if data['academic_year'] == 'N/A':
                        academic_year_match = re.search(r'Academic Year[:\s]*(?:<[^>]*>)*([^<\n]+)', page_text, re.IGNORECASE)
                        if academic_year_match:
                            data['academic_year'] = academic_year_match.group(1).strip()

                    if data['location'] == 'N/A':
                        location_match = re.search(r'Location[:\s]*(?:<[^>]*>)*([^<\n]+)', page_text, re.IGNORECASE)
                        if location_match:
                            data['location'] = location_match.group(1).strip()

                    if data['school_category'] == 'N/A':
                        category_match = re.search(r'School Category[:\s]*(?:<[^>]*>)*([^<\n]+)', page_text, re.IGNORECASE)
                        if category_match:
                            data['school_category'] = category_match.group(1).strip()

                    if data['school_type'] == 'N/A':
                        type_match = re.search(r'School Type[:\s]*(?:<[^>]*>)*([^<\n]+)', page_text, re.IGNORECASE)
                        if type_match:
                            data['school_type'] = type_match.group(1).strip()

                    # Combine class range if both from and to are found
                    if data['class_from'] != 'N/A' and data['class_to'] != 'N/A':
                        data['class_range'] = f"{data['class_from']} To {data['class_to']}"

                    logger.info(f"   ✅ Basic Details extracted: Category={data['school_category']}, Type={data['school_type']}")

                except Exception as e:
                    logger.debug(f"   Error extracting basic details: {e}")

                # 2. STUDENT ENROLLMENT SECTION - Extract from .bg-white div with .H3Value elements
                try:
                    logger.info(f"   👥 Extracting Student Enrollment from .bg-white div with .H3Value elements...")

                    # Try to find Student Enrollment section using Selenium elements first
                    try:
                        h3_value_elements = self.driver.find_elements(By.CSS_SELECTOR, ".bg-white .H3Value")
                        if h3_value_elements:
                            logger.info(f"   Found {len(h3_value_elements)} H3Value elements")

                            for element in h3_value_elements:
                                try:
                                    # Get the parent container to find the label
                                    parent = element.find_element(By.XPATH, "..")
                                    parent_text = parent.text.strip().lower()
                                    value = element.text.strip()

                                    if value.isdigit():
                                        if "total students" in parent_text:
                                            data['total_students'] = value
                                            logger.info(f"   Found Total Students: {value}")
                                        elif "boys" in parent_text and "total" not in parent_text:
                                            data['total_boys'] = value
                                            logger.info(f"   Found Boys: {value}")
                                        elif "girls" in parent_text:
                                            data['total_girls'] = value
                                            logger.info(f"   Found Girls: {value}")
                                except Exception as e:
                                    logger.debug(f"   Error processing H3Value element: {e}")
                                    continue
                    except Exception as e:
                        logger.debug(f"   Error finding H3Value elements: {e}")

                    # Fallback: Use regex patterns for student enrollment
                    if data['total_students'] == 'N/A':
                        total_students_patterns = [
                            r'Total Students[^>]*</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>',
                            r'Total Students[^>]*>\s*(\d+)\s*<',
                            r'Total Students[:\s]*(\d+)'
                        ]
                        for pattern in total_students_patterns:
                            match = re.search(pattern, page_text, re.IGNORECASE)
                            if match:
                                data['total_students'] = match.group(1).strip()
                                logger.info(f"   Found Total Students (regex): {data['total_students']}")
                                break

                    if data['total_boys'] == 'N/A':
                        boys_patterns = [
                            r'Boys[^>]*</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>',
                            r'Boys[^>]*>\s*(\d+)\s*<',
                            r'Boys[:\s]*(\d+)'
                        ]
                        for pattern in boys_patterns:
                            match = re.search(pattern, page_text, re.IGNORECASE)
                            if match:
                                data['total_boys'] = match.group(1).strip()
                                logger.info(f"   Found Boys (regex): {data['total_boys']}")
                                break

                    if data['total_girls'] == 'N/A':
                        girls_patterns = [
                            r'Girls[^>]*</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>',
                            r'Girls[^>]*>\s*(\d+)\s*<',
                            r'Girls[:\s]*(\d+)'
                        ]
                        for pattern in girls_patterns:
                            match = re.search(pattern, page_text, re.IGNORECASE)
                            if match:
                                data['total_girls'] = match.group(1).strip()
                                logger.info(f"   Found Girls (regex): {data['total_girls']}")
                                break

                    logger.info(f"   ✅ Student Enrollment extracted: Total={data['total_students']}, Boys={data['total_boys']}, Girls={data['total_girls']}")

                except Exception as e:
                    logger.debug(f"   Error extracting student enrollment: {e}")

                # 3. TEACHER SECTION - Extract from similar HTML structure with Total Teachers/Male/Female
                try:
                    logger.info(f"   👨‍🏫 Extracting Teacher data from similar HTML structure...")

                    # Try to find Teacher section using Selenium elements first
                    try:
                        # Look for teacher-related H3Value elements
                        all_h3_elements = self.driver.find_elements(By.CSS_SELECTOR, ".H3Value")
                        teacher_section_found = False

                        for element in all_h3_elements:
                            try:
                                # Get the parent container to find the label
                                parent = element.find_element(By.XPATH, "..")
                                parent_text = parent.text.strip().lower()
                                value = element.text.strip()

                                if value.isdigit():
                                    if "total teachers" in parent_text:
                                        data['total_teachers'] = value
                                        logger.info(f"   Found Total Teachers: {value}")
                                        teacher_section_found = True
                                    elif "male" in parent_text and "teacher" in parent_text:
                                        data['male_teachers'] = value
                                        logger.info(f"   Found Male Teachers: {value}")
                                        teacher_section_found = True
                                    elif "female" in parent_text and "teacher" in parent_text:
                                        data['female_teachers'] = value
                                        logger.info(f"   Found Female Teachers: {value}")
                                        teacher_section_found = True
                                    elif "male" in parent_text and teacher_section_found and data['male_teachers'] == 'N/A':
                                        # Sometimes just "Male" without "Teacher"
                                        data['male_teachers'] = value
                                        logger.info(f"   Found Male Teachers (short): {value}")
                                    elif "female" in parent_text and teacher_section_found and data['female_teachers'] == 'N/A':
                                        # Sometimes just "Female" without "Teacher"
                                        data['female_teachers'] = value
                                        logger.info(f"   Found Female Teachers (short): {value}")
                            except Exception as e:
                                logger.debug(f"   Error processing teacher H3Value element: {e}")
                                continue
                    except Exception as e:
                        logger.debug(f"   Error finding teacher H3Value elements: {e}")

                    # Fallback: Use regex patterns for teacher data
                    if data['total_teachers'] == 'N/A':
                        teacher_patterns = [
                            r'Total Teachers[^>]*</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>',
                            r'Total Teachers[^>]*>\s*(\d+)\s*<',
                            r'Total Teachers[:\s]*(\d+)'
                        ]
                        for pattern in teacher_patterns:
                            match = re.search(pattern, page_text, re.IGNORECASE)
                            if match:
                                data['total_teachers'] = match.group(1).strip()
                                logger.info(f"   Found Total Teachers (regex): {data['total_teachers']}")
                                break

                    if data['male_teachers'] == 'N/A':
                        male_patterns = [
                            r'Male[^>]*</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>',
                            r'Male Teachers[^>]*>\s*(\d+)\s*<',
                            r'Male[:\s]*(\d+)'
                        ]
                        for pattern in male_patterns:
                            match = re.search(pattern, page_text, re.IGNORECASE)
                            if match:
                                data['male_teachers'] = match.group(1).strip()
                                logger.info(f"   Found Male Teachers (regex): {data['male_teachers']}")
                                break

                    if data['female_teachers'] == 'N/A':
                        female_patterns = [
                            r'Female[^>]*</p>\s*<p[^>]*class="H3Value[^>]*>\s*(\d+)\s*</p>',
                            r'Female Teachers[^>]*>\s*(\d+)\s*<',
                            r'Female[:\s]*(\d+)'
                        ]
                        for pattern in female_patterns:
                            match = re.search(pattern, page_text, re.IGNORECASE)
                            if match:
                                data['female_teachers'] = match.group(1).strip()
                                logger.info(f"   Found Female Teachers (regex): {data['female_teachers']}")
                                break

                    logger.info(f"   ✅ Teacher data extracted: Total={data['total_teachers']}, Male={data['male_teachers']}, Female={data['female_teachers']}")

                except Exception as e:
                    logger.debug(f"   Error extracting teacher data: {e}")

                # 4. SCHOOL NAME - Extract from page title, header, or breadcrumb
                try:
                    logger.info(f"   🏫 Extracting School Name...")

                    # Method 1: Try to get school name from page title
                    page_title = self.driver.title
                    if page_title and page_title != "Know Your School" and "UDISE" not in page_title:
                        clean_title = page_title.replace("Know Your School", "").replace("-", "").strip()
                        if clean_title and len(clean_title) > 3:
                            data['detail_school_name'] = clean_title
                            logger.info(f"   Found school name from title: {clean_title}")

                    # Method 2: Try to find school name in breadcrumb or header elements
                    if data['detail_school_name'] == 'N/A':
                        try:
                            # Look for breadcrumb or header elements
                            name_selectors = [
                                "h1", "h2", "h3",
                                ".breadcrumb", ".page-title", ".school-name",
                                "[class*='title']", "[class*='name']", "[class*='header']"
                            ]

                            for selector in name_selectors:
                                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                for element in elements:
                                    text = element.text.strip()
                                    if text and len(text) > 5 and len(text) < 200:
                                        # Filter out common non-school-name text
                                        if not any(skip in text.lower() for skip in ['know your school', 'udise', 'dashboard', 'menu', 'search']):
                                            data['detail_school_name'] = text
                                            logger.info(f"   Found school name from {selector}: {text}")
                                            break
                                if data['detail_school_name'] != 'N/A':
                                    break
                        except Exception as e:
                            logger.debug(f"   Error finding school name in elements: {e}")

                    # Method 3: Extract from page content using regex
                    if data['detail_school_name'] == 'N/A':
                        name_patterns = [
                            r'School Name[:\s]*([^\n<]+)',
                            r'Name of School[:\s]*([^\n<]+)',
                            r'Institution Name[:\s]*([^\n<]+)'
                        ]
                        for pattern in name_patterns:
                            match = re.search(pattern, page_text, re.IGNORECASE)
                            if match:
                                school_name = match.group(1).strip()
                                if school_name and len(school_name) > 3:
                                    data['detail_school_name'] = school_name
                                    logger.info(f"   Found school name from regex: {school_name}")
                                    break

                    # Fallback: Use school ID as identifier
                    if data['detail_school_name'] == 'N/A' or data['detail_school_name'].startswith('POTENTIAL_ISSUE'):
                        data['detail_school_name'] = f"School_ID_{expected_school_id}"
                        logger.info(f"   Using school ID as name: {data['detail_school_name']}")

                except Exception as e:
                    logger.debug(f"   Error extracting school name: {e}")
                    data['detail_school_name'] = f"School_ID_{expected_school_id}"

                # Strategy 5: Fallback - Extract any visible numbers as potential data
                if data['total_students'] == 'N/A' or data['total_teachers'] == 'N/A':
                    try:
                        # Get all visible text elements
                        text_elements = self.driver.find_elements(By.CSS_SELECTOR, "span, div, p, td, th")

                        for element in text_elements:
                            try:
                                text = element.text.strip()
                                if text.isdigit() and 1 <= int(text) <= 10000:  # Reasonable range for school data
                                    # Check surrounding context
                                    parent_text = ""
                                    try:
                                        parent = element.find_element(By.XPATH, "..")
                                        parent_text = parent.text.lower()
                                    except:
                                        pass

                                    # Assign based on context or position
                                    if ('student' in parent_text or 'enrollment' in parent_text) and data['total_students'] == 'N/A':
                                        data['total_students'] = text
                                        logger.debug(f"   Found students from context: {text}")
                                    elif ('teacher' in parent_text or 'staff' in parent_text or 'faculty' in parent_text) and data['total_teachers'] == 'N/A':
                                        data['total_teachers'] = text
                                        logger.debug(f"   Found teachers from context: {text}")
                            except:
                                continue
                    except Exception as e:
                        logger.debug(f"   Error in fallback extraction: {e}")

                # COMPREHENSIVE DATA VALIDATION AND STATUS INDICATORS
                try:
                    logger.info(f"   📊 Validating extracted data...")

                    # Count successfully extracted fields
                    extracted_fields = 0
                    critical_fields = 0

                    # Critical fields for Phase 2
                    if data['total_students'] != 'N/A':
                        critical_fields += 1
                        extracted_fields += 1
                    if data['total_teachers'] != 'N/A':
                        critical_fields += 1
                        extracted_fields += 1
                    if data['detail_school_name'] != 'N/A' and not data['detail_school_name'].startswith('School_ID_'):
                        extracted_fields += 1

                    # Additional fields
                    additional_fields = [
                        'total_boys', 'total_girls', 'male_teachers', 'female_teachers',
                        'school_category', 'school_type', 'location', 'academic_year'
                    ]
                    for field in additional_fields:
                        if data[field] != 'N/A':
                            extracted_fields += 1

                    # Add extraction status indicators
                    data['extraction_status'] = 'SUCCESS' if critical_fields >= 2 else 'PARTIAL' if critical_fields >= 1 else 'FAILED'
                    data['fields_extracted'] = extracted_fields
                    data['critical_fields_extracted'] = critical_fields

                    # Validation summary
                    if critical_fields >= 2:
                        logger.info(f"✅ EXCELLENT extraction from {url}")
                        logger.info(f"   🎯 Critical fields: {critical_fields}/2, Total fields: {extracted_fields}")
                        logger.info(f"   📋 School: {data['detail_school_name']}")
                        logger.info(f"   👥 Students: {data['total_students']}, Teachers: {data['total_teachers']}")
                    elif critical_fields >= 1:
                        logger.info(f"⚠️ PARTIAL extraction from {url}")
                        logger.info(f"   🎯 Critical fields: {critical_fields}/2, Total fields: {extracted_fields}")
                        logger.info(f"   📋 School: {data['detail_school_name']}")
                        logger.info(f"   👥 Students: {data['total_students']}, Teachers: {data['total_teachers']}")
                    else:
                        logger.warning(f"❌ FAILED extraction from {url}")
                        logger.warning(f"   🎯 Critical fields: {critical_fields}/2, Total fields: {extracted_fields}")
                        logger.warning(f"   📄 Page title: {self.driver.title}")
                        logger.warning(f"   📄 Current URL: {self.driver.current_url}")
                        logger.warning(f"   📄 Page source length: {len(page_text)}")

                except Exception as e:
                    logger.debug(f"   Error in data validation: {e}")
                    data['extraction_status'] = 'ERROR'
                    data['fields_extracted'] = 0
                    data['critical_fields_extracted'] = 0

                return data

            except Exception as e:
                logger.warning(f"⚠️ Failed to extract data from {url} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"⏳ Retrying in 3 seconds...")
                    time.sleep(3)
                else:
                    return None

        return None

    def process_state_file_automated(self, csv_file):
        """Process entire state file automatically with optimal batching"""
        try:
            state_name = self.extract_state_name_from_filename(csv_file)
            logger.info(f"\n🏛️ PROCESSING STATE: {state_name}")
            logger.info(f"📁 File: {csv_file}")
            
            # Load data
            df = pd.read_csv(csv_file)
            logger.info(f"   📊 Loaded {len(df)} total records")
            
            # Filter Phase 2 ready schools
            schools_to_process = self.filter_phase2_ready_schools(df)
            
            if len(schools_to_process) == 0:
                logger.info("   ✅ No schools ready for Phase 2 processing")
                return True
            
            logger.info(f"   🎯 Processing {len(schools_to_process)} schools in batches of {self.optimal_batch_size}")
            
            # Process all schools in optimal batches
            total_batches = (len(schools_to_process) + self.optimal_batch_size - 1) // self.optimal_batch_size
            
            for batch_num in range(total_batches):
                start_idx = batch_num * self.optimal_batch_size
                end_idx = min(start_idx + self.optimal_batch_size, len(schools_to_process))
                
                batch = schools_to_process.iloc[start_idx:end_idx]
                logger.info(f"   🔄 Processing batch {batch_num + 1}/{total_batches}: schools {start_idx + 1}-{end_idx}")
                
                # Process batch
                self.process_batch_automated(batch, state_name, batch_num + 1)
                
                # Brief pause between batches
                time.sleep(1)
            
            logger.info(f"   ✅ Completed processing state: {state_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing state file {csv_file}: {e}")
            return False

    def process_batch_automated(self, batch, state_name, batch_num):
        """Process a batch of schools automatically"""
        try:
            batch_results = []
            batch_start_time = time.time()
            
            for idx, school in batch.iterrows():
                try:
                    # Extract data
                    extracted_data = self.extract_focused_data(school['know_more_link'])
                    
                    if extracted_data:
                        # Combine original and extracted data
                        combined_data = school.to_dict()
                        combined_data.update(extracted_data)
                        batch_results.append(combined_data)
                        self.success_count += 1
                    else:
                        self.fail_count += 1
                    
                    self.processed_count += 1
                    
                    # Brief pause between schools
                    time.sleep(0.2)  # Ultra-fast processing
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to process school {idx}: {e}")
                    self.fail_count += 1
                    continue
            
            # Save batch results
            if batch_results:
                self.save_batch_results(batch_results, state_name, batch_num)
            
            batch_time = time.time() - batch_start_time
            logger.info(f"      ⏱️ Batch completed in {batch_time:.1f}s ({len(batch_results)}/{len(batch)} successful)")
            
        except Exception as e:
            logger.error(f"❌ Error processing batch: {e}")

    def save_batch_results(self, results, state_name, batch_num):
        """Save batch results to CSV"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_state = state_name.replace(' ', '_').replace('&', 'and').replace('/', '_').upper()
            
            filename = f"{clean_state}_phase2_batch{batch_num}_{timestamp}.csv"
            
            df = pd.DataFrame(results)
            df.to_csv(filename, index=False)
            
            logger.info(f"      💾 Saved {len(results)} records to: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Error saving batch results: {e}")

    def run_automated_processing(self):
        """Main automated processing function"""
        try:
            logger.info("🚀 STARTING AUTOMATED PHASE 2 PROCESSING")
            logger.info("="*80)
            
            # Setup driver
            self.setup_driver()
            
            # Find Phase 1 CSV files
            csv_files = self.find_phase1_csv_files()
            
            if not csv_files:
                logger.error("❌ No Phase 1 CSV files found. Please run Phase 1 first.")
                return
            
            logger.info(f"📋 Found {len(csv_files)} state files to process")
            
            # Process all state files automatically
            for i, csv_file in enumerate(csv_files, 1):
                logger.info(f"\n{'='*80}")
                logger.info(f"🏛️ PROCESSING STATE {i}/{len(csv_files)}")
                logger.info(f"{'='*80}")
                
                success = self.process_state_file_automated(csv_file)
                
                if not success:
                    logger.warning(f"⚠️ Failed to process {csv_file}, continuing with next state")
                
                # Brief pause between states
                time.sleep(2)
            
            # Final summary
            self.show_final_summary()
            
        except Exception as e:
            logger.error(f"❌ Critical error in automated processing: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("🔒 Driver closed")

    def show_final_summary(self):
        """Show final processing summary"""
        logger.info(f"\n{'='*80}")
        logger.info("🎯 AUTOMATED PHASE 2 PROCESSING COMPLETED")
        logger.info(f"{'='*80}")
        logger.info(f"📊 FINAL STATISTICS:")
        logger.info(f"   🏫 Total schools processed: {self.processed_count}")
        logger.info(f"   ✅ Successful extractions: {self.success_count}")
        logger.info(f"   ❌ Failed extractions: {self.fail_count}")
        
        if self.processed_count > 0:
            success_rate = (self.success_count / self.processed_count) * 100
            logger.info(f"   📈 Success rate: {success_rate:.1f}%")
        
        logger.info(f"\n💾 Output files saved with pattern: *_phase2_batch*_*.csv")
        logger.info("🎉 Automated Phase 2 processing complete!")

def main():
    """Main function for automated Phase 2 processing"""
    print("🚀 AUTOMATED PHASE 2 PROCESSOR")
    print("Automatically processes ALL Phase 1 CSV files")
    print("No user interaction required - fully automated")
    print()
    
    try:
        processor = AutomatedPhase2Processor()
        processor.run_automated_processing()
    except Exception as e:
        print(f"❌ Critical error: {e}")
        print("Please check the logs above for details")

if __name__ == "__main__":
    main()
