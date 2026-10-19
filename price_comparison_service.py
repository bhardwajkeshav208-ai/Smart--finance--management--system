"""
price_comparison_service.py
===========================
Modular Price Comparison Service for FINSIGHT.

Features:
- Independent search across 4 platforms: Amazon India, Flipkart, Croma, Reliance Digital.
- Honest verification status (Verified vs Could Not Verify due to anti-bot / SPA constraints).
- Real price normalization and variant/accessory filtering (no hardcoding, no fabricated data).
- Dynamic best deal selection supporting:
    * Case A: One or more verified offers below user budget (shows lowest verified price + savings).
    * Case B: All verified offers above user budget (shows cheapest available option + excess amount).
    * Case C: Another platform cheaper than Flipkart (dynamic selection based on lowest price).
    * Case D: Unverified/unavailable platforms marked honestly without assuming ₹0 or inventing data.
    * Ties: Identifies equal lowest prices fairly without arbitrarily picking one platform.
- Optional external search provider integration (e.g. SerpApi Google Shopping) via environment variables.
"""

import os
import re
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import requests
from bs4 import BeautifulSoup

# Standard user-agents for legitimate browser-like requests
BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-IN,en;q=0.9',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

FLIPKART_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-IN,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

ACCESSORY_KEYWORDS = {
    'case', 'cover', 'glass', 'tempered glass', 'screen protector', 'screen guard',
    'cable', 'charger', 'adapter', 'skin', 'strap', 'band', 'pouch', 'sleeve',
    'replacement screen', 'digitizer', 'back cover', 'mount', 'stand', 'remote control'
}

PLATFORMS = ["Amazon India", "Flipkart", "Croma", "Reliance Digital"]


@dataclass
class ProductOffer:
    platform: str
    product_name: str
    price: Optional[float]
    url: str
    availability: str = "Unknown"
    variant: str = ""
    status: str = "Verified"
    is_verified: bool = True
    budget_status: str = "Unverified"
    diff_from_budget: Optional[float] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "product_name": self.product_name,
            "price": self.price,
            "url": self.url,
            "availability": self.availability,
            "variant": self.variant,
            "status": self.status,
            "is_verified": self.is_verified,
            "budget_status": self.budget_status,
            "diff_from_budget": self.diff_from_budget,
            "notes": self.notes
        }


@dataclass
class ComparisonResult:
    user_budget: float
    offers: List[ProductOffer]
    cheapest_offers: List[ProductOffer] = field(default_factory=list)
    lowest_verified_price: Optional[float] = None
    case: str = "D"  # 'A', 'B', 'C', 'D'
    summary_message: str = ""
    health_score_impact: int = 0
    checked_time: str = ""
    verified_count: int = 0
    total_count: int = 4
    has_tie: bool = False


# =========================================================================
# --- HELPER FUNCTIONS: NORMALIZATION & VARIANT MATCHING ---
# =========================================================================

def normalize_price(price_input: Any) -> Optional[float]:
    """
    Safely normalizes various price formats into a clean numeric float.
    Handles '₹67,999.00', 'Rs. 48,999', '51,999', 48999, None, etc.
    """
    if price_input is None:
        return None
    if isinstance(price_input, (int, float)):
        val = float(price_input)
        return val if val > 0 else None
    
    s = str(price_input).strip()
    # Remove prefix currency words like 'Rs.', 'INR', '₹', 'Rs'
    s = re.sub(r'(?i)\b(rs|inr|rupees?)\b\.?', '', s)
    s = s.replace('₹', '').replace(',', '').strip()
    
    match = re.search(r'(\d+(?:\.\d{1,2})?)', s)
    if match:
        try:
            val = float(match.group(1))
            return val if val > 0 else None
        except ValueError:
            return None
    return None


def is_accessory(title: str, query: str) -> bool:
    """
    Checks if a product title is likely an accessory when the user's query
    was looking for a main device.
    """
    q_lower = query.lower()
    t_lower = title.lower()
    
    # If user explicitly searched for an accessory, do not reject
    if any(k in q_lower for k in ACCESSORY_KEYWORDS):
        return False
        
    # If title explicitly has accessory terms, flag it
    for k in ACCESSORY_KEYWORDS:
        # Check as whole word or phrase
        pattern = r'\b' + re.escape(k) + r'\b'
        if re.search(pattern, t_lower):
            return True
            
    return False


