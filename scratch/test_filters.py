import sys
import os
sys.path.insert(0, ".")

from backend.routers.search import is_trusted_and_purchaseable

def test_filters():
    test_cases = [
        # (buy_url, platform, price_str, expected_result)
        ("https://www.amazon.in/dp/B08L5T3Z1D", "Amazon India", "₹1,299", True),
        ("https://www.flipkart.com/shoes", "Flipkart", "₹599", True),
        ("https://www.myntra.com/kurta", "Myntra", "₹899", True),
        ("https://pinterest.com/pin/123", "Pinterest", "₹999", False),  # Blocklisted domain
        ("https://youtube.com/watch?v=123", "YouTube", "₹1,500", False),  # Blocklisted domain
        ("https://www.amazon.in/dp/B08L5T3Z1D", "Amazon India", "Price on Website", False),  # No price
        ("https://www.amazon.in/dp/B08L5T3Z1D", "Amazon India", "", False),  # Empty price
        ("https://www.my-random-blog.com/post1", "My Blog", "₹999", False),  # Blog, not e-commerce, not whitelisted
        ("https://shop.brandstore.com/product", "Brand Store", "₹2,500", True),  # Whitelisted keyword 'shop' in domain
        ("https://brandstore.com/checkout", "Brand Checkout", "₹2,500", True),  # Whitelisted keyword 'checkout' in domain
        ("https://brandstore.com/product", "Brand Store", "₹2,500", True),  # Whitelisted keyword 'Store' in platform name
        ("https://facebook.com/marketplace/item/123", "Facebook Marketplace", "₹500", False),  # Blocklisted domain facebook
    ]

    passed = 0
    for idx, (url, platform, price, expected) in enumerate(test_cases):
        res = is_trusted_and_purchaseable(url, platform, price)
        price_display = price.replace("₹", "Rs.")
        if res == expected:
            print(f"CASE {idx+1} PASSED: {platform} ({price_display}) -> {res}")
            passed += 1
        else:
            print(f"CASE {idx+1} FAILED: {platform} ({price_display}) -> Expected {expected}, got {res}")

    print(f"\n{passed}/{len(test_cases)} tests passed.")

if __name__ == "__main__":
    test_filters()
