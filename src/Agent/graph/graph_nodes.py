from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.config.settings import OPENAI_API_KEY, ModelType
from src.database.vectodb import pinecone_db
from src.database.mysql import mysql_db
from src.prompt_set.sql_vector import sql_vector
from src.prompt_set.generate_sql import generate_sql
from src.prompt_set.generate_response import generate_response
from src.Agent.tools.sql_vector_tool import sql_vector_tool
from .graph_state import GraphState, DatabaseEnum

model = ChatOpenAI(
    model=ModelType.gpt4o,
    openai_api_key=OPENAI_API_KEY,
)


def extract_function_params(prompt, function):
    function_name = function[0]["function"]["name"]
    arg_name = list(function[0]["function"]["parameters"]["properties"].keys())[0]
    model_ = model.bind_tools(function, tool_choice=function_name)
    messages = [SystemMessage(prompt)]
    tool_call = model_.invoke(messages).tool_calls
    return tool_call[0]["args"][arg_name]


def format_conversation_history(messages: List[Dict[str, str]]) -> str:
    return "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])


def determine_database(state: GraphState) -> DatabaseEnum:
    is_sql = extract_function_params(
        prompt=sql_vector.format(
            query=state.query,
            conversation=format_conversation_history(state.messages),
        ),
        function=sql_vector_tool,
    )
    if is_sql == "yes":
        return DatabaseEnum.MYSQL
    return DatabaseEnum.VECTORDB


def txt2sql_node(state: GraphState) -> GraphState:
    state.database = DatabaseEnum.MYSQL
    response = model.invoke(
        state.messages + [SystemMessage(generate_sql.format(query=state.query))]
    )
    state.sql_query = response.content.strip().replace("```sql", "").replace("```", "").strip()
    return state


def data_retrieval_node(state: GraphState) -> GraphState:
    try:
        if state.database == DatabaseEnum.MYSQL:
            results = mysql_db.query(state.sql_query)
        else:
            results = pinecone_db.search(state.query, top_k=5)

        context = "\n\n".join(
            "\n".join(
                f"{key.replace('_', ' ').title()}: {value}"
                for key, value in result.items()
                if value is not None
            )
            for result in results
        )
        state.context = context

        prompt = generate_response.format(context=context)
        response = model.invoke(state.messages + [HumanMessage(prompt)])
        state.messages.append({"role": "assistant", "content": response.content})

    except Exception:
        state.messages.append({
            "role": "assistant",
            "content": "I apologize, but I encountered an error while retrieving the information. "
                       "Could you please rephrase your question?",
        })
        state.context = ""

    return state
