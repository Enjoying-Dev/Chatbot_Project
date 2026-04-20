from typing import List, Optional
from pinecone import Pinecone
from openai import OpenAI
from src.config import settings

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536


class PineconeService:
    def __init__(self):
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)
        self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)

    def _get_embedding(self, text: str) -> List[float]:
        response = self.openai.embeddings.create(
            input=text,
            model=EMBEDDING_MODEL,
        )
        return response.data[0].embedding

    @staticmethod
    def build_product_text(product: dict) -> str:
        """Build a rich semantic text from product fields for embedding.

        Combines name, description, ingredients, dietary badges, categories,
        and review content so similarity search captures questions like
        "Is this gluten free?" or "What's a healthy baking mix?"
        """
        parts = []

        if product.get("name"):
            parts.append(product["name"])

        if product.get("brand"):
            parts.append(f"Brand: {product['brand']}")

        if product.get("parent_category") or product.get("child_category"):
            cats = ", ".join(filter(None, [product.get("parent_category"), product.get("child_category")]))
            parts.append(f"Category: {cats}")

        if product.get("description"):
            parts.append(product["description"])

        if product.get("serving_suggestion"):
            parts.append(product["serving_suggestion"])

        if product.get("details") and isinstance(product["details"], list):
            parts.append("Details: " + "; ".join(product["details"]))

        if product.get("specs"):
            parts.append(f"Specs: {product['specs']}")

        if product.get("ingredients"):
            parts.append(f"Ingredients: {product['ingredients']}")

        if product.get("contains"):
            parts.append(f"Contains: {product['contains']}")

        badges = []
        badge_labels = {
            "gluten_free": "Gluten Free",
            "kosher_pareve": "Kosher Pareve",
            "kosher_dairy": "Kosher Dairy",
            "organic": "Organic",
            "whole_grain": "Whole Grain",
            "whole_grain_50": "50%+ Whole Grain",
            "whole_grain_100": "100% Whole Grain",
            "made_in_usa": "Made in USA",
            "sourced_non_gmo": "Sourced Non-GMO",
            "non_gmo": "Non-GMO",
        }
        for key, label in badge_labels.items():
            if product.get(key):
                badges.append(label)
        if badges:
            parts.append("Certifications: " + ", ".join(badges))

        reviews = product.get("reviews") or []
        if not isinstance(reviews, list):
            reviews = []
        review_texts = [r["content"] for r in reviews[:5] if isinstance(r, dict) and r.get("content")]
        if review_texts:
            parts.append("Customer reviews: " + " | ".join(review_texts))

        return "\n".join(parts)

    @staticmethod
    def _build_metadata(product: dict, text: str) -> dict:
        """Build Pinecone metadata, replacing None with safe defaults."""
        return {
            "sku": product.get("sku") or "",
            "name": product.get("name") or "",
            "brand": product.get("brand") or "",
            "price": product.get("price") or "",
            "price_value": product.get("price_value") or 0.0,
            "rating": product.get("rating") or "",
            "review_count": product.get("review_count") or "",
            "parent_category": product.get("parent_category") or "",
            "child_category": product.get("child_category") or "",
            "gluten_free": product.get("gluten_free") or False,
            "organic": product.get("organic") or False,
            "non_gmo": product.get("non_gmo") or False,
            "whole_grain": product.get("whole_grain") or False,
            "url": product.get("url") or "",
            "text": text[:9500],
        }

    def upsert_product(self, product: dict):
        sku = product.get("sku") or ""
        text = self.build_product_text(product)
        embedding = self._get_embedding(text)
        metadata = self._build_metadata(product, text)
        self.index.upsert(vectors=[(sku, embedding, metadata)])

    def upsert_products(self, products: List[dict], batch_size: int = 50):
        for i in range(0, len(products), batch_size):
            batch = products[i : i + batch_size]
            vectors = []
            for product in batch:
                sku = product.get("sku") or ""
                text = self.build_product_text(product)
                embedding = self._get_embedding(text)
                metadata = self._build_metadata(product, text)
                vectors.append((sku, embedding, metadata))
            self.index.upsert(vectors=vectors)
            print(f"Upserted batch {i // batch_size + 1} ({len(vectors)} products)")

    def search(self, query: str, top_k: int = 5, filter: Optional[dict] = None) -> List[dict]:
        embedding = self._get_embedding(query)
        results = self.index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter,
        )
        return [
            {"score": match.score, **match.metadata}
            for match in results.matches
        ]


pinecone_db = PineconeService()
