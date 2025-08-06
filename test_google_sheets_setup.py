#!/usr/bin/env python3
"""
Test Google Sheets Setup
Helps verify Google Sheets authentication and setup
"""

import json
import gspread
from google.oauth2.service_account import Credentials

def test_google_sheets_setup():
    """Test Google Sheets setup and provide setup instructions"""
    
    print("🧪 GOOGLE SHEETS SETUP TEST")
    print("="*60)
    
    # Step 1: Check credentials file
    try:
        with open('credentials.json', 'r') as f:
            creds_data = json.load(f)
        
        service_account_email = creds_data.get('client_email', 'Not found')
        project_id = creds_data.get('project_id', 'Not found')
        
        print("✅ Credentials file found")
        print(f"   📧 Service Account Email: {service_account_email}")
        print(f"   🏗️ Project ID: {project_id}")
        
    except Exception as e:
        print(f"❌ Error reading credentials.json: {e}")
        return False
    
    # Step 2: Test authentication
    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        credentials = Credentials.from_service_account_file('credentials.json', scopes=scope)
        client = gspread.authorize(credentials)
        
        print("✅ Authentication successful")
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False
    
    # Step 3: Test spreadsheet access
    sheet_name = "Know your School Database"
    try:
        spreadsheet = client.open(sheet_name)
        print(f"✅ Successfully opened spreadsheet: {sheet_name}")
        print(f"   📊 Spreadsheet ID: {spreadsheet.id}")
        print(f"   🔗 Spreadsheet URL: https://docs.google.com/spreadsheets/d/{spreadsheet.id}")
        
        # List existing worksheets
        worksheets = spreadsheet.worksheets()
        print(f"   📋 Existing worksheets: {len(worksheets)}")
        for ws in worksheets:
            print(f"      - {ws.title}")
        
        return True
        
    except gspread.SpreadsheetNotFound:
        print(f"❌ Spreadsheet '{sheet_name}' not found")
        print()
        print("📋 SETUP INSTRUCTIONS:")
        print("1. Create a Google Sheet named 'Know your School Database'")
        print("2. Share the sheet with your service account email:")
        print(f"   📧 {service_account_email}")
        print("3. Give 'Editor' permissions to the service account")
        print()
        print("🔗 Quick setup:")
        print("1. Go to: https://sheets.google.com")
        print("2. Create a new sheet")
        print("3. Rename it to: Know your School Database")
        print("4. Click 'Share' button")
        print(f"5. Add this email: {service_account_email}")
        print("6. Set permission to 'Editor'")
        print("7. Click 'Send'")
        
        return False
        
    except Exception as e:
        print(f"❌ Error accessing spreadsheet: {e}")
        print()
        print("📋 POSSIBLE ISSUES:")
        print("1. Spreadsheet name might be incorrect")
        print("2. Service account might not have access")
        print("3. Spreadsheet might be in a different Google account")
        print()
        print("🔧 TROUBLESHOOTING:")
        print(f"1. Verify spreadsheet name: 'Know your School Database'")
        print(f"2. Share spreadsheet with: {service_account_email}")
        print("3. Ensure service account has 'Editor' permissions")
        
        return False

def test_worksheet_creation():
    """Test creating a worksheet"""
    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        credentials = Credentials.from_service_account_file('credentials.json', scopes=scope)
        client = gspread.authorize(credentials)
        spreadsheet = client.open("Know your School Database")
        
        # Test creating a worksheet
        test_worksheet_name = "TEST_WORKSHEET"
        
        try:
            # Try to get existing test worksheet
            test_ws = spreadsheet.worksheet(test_worksheet_name)
            print(f"✅ Found existing test worksheet: {test_worksheet_name}")
        except gspread.WorksheetNotFound:
            # Create new test worksheet
            test_ws = spreadsheet.add_worksheet(title=test_worksheet_name, rows=100, cols=20)
            print(f"✅ Created test worksheet: {test_worksheet_name}")
        
        # Test adding data
        test_data = [
            ["State", "District", "School Name", "Total Students"],
            ["TEST_STATE", "TEST_DISTRICT", "TEST_SCHOOL", "100"]
        ]
        
        test_ws.clear()  # Clear existing data
        test_ws.append_rows(test_data)
        print("✅ Successfully added test data")
        
        # Clean up - delete test worksheet
        spreadsheet.del_worksheet(test_ws)
        print("✅ Cleaned up test worksheet")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing worksheet creation: {e}")
        return False

def main():
    """Main test function"""
    print("🔧 Testing Google Sheets integration for Schools project")
    print()
    
    # Test basic setup
    setup_success = test_google_sheets_setup()
    
    if setup_success:
        print()
        print("🧪 Testing worksheet operations...")
        worksheet_success = test_worksheet_creation()
        
        if worksheet_success:
            print()
            print("🎉 GOOGLE SHEETS SETUP COMPLETE!")
            print("✅ Authentication working")
            print("✅ Spreadsheet access working")
            print("✅ Worksheet operations working")
            print()
            print("🚀 Ready to use Google Sheets integration!")
            print("Run: python sequential_process_state.py")
        else:
            print()
            print("⚠️ Basic setup works but worksheet operations failed")
            print("Check permissions and try again")
    else:
        print()
        print("❌ Setup incomplete. Please follow the instructions above.")

if __name__ == "__main__":
    main()