def extract_variant_info(title: str) -> str:
    """
    Extracts key variant details such as storage (128GB, 256GB), screen size (32 inch), or color.
    """
    specs = []
    # Storage / RAM
    storage = re.findall(r'\b\d+\s*(?:GB|TB|MB)\b', title, re.IGNORECASE)
    if storage:
        specs.extend(storage[:2])
    # Screen size
    screen = re.findall(r'\b\d{2,3}(?:\.\d+)?\s*(?:inch|cm|-inch)\b', title, re.IGNORECASE)
    if screen:
        specs.append(screen[0])
    # 5G/4G
    if re.search(r'\b5G\b', title, re.IGNORECASE):
        specs.append("5G")
        
    return ", ".join(specs) if specs else "Standard"


def get_default_platform_search_url(platform: str, query: str) -> str:
    """Returns direct, valid search URL for a given platform."""
    encoded_q = urllib.parse.quote(query.strip())
    if "Amazon" in platform:
        return f"https://www.amazon.in/s?k={encoded_q}"
    elif "Flipkart" in platform:
        return f"https://www.flipkart.com/search?q={encoded_q}"
    elif "Croma" in platform:
        return f"https://www.croma.com/searchB?q={encoded_q}%3Arelevance&text={encoded_q}"
    elif "Reliance" in platform:
        return f"https://www.reliancedigital.in/search?q={encoded_q}"
    return f"https://www.google.com/search?q={encoded_q}"


# =========================================================================
# --- PLATFORM SEARCH WORKERS ---
# =========================================================================

def search_flipkart(query: str, timeout: int = 8) -> ProductOffer:
    """
    Searches Flipkart independently. Retrieves live title, direct product URL, and verified price.
    """
    platform = "Flipkart"
    clean_q = query.strip()
    search_url = get_default_platform_search_url(platform, clean_q)
    
    try:
        response = requests.get(search_url, headers=FLIPKART_HEADERS, timeout=timeout)
        if response.status_code != 200:
            return ProductOffer(
                platform=platform,
                product_name=f"{clean_q.title()} on Flipkart",
                price=None,
                url=search_url,
                availability="Unknown",
                status=f"Could not verify (HTTP {response.status_code})",
                is_verified=False,
                notes="Search request returned non-200 status code."
            )
            
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.select('div[data-id]')
        
        for item in items:
            # Extract title
            img = item.select_one('img[alt]')
            title = img['alt'].strip() if (img and img.get('alt')) else ""
            if not title:
                t_el = item.select_one('div.KzDlHZ, div._4rR01T, a.s1Q9rs, a.wBy4wf')
                title = t_el.get_text(strip=True) if t_el else ""
            if not title:
                continue
                
            # Filter accessories if user searched for main product
            if is_accessory(title, clean_q):
                continue
                
            # Extract URL
            a = item.select_one('a[href]')
            href = a['href'] if (a and a.get('href')) else ""
            if href.startswith('/'):
                product_url = "https://www.flipkart.com" + href
            elif href.startswith('http'):
                product_url = href
            else:
                product_url = search_url
                
            # Extract price
            price = None
            for el in item.find_all(True):
                txt = el.get_text(strip=True)
                if txt.startswith('₹') and len(el.find_all(True)) == 0:
                    price = normalize_price(txt)
                    if price:
                        break
                        
            if price and price > 0:
                variant = extract_variant_info(title)
                return ProductOffer(
                    platform=platform,
                    product_name=title,
                    price=price,
                    url=product_url,
                    availability="In Stock",
                    variant=variant,
                    status="Verified Live Price",
                    is_verified=True,
                    notes="Verified via Flipkart live listing."
                )
                
        # If no item with price was found
        return ProductOffer(
            platform=platform,
            product_name=f"{clean_q.title()} (Search listing)",
            price=None,
            url=search_url,
            availability="Check Store",
            status="Price unavailable",
            is_verified=False,
            notes="No direct pricing found in search results."
        )
        
    except Exception as e:
        return ProductOffer(
            platform=platform,
            product_name=f"{clean_q.title()} on Flipkart",
            price=None,
            url=search_url,
            availability="Unknown",
            status=f"Could not verify (Network error)",
            is_verified=False,
            notes=str(e)
        )


