import json
import logging
from typing import List, Dict, Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

from src.config.settings import OPENAI_API_KEY, ModelType
from src.database.vectodb import pinecone_db
from src.database.mysql import mysql_db
from src.prompt_set.sql_vector import sql_vector
from src.prompt_set.generate_sql import generate_sql
from src.prompt_set.generate_response import generate_response
from src.prompt_set.sql_prompt_generater import sql_prompt_generater
from src.prompt_set.vectordb_prompt_generator import vectordb_prompt_generator
from src.Agent.tools.sql_vector_tool import sql_vector_tool
from .graph_state import GraphState, DatabaseEnum

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="[%(name)s] %(message)s")

model = ChatOpenAI(
    model=ModelType.gpt4o,
    openai_api_key=OPENAI_API_KEY,
    temperature=0,
)

MAX_SQL_ATTEMPTS = 3
TOP_K_VECTOR = 5
TOP_K_MYSQL_DEFAULT_LIMIT = 5

IMAGE_SIZE_PLACEHOLDER = "{:size}"
IMAGE_SIZE_VALUE = "500x659"

# Columns we never want to dump into the LLM context — they are huge JSON blobs
# or low-signal display fields that just blow up the prompt.
MYSQL_HIDE_FIELDS = {
    "id", "images", "details", "reviews", "category",
    "label_path", "package_path", "add_to_cart_url",
    "weight_formatted", "weight_value", "currency", "promo_exclusion",
    "ground_shipping", "special_savings",
}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def extract_tool_args(prompt: str, function: list) -> dict:
    """Force the model to call `function` and return the parsed arguments."""
    function_name = function[0]["function"]["name"]
    bound = model.bind_tools(function, tool_choice=function_name)
    tool_calls = bound.invoke([SystemMessage(prompt)]).tool_calls
    if not tool_calls:
        return {}
    return tool_calls[0].get("args", {}) or {}


def format_conversation_history(messages: List[Dict[str, str]]) -> str:
    if not messages:
        return "(no prior conversation)"
    return "\n".join(f"{m['role']}: {m['content']}" for m in messages)


def _clean_sql(raw: str) -> str:
    """Strip code fences, leading 'sql'/'mysql' tags and trailing semicolons."""
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        for prefix in ("sql\n", "mysql\n", "sql ", "mysql "):
            if text.lower().startswith(prefix):
                text = text[len(prefix):]
                break
    text = text.replace("```sql", "").replace("```mysql", "").replace("```", "")
    text = text.strip().rstrip(";").strip()
    return text


def _rewrite_query(template: str, state: GraphState) -> str:
    prompt = template.format(
        query=state.query,
        conversation=format_conversation_history(state.messages[:-1]),
    )
    response = model.invoke([SystemMessage(prompt)])
    rewritten = (response.content or "").strip().strip('"').strip("'")
    return rewritten or state.query or ""


def _normalize_image_url(url: Optional[str]) -> Optional[str]:
    """BigCommerce stencil URLs contain a '{:size}' placeholder. Replace it
    with a real size so the URL actually loads in a browser."""
    if not url or not isinstance(url, str):
        return None
    return url.replace(IMAGE_SIZE_PLACEHOLDER, IMAGE_SIZE_VALUE)


def _extract_first_image_url(images_field: Any) -> Optional[str]:
    """`images` is stored as JSON in MySQL: a list of {alt, data} objects.
    Return the first usable URL or None."""
    if not images_field:
        return None
    images = images_field
    if isinstance(images, str):
        try:
            images = json.loads(images)
        except json.JSONDecodeError:
            return None
    if not isinstance(images, list) or not images:
        return None
    first = images[0]
    if isinstance(first, dict):
        url = first.get("data") or first.get("url")
    else:
        url = first if isinstance(first, str) else None
    return _normalize_image_url(url)


def _flatten_mysql_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Strip noisy fields, surface a clean image_url derived from `images`."""
    flat: Dict[str, Any] = {}
    image_url = _extract_first_image_url(row.get("images"))
    for key, value in row.items():
        if key in MYSQL_HIDE_FIELDS:
            continue
        if value is None or value == "":
            continue
        flat[key] = value
    if image_url:
        flat["image_url"] = image_url
    return flat


VECTOR_TEXT_TRUNCATE = 1500


def _flatten_vector_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Pinecone matches: keep a truncated `text` (which contains the rich
    description, ingredients and review snippets the LLM needs to actually
    answer qualitative / review-style questions) and normalize image URL."""
    flat: Dict[str, Any] = {}
    for key, value in row.items():
        if key == "text":
            if isinstance(value, str) and value:
                flat["text"] = (
                    value[:VECTOR_TEXT_TRUNCATE]
                    + ("..." if len(value) > VECTOR_TEXT_TRUNCATE else "")
                )
            continue
        if value in (None, "", 0.0):
            continue
        flat[key] = value
    image_url = _normalize_image_url(flat.get("image"))
    if image_url:
        flat["image_url"] = image_url
    flat.pop("image", None)
    return flat


