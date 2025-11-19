from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="User query")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What's the latest news on AI?"
            }
        }

class QueryResponse(BaseModel):
    query_id: int
    query: str
    agent: str
    response: str
    timestamp: datetime
    execution_time: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "query_id": 1,
                "query": "What's the latest news on AI?",
                "agent": "News Agent",
                "response": "### Latest News on: AI...",
                "timestamp": "2024-01-15T10:30:00",
                "execution_time": 2.5
            }
        }

class HistoryQuery(BaseModel):
    limit: Optional[int] = Field(50, ge=1, le=500, description="Number of records to retrieve")
    offset: Optional[int] = Field(0, ge=0, description="Number of records to skip")
    agent_filter: Optional[Literal["News Agent", "Market Research Agent", "Stock Analyst", "General Assistant"]] = None
    search: Optional[str] = Field(None, max_length=200, description="Search in queries")

class HistoryItem(BaseModel):
    query_id: int
    query: str
    agent: str
    response: str
    timestamp: datetime
    execution_time: float

class HistoryResponse(BaseModel):
    total: int
    items: list[HistoryItem]
    limit: int
    offset: int

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class StatsResponse(BaseModel):
    total_queries: int
    queries_by_agent: dict[str, int]
    avg_execution_time: float
    last_query_time: Optional[datetime] = None