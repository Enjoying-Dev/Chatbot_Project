"""Prompt for the post-retrieval reasoning step: judge context sufficiency."""

evaluate_retrieval_prompt = """You are reviewing retrieved evidence for a shopping / bakery assistant.

User question:
{query}

Conversation so far (excluding the latest user message if duplicated):
{conversation}

The assistant routed this request toward: {database_hint}
The last retrieval step was: {last_source}

Retrieved context (may include multiple blocks if there were prior attempts):
{context}

Decide whether this context is enough to answer the user accurately and completely.

If it is enough, choose next_step "respond".

If not enough, choose next_step "mysql" for structured catalog data (counts, filters, SKUs, prices, exact product rows)
or "vector" for semantic / qualitative needs (reviews, descriptions, recommendations, ingredients, general product knowledge).

If the user asked for BOTH structured and qualitative information and you only have one kind, pick the missing source.

Be conservative: if results are empty or clearly off-topic, request another retrieval step rather than responding.
"""