def _format_results(results: List[Dict[str, Any]], source: str) -> str:
    if not results:
        return f"--- {source} results ---\n(no rows)\n"
    if source == "MySQL":
        rows = [_flatten_mysql_row(r) for r in results]
    elif source == "Vector Search":
        rows = [_flatten_vector_row(r) for r in results]
    else:
        rows = results
    body = "\n\n".join(
        "\n".join(
            f"{key.replace('_', ' ').title()}: {value}"
            for key, value in row.items()
        )
        for row in rows
    )
    return f"--- {source} results ---\n{body}\n"


# ---------------------------------------------------------------------------
# router
# ---------------------------------------------------------------------------

def route_query(state: GraphState) -> GraphState:
    """Classify which database(s) to use, store the decision on the state."""
    args = extract_tool_args(
        prompt=sql_vector.format(
            query=state.query,
            conversation=format_conversation_history(state.messages[:-1]),
        ),
        function=sql_vector_tool,
    )
    raw_db = (args.get("database") or "vectordb").lower()
    try:
        state.database = DatabaseEnum(raw_db)
    except ValueError:
        logger.warning("Unknown database value from router: %r — defaulting to vectordb", raw_db)
        state.database = DatabaseEnum.VECTORDB
    state.routing_reason = args.get("reason", "")
    logger.info("router → %s (%s)", state.database.value, state.routing_reason)
    return state


def route_after_router(state: GraphState) -> str:
    if state.database in (DatabaseEnum.MYSQL, DatabaseEnum.BOTH):
        return "mysql_retrieval"
    return "vector_retrieval"


def route_after_mysql(state: GraphState) -> str:
    """After MySQL: continue to vector if BOTH, or fall back if MySQL was empty."""
    if state.database == DatabaseEnum.BOTH:
        return "vector_retrieval"
    if not state.mysql_results:
        state.fallback_used = "mysql→vector"
        logger.info("mysql returned no rows — falling back to vector search")
        return "vector_retrieval"
    return "respond"


# ---------------------------------------------------------------------------
# mysql retrieval (with text-to-SQL retry loop)
# ---------------------------------------------------------------------------

def mysql_retrieval_node(state: GraphState) -> GraphState:
    state.rewritten_sql_query = _rewrite_query(sql_prompt_generater, state)
    logger.info("mysql rewritten query: %s", state.rewritten_sql_query)

    last_error: str = ""
    sql: str = ""
    results: List[Dict[str, Any]] = []

    for attempt in range(1, MAX_SQL_ATTEMPTS + 1):
        error_hint = ""
        if last_error:
            error_hint = (
                "The previous attempt produced this MySQL error:\n"
                f"{last_error}\n"
                f"Previous SQL was:\n{sql}\n"
                "Fix the issue and produce a corrected query."
            )
        prompt = generate_sql.format(
            query=state.rewritten_sql_query,
            error_hint=error_hint,
        )
        response = model.invoke([SystemMessage(prompt)])
        sql = _clean_sql(response.content)
        logger.info("mysql attempt %d sql: %s", attempt, sql)

        if not sql:
            last_error = "Empty SQL was produced."
            continue
        try:
            results = mysql_db.query(sql)
            break
        except Exception as exc:  # noqa: BLE001 - we feed the error back to the LLM
            last_error = f"{type(exc).__name__}: {exc}"
            logger.warning("mysql attempt %d failed: %s", attempt, last_error)
            results = []

    state.sql_query = sql
    state.sql_error = last_error if not results else None
    state.mysql_results = results or []
    state.context = (state.context or "") + _format_results(state.mysql_results, "MySQL")
    return state


# ---------------------------------------------------------------------------
# vector retrieval
# ---------------------------------------------------------------------------

def vector_retrieval_node(state: GraphState) -> GraphState:
    state.rewritten_vector_query = _rewrite_query(vectordb_prompt_generator, state)
    logger.info("vector rewritten query: %s", state.rewritten_vector_query)

    try:
        results = pinecone_db.search(state.rewritten_vector_query, top_k=TOP_K_VECTOR)
    except Exception as exc:  # noqa: BLE001 - retrieval should never crash the graph
        logger.warning("vector search failed: %s", exc)
        results = []

    state.vector_results = results or []
    state.context = (state.context or "") + _format_results(state.vector_results, "Vector Search")
    return state


# ---------------------------------------------------------------------------
# final response
# ---------------------------------------------------------------------------

def respond_node(state: GraphState) -> GraphState:
    context = state.context or ""
    if not context.strip():
        context = "(no context — no rows were retrieved from either database)"

    prompt = generate_response.format(
        query=state.query or "",
        context=context,
    )
    try:
        response = model.invoke([SystemMessage(prompt), *state.messages])
        answer = response.content
    except Exception as exc:  # noqa: BLE001 - last-resort guard
        logger.exception("respond_node failed: %s", exc)
        answer = (
            "I'm sorry, something went wrong while putting together an answer. "
            "Could you try rephrasing your question?"
        )

    state.messages.append({"role": "assistant", "content": answer})
    return state
