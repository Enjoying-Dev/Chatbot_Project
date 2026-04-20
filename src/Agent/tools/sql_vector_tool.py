sql_vector_tool = [
    {
        "type": "function",
        "function": {
            "name": "classify_database",
            "description": (
                "Classify which database(s) should be used to answer the "
                "user's query: MySQL for structured/aggregation/filter "
                "questions, Pinecone vector DB for semantic/qualitative "
                "questions, or BOTH when the query mixes structured filters "
                "with semantic intent."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "enum": ["mysql", "vectordb", "both"],
                        "description": (
                            "'mysql' for structured catalog lookups (counts, "
                            "filters by exact attributes, sorting, lookups by "
                            "name/SKU). 'vectordb' for semantic / qualitative "
                            "questions, recommendations, reviews, recipes and "
                            "general baking conversation. 'both' when the "
                            "query combines a structured filter with a "
                            "qualitative or semantic intent."
                        ),
                    },
                    "reason": {
                        "type": "string",
                        "description": (
                            "One short sentence justifying the choice."
                        ),
                    },
                },
                "required": ["database", "reason"],
            },
        },
    }
]
