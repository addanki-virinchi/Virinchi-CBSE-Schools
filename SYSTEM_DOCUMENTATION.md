# School Scraping System - State-wise & Focused Processing

## Overview
This updated school scraping system provides state-wise data extraction with focused Phase 2 processing for improved speed and reliability.

## System Architecture

### Phase 1: State-wise Basic Data Extraction
**File:** `phase1_statewise_scraper.py`

**Purpose:** Extract basic school data and segregate by know_more_links availability

**Key Features:**
- ✅ **State-wise CSV Output**: Creates separate files for each state
- ✅ **Data Segregation**: Separates schools WITH and WITHOUT know_more_links
- ✅ **Comprehensive Coverage**: Processes all states or specific target states
- ✅ **Progress Tracking**: Real-time logging and state summaries

**Output Files per State:**
1. `[STATE_NAME]_with_links_[timestamp].csv` - Schools ready for Phase 2
2. `[STATE_NAME]_no_links_[timestamp].csv` - Schools without detail links (reference)
3. `[STATE_NAME]_complete_[timestamp].csv` - Combined complete dataset

### Phase 2: Comprehensive Detail Extraction
**File:** `phase2_comprehensive_processor.py`

**Purpose:** Extract ALL comprehensive data fields including school name from detail pages

**Comprehensive Data Categories:**
1. **School Name**: Extracted from detail page HTML (`<h3 class="custom-word-break schoolNameCSS mb-2">`)
2. **Student Data**: Total students, boys, girls breakdown
3. **Teacher Data**: Total teachers, male, female breakdown
4. **Location Details**: Location, category, type, establishment details
5. **Affiliation Boards**: Secondary & Higher Secondary education board affiliations
6. **Management Details**: National/State management information
7. **Additional Info**: Academic year, school codes, addresses, PIN codes

**Key Features:**
- 🌐 **Chrome Browser**: Reliable and widely compatible
- 📊 **Comprehensive Extraction**: All available data fields
- 🔄 **Batch Processing**: Handles large datasets efficiently
- 📈 **Progress Tracking**: Real-time success rate monitoring
- 🔍 **Duplicate Detection**: Enhanced error handling and retry mechanisms

## Usage Instructions

### Running Phase 1 (State-wise Scraper)

```bash
cd Schools
python phase1_statewise_scraper.py
```

**Options:**
1. **Process ALL states** - Complete nationwide extraction
2. **Process specific states** - Target particular states
3. **Test mode** - Limited districts for testing

**Example for specific states:**
```
Select option: 2
Enter state names: ANDAMAN & NICOBAR ISLANDS, GOA, SIKKIM
```

### Running Phase 2 (Comprehensive Processor)

```bash
cd Schools
python phase2_comprehensive_processor.py
```

**Process:**
1. Select from available `_with_links_` CSV files
2. Choose batch size (recommended: 20-30 schools)
3. Set start index for resuming processing
4. Monitor comprehensive data extraction progress
5. Review extracted school names and all detail fields

## File Naming Conventions

### Phase 1 Output Files
- **With Links**: `[STATE_NAME]_with_links_[timestamp].csv`
- **No Links**: `[STATE_NAME]_no_links_[timestamp].csv`  
- **Complete**: `[STATE_NAME]_complete_[timestamp].csv`

**Examples:**
- `ANDAMAN_AND_NICOBAR_ISLANDS_with_links_20250805_143022.csv`
- `GOA_with_links_20250805_143022.csv`
- `SIKKIM_no_links_20250805_143022.csv`

### Phase 2 Output Files
- **Comprehensive Details**: `[STATE_NAME]_with_comprehensive_details_[timestamp].csv`
- **Backup**: `[STATE_NAME]_with_comprehensive_details_backup_[timestamp].csv`

## Data Structure

### Phase 1 Basic Data Fields
```
- state, state_id, district, district_id
- extraction_date, udise_code, operational_status
- school_name, edu_district, edu_block
- academic_year, school_category, school_management
- class_range, school_type, school_location
- address, pin_code, last_modified
- know_more_link (CRITICAL for Phase 2)
```

### Phase 2 Comprehensive Data Fields
```
- detail_school_name (from HTML detail page)
- total_students, total_boys, total_girls
- total_teachers, male_teachers, female_teachers
- location_detail, school_category_detail, class_from, class_to
- school_type_detail, year_of_establishment
- national_management, state_management
- affiliation_board_sec, affiliation_board_hsec
- academic_year_detail, school_code, village_name, cluster_name
- block_name, district_name, pin_code_detail
- extraction_status (SUCCESS/FAILED)
```

## Processing Workflow

### Complete State Processing Workflow

1. **Phase 1 Execution**
   ```bash
   python phase1_statewise_scraper.py
   # Select: Process specific states
   # Enter: ANDAMAN & NICOBAR ISLANDS
   ```

