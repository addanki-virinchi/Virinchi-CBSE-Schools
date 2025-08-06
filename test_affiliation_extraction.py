#!/usr/bin/env python3
"""
Test Affiliation Board Extraction
Tests the enhanced extraction logic with the actual HTML structure
"""

import re

def test_affiliation_extraction():
    """Test affiliation board extraction with real HTML structure"""
    
    # Sample HTML structure as provided by user
    sample_html = '''
    <div _ngcontent-ng-c1808753454="" class="schoolInfoCol">
        <div _ngcontent-ng-c1808753454="" class="title">
            <p _ngcontent-ng-c1808753454="" class="fw-600">Affiliation Board Sec.</p>
        </div>
        <div _ngcontent-ng-c1808753454="" class="blueCol">
            <span _ngcontent-ng-c1808753454="">1-CBSE</span>
        </div>
    </div>
    <div _ngcontent-ng-c1808753454="" class="schoolInfoCol disable-card">
        <div _ngcontent-ng-c1808753454="" class="title">
            <p _ngcontent-ng-c1808753454="" class="fw-600">Affiliation Board HSec.</p>
        </div>
        <div _ngcontent-ng-c1808753454="" class="blueCol">
            <span _ngcontent-ng-c1808753454="">NA</span>
        </div>
    </div>
    '''
    
    print("🧪 TESTING AFFILIATION BOARD EXTRACTION")
    print("="*60)
    print("Testing with actual HTML structure from Phase 2 pages")
    print()
    
    # Test regex patterns
    print("📋 Testing Regex Patterns:")
    
    # Test Affiliation Board Sec.
    sec_patterns = [
        r'Affiliation Board Sec\.[^>]*>[^<]*</[^>]*>[^<]*<[^>]*>[^<]*<[^>]*>([^<]+)',
        r'Affiliation Board Sec\.[:\s]*([^\n<]+)',
        r'Affiliation Board Sec\.</p></div><div[^>]*><span[^>]*>([^<]+)</span>'
    ]
    
    sec_found = False
    for i, pattern in enumerate(sec_patterns, 1):
        match = re.search(pattern, sample_html, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            print(f"   ✅ Pattern {i} found Affiliation Board Sec: '{value}'")
            sec_found = True
            break
        else:
            print(f"   ❌ Pattern {i} failed for Affiliation Board Sec")
    
    # Test Affiliation Board HSec.
    hsec_patterns = [
        r'Affiliation Board HSec\.[^>]*>[^<]*</[^>]*>[^<]*<[^>]*>[^<]*<[^>]*>([^<]+)',
        r'Affiliation Board HSec\.[:\s]*([^\n<]+)',
        r'Affiliation Board HSec\.</p></div><div[^>]*><span[^>]*>([^<]+)</span>'
    ]
    
    hsec_found = False
    for i, pattern in enumerate(hsec_patterns, 1):
        match = re.search(pattern, sample_html, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            print(f"   ✅ Pattern {i} found Affiliation Board HSec: '{value}'")
            hsec_found = True
            break
        else:
            print(f"   ❌ Pattern {i} failed for Affiliation Board HSec")
    
    print()
    print("📊 EXTRACTION RESULTS:")
    print(f"   Affiliation Board Sec: {'✅ Successfully extracted' if sec_found else '❌ Not extracted'}")
    print(f"   Affiliation Board HSec: {'✅ Successfully extracted' if hsec_found else '❌ Not extracted'}")
    
    # Test value handling
    print()
    print("🔍 VALUE HANDLING TEST:")
    test_values = ["1-CBSE", "NA", "N/A", "CBSE", "State Board", ""]
    
    for value in test_values:
        should_keep = value and value.upper() not in ['N/A', 'NA', '']
        status = "✅ Keep" if should_keep else "❌ Skip"
        print(f"   Value '{value}': {status}")
    
    print()
    print("="*60)
    if sec_found and hsec_found:
        print("🎉 AFFILIATION BOARD EXTRACTION TEST PASSED!")
        print("✅ Both fields can be successfully extracted from Phase 2 pages")
    else:
        print("⚠️ AFFILIATION BOARD EXTRACTION NEEDS IMPROVEMENT")
        print("❌ Some fields could not be extracted")
    
    print()
    print("📁 These fields will appear in Phase 2 CSV output:")
    print("   - affiliation_board_sec: Contains values like '1-CBSE', 'State Board', etc.")
    print("   - affiliation_board_hsec: Contains values like 'CBSE', 'NA', etc.")
    print("="*60)

if __name__ == "__main__":
    test_affiliation_extraction()
