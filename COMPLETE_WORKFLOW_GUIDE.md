# Complete Workflow Guide - Phase 1 & Phase 2 Scrapers

## Overview

This guide covers the complete workflow for scraping school data using both Phase 1 (basic data extraction) and Phase 2 (detailed data extraction) scrapers with Chrome browser.

## Requirements Met

✅ **Phase 1 Scraper:**
- State selection functionality works properly
- Pagination handles all pages correctly for selected states
- Basic data extraction captures all required fields from listing pages
- Processes complete states sequentially with optimized performance

✅ **Phase 2 Scraper:**
- Performs immediate browser refresh after entering know_more_link URL
- Extracts comprehensive data from detailed school pages including:
  - Basic Details from .innerPad div with .schoolInfoCol elements
  - Student Enrollment data (Total Students/Boys/Girls) from .bg-white div with .H3Value elements
  - Teacher data (Total Teachers/Male/Female) from similar HTML structures
- Extracts all available relevant data fields
- Provides clear extraction status indicators for each processed record

✅ **Overall Requirements:**
- Both scrapers use Chrome browser
- Maintain fast/efficient performance for large datasets
- Clean separation between Phase 1 and Phase 2 processing
- Complete workflow testing available

## Quick Start

### 1. Test the Complete Workflow
```bash
python run_workflow_test.py
```

This will test both scrapers with a small state to ensure everything works correctly.

### 2. Run Phase 1 (Basic Data Extraction)
```bash
python phase1_statewise_scraper.py
```

Options:
- **Option 1**: Process ALL states (full scraping)
- **Option 2**: Process specific states (enter comma-separated state names)
- **Option 3**: Test mode (limited districts for testing)

### 3. Run Phase 2 (Detailed Data Extraction)
```bash
python phase2_automated_processor.py
```

This automatically finds and processes all Phase 1 CSV files.

## File Structure

### Input Files
- No input files required for Phase 1
- Phase 2 automatically reads Phase 1 output files

### Output Files

**Phase 1 Output:**
- `{STATE_NAME}_phase1_complete_{timestamp}.csv` - Consolidated state data
  - Contains both schools with and without know_more_links
  - Includes `has_know_more_link` and `phase2_ready` columns for easy filtering

**Phase 2 Output:**
- `{STATE_NAME}_phase2_batch{N}_{timestamp}.csv` - Detailed extraction results
  - Contains comprehensive school data from detail pages
  - Includes extraction status indicators

## Key Features

### Phase 1 Scraper Features
- **State Selection**: Robust state selection with multiple fallback methods
- **Pagination**: Automatic pagination with disabled button detection
- **Performance**: Optimized for speed with balanced timeouts
- **Data Segregation**: Separates schools with/without know_more_links
- **Error Recovery**: Continues processing even if individual districts fail

### Phase 2 Scraper Features
- **Immediate Refresh**: Performs browser refresh immediately after navigation
- **Comprehensive Extraction**: Targets specific HTML structures:
  - `.innerPad .schoolInfoCol` for basic details
  - `.bg-white .H3Value` for student enrollment
  - Similar structures for teacher data
- **Status Indicators**: Clear success/partial/failed status for each extraction
- **Batch Processing**: Processes schools in optimal batches for efficiency

## Browser Configuration

Both scrapers use Chrome browser with optimized settings:

```python
# Chrome options for optimal performance
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-extensions")
options.add_argument("--disable-images")  # Speed optimization
options.add_argument("--memory-pressure-off")
```

**Note**: Phase 2 keeps JavaScript enabled for dynamic content extraction.

## Data Extraction Details

### Phase 1 Data Fields
- State and district information
- UDISE code
- School name
- Operational status
- Basic school details (category, type, location, etc.)
- Know_more_link (critical for Phase 2)

### Phase 2 Data Fields
- **Basic Details**: Academic year, location, school category, class range, school type, year of establishment, management details, affiliation boards
- **Student Enrollment**: Total students, boys count, girls count
- **Teacher Data**: Total teachers, male teachers, female teachers
- **Extraction Metadata**: Status indicators, field counts, timestamps

## Performance Optimizations

### Phase 1 Optimizations
- Reduced wait times between operations
- Optimized pagination handling
- Parallel-ready architecture
- Efficient regex patterns for data extraction

### Phase 2 Optimizations
- Immediate browser refresh for fresh content
- Batch processing with optimal batch sizes
- Multiple extraction methods (Selenium + regex fallbacks)
- Comprehensive validation and status reporting

## Troubleshooting

### Common Issues

1. **Chrome Driver Issues**
   - Ensure Chrome browser is installed and updated
   - Update undetected-chromedriver: `pip install --upgrade undetected-chromedriver`

2. **No Data Extracted**
   - Check internet connection
   - Verify website is accessible
   - Run the workflow test to identify specific issues

3. **Phase 2 Extraction Failures**
   - Check if know_more_links are valid
   - Verify browser refresh is working
   - Review extraction status indicators in output

### Error Recovery
- Both scrapers continue processing even if individual records fail
- Detailed logging helps identify and resolve issues
- Batch processing in Phase 2 prevents total failure

## Advanced Usage

### Custom State Processing
```python
# Process specific states only
scraper.run_statewise_scraping(target_states=["TAMIL NADU", "KERALA"])
```

### Limited Testing
```python
# Test with limited districts per state
scraper.run_statewise_scraping(max_districts_per_state=2)
```

### Batch Size Adjustment
```python
# Adjust Phase 2 batch size
processor.optimal_batch_size = 25  # Default is 50
```

## Output Analysis

### Phase 1 Analysis
```python
import pandas as pd
df = pd.read_csv("STATE_NAME_phase1_complete_timestamp.csv")

# Check Phase 2 readiness
phase2_ready = df[df['phase2_ready'] == True]
print(f"Schools ready for Phase 2: {len(phase2_ready)}")
```

### Phase 2 Analysis
```python
# Check extraction success rates
df = pd.read_csv("STATE_NAME_phase2_batch1_timestamp.csv")
success_rate = len(df[df['extraction_status'] == 'SUCCESS']) / len(df) * 100
print(f"Extraction success rate: {success_rate:.1f}%")
```

## Next Steps

1. **Run Workflow Test**: Start with `python run_workflow_test.py`
2. **Phase 1 Processing**: Use `python phase1_statewise_scraper.py`
3. **Phase 2 Processing**: Use `python phase2_automated_processor.py`
4. **Data Analysis**: Analyze output CSV files for insights
5. **Scale Up**: Process additional states as needed

## Support

For issues or questions:
1. Check the detailed logs in the console output
2. Review the troubleshooting section above
3. Run the workflow test to identify specific problems
4. Verify all requirements are met
