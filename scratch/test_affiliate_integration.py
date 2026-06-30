import sys
import os
sys.path.insert(0, ".")

from backend.routers.search import get_integrated_platform_results

def test_affiliate_integration():
    mock_top_item = {
        "id": "SNEAKER_001",
        "title": "Nike Air Max 270 Running Shoes White",
        "price": "₹7,995",
        "original_price": "₹9,995",
        "discount": "20% off",
        "platform": "Amazon India",
        "category": "footwear",
        "rating": "4.6"
    }

    print("Running affiliate integration checks...")
    results = get_integrated_platform_results(mock_top_item["title"], mock_top_item)

    expected_platforms = ["Amazon India", "Flipkart", "Myntra", "Meesho"]
    
    # Check 1: Ensure exactly 4 platform results exist
    if len(results) != 4:
        print(f"FAILED: Expected 4 platform results, got {len(results)}")
        return
    else:
        print("CHECK 1 PASSED: Got exactly 4 platform results.")

    # Check 2: Verify platforms, prices, and affiliate URLs
    passed_checks = 0
    for pr in results:
        plat = pr.platform
        url = pr.affiliate_url
        price_display = str(pr.price).replace("₹", "Rs.")
        
        print(f"\nPlatform: {plat}")
        print(f"  Price: {price_display}")
        print(f"  Affiliate URL: {url}")
        
        if plat not in expected_platforms:
            print(f"  FAILED: Platform name '{plat}' is unexpected.")
            continue
            
        if plat == "Amazon India":
            # Amazon URL check (tag=yourtag-21)
            if "amazon.in" in url and "tag=yourtag-21" in url:
                print("  PASSED: Valid Amazon India search link + affiliate tag.")
                passed_checks += 1
            else:
                print("  FAILED: Missing affiliate tag or wrong domain.")
                
        elif plat == "Flipkart":
            # Flipkart URL check (ad/affiliate, affid=)
            if "flipkart.com" in url and "ad/affiliate" in url:
                print("  PASSED: Valid Flipkart redirect link + affiliate tag.")
                passed_checks += 1
            else:
                print("  FAILED: Missing affiliate wrapper or wrong domain.")
                
        elif plat == "Myntra":
            # Myntra URL check (linksredirect.com, Myntra.com encoded)
            if "linksredirect.com" in url and "myntra.com" in url:
                print("  PASSED: Valid Myntra link mapped through Cuelinks.")
                passed_checks += 1
            else:
                print("  FAILED: Missing cuelinks wrapper or wrong target domain.")
                
        elif plat == "Meesho":
            # Meesho URL check (linksredirect.com, meesho.com encoded)
            if "linksredirect.com" in url and "meesho.com" in url:
                print("  PASSED: Valid Meesho link mapped through Cuelinks.")
                passed_checks += 1
            else:
                print("  FAILED: Missing cuelinks wrapper or wrong target domain.")

    print(f"\nIntegrated Platform checks: {passed_checks}/4 passed.")

if __name__ == "__main__":
    test_affiliate_integration()
