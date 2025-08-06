#!/usr/bin/env python3
"""
Test Sequential Processor - Quick test of the unified workflow
Tests the sequential state processor with a small state
"""

import os
import time
import logging
from sequential_process_state import SequentialStateProcessor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_sequential_processor():
    """Test the sequential processor with a small state"""
    try:
        print("🧪 TESTING SEQUENTIAL STATE PROCESSOR")
        print("="*60)
        print("This will test the unified Phase 1 + Phase 2 workflow")
        print("Using a small test state for quick validation")
        print("="*60)

        # Check if we're in the right directory
        if not os.path.exists('sequential_process_state.py'):
            print("❌ Error: Please run this script from the Schools directory")
            print("   Current directory should contain sequential_process_state.py")
            return False

        print("✅ Found sequential_process_state.py")
        print()

        # Ask user for confirmation
        response = input("Do you want to run the sequential processor test? (y/N): ").strip().lower()

        if response != 'y':
            print("Test cancelled.")
            return False

        print("\n🚀 Starting sequential processor test...")
        print("This will process one small state completely (Phase 1 + Phase 2)")
        print()

        # Create processor instance
        processor = SequentialStateProcessor()

        # Get available states
        logger.info("Getting available states for testing...")
        states = processor.get_available_states()

        if not states:
            print("❌ Failed to get available states")
            return False

        # Find a small test state
        test_states = [s for s in states if s['stateName'] in [
            'ANDAMAN & NICOBAR ISLANDS',
            'LAKSHADWEEP',
            'CHANDIGARH',
            'DADRA & NAGAR HAVELI AND DAMAN & DIU'
        ]]

        if not test_states:
            # Fallback to first state
            test_state = states[0]
            print(f"⚠️ Using fallback test state: {test_state['stateName']}")
        else:
            test_state = test_states[0]
            print(f"✅ Using test state: {test_state['stateName']}")

        print(f"\n🎯 Testing complete workflow with: {test_state['stateName']}")
        print("This will:")
        print("1. Run Phase 1 (basic data extraction) for the entire state")
        print("2. Immediately run Phase 2 (detailed extraction) on schools with links")
        print("3. Generate both Phase 1 and Phase 2 output files")
        print()

        start_time = time.time()

        # Process the test state completely
        success = processor.process_single_state_complete(test_state)

        total_time = time.time() - start_time

        print(f"\n{'='*60}")
        if success:
            print("🎉 SEQUENTIAL PROCESSOR TEST PASSED!")
            print(f"✅ Successfully processed {test_state['stateName']}")
            print(f"⏱️ Total time: {total_time:.1f} seconds")
            print()
            print("📁 Output files created:")
            print("   - *_phase1_complete_*.csv (basic school data)")
            print("   - *_phase2_batch*_*.csv (detailed school data)")
            print()
            print("🚀 The sequential processor is working correctly!")
            print("You can now run: python sequential_process_state.py")
        else:
            print("⚠️ SEQUENTIAL PROCESSOR TEST HAD ISSUES")
            print(f"❌ Issues processing {test_state['stateName']}")
            print(f"⏱️ Time taken: {total_time:.1f} seconds")
            print()
            print("Please check the logs above for details")
        print(f"{'='*60}")

        return success

    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        print("Please check the error details above")
        return False

def main():
    """Main function"""
    success = test_sequential_processor()

    if success:
        print("\n✅ Test completed successfully!")
        print("\nNext steps:")
        print("1. Run the full sequential processor:")
        print("   python sequential_process_state.py")
        print()
        print("2. Select your processing option:")
        print("   - Process ALL states sequentially")
        print("   - Process specific states")
        print("   - Test mode (single small state)")
    else:
        print("\n⚠️ Test had issues. Please review the logs above.")

if __name__ == "__main__":
    main()
