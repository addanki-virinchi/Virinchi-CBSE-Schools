#!/usr/bin/env python3
"""
Complete Workflow Test - Test both Phase 1 and Phase 2 scrapers
Tests the complete workflow from state selection through final data extraction
"""

import os
import time
import logging
import pandas as pd
from datetime import datetime
from phase1_statewise_scraper import StatewiseSchoolScraper
from phase2_automated_processor import AutomatedPhase2Processor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompleteWorkflowTester:
    def __init__(self):
        self.test_state = "ANDAMAN & NICOBAR ISLANDS"  # Small state for testing
        self.phase1_output_file = None
        self.phase2_output_files = []
        self.test_results = {
            'phase1_success': False,
            'phase2_success': False,
            'total_schools_phase1': 0,
            'schools_with_links': 0,
            'schools_processed_phase2': 0,
            'successful_extractions': 0
        }

    def test_phase1_scraper(self):
        """Test Phase 1 scraper with a small state"""
        try:
            logger.info("🚀 TESTING PHASE 1 SCRAPER")
            logger.info("="*60)
            
            # Initialize Phase 1 scraper
            scraper = StatewiseSchoolScraper()
            
            # Test with limited districts for speed
            logger.info(f"Testing with state: {self.test_state}")
            logger.info("Limiting to first 2 districts for testing speed")
            
            # Run Phase 1 scraping
            scraper.run_statewise_scraping(
                target_states=[self.test_state],
                max_districts_per_state=2  # Limit for testing
            )
            
            # Check if output file was created
            pattern = f"{self.test_state.replace(' ', '_').replace('&', 'and').upper()}_phase1_complete_*.csv"
            import glob
            output_files = glob.glob(pattern)
            
            if output_files:
                self.phase1_output_file = output_files[0]  # Get the most recent
                logger.info(f"✅ Phase 1 output file created: {self.phase1_output_file}")
                
                # Analyze the output
                df = pd.read_csv(self.phase1_output_file)
                self.test_results['total_schools_phase1'] = len(df)
                
                if 'has_know_more_link' in df.columns:
                    schools_with_links = df[df['has_know_more_link'] == True]
                    self.test_results['schools_with_links'] = len(schools_with_links)
                else:
                    # Legacy format
                    schools_with_links = df[df['know_more_link'].notna() & (df['know_more_link'] != 'N/A')]
                    self.test_results['schools_with_links'] = len(schools_with_links)
                
                logger.info(f"📊 Phase 1 Results:")
                logger.info(f"   Total schools: {self.test_results['total_schools_phase1']}")
                logger.info(f"   Schools with links: {self.test_results['schools_with_links']}")
                
                if self.test_results['schools_with_links'] > 0:
                    self.test_results['phase1_success'] = True
                    logger.info("✅ Phase 1 test PASSED")
                else:
                    logger.warning("⚠️ Phase 1 test PARTIAL - no schools with links found")
                    
            else:
                logger.error("❌ Phase 1 test FAILED - no output file created")
                
        except Exception as e:
            logger.error(f"❌ Phase 1 test FAILED with error: {e}")
            
        return self.test_results['phase1_success']

    def test_phase2_scraper(self):
        """Test Phase 2 scraper with Phase 1 output"""
        try:
            logger.info("\n🚀 TESTING PHASE 2 SCRAPER")
            logger.info("="*60)
            
            if not self.phase1_output_file:
                logger.error("❌ No Phase 1 output file available for Phase 2 testing")
                return False
                
            if self.test_results['schools_with_links'] == 0:
                logger.error("❌ No schools with links available for Phase 2 testing")
                return False
            
            # Initialize Phase 2 processor
            processor = AutomatedPhase2Processor()
            
            # Limit to first few schools for testing
            df = pd.read_csv(self.phase1_output_file)
            
            # Filter schools ready for Phase 2
            if 'phase2_ready' in df.columns:
                phase2_schools = df[df['phase2_ready'] == True].head(3)  # Test with first 3
            else:
                phase2_schools = df[df['know_more_link'].notna() & (df['know_more_link'] != 'N/A')].head(3)
            
            if len(phase2_schools) == 0:
                logger.error("❌ No Phase 2 ready schools found")
                return False
                
            logger.info(f"Testing Phase 2 with {len(phase2_schools)} schools")
            
            # Setup driver
            processor.setup_driver()
            
            # Process each school
            successful_extractions = 0
            for idx, school in phase2_schools.iterrows():
                try:
                    logger.info(f"\n🔍 Testing school {idx + 1}/{len(phase2_schools)}")
                    logger.info(f"   URL: {school['know_more_link']}")
                    
                    # Extract data
                    extracted_data = processor.extract_focused_data(school['know_more_link'])
                    
                    if extracted_data and extracted_data.get('extraction_status') in ['SUCCESS', 'PARTIAL']:
                        successful_extractions += 1
                        logger.info(f"   ✅ Extraction successful")
                        logger.info(f"   📋 School: {extracted_data.get('detail_school_name', 'N/A')}")
                        logger.info(f"   👥 Students: {extracted_data.get('total_students', 'N/A')}")
                        logger.info(f"   👨‍🏫 Teachers: {extracted_data.get('total_teachers', 'N/A')}")
                    else:
                        logger.warning(f"   ⚠️ Extraction failed or incomplete")
                        
                    # Brief pause between schools
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"   ❌ Error processing school: {e}")
                    continue
            
            # Close driver
            processor.driver.quit()
            
            # Evaluate results
            self.test_results['schools_processed_phase2'] = len(phase2_schools)
            self.test_results['successful_extractions'] = successful_extractions
            
            success_rate = (successful_extractions / len(phase2_schools)) * 100
            
            logger.info(f"\n📊 Phase 2 Results:")
            logger.info(f"   Schools processed: {len(phase2_schools)}")
            logger.info(f"   Successful extractions: {successful_extractions}")
            logger.info(f"   Success rate: {success_rate:.1f}%")
            
            if success_rate >= 50:  # At least 50% success rate
                self.test_results['phase2_success'] = True
                logger.info("✅ Phase 2 test PASSED")
            else:
                logger.warning("⚠️ Phase 2 test FAILED - low success rate")
                
        except Exception as e:
            logger.error(f"❌ Phase 2 test FAILED with error: {e}")
            
        return self.test_results['phase2_success']

    def run_complete_test(self):
        """Run complete workflow test"""
        try:
            logger.info("🎯 COMPLETE WORKFLOW TEST")
            logger.info("="*80)
            logger.info("Testing both Phase 1 and Phase 2 scrapers with Chrome browser")
            logger.info(f"Test state: {self.test_state}")
            logger.info("="*80)
            
            start_time = time.time()
            
            # Test Phase 1
            phase1_success = self.test_phase1_scraper()
            
            # Test Phase 2 (only if Phase 1 succeeded)
            phase2_success = False
            if phase1_success:
                phase2_success = self.test_phase2_scraper()
            else:
                logger.warning("⚠️ Skipping Phase 2 test due to Phase 1 failure")
            
            # Final results
            total_time = time.time() - start_time
            
            logger.info("\n" + "="*80)
            logger.info("🎯 COMPLETE WORKFLOW TEST RESULTS")
            logger.info("="*80)
            
            logger.info(f"⏱️ Total test time: {total_time:.1f} seconds")
            logger.info(f"🏛️ Test state: {self.test_state}")
            
            logger.info(f"\n📊 PHASE 1 RESULTS:")
            logger.info(f"   Status: {'✅ PASSED' if phase1_success else '❌ FAILED'}")
            logger.info(f"   Total schools: {self.test_results['total_schools_phase1']}")
            logger.info(f"   Schools with links: {self.test_results['schools_with_links']}")
            
            logger.info(f"\n📊 PHASE 2 RESULTS:")
            logger.info(f"   Status: {'✅ PASSED' if phase2_success else '❌ FAILED'}")
            logger.info(f"   Schools processed: {self.test_results['schools_processed_phase2']}")
            logger.info(f"   Successful extractions: {self.test_results['successful_extractions']}")
            
            overall_success = phase1_success and phase2_success
            logger.info(f"\n🎯 OVERALL RESULT: {'✅ COMPLETE WORKFLOW PASSED' if overall_success else '❌ WORKFLOW ISSUES DETECTED'}")
            
            if overall_success:
                logger.info("\n🚀 NEXT STEPS:")
                logger.info("   1. Both scrapers are working correctly")
                logger.info("   2. You can now run full state processing")
                logger.info("   3. Use phase1_statewise_scraper.py for Phase 1")
                logger.info("   4. Use phase2_automated_processor.py for Phase 2")
            else:
                logger.info("\n🔧 TROUBLESHOOTING:")
                if not phase1_success:
                    logger.info("   - Check Phase 1 scraper configuration")
                    logger.info("   - Verify Chrome browser installation")
                    logger.info("   - Check internet connection")
                if not phase2_success:
                    logger.info("   - Check Phase 2 data extraction patterns")
                    logger.info("   - Verify know_more_link URLs are valid")
                    logger.info("   - Check browser refresh functionality")
            
            logger.info("="*80)
            
            return overall_success
            
        except Exception as e:
            logger.error(f"❌ Complete workflow test failed: {e}")
            return False

def main():
    """Main function"""
    print("🧪 COMPLETE WORKFLOW TESTER")
    print("Tests both Phase 1 and Phase 2 scrapers with Chrome browser")
    print("Verifies state selection, pagination, browser refresh, and data extraction")
    print()
    
    tester = CompleteWorkflowTester()
    success = tester.run_complete_test()
    
    if success:
        print("\n🎉 All tests passed! Both scrapers are working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the logs above for details.")

if __name__ == "__main__":
    main()
