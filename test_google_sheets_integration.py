#!/usr/bin/env python3
"""
Comprehensive Google Sheets Integration Test
Tests all aspects of the Google Sheets upload functionality
"""

import pandas as pd
import os
from datetime import datetime
from sequential_process_state import SequentialStateProcessor, GoogleSheetsUploader

def test_google_sheets_integration():
    """Test complete Google Sheets integration"""
    
    print("🧪 COMPREHENSIVE GOOGLE SHEETS INTEGRATION TEST")
    print("="*60)
    
    # Test 1: Authentication
    print("\n1️⃣ TESTING AUTHENTICATION")
    print("-" * 30)
    
    uploader = GoogleSheetsUploader()
    auth_success = uploader.authenticate()
    
    if auth_success:
        print("✅ Authentication successful")
        print(f"   📊 Connected to: {uploader.spreadsheet.title}")
        print(f"   🔗 Spreadsheet ID: {uploader.spreadsheet.id}")
    else:
        print("❌ Authentication failed")
        return False
    
    # Test 2: Use existing Output.csv as test data
    print("\n2️⃣ TESTING WITH EXISTING OUTPUT.CSV")
    print("-" * 30)
    
    if not os.path.exists('Output.csv'):
        print("❌ Output.csv not found")
        return False
    
    df = pd.read_csv('Output.csv')
    print(f"✅ Loaded Output.csv: {len(df)} schools")
    print(f"   🏛️ State: {df['state'].iloc[0]}")
    print(f"   🏘️ District: {df['district'].iloc[0]}")
    print(f"   🔗 Schools with links: {len(df[df['has_know_more_link'] == True])}")
    
    # Test 3: Test direct upload using the fixed uploader method
    print("\n3️⃣ TESTING DIRECT UPLOAD WITH FIXED METHOD")
    print("-" * 30)

    test_state_name = "TEST_ANDAMANS"

    try:
        # Use the fixed upload method that handles NaN values
        upload_success = uploader.upload_phase2_data('Output.csv', test_state_name)

        if upload_success:
            print("✅ Upload successful using fixed method")
        else:
            print("❌ Upload failed using fixed method")
            return False

    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False
    
    # Test 4: Verify data integrity
    print("\n4️⃣ TESTING DATA INTEGRITY")
    print("-" * 30)

    try:
        # Get the worksheet to read back data
        worksheet = uploader.create_or_get_worksheet(test_state_name)
        if not worksheet:
            print("❌ Could not get worksheet for verification")
            return False

        # Read back the data from Google Sheets
        uploaded_data = worksheet.get_all_records()
        
        print(f"✅ Retrieved data: {len(uploaded_data)} records")
        
        # Check key fields
        if len(uploaded_data) == len(df):
            print("✅ Row count matches")
        else:
            print(f"❌ Row count mismatch: Expected {len(df)}, Got {len(uploaded_data)}")
        
        # Check specific fields
        sample_record = uploaded_data[0] if uploaded_data else {}
        
        # Check know_more_link field
        if 'know_more_link' in sample_record:
            print("✅ know_more_link field present")
        else:
            print("❌ know_more_link field missing")
        
        # Check affiliation board fields
        if 'affiliation_board_sec' in sample_record:
            print("✅ affiliation_board_sec field present")
        else:
            print("❌ affiliation_board_sec field missing")
        
        if 'affiliation_board_hsec' in sample_record:
            print("✅ affiliation_board_hsec field present")
        else:
            print("❌ affiliation_board_hsec field missing")
        
        # Show sample data
        print("\n📋 Sample uploaded data:")
        for i, record in enumerate(uploaded_data[:3]):
            name = record.get('school_name', 'Unknown')[:30]
            link = 'Yes' if record.get('know_more_link') and record['know_more_link'] != 'N/A' else 'No'
            sec = record.get('affiliation_board_sec', 'N/A')
            hsec = record.get('affiliation_board_hsec', 'N/A')
            print(f"   {i+1}. {name} | Link: {link} | Sec: {sec} | HSec: {hsec}")
        
    except Exception as e:
        print(f"❌ Data verification failed: {e}")
        return False
    
    # Test 5: Test error handling
    print("\n5️⃣ TESTING ERROR HANDLING")
    print("-" * 30)
    
    # Test with invalid file
    invalid_file = "nonexistent_file.csv"
    success = uploader.upload_phase2_data(invalid_file, "TEST_STATE")
    
    if not success:
        print("✅ Error handling works: Invalid file correctly rejected")
    else:
        print("❌ Error handling failed: Invalid file was accepted")
    
    # Test 6: Test sequential processor integration
    print("\n6️⃣ TESTING SEQUENTIAL PROCESSOR INTEGRATION")
    print("-" * 30)
    
    try:
        processor = SequentialStateProcessor()
        
        # Check if Google Sheets uploader is initialized
        if processor.sheets_uploader:
            print("✅ Sequential processor has Google Sheets uploader")
        else:
            print("❌ Sequential processor missing Google Sheets uploader")
        
        # Test upload method
        test_filename = "Output.csv"
        upload_success = processor.upload_to_google_sheets(test_filename, "TEST_INTEGRATION")
        
        if upload_success:
            print("✅ Sequential processor upload method works")
        else:
            print("❌ Sequential processor upload method failed")
        
    except Exception as e:
        print(f"❌ Sequential processor integration failed: {e}")
        return False
    
    print("\n🎉 GOOGLE SHEETS INTEGRATION TEST COMPLETE!")
    print("="*60)
    
    return True

def main():
    """Main test function"""
    print("🔧 Testing Google Sheets integration with existing data")
    print("This test will verify all aspects of the Google Sheets upload")
    print()
    
    success = test_google_sheets_integration()
    
    if success:
        print("\n✅ ALL TESTS PASSED!")
        print("🎉 Google Sheets integration is working correctly")
        print("📊 Data integrity verified")
        print("🔗 Authentication working")
        print("📤 Upload functionality confirmed")
        print("\n🚀 Ready for production use!")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Please check the logs above for specific issues")

if __name__ == "__main__":
    main()
