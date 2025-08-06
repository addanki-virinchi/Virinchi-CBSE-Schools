#!/usr/bin/env python3
"""
School Data Scraper Runner
This script provides different modes to run the school data scraper
"""

import sys
import os
from Schools import SchoolDataScraper
from phase2_detailed_scraper import Phase2DetailedScraper
import config

def run_phase1_test_mode():
    """Run Phase 1 scraper in test mode with limited states and districts"""
    print("Running PHASE 1 TEST mode (basic data extraction)...")
    scraper = SchoolDataScraper()
    scraper.run_phase1_basic_scraping(max_states=2, max_districts_per_state=2)
    print(f"Phase 1 test completed. Total schools extracted: {len(scraper.all_schools_data)}")

def run_phase2_test_mode():
    """Run Phase 2 scraper in test mode"""
    print("Running PHASE 2 TEST mode (detailed data extraction)...")
    scraper = Phase2DetailedScraper()

    # Load basic data from Phase 1
    basic_data = scraper.load_basic_data_files()

    if basic_data is not None:
        scraper.process_schools_detailed_data(basic_data, max_schools=10)
        print(f"Phase 2 test completed. Total detailed schools: {len(scraper.detailed_schools_data)}")
    else:
        print("No basic data files found. Please run Phase 1 first.")

def run_phase1_single_state(state_name=None):
    """Run Phase 1 scraper for a single state"""
    if not state_name:
        state_name = input("Enter state name (e.g., 'ANDAMAN & NICOBAR ISLANDS'): ")

    print(f"Running Phase 1 scraper for state: {state_name}")
    scraper = SchoolDataScraper()

    try:
        scraper.setup_driver()
        scraper.navigate_to_portal()
        states = scraper.extract_states_data()

        # Find the specified state
        target_state = None
        for state in states:
            if state['stateName'].upper() == state_name.upper():
                target_state = state
                break

        if not target_state:
            print(f"State '{state_name}' not found!")
            print("Available states:")
            for state in states[:10]:  # Show first 10
                print(f"  - {state['stateName']}")
            print("  ... and more")
            return

        # Process only the target state
        scraper.select_state(target_state)
        districts = scraper.extract_districts_data()

        for district in districts:
            try:
                scraper.select_district(district)
                if scraper.click_search_button():
                    district_schools_data = scraper.extract_schools_basic_data()
                    if district_schools_data:
                        scraper.save_district_data_to_csv(
                            district_schools_data,
                            target_state['stateName'],
                            district['districtName']
                        )
                        scraper.all_schools_data.extend(district_schools_data)
            except Exception as e:
                print(f"Error processing district {district['districtName']}: {e}")
                continue

        scraper.save_data_to_csv(f"schools_basic_{state_name.replace(' ', '_').replace('&', 'and')}.csv")
        print(f"Phase 1 completed. Total schools extracted: {len(scraper.all_schools_data)}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if scraper.driver:
            scraper.driver.quit()

def run_phase1_full_mode():
    """Run Phase 1 scraper for all states and districts"""
    print("Running PHASE 1 FULL mode (all states and districts)...")
    print("This will take a very long time. Are you sure? (y/N): ", end="")

    if input().lower() != 'y':
        print("Cancelled.")
        return

    scraper = SchoolDataScraper()
    scraper.run_phase1_basic_scraping()
    print(f"Phase 1 full scraping completed. Total schools extracted: {len(scraper.all_schools_data)}")

def run_phase1_custom_mode():
    """Run Phase 1 scraper with custom limits"""
    print("Phase 1 Custom mode - set your own limits")

    try:
        max_states = input("Max states to process (press Enter for all): ")
        max_states = int(max_states) if max_states else None

        max_districts = input("Max districts per state (press Enter for all): ")
        max_districts = int(max_districts) if max_districts else None

        print(f"Running Phase 1 with limits: {max_states} states, {max_districts} districts per state")

        scraper = SchoolDataScraper()
        scraper.run_phase1_basic_scraping(max_states=max_states, max_districts_per_state=max_districts)
        print(f"Phase 1 custom scraping completed. Total schools extracted: {len(scraper.all_schools_data)}")

    except ValueError:
        print("Invalid input. Please enter numbers only.")
    except Exception as e:
        print(f"Error: {e}")

def run_phase2_full_mode():
    """Run Phase 2 scraper for all schools from Phase 1"""
    print("Running PHASE 2 FULL mode (detailed data for all schools)...")
    print("This will take a very long time. Are you sure? (y/N): ", end="")

    if input().lower() != 'y':
        print("Cancelled.")
        return

    scraper = Phase2DetailedScraper()
    basic_data = scraper.load_basic_data_files()

    if basic_data is not None:
        scraper.process_schools_detailed_data(basic_data)
        print(f"Phase 2 full scraping completed. Total detailed schools: {len(scraper.detailed_schools_data)}")
    else:
        print("No basic data files found. Please run Phase 1 first.")

def run_phase2_custom_mode():
    """Run Phase 2 scraper with custom limits"""
    print("Phase 2 Custom mode - set your own limits")

    try:
        max_schools = input("Max schools to process for detailed data (press Enter for all): ")
        max_schools = int(max_schools) if max_schools else None

        print(f"Running Phase 2 with limit: {max_schools} schools")

        scraper = Phase2DetailedScraper()
        basic_data = scraper.load_basic_data_files()

        if basic_data is not None:
            scraper.process_schools_detailed_data(basic_data, max_schools=max_schools)
            print(f"Phase 2 custom scraping completed. Total detailed schools: {len(scraper.detailed_schools_data)}")
        else:
            print("No basic data files found. Please run Phase 1 first.")

    except ValueError:
        print("Invalid input. Please enter numbers only.")
    except Exception as e:
        print(f"Error: {e}")

def show_menu():
    """Display the main menu"""
    print("\n" + "="*60)
    print("UDISE Plus School Data Scraper - Two Phase System")
    print("="*60)
    print("PHASE 1 - Basic Data Extraction (with Know More links):")
    print("1. Phase 1 Test Mode (2 states, 2 districts each)")
    print("2. Phase 1 Single State Mode")
    print("3. Phase 1 Custom Mode (set your own limits)")
    print("4. Phase 1 Full Mode (ALL states and districts)")
    print("")
    print("PHASE 2 - Detailed Data Extraction (from Know More links):")
    print("5. Phase 2 Test Mode (10 schools)")
    print("6. Phase 2 Custom Mode (set school limit)")
    print("7. Phase 2 Full Mode (ALL schools from Phase 1)")
    print("")
    print("8. Exit")
    print("="*60)

def main():
    """Main function"""
    # Create output directory if it doesn't exist
    if not os.path.exists(config.OUTPUT_DIRECTORY):
        os.makedirs(config.OUTPUT_DIRECTORY)
    
    while True:
        show_menu()
        choice = input("Select an option (1-8): ").strip()

        if choice == '1':
            run_phase1_test_mode()
        elif choice == '2':
            run_phase1_single_state()
        elif choice == '3':
            run_phase1_custom_mode()
        elif choice == '4':
            run_phase1_full_mode()
        elif choice == '5':
            run_phase2_test_mode()
        elif choice == '6':
            run_phase2_custom_mode()
        elif choice == '7':
            run_phase2_full_mode()
        elif choice == '8':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please select 1-8.")

        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
