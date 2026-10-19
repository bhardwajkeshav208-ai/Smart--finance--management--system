"""
test_price_comparison.py
========================
Automated Test Suite for Smart Suggestion & Price Comparison Engine.

Tests covering the 8 required scenarios:
1. Flipkart is the cheapest.
2. Amazon is the cheapest.
3. Croma is the cheapest.
4. Reliance Digital is the cheapest.
5. Every available offer is above the user's budget.
6. One or more platforms fail to return a valid price.
7. Two platforms have the same lowest price (Tie).
8. A result is for the wrong product variant / accessory rejection.
"""

import unittest
from price_comparison_service import (
    ProductOffer,
    evaluate_price_comparison,
    normalize_price,
    is_accessory,
    extract_variant_info,
)


class TestPriceComparisonScenarios(unittest.TestCase):

    def setUp(self):
        self.default_budget = 50000.0

    def test_scenario_1_flipkart_cheapest(self):
        """Scenario 1: Flipkart has the lowest price below budget."""
        offers = [
            ProductOffer(platform="Amazon India", product_name="Phone X", price=49500.0, url="https://amazon.in/dp/1"),
            ProductOffer(platform="Flipkart", product_name="Phone X", price=47999.0, url="https://flipkart.com/p/1"),
            ProductOffer(platform="Croma", product_name="Phone X", price=48999.0, url="https://croma.com/p/1"),
            ProductOffer(platform="Reliance Digital", product_name="Phone X", price=49999.0, url="https://reliance.in/p/1"),
        ]
        res = evaluate_price_comparison(offers, user_budget=50000.0)
        self.assertEqual(res.case, "A")
        self.assertEqual(len(res.cheapest_offers), 1)
        self.assertEqual(res.cheapest_offers[0].platform, "Flipkart")
        self.assertEqual(res.lowest_verified_price, 47999.0)
        self.assertIn("Flipkart", res.summary_message)
        self.assertFalse(res.has_tie)

    def test_scenario_2_amazon_cheapest(self):
        """Scenario 2: Amazon is cheaper than Flipkart and all other platforms."""
        offers = [
            ProductOffer(platform="Amazon India", product_name="Laptop Pro", price=48999.0, url="https://amazon.in/dp/2"),
            ProductOffer(platform="Flipkart", product_name="Laptop Pro", price=51999.0, url="https://flipkart.com/p/2"),
            ProductOffer(platform="Croma", product_name="Laptop Pro", price=50499.0, url="https://croma.com/p/2"),
            ProductOffer(platform="Reliance Digital", product_name="Laptop Pro", price=52499.0, url="https://reliance.in/p/2"),
        ]
        res = evaluate_price_comparison(offers, user_budget=55000.0)
        self.assertEqual(res.case, "A")
        self.assertEqual(len(res.cheapest_offers), 1)
        self.assertEqual(res.cheapest_offers[0].platform, "Amazon India")
        self.assertEqual(res.lowest_verified_price, 48999.0)
        self.assertIn("Amazon India", res.summary_message)
        # Ensure Flipkart was NOT automatically recommended
        self.assertNotIn("Flipkart for ₹48,999", res.summary_message)

    def test_scenario_3_croma_cheapest(self):
        """Scenario 3: Croma has the lowest verified price."""
        offers = [
            ProductOffer(platform="Amazon India", product_name="LED TV 43", price=29999.0, url="https://amazon.in/dp/3"),
            ProductOffer(platform="Flipkart", product_name="LED TV 43", price=29499.0, url="https://flipkart.com/p/3"),
            ProductOffer(platform="Croma", product_name="LED TV 43", price=27990.0, url="https://croma.com/p/3"),
            ProductOffer(platform="Reliance Digital", product_name="LED TV 43", price=28990.0, url="https://reliance.in/p/3"),
        ]
        res = evaluate_price_comparison(offers, user_budget=30000.0)
        self.assertEqual(res.case, "A")
        self.assertEqual(res.cheapest_offers[0].platform, "Croma")
        self.assertEqual(res.lowest_verified_price, 27990.0)

    def test_scenario_4_reliance_digital_cheapest(self):
        """Scenario 4: Reliance Digital has the lowest verified price."""
        offers = [
            ProductOffer(platform="Amazon India", product_name="Tablet Air", price=34000.0, url="https://amazon.in/dp/4"),
            ProductOffer(platform="Flipkart", product_name="Tablet Air", price=33500.0, url="https://flipkart.com/p/4"),
            ProductOffer(platform="Croma", product_name="Tablet Air", price=33000.0, url="https://croma.com/p/4"),
            ProductOffer(platform="Reliance Digital", product_name="Tablet Air", price=31999.0, url="https://reliance.in/p/4"),
        ]
        res = evaluate_price_comparison(offers, user_budget=35000.0)
        self.assertEqual(res.case, "A")
        self.assertEqual(res.cheapest_offers[0].platform, "Reliance Digital")
        self.assertEqual(res.lowest_verified_price, 31999.0)

    def test_scenario_5_all_offers_above_budget(self):
        """Scenario 5: Every available offer exceeds the user's budget (Case B)."""
        user_budget = 40000.0
        offers = [
            ProductOffer(platform="Amazon India", product_name="Flagship Mobile", price=48999.0, url="https://amazon.in/dp/5"),
            ProductOffer(platform="Flipkart", product_name="Flagship Mobile", price=46999.0, url="https://flipkart.com/p/5"),
            ProductOffer(platform="Croma", product_name="Flagship Mobile", price=47500.0, url="https://croma.com/p/5"),
            ProductOffer(platform="Reliance Digital", product_name="Flagship Mobile", price=49000.0, url="https://reliance.in/p/5"),
        ]
        res = evaluate_price_comparison(offers, user_budget=user_budget)
        self.assertEqual(res.case, "B")
        self.assertEqual(res.lowest_verified_price, 46999.0)
        self.assertEqual(res.cheapest_offers[0].platform, "Flipkart")
        # Explains that it exceeds budget
        self.assertIn("exceeds your budget by ₹6,999.00", res.summary_message)
        self.assertIn("No verified offer is available below your budget", res.summary_message)
        # Check offer budget status labels
        for o in res.offers:
            self.assertIn("Over Budget", o.budget_status)

    def test_scenario_6_platforms_unavailable_or_unverified(self):
        """Scenario 6: One or more platforms fail to return a valid price (Case D handling)."""
        offers = [
            ProductOffer(platform="Amazon India", product_name="Smart Watch", price=None, url="https://amazon.in/s",
                         status="Could not verify (Anti-bot protection)", is_verified=False),
            ProductOffer(platform="Flipkart", product_name="Smart Watch Ultra", price=18999.0, url="https://flipkart.com/p/6",
                         status="Verified Live Price", is_verified=True),
            ProductOffer(platform="Croma", product_name="Smart Watch", price=None, url="https://croma.com/s",
                         status="Could not verify (Access restricted)", is_verified=False),
            ProductOffer(platform="Reliance Digital", product_name="Smart Watch", price=None, url="https://reliance.in/s",
                         status="Could not verify (Client-side SPA)", is_verified=False),
        ]
        res = evaluate_price_comparison(offers, user_budget=20000.0)
        self.assertEqual(res.verified_count, 1)
        self.assertEqual(res.total_count, 4)
        self.assertEqual(res.lowest_verified_price, 18999.0)
        self.assertEqual(res.cheapest_offers[0].platform, "Flipkart")
        # Unverified platforms must have budget_status "Unverified" and price None
        croma_offer = [o for o in res.offers if o.platform == "Croma"][0]
        self.assertIsNone(croma_offer.price)
        self.assertEqual(croma_offer.budget_status, "Unverified")

    def test_scenario_7_two_platforms_tie(self):
        """Scenario 7: Two platforms have the exact same lowest price."""
        offers = [
            ProductOffer(platform="Amazon India", product_name="Headphones ANC", price=24990.0, url="https://amazon.in/dp/7"),
            ProductOffer(platform="Flipkart", product_name="Headphones ANC", price=24990.0, url="https://flipkart.com/p/7"),
            ProductOffer(platform="Croma", product_name="Headphones ANC", price=26990.0, url="https://croma.com/p/7"),
            ProductOffer(platform="Reliance Digital", product_name="Headphones ANC", price=25990.0, url="https://reliance.in/p/7"),
        ]
        res = evaluate_price_comparison(offers, user_budget=28000.0)
        self.assertTrue(res.has_tie)
        self.assertEqual(len(res.cheapest_offers), 2)
        platforms = {o.platform for o in res.cheapest_offers}
        self.assertEqual(platforms, {"Amazon India", "Flipkart"})
        self.assertIn("tie", res.summary_message.lower())

    def test_scenario_8_variant_and_accessory_filtering(self):
        """Scenario 8: Rejection of accessories and extraction of variant information."""
        # Check accessory detection
        self.assertTrue(is_accessory("Tempered Glass Screen Protector for iPhone 15", "iPhone 15"))
        self.assertTrue(is_accessory("Silicone Back Cover for Samsung S24", "Samsung S24"))
        self.assertTrue(is_accessory("USB-C Fast Charging Cable 2m", "MacBook Air"))
        # If user explicitly searched for cover, should NOT reject
        self.assertFalse(is_accessory("Silicone Cover for iPhone 15", "iPhone 15 cover"))

        # Check variant info extraction
        title_iphone = "Apple iPhone 15 (Blue, 128 GB)"
        self.assertIn("128 GB", extract_variant_info(title_iphone))

        title_tv = "LG 80 cm (32 inch) Full HD Smart LED TV"
        var_tv = extract_variant_info(title_tv)
        self.assertTrue("32 inch" in var_tv or "80 cm" in var_tv)

    def test_price_normalization(self):
        """Test safe price normalization from diverse inputs."""
        self.assertEqual(normalize_price("₹67,999.00"), 67999.0)
        self.assertEqual(normalize_price("Rs. 48,999"), 48999.0)
        self.assertEqual(normalize_price("51,999"), 51999.0)
        self.assertEqual(normalize_price(49999), 49999.0)
        self.assertEqual(normalize_price(""), None)
        self.assertEqual(normalize_price(None), None)
        self.assertEqual(normalize_price("Price on request"), None)


if __name__ == "__main__":
    unittest.main()
