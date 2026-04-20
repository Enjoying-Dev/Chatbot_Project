sql_vector_tool = [
    {
        "type": "function",
        "function": {
            "name": "classify_database",
            "description": "Classify whether the user query should be routed to SQL (MySQL) or vector search (Pinecone).",
            "parameters": {
                "type": "object",
                "properties": {
                    "is_sql": {
                        "type": "string",
                        "enum": ["yes", "no"],
                        "description": "'yes' if the query should use SQL for structured lookups, 'no' if it should use vector search for semantic/qualitative questions.",
                    }
                },
                "required": ["is_sql"],
            },
        },
    }
]