2. **Review Phase 1 Results**
   - Check `ANDAMAN_AND_NICOBAR_ISLANDS_with_links_[timestamp].csv`
   - Verify schools have valid know_more_links
   - Note total schools ready for Phase 2

3. **Phase 2 Execution**
   ```bash
   python phase2_focused_processor.py
   # Select: ANDAMAN_AND_NICOBAR_ISLANDS_with_links_[timestamp].csv
   # Batch size: 30
   # Start index: 0
   ```

4. **Monitor Progress**
   - Watch success rates in real-time
   - Check for duplicate data warnings
   - Resume from last processed index if needed

5. **Final Results**
   - `ANDAMAN_AND_NICOBAR_ISLANDS_with_details_[timestamp].csv`
   - Contains both Phase 1 basic data + Phase 2 focused details

## Performance Optimizations

### Phase 1 Optimizations
- **State-wise processing**: Prevents data loss if process interrupts
- **Immediate CSV saving**: Data saved per district completion
- **Memory efficient**: Processes one state at a time

### Phase 2 Optimizations
- **Focused extraction**: Only 4 data categories vs 10+ previously
- **Reduced wait times**: Optimized for essential data only
- **Batch processing**: 20-30 schools per batch for stability
- **Duplicate detection**: Prevents processing same data repeatedly

## Error Handling & Recovery

### Phase 1 Recovery
- **State-level**: If a state fails, others continue processing
- **District-level**: Failed districts logged, others continue
- **Data preservation**: Completed districts saved immediately

### Phase 2 Recovery
- **Batch-level**: Process in small batches to minimize loss
- **School-level**: Failed schools marked, others continue
- **Progress saving**: Every 10 schools processed
- **Resume capability**: Start from any index to resume

## Monitoring & Troubleshooting

### Success Rate Monitoring
- **Target Phase 2 success rate**: 70-85%
- **Warning threshold**: <50% success rate
- **Critical threshold**: <25% success rate

### Common Issues & Solutions

1. **Low Success Rate (<50%)**
   - Reduce batch size to 10-15 schools
   - Increase wait times in navigation
   - Check internet connectivity

2. **Duplicate Data Detection**
   - Automatic retry with page refresh
   - Manual verification of extracted data
   - Check for website changes

3. **Navigation Failures**
   - Verify know_more_links are valid
   - Check for website maintenance
   - Retry with fresh browser session

## Best Practices

### For Large-Scale Processing
1. **Start with test mode** - Verify system works with limited data
2. **Process in batches** - Don't attempt all schools at once
3. **Monitor actively** - Watch for success rate drops
4. **Save frequently** - Use built-in progress saving
5. **Plan for interruptions** - Note last processed index

### For Production Use
1. **Schedule during off-peak hours** - Reduce website load
2. **Use stable internet connection** - Prevent navigation failures
3. **Monitor disk space** - CSV files can become large
4. **Keep backups** - Multiple copies of successful extractions

## File Management

### Recommended Directory Structure
```
Schools/
├── phase1_statewise_scraper.py
├── phase2_focused_processor.py
├── results/
│   ├── phase1/
│   │   ├── ANDAMAN_AND_NICOBAR_ISLANDS_with_links_20250805.csv
│   │   ├── GOA_with_links_20250805.csv
│   │   └── ...
│   └── phase2/
│       ├── ANDAMAN_AND_NICOBAR_ISLANDS_with_details_20250805.csv
│       ├── GOA_with_details_20250805.csv
│       └── ...
└── logs/
    ├── phase1_20250805.log
    └── phase2_20250805.log
```

### Cleanup Recommendations
- **Keep latest 3 versions** of each state file
- **Archive older files** to separate directory
- **Compress large CSV files** for storage efficiency

## Support & Maintenance

### Regular Maintenance
- **Update Chrome driver** monthly
- **Test with sample data** before large runs
- **Monitor website changes** that might affect extraction
- **Review success rates** and adjust parameters

### Troubleshooting Resources
- **Detailed logging**: All operations logged with timestamps
- **Progress tracking**: Real-time success rate monitoring
- **Error categorization**: Navigation vs extraction vs data issues
- **Recovery procedures**: Resume from any point in process

---

## Quick Start Guide

### For First-Time Users
1. Run Phase 1 in test mode: `python phase1_statewise_scraper.py` → Option 3
2. Verify output files are created correctly
3. Run Phase 2 on test results: `python phase2_focused_processor.py`
4. Check success rates and data quality
5. Scale up to full state processing

### For Production Processing
1. Plan processing schedule (off-peak hours recommended)
2. Start Phase 1 for target states
3. Monitor Phase 1 completion and file creation
4. Begin Phase 2 processing in batches
5. Monitor success rates and adjust batch sizes as needed