def search_amazon(query: str, timeout: int = 8) -> ProductOffer:
    """
    Searches Amazon India independently. Retrieves live title, direct product URL, and verified price.
    Gracefully handles bot detection / CAPTCHA without inventing fake prices.
    """
    platform = "Amazon India"
    clean_q = query.strip()
    search_url = get_default_platform_search_url(platform, clean_q)
    
    try:
        response = requests.get(search_url, headers=BROWSER_HEADERS, timeout=timeout)
        
        # Check for bot detection / CAPTCHA
        if response.status_code == 503 or "api-services-support@amazon.com" in response.text or "Robot Check" in response.text:
            return ProductOffer(
                platform=platform,
                product_name=f"{clean_q.title()} on Amazon",
                price=None,
                url=search_url,
                availability="Unknown",
                status="Could not verify (Anti-bot protection)",
                is_verified=False,
                notes="Amazon automated request challenged by anti-bot verification. Click View Deal to check live in browser."
            )
            
        if response.status_code != 200:
            return ProductOffer(
                platform=platform,
                product_name=f"{clean_q.title()} on Amazon",
                price=None,
                url=search_url,
                availability="Unknown",
                status=f"Could not verify (HTTP {response.status_code})",
                is_verified=False,
                notes=f"HTTP status {response.status_code}"
            )
            
        html = response.content.decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.find_all('div', attrs={'data-component-type': 's-search-result'})
        
        for card in cards:
            title = ""
            product_url = ""
            
            # 1. Search anchors for direct product link and full descriptive title
            for a in card.find_all('a'):
                href = a.get('href', '')
                if any(x in href for x in ['/dp/', '/gp/product/', '/sspa/click']):
                    span = a.find('span')
                    txt = span.get_text(strip=True) if span else a.get_text(strip=True)
                    if len(txt) > 12 and not any(skip in txt.lower() for skip in ['bought in past', 'save extra', 'see more', 'stars', 'colors', 'deal']):
                        title = txt
                        asin = card.get('data-asin')
                        if asin:
                            product_url = f"https://www.amazon.in/dp/{asin}"
                        elif href.startswith('http'):
                            product_url = href
                        else:
                            product_url = f"https://www.amazon.in{href}"
                        break
                        
            # 2. Fallback to h2 if anchor title not found
            if not title:
                h2 = card.find('h2')
                if h2:
                    span = h2.find('span')
                    t = span.get_text(strip=True) if span else h2.get_text(strip=True)
                    if len(t) > 5:
                        title = t
                        
            if not title:
                continue
                
            # Filter accessories
            if is_accessory(title, clean_q):
                continue
                
            # Extract price
            price_el = card.find('span', class_='a-offscreen') or card.find('span', class_='a-price-whole')
            price = normalize_price(price_el.get_text(strip=True) if price_el else None)
            if not price:
                continue
                
            if not product_url:
                asin = card.get('data-asin')
                product_url = f"https://www.amazon.in/dp/{asin}" if asin else search_url
                    
            variant = extract_variant_info(title)
            return ProductOffer(
                platform=platform,
                product_name=title,
                price=price,
                url=product_url,
                availability="In Stock",
                variant=variant,
                status="Verified Live Price",
                is_verified=True,
                notes="Verified via Amazon India live listing."
            )
            
        return ProductOffer(
            platform=platform,
            product_name=f"{clean_q.title()} (Search listing)",
            price=None,
            url=search_url,
            availability="Check Store",
            status="Price unavailable",
            is_verified=False,
            notes="No directly matched product with listed price found."
        )
        
    except Exception as e:
        return ProductOffer(
            platform=platform,
            product_name=f"{clean_q.title()} on Amazon",
            price=None,
            url=search_url,
            availability="Unknown",
            status="Could not verify (Network error)",
            is_verified=False,
            notes=str(e)
        )


