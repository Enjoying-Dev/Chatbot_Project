import requests
import re
import json
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent.parent / "scraped_data"
DB_DIR.mkdir(exist_ok=True)

base_url = "https://shop.kingarthurbaking.com/mixes?page="
all_products = []
current_page = 1

# These headers trick the server into thinking we are a real Chrome browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

print("Starting extraction...\n")

while True:
    print(f"Fetching page {current_page}...")
    
    # Pass the headers into our get request
    response = requests.get(f"{base_url}{current_page}", headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to retrieve page {current_page}. Status code: {response.status_code}")
        break

    html_content = response.text

    match = re.search(r'bcJsContext\s*=\s*"(.*?)";', html_content)
    
    if match:
        escaped_json_string = match.group(1)
        clean_json_string = escaped_json_string.encode('utf-8').decode('unicode_escape')
        
        data = json.loads(clean_json_string)
        page_products = data.get("categoryProducts", [])
        
        if not page_products:
            print("No products found on this page. Extraction complete.")
            break
            
        all_products.extend(page_products)
        print(f"Found {len(page_products)} products.")
        
        current_page += 1
    else:
        print("Could not find the JSON data block. The site layout may have changed.")
        break

print("-" * 30)
print(f"Success! Extracted a total of {len(all_products)} products.")

with open(DB_DIR / 'all_mixes.json', 'w', encoding='utf-8') as f:
    json.dump(all_products, f, indent=4, ensure_ascii=False)
    print(f"Saved all data to '{DB_DIR / 'all_mixes.json'}'")



from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

scraped_products = []

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()

    for i, product in enumerate(all_products):
        url = product['url']
        print(f"[{i+1}/{len(all_products)}] {url}")

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)

            # Click the Ingredients tab to trigger its content to render
            try:
                page.click("a#ingredients-tab", timeout=3000)
                page.wait_for_timeout(1000)
            except Exception:
                pass

            html = page.content()
        except Exception as e:
            print(f"  SKIP – {e}")
            continue

        soup = BeautifulSoup(html, "lxml")

        # ── New flag ──────────────────────────────────────────
        new_flag_el = soup.find("span", class_="new-flag")
        new_tag = new_flag_el.get_text(strip=True) if new_flag_el else ""

        # ── Product Name ──────────────────────────────────────
        name_el = soup.find("h1", class_="productView-title")
        product_name = name_el.get_text(strip=True) if name_el else "No name"

        # ── Reviews count & Rating ────────────────────────────
        rating_widget = soup.find("div", class_="kab-product-rating")
        if rating_widget and rating_widget.get("data-reviews", "0") != "0":
            review_count = rating_widget["data-reviews"]
            rating = rating_widget["data-rating"]
        else:
            review_count = "No reviews"
            rating = "No rating"

        # ── Price ─────────────────────────────────────────────
        price_div = soup.find("div", class_="productView-price")
        price = "No price"
        if price_div:
            sale = price_div.find("span", class_="price-sale-available")
            if sale:
                price = sale.get_text(strip=True)
            else:
                regular = price_div.select_one(
                    "div.price-section--withoutTax:not(.rrp-price--withoutTax)"
                    ":not(.non-sale-price--withoutTax) span.price--withoutTax"
                )
                if regular:
                    price = regular.get_text(strip=True)

        # ── Product ID (SKU) ─────────────────────────────────
        sku_el = soup.find("div", class_="product-sku")
        product_id = sku_el.get_text(strip=True) if sku_el else "No SKU"

        # ── Description & Serving Suggestion ──────────────────
        description = "No description"
        serving_suggestion = "No serving suggestion"
        details = "No details"

        desc_tab = soup.find("div", id="tab-description")
        if desc_tab:
            left = desc_tab.find("div", class_="tab-content-left")
            if left:
                description = left.get_text(separator="\n", strip=True)

                serving_tag = left.find("strong", string=re.compile(r"Serving", re.I))
                if not serving_tag:
                    serving_tag = left.find("h3", string=re.compile(r"Serving", re.I))
                if serving_tag:
                    parent_p = serving_tag.find_parent("p")
                    if parent_p:
                        serving_suggestion = parent_p.get_text(strip=True)
                    else:
                        parts = []
                        for sib in serving_tag.next_siblings:
                            if hasattr(sib, "name") and sib.name in ("h3", "strong"):
                                break
                            txt = sib.get_text(strip=True) if hasattr(sib, "get_text") else str(sib).strip()
                            if txt:
                                parts.append(txt)
                        serving_suggestion = " ".join(parts) if parts else "No serving suggestion"

            right = desc_tab.find("div", class_="tab-content-right")
            if right:
                details_list = right.find("ul")
                if details_list:
                    details = [li.get_text(strip=True) for li in details_list.find_all("li")]
                else:
                    details = right.get_text(separator="\n", strip=True)

        # ── Specs ────────────────────────────────────────────
        specs_div = soup.find("div", id="specs")
        specs = specs_div.get_text(separator="\n", strip=True) if specs_div else "No specs"

        # ── Ingredients & Contains ───────────────────────────
        ingredients = "No ingredients"
        contains = "No allergen info"

        ing_div = soup.find("div", class_="ingredients-html")
        if ing_div:
            ing_h3 = ing_div.find("h3", string="Ingredients")
            if ing_h3:
                ing_p = ing_h3.find_next_sibling("p")
                if ing_p:
                    ingredients = ing_p.get_text(strip=True)

            con_h3 = ing_div.find("h3", string="Contains")
            if con_h3:
                con_p = con_h3.find_next_sibling("p")
                if con_p:
                    contains = con_p.get_text(strip=True)

        # ── Individual Reviews (Yotpo) ───────────────────────
        reviews = []
        review_cards = soup.find_all("div", class_="yotpo-review")
        for card in review_cards:
            reviewer_el = card.find("span", class_="yotpo-reviewer-name")
            title_el = card.find("div", class_="yotpo-review-title")
            content_el = card.find("div", class_="yotpo-read-more-text")
            date_el = card.find("div", class_="yotpo-date-format")
            stars_el = card.find("div", class_="yotpo-review-star-rating")
            recommend_el = card.find(string=re.compile(r"recommend", re.I))

            star_rating = "No rating"
            if stars_el:
                aria = stars_el.get("aria-label", "")
                m = re.search(r"(\d+)\s*star", aria)
                if m:
                    star_rating = m.group(1)

            reviews.append({
                "reviewer":       reviewer_el.get_text(strip=True) if reviewer_el else "Anonymous",
                "rating":         star_rating,
                "title":          title_el.get_text(strip=True) if title_el else "No title",
                "content":        content_el.get_text(strip=True) if content_el else "No content",
                "date":           date_el.get_text(strip=True) if date_el else "No date",
                "recommendation": "Yes" if recommend_el else "No",
            })

        if not reviews:
            reviews = "No reviews"

        scraped_products.append({
            "product_name":       product_name,
            "new_tag":            new_tag,
            "review_count":       review_count,
            "rating":             rating,
            "price":              price,
            "product_id":         product_id,
            "description":        description,
            "serving_suggestion": serving_suggestion,
            "details":            details,
            "specs":              specs,
            "ingredients":        ingredients,
            "contains":           contains,
            "reviews":            reviews,
        })
        print(f"  Done: {product_name}")

    browser.close()

