"""Quick inspection of the MySQL data so we can see real field shapes."""
import json
import sys
from src.database.mysql import mysql_db

def flush(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

flush("connecting...")
flush("=" * 70)
flush("Counts & coverage")
flush("=" * 70)
total = mysql_db.query("SELECT COUNT(*) AS n FROM products")[0]["n"]
print(f"Total products: {total}")

for col in [
    "name", "price_value", "rating", "review_count", "url", "images",
    "description", "ingredients", "category", "parent_category",
    "child_category", "`contains`", "details", "reviews",
]:
    label = col.strip("`")
    sql = f"SELECT COUNT(*) AS n FROM products WHERE {col} IS NOT NULL AND {col} != ''"
    n = mysql_db.query(sql)[0]["n"]
    flush(f"  {label:20s} non-null/non-empty: {n}/{total}")

print("\n" + "=" * 70)
print("Distinct parent_category / child_category")
print("=" * 70)
for row in mysql_db.query("SELECT parent_category, COUNT(*) AS n FROM products GROUP BY parent_category ORDER BY n DESC"):
    print(f"  parent={row['parent_category']!r:40s} n={row['n']}")
print()
for row in mysql_db.query("SELECT child_category, COUNT(*) AS n FROM products GROUP BY child_category ORDER BY n DESC LIMIT 15"):
    print(f"  child ={row['child_category']!r:40s} n={row['n']}")

print("\n" + "=" * 70)
print("Badge coverage")
print("=" * 70)
for badge in [
    "gluten_free", "kosher_pareve", "kosher_dairy", "organic",
    "whole_grain", "whole_grain_50", "whole_grain_100",
    "made_in_usa", "sourced_non_gmo", "non_gmo",
    "sale", "clearance", "free_shipping",
]:
    n = mysql_db.query(f"SELECT COUNT(*) AS n FROM products WHERE {badge} = 1")[0]["n"]
    print(f"  {badge:20s} = 1: {n}")

print("\n" + "=" * 70)
print("Price stats")
print("=" * 70)
print(mysql_db.query(
    "SELECT MIN(price_value) AS min_p, MAX(price_value) AS max_p, AVG(price_value) AS avg_p FROM products WHERE price_value IS NOT NULL"
))

print("\n" + "=" * 70)
print("Sample row (raw)")
print("=" * 70)
sample = mysql_db.query("SELECT * FROM products LIMIT 1")[0]
for k, v in sample.items():
    s = str(v)
    if len(s) > 200:
        s = s[:200] + "..."
    print(f"  {k:20s} ({type(v).__name__}): {s}")

print("\n" + "=" * 70)
print("Images field shape (first 3 products)")
print("=" * 70)
for row in mysql_db.query("SELECT sku, name, images FROM products WHERE images IS NOT NULL LIMIT 3"):
    print(f"\nSKU={row['sku']}  name={row['name']}")
    images = row["images"]
    if isinstance(images, str):
        try:
            images = json.loads(images)
        except Exception:
            pass
    print(f"  type={type(images).__name__}")
    if isinstance(images, list) and images:
        print(f"  count={len(images)}")
        print(f"  first={json.dumps(images[0], indent=2)[:600]}")
