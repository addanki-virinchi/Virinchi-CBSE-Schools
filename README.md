# UDISE Plus School Data Scraper - Two Phase System

This project scrapes comprehensive school data from the UDISE Plus portal (https://udiseplus.gov.in) for all Indian states and districts using a sophisticated two-phase approach.

## 🚀 Two-Phase Scraping System

### **Phase 1: Basic Data Extraction**
- Extracts basic school information from search results
- Handles pagination automatically
- Saves "Know More" links for detailed extraction
- Fast and efficient for getting overview data
- Saves progress by district for recovery

### **Phase 2: Detailed Data Extraction**
- Uses "Know More" links from Phase 1
- Extracts comprehensive school details
- Gets student enrollment and teacher data
- Slower but provides complete information

## 📁 Files

- `Schools.py` - Phase 1 scraper (basic data + know more links)
- `phase2_detailed_scraper.py` - Phase 2 scraper (detailed data)
- `run_scraper.py` - Interactive runner with all modes
- `consolidate_data.py` - Merges Phase 1 and Phase 2 data
- `config.py` - Configuration settings
- `requirements.txt` - Dependencies
- `README.md` - This documentation

## ✨ Key Features

- **Two-Phase Architecture**: Efficient separation of basic and detailed data extraction
- **Automated Pagination**: Processes all pages for each state-district combination
- **Progress Saving**: District-level saves prevent data loss
- **Error Recovery**: Continues processing even if individual schools fail
- **Data Consolidation**: Merges basic and detailed data intelligently
- **Comprehensive Logging**: Detailed progress tracking and error reporting

## Prerequisites

```bash
pip install pandas selenium undetected-chromedriver
```

Make sure you have Chrome browser installed.

## 🎯 Usage

### Quick Start (Recommended Workflow)

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Phase 1 Test** (Start here!):
```bash
python run_scraper.py
# Select option 1: Phase 1 Test Mode
```

3. **Phase 2 Test** (After Phase 1):
```bash
python run_scraper.py
# Select option 5: Phase 2 Test Mode
```

4. **Consolidate Data**:
```bash
python consolidate_data.py
```

### Production Workflow

1. **Phase 1 - Basic Data** (Choose one):
   - Option 2: Single State
   - Option 3: Custom limits
   - Option 4: All states (takes hours!)

2. **Phase 2 - Detailed Data** (Choose one):
   - Option 6: Custom school limit
   - Option 7: All schools (takes very long!)

3. **Consolidate**:
   - Run `consolidate_data.py` to merge all data

### Direct Python Usage

```python
from Schools import SchoolDataScraper

# Create scraper instance
scraper = SchoolDataScraper()

# Test with limited data
scraper.run_full_scraping(max_states=2, max_districts_per_state=2)

# Or run for all data (takes very long time)
# scraper.run_full_scraping()
```

## Configuration

Edit `config.py` to customize:

- **Timing**: Delays between requests
- **Limits**: Default maximum states/districts
- **Output**: File naming and directory
- **Browser**: Headless mode, window size
- **Logging**: Log level and format

## 📊 Output Data Structure

### Phase 1 Files: `schools_basic_[State]_[District]_[timestamp].csv`
**Basic Information:**
- `udise_code` - Unique school identifier
- `school_name` - School name
- `state`, `district`, `edu_district`, `edu_block` - Location info
- `school_category`, `school_management`, `school_type` - School classification
- `class_range`, `school_location` - Educational details
- `address`, `pin_code` - Contact information
- `operational_status`, `last_modified` - Status info
- `know_more_link` - URL for detailed data (Phase 2)

### Phase 2 Files: `schools_detailed_complete_[timestamp].csv`
**Detailed Information (includes all Phase 1 data plus):**
- `detail_location`, `detail_school_category` - Enhanced classification
- `detail_class_from`, `detail_class_to` - Grade range
- `year_of_establishment` - Founding year
- `national_management`, `state_management` - Management details
- `affiliation_board_sec`, `affiliation_board_hsec` - Board affiliations
- `total_students`, `total_boys`, `total_girls` - Student enrollment
- `total_teachers`, `male_teachers`, `female_teachers` - Staff data

### Consolidated File: `schools_consolidated_complete_[timestamp].csv`
**Complete Dataset:** Merges Phase 1 and Phase 2 data with comprehensive school information

## States Covered

The scraper processes all Indian states and union territories:
- Andaman & Nicobar Islands
- Andhra Pradesh
- Arunachal Pradesh
- Assam
- Bihar
- Chandigarh
- Chhattisgarh
- Dadra & Nagar Haveli and Daman & Diu
- Delhi
- Goa
- Gujarat
- Haryana
- Himachal Pradesh
- Jammu & Kashmir
- Jharkhand
- Karnataka
- Kendriya Vidyalaya Sanghathan
- Kerala
- Ladakh
- Lakshadweep
- Madhya Pradesh
- Maharashtra
- Manipur
- Meghalaya
- Mizoram
- Nagaland
- Navodaya Vidyalaya Samiti
- Odisha
- Puducherry
- Punjab
- Rajasthan
- Sikkim
- Tamil Nadu
- Telangana
- Tripura
- Uttarakhand
- Uttar Pradesh
- West Bengal

## Important Notes

1. **Rate Limiting**: The scraper includes delays to avoid overwhelming the server
2. **Long Runtime**: Full scraping can take many hours or days
3. **Backup Files**: Intermediate backups are saved every 100 records
4. **Error Recovery**: Individual state/district failures won't stop the entire process
5. **Browser Automation**: Uses undetected-chromedriver to avoid detection

## Troubleshooting

### Common Issues

1. **Chrome Driver Issues**:
   - Make sure Chrome browser is installed
   - Update undetected-chromedriver: `pip install --upgrade undetected-chromedriver`

2. **Timeout Errors**:
   - Increase wait times in `config.py`
   - Check internet connection

3. **Element Not Found**:
   - Website structure may have changed
   - Check if selectors in the code need updating

4. **Memory Issues**:
   - For very large datasets, consider processing states individually
   - Increase backup frequency in config

### Logs

Check the console output for detailed logging information about:
- Progress through states and districts
- Errors and warnings
- Data extraction statistics

## Legal and Ethical Considerations

- This scraper is for educational and research purposes
- Respect the website's terms of service
- Use reasonable delays between requests
- Don't overload the server with too many concurrent requests

## Contributing

Feel free to improve the scraper by:
- Adding better error handling
- Improving data extraction accuracy
- Adding new output formats
- Optimizing performance
