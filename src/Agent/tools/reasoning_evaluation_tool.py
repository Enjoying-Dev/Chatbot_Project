reasoning_evaluation_tool = [
    {
        "type": "function",
        "function": {
            "name": "evaluate_retrieval",
            "description": (
                "After database retrieval, decide whether the evidence is enough "
                "to answer the user, or which retrieval source should run next."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sufficient": {
                        "type": "boolean",
                        "description": (
                            "True if the current context is enough for a correct, "
                            "complete answer."
                        ),
                    },
                    "next_step": {
                        "type": "string",
                        "enum": ["respond", "mysql", "vector"],
                        "description": (
                            "If sufficient is true, use respond. If false, "
                            "choose mysql or vector for the next retrieval."
                        ),
                    },
                    "reason": {
                        "type": "string",
                        "description": "One short sentence explaining the decision.",
                    },
                },
                "required": ["sufficient", "next_step", "reason"],
            },
        },
    }
]
