"""End-to-end eval harness — runs realistic scenarios through chat_service
and prints the routing decision, generated SQL, fallback usage, the context
the model received, and the final answer."""
import sys

from src.Agent.chat import chat_service


def flush(*a, **k):
    print(*a, **k)
    sys.stdout.flush()


def show(label, query, history):
    flush("\n" + "#" * 80)
    flush(f"# {label}")
    flush(f"# Q: {query}")
    flush("#" * 80)
    result = chat_service.process_message(query, history)
    flush(f"[router]   db={result.get('database')}  reason={result.get('routing_reason')}")
    if result.get("sql_query"):
        flush(f"[sql]      {result['sql_query']}")
    if result.get("fallback_used"):
        flush(f"[fallback] {result['fallback_used']}")
    ctx = (result.get("context") or "").strip()
    flush("--- CONTEXT (truncated to 1200 chars) ---")
    flush(ctx[:1200] + (" ...[truncated]" if len(ctx) > 1200 else ""))
    flush("--- ANSWER ---")
    flush(result["response"])
    return result


SCENARIOS = [
    ("S1 MySQL count",
     "How many gluten-free products do you have?", []),
    ("S2 MySQL filter+sort",
     "Show me the 5 cheapest bread mixes.", []),
    ("S3 MySQL lookup by SKU",
     "Tell me about SKU 400382.", []),
    ("S4 MySQL aggregation",
     "What is the average price of all your mixes?", []),
    ("S5 MySQL likely-empty result",
     "List 5 organic baking mixes.", []),
    ("S6 MySQL contains allergen",
     "Which products contain wheat?", []),
    ("S7 MySQL kosher",
     "Show me kosher pareve products.", []),
    ("S8 Vector qualitative",
     "Which mix would you recommend for a beginner baker?", []),
    ("S9 Vector reviews",
     "What do customers say about the brownie mix?", []),
    ("S10 Vector recipe/usage",
     "How do I use the gluten-free pizza mix?", []),
    ("S11 BOTH — filter + qualitative",
     "Recommend a beginner-friendly gluten-free baking mix under $10.", []),
    ("S12 Greeting",
     "Hi, who are you?", []),
    ("S13 Off-topic",
     "What's the weather today?", []),
]

# Multi-turn follow-ups — share history within the test
FOLLOWUP_TESTS = [
    ("F1 follow-up resolves 'those' (SQL rewriter)",
     [
         ("Show me 3 cake mixes.", []),
         ("And which of those are kosher?", None),  # uses prev history
     ]),
    ("F2 follow-up resolves 'it' (vector rewriter)",
     [
         ("What is the Coffee Cake Mix?", []),
         ("Is it gluten-free?", None),
     ]),
]


def main():
    for label, query, history in SCENARIOS:
        try:
            show(label, query, history)
        except Exception as exc:  # noqa: BLE001 - keep going
            flush(f"!!! {label} crashed: {type(exc).__name__}: {exc}")

    for label, turns in FOLLOWUP_TESTS:
        history: list = []
        for i, (query, _) in enumerate(turns, 1):
            try:
                result = show(f"{label} :: turn {i}", query, history)
                history.append({"role": "user", "content": query})
                history.append({"role": "assistant", "content": result["response"]})
            except Exception as exc:  # noqa: BLE001
                flush(f"!!! {label} turn {i} crashed: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
