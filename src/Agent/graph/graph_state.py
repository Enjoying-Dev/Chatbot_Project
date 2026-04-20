from typing import List, Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class DatabaseEnum(str, Enum):
    MYSQL = "mysql"
    VECTORDB = "vectordb"
    BOTH = "both"


class GraphState(BaseModel):
    messages: List[Dict[str, str]]
    query: Optional[str] = None

    database: Optional[DatabaseEnum] = DatabaseEnum.VECTORDB
    routing_reason: Optional[str] = None

    rewritten_sql_query: Optional[str] = None
    rewritten_vector_query: Optional[str] = None

    sql_query: Optional[str] = None
    sql_error: Optional[str] = None

    mysql_results: List[Dict[str, Any]] = Field(default_factory=list)
    vector_results: List[Dict[str, Any]] = Field(default_factory=list)

    context: Optional[str] = None
    fallback_used: Optional[str] = None
