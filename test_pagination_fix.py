#!/usr/bin/env python3
"""
Test Pagination Fix
Quick test to verify pagination improvements work correctly
"""

import logging
from sequential_process_state import SequentialStateProcessor

# Setup logging to see debug messages
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pagination_fix():
    """Test the pagination fix with MIDDLE AND NORTH ANDAMANS district"""
    try:
        print("🧪 TESTING PAGINATION FIX")
        print("="*60)
        print("Testing with MIDDLE AND NORTH ANDAMANS district")
        print("Expected: Should extract all 181 schools across multiple pages")
        print("="*60)
        
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
            print("Available districts:")
            for d in districts:
                print(f"   - {d['districtName']}")
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
        
        # Extract schools with improved pagination
        print("\n🔍 Starting school extraction with improved pagination...")
        schools_data = processor.extract_schools_basic_data()
        
        # Results
        total_schools = len(schools_data)
        print(f"\n📊 PAGINATION TEST RESULTS:")
        print(f"   🏫 Total schools extracted: {total_schools}")
        print(f"   🎯 Expected: 181 schools")
        
        if total_schools >= 181:
            print("✅ PAGINATION FIX SUCCESSFUL!")
            print("   All schools extracted correctly")
        elif total_schools >= 100:
            print("⚠️ PARTIAL SUCCESS")
            print(f"   Extracted {total_schools} schools, but expected 181")
            print("   Pagination may still have issues")
        else:
            print("❌ PAGINATION FIX FAILED")
            print(f"   Only extracted {total_schools} schools")
        
        # Show schools with links
        schools_with_links = [s for s in schools_data if s.get('know_more_link') and s['know_more_link'] != 'N/A']
        print(f"   🔗 Schools with know_more_links: {len(schools_with_links)}")
        
        # Cleanup
        processor.close_driver()
        
        return total_schools >= 181
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def main():
    """Main test function"""
    print("🔧 Testing pagination fix for MIDDLE AND NORTH ANDAMANS")
    print("This test will verify that all 181 schools are extracted")
    print()
    
    success = test_pagination_fix()
    
    if success:
        print("\n🎉 PAGINATION FIX VERIFIED!")
        print("The sequential processor should now extract all schools correctly")
    else:
        print("\n⚠️ PAGINATION STILL HAS ISSUES")
        print("Please check the debug logs above for details")

if __name__ == "__main__":
    main()
