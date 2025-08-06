#!/usr/bin/env python3
"""
Sequential State Processor - Complete Phase 1 → Phase 2 workflow per state
- Processes one state at a time: Phase 1 → Phase 2 → Next State
- Robust connection error handling and retry mechanisms
- Maintains ultra-fast performance optimizations
- Resilient to connection issues with automatic recovery
"""

import time
import logging
import os
import glob
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SequentialStateProcessor:
    def __init__(self):
        self.processed_states = []
        self.failed_states = []
        self.total_schools_processed = 0
        self.start_time = None
        self.max_retries = 3
        self.retry_delay = 30  # seconds
        
        # State list (all 38 Indian states)
        self.states_list = [
            "ANDAMAN & NICOBAR ISLANDS",
            "ANDHRA PRADESH", 
            "ARUNACHAL PRADESH",
            "ASSAM",
            "BIHAR",
            "CHANDIGARH",
            "CHHATTISGARH",
            "DADRA & NAGAR HAVELI AND DAMAN & DIU",
            "DELHI",
            "GOA",
            "GUJARAT",
            "HARYANA",
            "HIMACHAL PRADESH",
            "JAMMU & KASHMIR",
            "JHARKHAND",
            "KARNATAKA",
            "KENDRIYA VIDYALAYA SANGHATHAN",
            "KERALA",
            "LADAKH",
            "LAKSHADWEEP",
            "MADHYA PRADESH",
            "MAHARASHTRA",
            "MANIPUR",
            "MEGHALAYA",
            "MIZORAM",
            "NAGALAND",
            "NAVODAYA VIDYALAYA SAMITI",
            "ODISHA",
            "PUDUCHERRY",
            "PUNJAB",
            "RAJASTHAN",
            "SIKKIM",
            "TAMILNADU",
            "TELANGANA",
            "TRIPURA",
            "UTTARAKHAND",
            "UTTAR PRADESH",
            "WEST BENGAL"
        ]

    def run_phase1_for_state(self, state_name):
        """Run Phase 1 scraper for a specific state with retry mechanism"""
        logger.info(f"🚀 Starting Phase 1 for state: {state_name}")
        
        for attempt in range(self.max_retries):
            try:
                # Create a modified Phase 1 script for single state processing
                result = self.execute_phase1_single_state(state_name)
                
                if result:
                    logger.info(f"✅ Phase 1 completed successfully for {state_name}")
                    return True
                else:
                    logger.warning(f"⚠️ Phase 1 failed for {state_name} (attempt {attempt + 1}/{self.max_retries})")
                    
            except Exception as e:
                logger.error(f"❌ Phase 1 error for {state_name} (attempt {attempt + 1}/{self.max_retries}): {e}")
            
            if attempt < self.max_retries - 1:
                logger.info(f"⏳ Retrying Phase 1 for {state_name} in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
        
        logger.error(f"❌ Phase 1 failed for {state_name} after {self.max_retries} attempts")
        return False

    def execute_phase1_single_state(self, state_name):
        """Execute Phase 1 for a single state"""
        try:
            # Import the Phase 1 scraper components
            from phase1_statewise_scraper import StatewiseSchoolScraper

            logger.info(f"   🔧 Initializing Phase 1 scraper for {state_name}")
            scraper = StatewiseSchoolScraper()
            
            # Setup driver with connection error handling
            scraper.setup_driver()
            
            # Navigate to portal with retry
            success = scraper.navigate_to_portal()
            if not success:
                logger.error(f"   ❌ Failed to navigate to portal for {state_name}")
                return False
            
            # Extract states list
            states = scraper.extract_states_data()
            if not states:
                logger.error(f"   ❌ Failed to extract states data for {state_name}")
                return False
            
            # Find the target state
            target_state = None
            for state in states:
                if state['stateName'] == state_name:
                    target_state = state
                    break
            
            if not target_state:
                logger.error(f"   ❌ State {state_name} not found in states list")
                return False
            
            # Process the single state
            logger.info(f"   🎯 Processing single state: {state_name}")
            success = scraper.process_single_state(target_state)
            
            # Cleanup
            scraper.driver.quit()
            
            return success
            
        except Exception as e:
            logger.error(f"   ❌ Error in Phase 1 execution for {state_name}: {e}")
            return False

    def find_phase1_csv_for_state(self, state_name):
        """Find the Phase 1 CSV file for a specific state"""
        try:
            # Clean state name for filename matching
            clean_state = state_name.replace(' ', '_').replace('&', 'and').replace('/', '_').upper()
            
            # Look for the Phase 1 CSV file
            pattern = f"{clean_state}_phase1_complete_*.csv"
            csv_files = glob.glob(pattern)
            
            if csv_files:
                # Return the most recent file
                latest_file = max(csv_files, key=os.path.getctime)
                logger.info(f"   📁 Found Phase 1 CSV: {latest_file}")
                return latest_file
            else:
                logger.error(f"   ❌ No Phase 1 CSV found for {state_name}")
                return None
                
        except Exception as e:
            logger.error(f"   ❌ Error finding Phase 1 CSV for {state_name}: {e}")
            return None

    def run_phase2_for_state(self, state_name, csv_file):
        """Run Phase 2 processing for a specific state with retry mechanism"""
        logger.info(f"🔄 Starting Phase 2 for state: {state_name}")
        
        for attempt in range(self.max_retries):
            try:
                result = self.execute_phase2_single_state(state_name, csv_file)
                
                if result:
                    logger.info(f"✅ Phase 2 completed successfully for {state_name}")
                    return True
                else:
                    logger.warning(f"⚠️ Phase 2 failed for {state_name} (attempt {attempt + 1}/{self.max_retries})")
                    
            except Exception as e:
                logger.error(f"❌ Phase 2 error for {state_name} (attempt {attempt + 1}/{self.max_retries}): {e}")
            
            if attempt < self.max_retries - 1:
                logger.info(f"⏳ Retrying Phase 2 for {state_name} in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
        
        logger.error(f"❌ Phase 2 failed for {state_name} after {self.max_retries} attempts")
        return False

    def execute_phase2_single_state(self, state_name, csv_file):
        """Execute Phase 2 for a single state"""
        try:
            # Import the Phase 2 processor components
            from phase2_automated_processor import AutomatedPhase2Processor
            
            logger.info(f"   🔧 Initializing Phase 2 processor for {state_name}")
            processor = AutomatedPhase2Processor()
            
            # Setup driver with connection error handling
            processor.setup_driver()
            
            # Process the single state file
            success = processor.process_state_file_automated(csv_file)
            
            # Cleanup
            processor.driver.quit()
            
            return success
            
        except Exception as e:
            logger.error(f"   ❌ Error in Phase 2 execution for {state_name}: {e}")
            return False

    def process_state_complete_cycle(self, state_name):
        """Process a complete Phase 1 → Phase 2 cycle for one state"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🏛️ PROCESSING STATE: {state_name}")
        logger.info(f"{'='*80}")
        
        state_start_time = time.time()
        
        try:
            # Phase 1: Extract school data
            logger.info(f"📋 PHASE 1: Extracting school data for {state_name}")
            phase1_success = self.run_phase1_for_state(state_name)
            
            if not phase1_success:
                logger.error(f"❌ Phase 1 failed for {state_name} - skipping Phase 2")
                self.failed_states.append(f"{state_name} (Phase 1 failed)")
                return False
            
            # Find the generated CSV file
            csv_file = self.find_phase1_csv_for_state(state_name)
            if not csv_file:
                logger.error(f"❌ No Phase 1 CSV found for {state_name} - skipping Phase 2")
                self.failed_states.append(f"{state_name} (CSV not found)")
                return False
            
            # Brief pause between phases
            time.sleep(5)
            
            # Phase 2: Process detailed data
            logger.info(f"🔍 PHASE 2: Processing detailed data for {state_name}")
            phase2_success = self.run_phase2_for_state(state_name, csv_file)
            
            if not phase2_success:
                logger.error(f"❌ Phase 2 failed for {state_name}")
                self.failed_states.append(f"{state_name} (Phase 2 failed)")
                return False
            
            # Success!
            state_time = time.time() - state_start_time
            self.processed_states.append(state_name)
            
            logger.info(f"✅ COMPLETED {state_name} in {state_time/60:.1f} minutes")
            logger.info(f"📊 Progress: {len(self.processed_states)}/{len(self.states_list)} states completed")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Critical error processing {state_name}: {e}")
            self.failed_states.append(f"{state_name} (Critical error)")
            return False

    def run_sequential_processing(self):
        """Run the complete sequential state processing workflow"""
        try:
            self.start_time = time.time()
            
            logger.info("🚀 STARTING SEQUENTIAL STATE PROCESSING")
            logger.info("="*80)
            logger.info(f"📋 Total states to process: {len(self.states_list)}")
            logger.info(f"🔄 Workflow: State → Phase 1 → Phase 2 → Next State")
            logger.info("="*80)
            
            # Process each state sequentially
            for i, state_name in enumerate(self.states_list, 1):
                logger.info(f"\n🎯 STARTING STATE {i}/{len(self.states_list)}: {state_name}")
                
                success = self.process_state_complete_cycle(state_name)
                
                if success:
                    logger.info(f"✅ State {i} completed successfully: {state_name}")
                else:
                    logger.warning(f"⚠️ State {i} failed: {state_name}")
                
                # Brief pause between states
                if i < len(self.states_list):
                    logger.info("⏳ Brief pause before next state...")
                    time.sleep(10)
            
            # Final summary
            self.show_final_summary()
            
        except Exception as e:
            logger.error(f"❌ Critical error in sequential processing: {e}")
        finally:
            logger.info("🔒 Sequential processing completed")

    def show_final_summary(self):
        """Show final processing summary"""
        total_time = time.time() - self.start_time
        
        logger.info(f"\n{'='*80}")
        logger.info("🎯 SEQUENTIAL PROCESSING COMPLETED")
        logger.info(f"{'='*80}")
        logger.info(f"⏱️ Total processing time: {total_time/3600:.1f} hours")
        logger.info(f"✅ Successfully processed states: {len(self.processed_states)}")
        logger.info(f"❌ Failed states: {len(self.failed_states)}")
        logger.info(f"📈 Success rate: {len(self.processed_states)/len(self.states_list)*100:.1f}%")
        
        if self.processed_states:
            logger.info(f"\n✅ SUCCESSFUL STATES:")
            for state in self.processed_states:
                logger.info(f"   ✓ {state}")
        
        if self.failed_states:
            logger.info(f"\n❌ FAILED STATES:")
            for state in self.failed_states:
                logger.info(f"   ✗ {state}")
        
        logger.info(f"\n💾 Output files pattern:")
        logger.info(f"   Phase 1: *_phase1_complete_*.csv")
        logger.info(f"   Phase 2: *_phase2_batch*_*.csv")
        logger.info("🎉 Sequential processing complete!")

def main():
    """Main function for sequential state processing"""
    print("🚀 SEQUENTIAL STATE PROCESSOR")
    print("Processes each state completely (Phase 1 → Phase 2) before moving to next state")
    print("Resilient to connection issues with automatic retry mechanisms")
    print()
    
    try:
        processor = SequentialStateProcessor()
        processor.run_sequential_processing()
    except Exception as e:
        print(f"❌ Critical error: {e}")
        print("Please check the logs above for details")

if __name__ == "__main__":
    main()
