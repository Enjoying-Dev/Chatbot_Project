from pydantic import BaseModel
from typing import Optional, List


class Product(BaseModel):
    sku: Optional[str] = None   # sku = product_id
    name: Optional[str] = None
    url: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[str] = None
    price_value: Optional[float] = None
    currency: Optional[str] = 'USD'
    new_tag: Optional[str] = None
    rating: Optional[str] = None
    review_count: Optional[str] = None
    availability: Optional[str] = None
    weight_formatted: Optional[str] = None
    weight_value: Optional[float] = None
    date_added: Optional[str] = None
    images: Optional[List[dict]] = None
    add_to_cart_url: Optional[str] = None
    category: Optional[List[str]] = None
    gluten_free: Optional[bool] = False
    kosher_pareve: Optional[bool] = False
    kosher_dairy: Optional[bool] = False
    organic: Optional[bool] = False
    whole_grain: Optional[bool] = False
    whole_grain_50: Optional[bool] = False
    whole_grain_100: Optional[bool] = False
    made_in_usa: Optional[bool] = False
    sourced_non_gmo: Optional[bool] = False
    non_gmo: Optional[bool] = False
    sale: Optional[bool] = False
    clearance: Optional[bool] = False
    free_shipping: Optional[bool] = False
    ground_shipping: Optional[bool] = False
    special_savings: Optional[bool] = False
    promo_exclusion: Optional[bool] = False
    parent_category: Optional[str] = None
    child_category: Optional[str] = None
    label_path: Optional[str] = None
    package_path: Optional[str] = None
    description: Optional[str] = None
    serving_suggestion: Optional[str] = None
    details: Optional[List[str]] = None
    specs: Optional[str] = None
    ingredients: Optional[str] = None
    contains: Optional[str] = None
    reviews: Optional[List[dict]] = None

    class Config:
        from_attributes = True
