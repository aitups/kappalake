from pydantic import BaseModel
from typing import List, Optional

class Column(BaseModel):
    name: str
    type: str
    comment: Optional[str] = None

class Table(BaseModel):
    catalog: str
    schema_name: str
    table_name: str
    columns: List[Column] = []

class QueryRequest(BaseModel):
    query: str

class PipelineRequest(BaseModel):
    prompt: str
    
class PipelineResponse(BaseModel):
    sql_query: str
    explanation: str


class ExecuteRequest(BaseModel):
    prompt: str


class ExecuteResponse(BaseModel):
    sql_query: str
    explanation: str
    columns: list = []
    rows: list = []


class AgentRequest(BaseModel):
    task: str


class AgentResponse(BaseModel):
    success: bool
    output: object = None
    details: object = None
    reflection_rounds: int = 0
    attempts: list = []
