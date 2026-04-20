from typing import List
import pymysql
from src.config import settings
from src.schema.product_schema import Product


class MySQLService:
    def __init__(self):
        self.config = {
            "host": settings.DB_HOST,
            "user": settings.DB_USER,
            "password": settings.DB_PASSWORD,
            "db": settings.DB_NAME,
            "port": settings.DB_PORT,
            "charset": "utf8mb4",
            "cursorclass": pymysql.cursors.DictCursor,
            "connect_timeout": 10,
            "read_timeout": 10,
            "write_timeout": 10,
        }

    def _get_connection(self):
        return pymysql.connect(**self.config)

    def query(self, sql: str, params: tuple = None) -> List[dict]:
        connection = self._get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                results = cursor.fetchall()
                return results
        finally:
            connection.close()

    def execute(self, sql: str, params: tuple = None):
        connection = self._get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
            connection.commit()
        finally:
            connection.close()

    def create_products_table(self):
        sql = """
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
        """
        self.execute(sql)

    def insert_products(self, products: List[dict]):
        """Batch-insert products in a single connection/transaction.

        Uses ON DUPLICATE KEY UPDATE so re-runs refresh existing rows
        instead of failing.
        """
        sql = """
        INSERT INTO products (
            sku, name, url, brand, price, price_value, currency,
            new_tag, rating, review_count, availability, weight_formatted,
            weight_value, date_added, images, add_to_cart_url, category,
            gluten_free, kosher_pareve, kosher_dairy, organic, whole_grain,
            whole_grain_50, whole_grain_100, made_in_usa, sourced_non_gmo,
            non_gmo, sale, clearance, free_shipping, ground_shipping,
            special_savings, promo_exclusion, parent_category, child_category,
            label_path, package_path, description, serving_suggestion,
            details, specs, ingredients, `contains`, reviews
        ) VALUES (
            %(sku)s, %(name)s, %(url)s, %(brand)s, %(price)s, %(price_value)s,
            %(currency)s, %(new_tag)s, %(rating)s, %(review_count)s,
            %(availability)s, %(weight_formatted)s, %(weight_value)s,
            %(date_added)s, %(images)s, %(add_to_cart_url)s, %(category)s,
            %(gluten_free)s, %(kosher_pareve)s, %(kosher_dairy)s, %(organic)s,
            %(whole_grain)s, %(whole_grain_50)s, %(whole_grain_100)s,
            %(made_in_usa)s, %(sourced_non_gmo)s, %(non_gmo)s, %(sale)s,
            %(clearance)s, %(free_shipping)s, %(ground_shipping)s,
            %(special_savings)s, %(promo_exclusion)s, %(parent_category)s,
            %(child_category)s, %(label_path)s, %(package_path)s,
            %(description)s, %(serving_suggestion)s, %(details)s, %(specs)s,
            %(ingredients)s, %(contains)s, %(reviews)s
        ) ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            url = VALUES(url),
            price = VALUES(price),
            price_value = VALUES(price_value),
            rating = VALUES(rating),
            review_count = VALUES(review_count),
            description = VALUES(description),
            ingredients = VALUES(ingredients),
            reviews = VALUES(reviews)
        """
        connection = self._get_connection()
        try:
            with connection.cursor() as cursor:
                for product in products:
                    cursor.execute(sql, product)
            connection.commit()
        finally:
            connection.close()

    def get_all_products(self) -> List[Product]:
        results = self.query("SELECT * FROM products")
        return [Product(**row) for row in results]

    def get_product_by_sku(self, sku: str) -> Product | None:
        results = self.query("SELECT * FROM products WHERE sku = %s", (sku,))
        return Product(**results[0]) if results else None


mysql_db = MySQLService()