def search_croma(query: str, timeout: int = 8) -> ProductOffer:
    """
    Searches Croma independently.
    Handles Akamai bot-manager restriction honestly.
    Provides direct, verified search URL to view product in user's browser.
    """
    platform = "Croma"
    clean_q = query.strip()
    search_url = get_default_platform_search_url(platform, clean_q)
    
    try:
        response = requests.get(search_url, headers=BROWSER_HEADERS, timeout=timeout)
        if response.status_code == 403:
            return ProductOffer(
                platform=platform,
                product_name=f"{clean_q.title()} on Croma",
                price=None,
                url=search_url,
                availability="Unknown",
                status="Could not verify (Access restricted / WAF)",
                is_verified=False,
                notes="Croma uses Akamai Bot Manager which restricts direct automated requests. Direct store search link provided."
            )
            
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Look for product cards if accessible
            items = soup.select('li.product-item, div.cp-product')
            for it in items:
                title_el = it.select_one('h3.product-title, a.product-title')
                price_el = it.select_one('span.amount, span.pdpPrice')
                link_el = it.select_one('a[href]')
                
                title = title_el.get_text(strip=True) if title_el else ""
                price = normalize_price(price_el.get_text(strip=True) if price_el else None)
                if title and price and not is_accessory(title, clean_q):
                    href = link_el['href'] if link_el else ""
                    p_url = href if href.startswith('http') else f"https://www.croma.com{href}"
                    return ProductOffer(
                        platform=platform,
                        product_name=title,
                        price=price,
                        url=p_url,
                        availability="In Stock",
                        variant=extract_variant_info(title),
                        status="Verified Live Price",
                        is_verified=True
                    )
                    
        return ProductOffer(
            platform=platform,
            product_name=f"{clean_q.title()} on Croma",
            price=None,
            url=search_url,
            availability="Check Store",
            status="Could not verify (Requires browser verification)",
            is_verified=False,
            notes="Direct automated search did not return server-rendered price data."
        )
        
    except Exception as e:
        return ProductOffer(
            platform=platform,
            product_name=f"{clean_q.title()} on Croma",
            price=None,
            url=search_url,
            availability="Unknown",
            status="Could not verify (Connection error)",
            is_verified=False,
            notes=str(e)
        )


def search_reliance(query: str, timeout: int = 8) -> ProductOffer:
    """
    Searches Reliance Digital independently.
    Handles client-side Single-Page Application (SPA) architecture honestly.
    Provides direct, verified search URL to view product in user's browser.
    """
    platform = "Reliance Digital"
    clean_q = query.strip()
    search_url = get_default_platform_search_url(platform, clean_q)
    
    try:
        response = requests.get(search_url, headers=BROWSER_HEADERS, timeout=timeout)
        if response.status_code == 200:
            # Reliance Digital renders product listings client-side via React
            # Check if server-side rendered products exist in script or HTML
            html = response.text
            if "sp__name" in html or "slider-text" in html:
                soup = BeautifulSoup(html, 'html.parser')
                items = soup.select('div.sp, li.grid')
                for it in items:
                    t_el = it.select_one('p.sp__name')
                    p_el = it.select_one('span.gDOPPt, span.amount')
                    if t_el and p_el:
                        title = t_el.get_text(strip=True)
                        price = normalize_price(p_el.get_text(strip=True))
                        if title and price and not is_accessory(title, clean_q):
                            a = it.select_one('a[href]')
                            href = a['href'] if a else ""
                            p_url = href if href.startswith('http') else f"https://www.reliancedigital.in{href}"
                            return ProductOffer(
                                platform=platform,
                                product_name=title,
                                price=price,
                                url=p_url,
                                availability="In Stock",
                                variant=extract_variant_info(title),
                                status="Verified Live Price",
                                is_verified=True
                            )

        return ProductOffer(
            platform=platform,
            product_name=f"{clean_q.title()} on Reliance Digital",
            price=None,
            url=search_url,
            availability="Check Store",
            status="Could not verify (Client-side SPA / Verification required)",
            is_verified=False,
            notes="Reliance Digital catalog is rendered client-side. Click View Deal to see live offers in browser."
        )
        
    except Exception as e:
        return ProductOffer(
            platform=platform,
            product_name=f"{clean_q.title()} on Reliance Digital",
            price=None,
            url=search_url,
            availability="Unknown",
            status="Could not verify (Network error)",
            is_verified=False,
            notes=str(e)
        )


# =========================================================================
# --- OPTIONAL EXTERNAL API INTEGRATION (SERPAPI / SEARCH PROVIDER) ---
# =========================================================================

