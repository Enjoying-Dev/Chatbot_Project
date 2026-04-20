import json
import os
from typing import List

from src.database.mysql import mysql_db
from src.database.vectodb import pinecone_db

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "scraped_data", "products_merged.json")


def load_products(path: str = DATA_PATH) -> List[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize_to_list(value, fallback_sentinel: str = "No ") -> list | None:
    """Return a proper list, or None if the value is a sentinel string."""
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.startswith(fallback_sentinel):
        return None
    return None


def _normalize_to_str(value, fallback_sentinel: str = "No ") -> str | None:
    if isinstance(value, str):
        return None if value.startswith(fallback_sentinel) else value
    return None


def transform_product(raw: dict) -> dict:
    """Flatten a raw scraped product dict into the schema expected by both databases."""
    weight = raw.get("weight") or {}
    badges = raw.get("badges") or {}
    labels = raw.get("labels") or {}

    images = _normalize_to_list(raw.get("images"))
    category = _normalize_to_list(raw.get("category"))
    details = _normalize_to_list(raw.get("details"))
    reviews = _normalize_to_list(raw.get("reviews"))

    return {
        "sku": raw.get("sku"),
        "name": raw.get("name"),
        "url": raw.get("url"),
        "brand": raw.get("brand"),
        "price": raw.get("price"),
        "price_value": raw.get("price_value"),
        "currency": raw.get("currency", "USD"),
        "new_tag": raw.get("new_tag"),
        "rating": raw.get("rating"),
        "review_count": raw.get("review_count"),
        "availability": raw.get("availability"),
        "weight_formatted": weight.get("formatted") if isinstance(weight, dict) else None,
        "weight_value": weight.get("value") if isinstance(weight, dict) else None,
        "date_added": raw.get("date_added"),
        "images": json.dumps(images) if images else None,
        "add_to_cart_url": raw.get("add_to_cart_url"),
        "category": json.dumps(category) if category else None,
        "gluten_free": badges.get("gluten_free", False),
        "kosher_pareve": badges.get("kosher_pareve", False),
        "kosher_dairy": badges.get("kosher_dairy", False),
        "organic": badges.get("organic", False),
        "whole_grain": badges.get("whole_grain", False),
        "whole_grain_50": badges.get("whole_grain_50", False),
        "whole_grain_100": badges.get("whole_grain_100", False),
        "made_in_usa": badges.get("made_in_usa", False),
        "sourced_non_gmo": badges.get("sourced_non_gmo", False),
        "non_gmo": badges.get("non_gmo", False),
        "sale": labels.get("sale", False),
        "clearance": labels.get("clearance", False),
        "free_shipping": labels.get("free_shipping", False),
        "ground_shipping": labels.get("ground_shipping", False),
        "special_savings": labels.get("special_savings", False),
        "promo_exclusion": raw.get("promo_exclusion", False),
        "parent_category": raw.get("parent_category"),
        "child_category": raw.get("child_category"),
        "label_path": raw.get("label_path"),
        "package_path": raw.get("package_path"),
        "description": _normalize_to_str(raw.get("description")),
        "serving_suggestion": _normalize_to_str(raw.get("serving_suggestion")),
        "details": json.dumps(details) if details else None,
        "specs": _normalize_to_str(raw.get("specs")) or None,
        "ingredients": _normalize_to_str(raw.get("ingredients")),
        "contains": _normalize_to_str(raw.get("contains")),
        "reviews": json.dumps(reviews) if reviews else None,
    }


def transform_all(raw_products: List[dict]) -> List[dict]:
    return [transform_product(p) for p in raw_products]


def seed_mysql(products: List[dict]):
    print(f"Creating products table if not exists...")
    mysql_db.create_products_table()
    print(f"Inserting {len(products)} products into MySQL...")
    mysql_db.insert_products(products)
    print("MySQL seeding complete.")


def seed_pinecone(products: List[dict]):
    print(f"Upserting {len(products)} products into Pinecone...")
    pinecone_db.upsert_products(products)
    print("Pinecone seeding complete.")


def seed_all():
    raw = load_products()
    print(f"Loaded {len(raw)} products from {DATA_PATH}")
    products = transform_all(raw)

    seed_mysql(products)
    seed_pinecone(products)

    print(f"Done — {len(products)} products seeded into both databases.")


if __name__ == "__main__":
    seed_all()
