# Sequential State Processor - Unified Phase 1 + Phase 2 Workflow

## Overview

The **Sequential State Processor** (`sequential_process_state.py`) is a unified workflow that combines Phase 1 and Phase 2 scrapers into a single, streamlined process. This allows you to process states completely (both phases) one by one with a single command.

## Key Features

✅ **Single Entry Point**: Run everything with one command  
✅ **Sequential Processing**: Complete each state (Phase 1 + Phase 2) before moving to next  
✅ **Integrated Workflow**: Automatic transition from Phase 1 to Phase 2  
✅ **Chrome Browser**: Uses Chrome for both phases  
✅ **All Current Features**: Maintains state selection, pagination, immediate browser refresh, comprehensive data extraction  
✅ **Same Output Formats**: Generates identical CSV files as separate scrapers  

## Quick Start

### 1. Test the Sequential Processor
```bash
python test_sequential_processor.py
```
This tests the unified workflow with a small state to ensure everything works.

### 2. Run the Sequential Processor
```bash
python sequential_process_state.py
```
This is your **single entry point** for complete state processing.

## Processing Options

When you run `sequential_process_state.py`, you'll see:

```
🏛️ SEQUENTIAL STATE PROCESSOR
============================================================
Available processing options:

1. Process ALL states sequentially
2. Process specific states  
3. Test mode (single small state)
4. Show available states
5. Exit
```

### Option 1: Process ALL States
- Processes every available state in India
- Each state is completed (Phase 1 + Phase 2) before moving to next
- Recommended for comprehensive data collection

### Option 2: Process Specific States
- Enter state numbers (e.g., `1,5,10`) or names (e.g., `TAMIL NADU,KERALA`)
- Only selected states will be processed
- Good for targeted data collection

### Option 3: Test Mode
- Processes one small state (like Andaman & Nicobar Islands)
- Perfect for testing and validation
- Quick way to verify everything works

## Workflow Details

For each state, the processor follows this sequence:

```
🏛️ STATE: [State Name]
├── 📋 PHASE 1: Extract basic school data for entire state
│   ├── Navigate to UDISE Plus portal
│   ├── Select state and extract all districts
│   ├── Process each district with pagination
│   ├── Extract basic school data from listing pages
│   └── Save consolidated CSV: [STATE]_phase1_complete_[timestamp].csv
│
├── 🔍 PHASE 2: Process schools with know_more_links
│   ├── Load Phase 1 CSV and filter schools ready for Phase 2
│   ├── Setup Chrome driver for detailed extraction
│   ├── For each school with know_more_link:
│   │   ├── Navigate to detail page
│   │   ├── Perform IMMEDIATE browser refresh
│   │   ├── Extract comprehensive data from specific HTML structures
│   │   └── Save extraction status indicators
│   └── Save batch results: [STATE]_phase2_batch[N]_[timestamp].csv
│
└── ✅ COMPLETE: Move to next state
```

## Data Extraction

### Phase 1 Data (Basic)
- State and district information
- UDISE codes
- School names and basic details
- Know_more_links (critical for Phase 2)
- Operational status and categories

### Phase 2 Data (Detailed)
- **Basic Details**: From `.innerPad div` with `.schoolInfoCol` elements
- **Student Enrollment**: From `.bg-white div` with `.H3Value` elements
  - Total Students, Boys, Girls
- **Teacher Data**: From similar HTML structures
  - Total Teachers, Male Teachers, Female Teachers
- **Extraction Status**: SUCCESS/PARTIAL/FAILED indicators

## Output Files

### Phase 1 Output
```
[STATE_NAME]_phase1_complete_[timestamp].csv
```
- Contains ALL schools from the state
- Includes `has_know_more_link` and `phase2_ready` columns
- Schools with and without know_more_links are segregated

### Phase 2 Output
```
[STATE_NAME]_phase2_batch[N]_[timestamp].csv
```
- Contains detailed data for schools with know_more_links
- Multiple batch files per state for large datasets
- Includes extraction status and field counts

## Performance Features

### Chrome Browser Optimization
- Optimized Chrome settings for both phases
- JavaScript enabled for Phase 2 dynamic content
- Memory and resource optimizations
- Balanced timeouts for reliability

### Sequential Processing Benefits
- **No Manual Intervention**: Automatic Phase 1 → Phase 2 transition
- **Complete State Processing**: Each state fully processed before next
- **Error Recovery**: Continues with next state if current state fails
- **Progress Tracking**: Clear status indicators and summaries

## Error Handling

- **State-Level Recovery**: If one state fails, processing continues with next
- **Phase-Level Recovery**: If Phase 1 fails, Phase 2 is skipped for that state
- **Detailed Logging**: Comprehensive logs for troubleshooting
- **Status Indicators**: Clear success/failure indicators for each extraction

## Monitoring Progress

The processor provides real-time progress updates:

```
🏛️ PROCESSING STATE 2/5: TAMIL NADU
📋 PHASE 1: Extracting basic school data for TAMIL NADU
   🏘️ Processing district 1/32: ARIYALUR
   ✅ Completed ARIYALUR: 156 schools
📊 PHASE 1 SUMMARY - TAMIL NADU:
   🏫 Total schools: 4,523
   🔗 Schools with links (Phase 2 ready): 3,891
🔍 PHASE 2: Processing detailed data for TAMIL NADU
   🔄 Processing batch 1/156: schools 1-25
   ✅ Batch 1 completed: 23/25 successful
✅ COMPLETED: Both phases successful for TAMIL NADU
```

## Comparison with Separate Scrapers

| Feature | Separate Scrapers | Sequential Processor |
|---------|------------------|---------------------|
| **Commands** | 2 separate commands | 1 single command |
| **Manual Steps** | Run Phase 1, wait, run Phase 2 | Fully automated |
| **State Processing** | Manual coordination | Automatic sequential |
| **Error Recovery** | Manual intervention | Automatic continuation |
| **Progress Tracking** | Separate logs | Unified progress view |
| **Data Quality** | Same | Same |
| **Performance** | Same | Same |

## Troubleshooting

### Common Issues

1. **Chrome Driver Issues**
   ```bash
   pip install --upgrade undetected-chromedriver
   ```

2. **Import Errors**
   - Ensure you're in the Schools directory
   - All required files should be present

3. **Network Issues**
   - Check internet connection
   - Verify UDISE Plus portal accessibility

### Testing
Always test first:
```bash
python test_sequential_processor.py
```

## Next Steps

1. **Test**: Run `python test_sequential_processor.py`
2. **Execute**: Run `python sequential_process_state.py`
3. **Select**: Choose your processing option
4. **Monitor**: Watch the progress logs
5. **Analyze**: Review generated CSV files

The Sequential State Processor provides the same high-quality data extraction as the separate scrapers but with a much more streamlined and automated workflow.
