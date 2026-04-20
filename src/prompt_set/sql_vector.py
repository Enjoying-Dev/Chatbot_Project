sql_vector = """
You need to select one proper database, Pinecone VectorDB or MySQL Database to gather information that related to following query.

The query is as follows.
{query}

Here is the original conversation.
{conversation}

Here is SQL Query that is used to create table.
```
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sku VARCHAR(50) UNIQUE,
    name VARCHAR(255),
    url VARCHAR(500),
    brand VARCHAR(100),
    price VARCHAR(20),
    price_value FLOAT,
    currency VARCHAR(10) DEFAULT 'USD',
    new_tag VARCHAR(50),
    rating VARCHAR(10),
    review_count VARCHAR(10),
    availability VARCHAR(100),
    weight_formatted VARCHAR(50),
    weight_value FLOAT,
    date_added VARCHAR(50),
    images JSON,
    add_to_cart_url VARCHAR(500),
    category JSON,
    gluten_free BOOLEAN DEFAULT FALSE,
    kosher_pareve BOOLEAN DEFAULT FALSE,
    kosher_dairy BOOLEAN DEFAULT FALSE,
    organic BOOLEAN DEFAULT FALSE,
    whole_grain BOOLEAN DEFAULT FALSE,
    whole_grain_50 BOOLEAN DEFAULT FALSE,
    whole_grain_100 BOOLEAN DEFAULT FALSE,
    made_in_usa BOOLEAN DEFAULT FALSE,
    sourced_non_gmo BOOLEAN DEFAULT FALSE,
    non_gmo BOOLEAN DEFAULT FALSE,
    sale BOOLEAN DEFAULT FALSE,
    clearance BOOLEAN DEFAULT FALSE,
    free_shipping BOOLEAN DEFAULT FALSE,
    ground_shipping BOOLEAN DEFAULT FALSE,
    special_savings BOOLEAN DEFAULT FALSE,
    promo_exclusion BOOLEAN DEFAULT FALSE,
    parent_category VARCHAR(100),
    child_category VARCHAR(100),
    label_path VARCHAR(255),
    package_path VARCHAR(255),
    description TEXT,
    serving_suggestion TEXT,
    details JSON,
    specs TEXT,
    ingredients TEXT,
    `contains` VARCHAR(255),
    reviews JSON
)
```
"""