def search_via_external_api(query: str) -> Dict[str, ProductOffer]:
    """
    If the user has configured SERPAPI_API_KEY or RAPIDAPI_KEY in environment variables,
    queries Google Shopping API to retrieve verified live listings for all four platforms.
    Returns a dictionary mapping platform name -> ProductOffer.
    """
    api_key = os.getenv("SERPAPI_API_KEY")
    results: Dict[str, ProductOffer] = {}
    
    if not api_key:
        return results
        
    try:
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_shopping",
            "q": query.strip(),
            "google_domain": "google.co.in",
            "gl": "in",
            "hl": "en",
            "api_key": api_key
        }
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            data = res.json()
            shopping_results = data.get("shopping_results", [])
            for item in shopping_results:
                source = item.get("source", "").lower()
                matched_platform = None
                if "amazon" in source:
                    matched_platform = "Amazon India"
                elif "flipkart" in source:
                    matched_platform = "Flipkart"
                elif "croma" in source:
                    matched_platform = "Croma"
                elif "reliance" in source:
                    matched_platform = "Reliance Digital"
                    
                if matched_platform and matched_platform not in results:
                    title = item.get("title", "")
                    if is_accessory(title, query):
                        continue
                    price_val = normalize_price(item.get("extracted_price") or item.get("price"))
                    link = item.get("product_link") or item.get("link") or get_default_platform_search_url(matched_platform, query)
                    if price_val:
                        results[matched_platform] = ProductOffer(
                            platform=matched_platform,
                            product_name=title,
                            price=price_val,
                            url=link,
                            availability="In Stock",
                            variant=extract_variant_info(title),
                            status="Verified Live Price (SerpApi)",
                            is_verified=True,
                            notes="Verified through Google Shopping API."
                        )
    except Exception as e:
        print("External API search error:", e)
        
    return results


# =========================================================================
# --- SEARCH ORCHESTRATOR & COMPARISON EVALUATOR ---
# =========================================================================

def search_all_platforms(query: str) -> List[ProductOffer]:
    """
    Searches all four platforms independently:
    - Amazon India
    - Flipkart
    - Croma
    - Reliance Digital
    
    Does NOT hardcode any platform or fabricate prices.
    Uses optional external API if configured, otherwise executes independent workers.
    """
    clean_q = query.strip()
    
    # 1. Check if external API (e.g. SerpApi) is configured
    external_offers = search_via_external_api(clean_q)
    
    # 2. Query each platform independently
    offers: List[ProductOffer] = []
    
    # Amazon
    if "Amazon India" in external_offers:
        offers.append(external_offers["Amazon India"])
    else:
        offers.append(search_amazon(clean_q))
        
    # Flipkart
    if "Flipkart" in external_offers:
        offers.append(external_offers["Flipkart"])
    else:
        offers.append(search_flipkart(clean_q))
        
    # Croma
    if "Croma" in external_offers:
        offers.append(external_offers["Croma"])
    else:
        offers.append(search_croma(clean_q))
        
    # Reliance Digital
    if "Reliance Digital" in external_offers:
        offers.append(external_offers["Reliance Digital"])
    else:
        offers.append(search_reliance(clean_q))
        
    return offers


