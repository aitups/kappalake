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
