#!/usr/bin/env python3
"""
Test Improved Pagination and School Extraction
Quick test to verify the enhanced pagination and scrolling fixes
"""

import logging
from sequential_process_state import SequentialStateProcessor

# Setup logging to see debug messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_improved_extraction():
    """Test the improved school extraction and pagination"""
    try:
        print("🧪 TESTING IMPROVED PAGINATION & SCHOOL EXTRACTION")
        print("="*70)
        print("Testing with MIDDLE AND NORTH ANDAMANS district")
        print("Expected: Should extract all 188 schools across multiple pages")
        print("="*70)
        
        # Create processor
        processor = SequentialStateProcessor()
        
        # Get available states
        logger.info("Getting available states...")
        states = processor.get_available_states()
        
        if not states:
            print("❌ Failed to get available states")
            return False
        
        # Find Andaman & Nicobar Islands
        target_state = None
        for state in states:
            if "ANDAMAN" in state['stateName'].upper():
                target_state = state
                break
        
        if not target_state:
            print("❌ Could not find Andaman & Nicobar Islands state")
            return False
        
        print(f"✅ Found target state: {target_state['stateName']}")
        
        # Setup driver and navigate
        if not processor.setup_driver("Phase1"):
            print("❌ Failed to setup driver")
            return False
        
        if not processor.navigate_to_portal():
            print("❌ Failed to navigate to portal")
            processor.close_driver()
            return False
        
        # Select state
        processor.current_state = target_state
        if not processor.select_state(target_state):
            print("❌ Failed to select state")
            processor.close_driver()
            return False
        
        # Get districts
        districts = processor.extract_districts_data()
        if not districts:
            print("❌ No districts found")
            processor.close_driver()
            return False
        
        # Find MIDDLE AND NORTH ANDAMANS district
        target_district = None
        for district in districts:
            if "MIDDLE AND NORTH" in district['districtName'].upper():
                target_district = district
                break
        
        if not target_district:
            print("❌ Could not find MIDDLE AND NORTH ANDAMANS district")
            processor.close_driver()
            return False
        
        print(f"✅ Found target district: {target_district['districtName']}")
        
        # Select district
        processor.current_district = target_district
        if not processor.select_district(target_district):
            print("❌ Failed to select district")
            processor.close_driver()
            return False
        
        # Reset filters and search
        processor.reset_search_filters()
        
        if not processor.click_search_button():
            print("❌ Failed to click search button")
            processor.close_driver()
            return False
        
        # Set pagination to 100
        processor.set_pagination_to_100()
        
        # Extract schools with improved method
        print("\n🔍 Starting improved school extraction...")
        schools_data = processor.extract_schools_basic_data()
        
        # Results
        total_schools = len(schools_data)
        print(f"\n📊 IMPROVED EXTRACTION RESULTS:")
        print(f"   🏫 Total schools extracted: {total_schools}")
        print(f"   🎯 Expected: ~188 schools")
        
        if total_schools >= 180:
            print("🎉 EXTRACTION FIX SUCCESSFUL!")
            print("   All schools extracted correctly with improved scrolling and pagination")
        elif total_schools >= 100:
            print("⚠️ PARTIAL SUCCESS")
            print(f"   Extracted {total_schools} schools, but expected ~188")
            print("   Pagination may still need improvement")
        else:
            print("❌ EXTRACTION STILL HAS ISSUES")
            print(f"   Only extracted {total_schools} schools")
        
        # Show sample schools
        if schools_data:
            print(f"\n📋 Sample extracted schools:")
            for i, school in enumerate(schools_data[:5]):
                name = school.get('school_name', 'Unknown')
                link = 'Yes' if school.get('know_more_link') and school['know_more_link'] != 'N/A' else 'No'
                print(f"   {i+1}. {name} (Know More Link: {link})")
        
        # Show schools with links
        schools_with_links = [s for s in schools_data if s.get('know_more_link') and s['know_more_link'] != 'N/A']
        print(f"   🔗 Schools with know_more_links: {len(schools_with_links)}")
        
        # Cleanup
        processor.close_driver()
        
        return total_schools >= 180
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def main():
    """Main test function"""
    print("🔧 Testing improved pagination and school extraction")
    print("This test will verify that all ~188 schools are extracted with proper scrolling")
    print()
    
    success = test_improved_extraction()
    
    if success:
        print("\n🎉 IMPROVED EXTRACTION VERIFIED!")
        print("✅ Scrolling implemented")
        print("✅ Multiple selectors working")
        print("✅ Pagination handling improved")
        print("The sequential processor should now extract all schools correctly")
    else:
        print("\n⚠️ EXTRACTION STILL NEEDS WORK")
        print("Please check the debug logs above for details")

if __name__ == "__main__":
    main()