def evaluate_price_comparison(offers: List[ProductOffer], user_budget: float) -> ComparisonResult:
    """
    Dynamically compares collected offers against the user's budget threshold.
    
    Cases implemented:
    - Case A: One or more platforms have a price below the user's budget.
              Recommend the lowest verified price, showing savings.
    - Case B: All four platforms have prices above the user's budget.
              Clearly state that no verified offer is available below budget.
              Recommend the lowest verified price among available options and
              show how much it exceeds the budget.
    - Case C: Another platform is cheaper than Flipkart.
              Recommends whichever platform has the genuinely lowest price.
    - Case D: Platform cannot be searched / verified.
              Marked as 'Could not verify' without assuming 0 or inventing prices.
    - Ties:   If multiple platforms have the same lowest price, show the tie.
    """
    now_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    verified_offers = [o for o in offers if o.is_verified and o.price is not None and o.price > 0]
    verified_count = len(verified_offers)
    total_count = len(offers)
    
    # Update budget_status and diff_from_budget for each offer
    for o in offers:
        if o.price is not None and o.is_verified:
            diff = o.price - user_budget
            o.diff_from_budget = diff
            if o.price <= user_budget:
                o.budget_status = "Under Budget"
            else:
                o.budget_status = f"Over Budget (+₹{diff:,.2f})"
        else:
            o.budget_status = "Unverified"
            o.diff_from_budget = None

    # Handle Case D (No verified prices available at all)
    if not verified_offers:
        return ComparisonResult(
            user_budget=user_budget,
            offers=offers,
            cheapest_offers=[],
            lowest_verified_price=None,
            case="D",
            summary_message=(
                f"⚠️ Could not verify live prices directly due to platform anti-bot / SPA protections. "
                f"Direct store search links have been provided below so you can inspect prices live in your browser."
            ),
            health_score_impact=0,
            checked_time=now_str,
            verified_count=0,
            total_count=total_count,
            has_tie=False
        )

    # Sort verified offers by price ascending
    verified_offers.sort(key=lambda x: x.price)
    lowest_price = verified_offers[0].price
    
    # Identify all offers matching the lowest price (check for ties)
    cheapest_offers = [o for o in verified_offers if abs(o.price - lowest_price) < 0.01]
    has_tie = len(cheapest_offers) > 1
    
    # Check offers below budget
    under_budget_offers = [o for o in verified_offers if o.price <= user_budget]
    
    if under_budget_offers:
        # CASE A (or Case C if another store is cheaper than Flipkart)
        # Lowest price is <= user_budget
        lowest_under = under_budget_offers[0].price
        cheapest_under = [o for o in under_budget_offers if abs(o.price - lowest_under) < 0.01]
        savings = user_budget - lowest_under
        savings_pct = (savings / user_budget) * 100 if user_budget > 0 else 0
        score_boost = int(min(15, max(1, savings / 1000)))
        
        if len(cheapest_under) > 1:
            names = " & ".join([o.platform for o in cheapest_under])
            msg = (
                f"🎉 Great news! We found a tie deal below your budget!\n"
                f"Both {names} offer this at ₹{lowest_under:,.2f}.\n"
                f"You save ₹{savings:,.2f} ({savings_pct:.1f}% below your budget of ₹{user_budget:,.2f})."
            )
        else:
            best = cheapest_under[0]
            msg = (
                f"🎉 Cheaper Deal Available Below Budget!\n"
                f"Best verified price is on {best.platform} for ₹{best.price:,.2f}.\n"
                f"You save ₹{savings:,.2f} ({savings_pct:.1f}% below your budget of ₹{user_budget:,.2f})."
            )
            
        return ComparisonResult(
            user_budget=user_budget,
            offers=offers,
            cheapest_offers=cheapest_under,
            lowest_verified_price=lowest_under,
            case="A",
            summary_message=msg,
            health_score_impact=score_boost,
            checked_time=now_str,
            verified_count=verified_count,
            total_count=total_count,
            has_tie=(len(cheapest_under) > 1)
        )
    else:
        # CASE B: All verified platforms have prices ABOVE the user's budget
        excess = lowest_price - user_budget
        excess_pct = (excess / user_budget) * 100 if user_budget > 0 else 0
        
        if has_tie:
            names = " & ".join([o.platform for o in cheapest_offers])
            msg = (
                f"ℹ️ No verified offer is available below your budget of ₹{user_budget:,.2f}.\n"
                f"The cheapest available option is a tie between {names} at ₹{lowest_price:,.2f}.\n"
                f"Note: This is the cheapest available option among platforms checked, but it exceeds your budget by ₹{excess:,.2f} (+{excess_pct:.1f}%)."
            )
        else:
            best = cheapest_offers[0]
            msg = (
                f"ℹ️ No verified offer is available below your budget of ₹{user_budget:,.2f}.\n"
                f"The cheapest available option among checked platforms is {best.platform} at ₹{best.price:,.2f}.\n"
                f"Note: This exceeds your budget by ₹{excess:,.2f} (+{excess_pct:.1f}%). We recommend waiting for a sale or revising your budget."
            )
            
        return ComparisonResult(
            user_budget=user_budget,
            offers=offers,
            cheapest_offers=cheapest_offers,
            lowest_verified_price=lowest_price,
            case="B",
            summary_message=msg,
            health_score_impact=0,
            checked_time=now_str,
            verified_count=verified_count,
            total_count=total_count,
            has_tie=has_tie
        )