with open(DB_DIR / 'product_details.json', 'w', encoding='utf-8') as f:
    json.dump(scraped_products, f, indent=4, ensure_ascii=False)

print(f"\nSaved {len(scraped_products)} products to '{DB_DIR / 'product_details.json'}'")


# ── Phase 3: Merge catalog data (all_mixes) + detail data (product_details) ──

BADGE_FIELDS = {
    "_badge_glutenfree":    "gluten_free",
    "_badge_kosherpareve":  "kosher_pareve",
    "_badge_kosherdairy":   "kosher_dairy",
    "_badge_organic":       "organic",
    "_badge_wholegrain":    "whole_grain",
    "_badge_wholegrain50":  "whole_grain_50",
    "_badge_wholegrain100": "whole_grain_100",
    "_badge_madeintheusa":  "made_in_usa",
    "_badge_sourcednongmo": "sourced_non_gmo",
    "_badge_nongmo":        "non_gmo",
}
LABEL_FIELDS = {
    "_sale_label":      "sale",
    "_clearance_label":  "clearance",
    "_free_ship_label":  "free_shipping",
    "_ground_ship_label":"ground_shipping",
    "_Special_Savings":  "special_savings",
}

def parse_custom_fields(custom_fields):
    cf = {f["name"]: f["value"] for f in custom_fields}
    badges = {nice: cf.get(raw, "No") == "Yes" for raw, nice in BADGE_FIELDS.items()}
    labels = {nice: cf.get(raw, "No") == "Yes" for raw, nice in LABEL_FIELDS.items()}
    return {
        "badges": badges,
        "labels": labels,
        "promo_exclusion": cf.get("_Promo_Exclusion", "No") == "Yes",
        "parent_category": cf.get("_Parent_Category", ""),
        "child_category": cf.get("_Child_Category", ""),
        "label_path": cf.get("_label_path", ""),
        "package_path": cf.get("_package_path", ""),
    }


print("\n" + "=" * 30)
print("Merging catalog + detail data...")

catalog_by_sku = {p["sku"]: p for p in all_products}

merged_products = []
for detail in scraped_products:
    sku = detail["product_id"].lstrip("#")
    catalog = catalog_by_sku.get(sku, {})
    cf = parse_custom_fields(catalog.get("custom_fields", []))

    merged = {
        "sku":               sku,
        "name":              detail["product_name"],
        "url":               catalog.get("url", ""),
        "brand":             catalog.get("brand", {}).get("name", ""),
        "price":             detail["price"],
        "price_value":       catalog.get("price", {}).get("without_tax", {}).get("value"),
        "currency":          catalog.get("price", {}).get("without_tax", {}).get("currency", "USD"),
        "new_tag":           detail["new_tag"],
        "rating":            detail["rating"],
        "review_count":      detail["review_count"],
        "availability":      catalog.get("availability", ""),
        "weight":            catalog.get("weight"),
        "date_added":        catalog.get("date_added", ""),
        "images":            catalog.get("images", []),
        "add_to_cart_url":   catalog.get("add_to_cart_url", ""),
        "category":          catalog.get("category", []),
        "badges":            cf["badges"],
        "labels":            cf["labels"],
        "promo_exclusion":   cf["promo_exclusion"],
        "parent_category":   cf["parent_category"],
        "child_category":    cf["child_category"],
        "label_path":        cf["label_path"],
        "package_path":      cf["package_path"],
        "description":       detail["description"],
        "serving_suggestion":detail["serving_suggestion"],
        "details":           detail["details"],
        "specs":             detail["specs"],
        "ingredients":       detail["ingredients"],
        "contains":          detail["contains"],
        "reviews":           detail["reviews"],
    }
    merged_products.append(merged)

with open(DB_DIR / 'products_merged.json', 'w', encoding='utf-8') as f:
    json.dump(merged_products, f, indent=4, ensure_ascii=False)

print(f"Saved {len(merged_products)} merged products to '{DB_DIR / 'products_merged.json'}'")

