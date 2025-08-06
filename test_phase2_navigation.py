#!/usr/bin/env python3
"""
Quick test to verify Phase 2 navigation and data extraction fixes
"""

import logging
from phase2_automated_processor import AutomatedPhase2Processor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_phase2_navigation():
    """Test Phase 2 navigation with a few sample URLs"""
    
    # Sample URLs from the CSV file
    test_urls = [
        "https://kys.udiseplus.gov.in/#/schooldetail/5300055/12",
        "https://kys.udiseplus.gov.in/#/schooldetail/5300172/12", 
        "https://kys.udiseplus.gov.in/#/schooldetail/5300065/12"
    ]
    
    logger.info("🧪 TESTING PHASE 2 NAVIGATION AND DATA EXTRACTION")
    logger.info("="*60)
    
    try:
        # Initialize processor
        processor = AutomatedPhase2Processor()
        processor.setup_driver()
        
        results = []
        
        for i, url in enumerate(test_urls, 1):
            logger.info(f"\n🎯 TEST {i}/3: {url}")
            logger.info("-" * 50)
            
            # Extract data
            data = processor.extract_focused_data(url)
            
            if data:
                results.append({
                    'url': url,
                    'school_name': data.get('detail_school_name', 'N/A'),
                    'students': data.get('total_students', 'N/A'),
                    'teachers': data.get('total_teachers', 'N/A')
                })
                
                logger.info(f"✅ Result: {data.get('detail_school_name', 'N/A')} | Students: {data.get('total_students', 'N/A')} | Teachers: {data.get('total_teachers', 'N/A')}")
            else:
                logger.error(f"❌ Failed to extract data from {url}")
                results.append({
                    'url': url,
                    'school_name': 'FAILED',
                    'students': 'FAILED',
                    'teachers': 'FAILED'
                })
        
        # Summary
        logger.info(f"\n📊 TEST SUMMARY:")
        logger.info("="*60)
        
        unique_names = set()
        unique_students = set()
        unique_teachers = set()
        
        for result in results:
            logger.info(f"URL: {result['url']}")
            logger.info(f"   School: {result['school_name']}")
            logger.info(f"   Students: {result['students']}")
            logger.info(f"   Teachers: {result['teachers']}")
            logger.info("")
            
            unique_names.add(result['school_name'])
            unique_students.add(result['students'])
            unique_teachers.add(result['teachers'])
        
        # Check for uniqueness
        logger.info(f"🔍 UNIQUENESS CHECK:")
        logger.info(f"   Unique school names: {len(unique_names)} (should be 3)")
        logger.info(f"   Unique student counts: {len(unique_students)} (should be > 1)")
        logger.info(f"   Unique teacher counts: {len(unique_teachers)} (should be > 1)")
        
        if len(unique_names) == 3 and len(unique_students) > 1:
            logger.info("✅ SUCCESS: Data extraction is working correctly!")
        else:
            logger.error("❌ FAILURE: Still extracting duplicate data!")
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
    finally:
        try:
            processor.driver.quit()
        except:
            pass

if __name__ == "__main__":
    test_phase2_navigation()
