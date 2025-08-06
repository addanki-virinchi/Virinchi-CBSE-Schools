#!/usr/bin/env python3
"""
Quick Workflow Test Runner
Simple script to test both Phase 1 and Phase 2 scrapers
"""

import sys
import os

def main():
    print("🧪 QUICK WORKFLOW TEST")
    print("="*50)
    print("This will test both Phase 1 and Phase 2 scrapers")
    print("Using Chrome browser with a small test state")
    print("="*50)
    
    # Check if we're in the right directory
    if not os.path.exists('phase1_statewise_scraper.py'):
        print("❌ Error: Please run this script from the Schools directory")
        print("   Current directory should contain phase1_statewise_scraper.py")
        return
    
    if not os.path.exists('phase2_automated_processor.py'):
        print("❌ Error: phase2_automated_processor.py not found")
        print("   Please ensure all scraper files are in the current directory")
        return
    
    print("✅ Found required scraper files")
    print()
    
    # Ask user for confirmation
    response = input("Do you want to run the complete workflow test? (y/N): ").strip().lower()
    
    if response != 'y':
        print("Test cancelled.")
        return
    
    print("\n🚀 Starting workflow test...")
    print("This may take 5-10 minutes depending on your internet connection")
    print()
    
    try:
        # Import and run the test
        from test_complete_workflow import CompleteWorkflowTester
        
        tester = CompleteWorkflowTester()
        success = tester.run_complete_test()
        
        print("\n" + "="*60)
        if success:
            print("🎉 WORKFLOW TEST COMPLETED SUCCESSFULLY!")
            print("Both Phase 1 and Phase 2 scrapers are working correctly.")
            print()
            print("Next steps:")
            print("1. Run Phase 1 for your target states:")
            print("   python phase1_statewise_scraper.py")
            print()
            print("2. Run Phase 2 on the generated CSV files:")
            print("   python phase2_automated_processor.py")
        else:
            print("⚠️ WORKFLOW TEST DETECTED ISSUES")
            print("Please check the detailed logs above for troubleshooting.")
            print()
            print("Common issues:")
            print("- Chrome browser not installed or outdated")
            print("- Internet connection problems")
            print("- Website structure changes")
        print("="*60)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure all required packages are installed:")
        print("pip install pandas selenium undetected-chromedriver")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        print("Please check the error details above")

if __name__ == "__main__":
    main()
