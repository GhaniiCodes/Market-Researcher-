from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional
from datetime import datetime
import time
import sys
from pathlib import Path as PathLib

# Add parent directory to path
sys.path.append(str(PathLib(__file__).parent.parent))

from api.models import (
    QueryRequest, 
    QueryResponse, 
    HistoryResponse, 
    HistoryItem,
    StatsResponse,
    ErrorResponse
)
from api.database import (
    save_query, 
    get_query_history, 
    get_query_by_id,
    get_statistics,
    delete_query,
    clear_history
)
from supervisor.supervisor import supervisor_agent

# Query Router
query_router = APIRouter()

@query_router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a user query through the multi-agent system.
    
    The query will be automatically routed to the appropriate agent:
    - News Agent: for latest news and events
    - Market Agent: for product research and reviews
    - Stock Agent: for stock analysis
    - General Assistant: for general knowledge queries
    """
    try:
        start_time = time.time()
        
        # Process query through supervisor
        result = supervisor_agent(request.query)
        
        execution_time = time.time() - start_time
        
        # Save to database
        query_id = save_query(
            query=result["query"],
            agent=result["agent"],
            response=result["response"],
            execution_time=execution_time
        )
        
        return QueryResponse(
            query_id=query_id,
            query=result["query"],
            agent=result["agent"],
            response=result["response"],
            timestamp=datetime.now(),
            execution_time=execution_time
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )

@query_router.get("/query/{query_id}", response_model=QueryResponse)
async def get_query(query_id: int = Path(..., gt=0, description="Query ID")):
    """Retrieve a specific query by ID"""
    query_data = get_query_by_id(query_id)
    
    if not query_data:
        raise HTTPException(status_code=404, detail="Query not found")
    
    return QueryResponse(**query_data)

# History Router
history_router = APIRouter()

@history_router.get("/history", response_model=HistoryResponse)
async def get_history(
    limit: int = Query(50, ge=1, le=500, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    agent: Optional[str] = Query(None, description="Filter by agent name"),
    search: Optional[str] = Query(None, max_length=200, description="Search in queries")
):
    """
    Retrieve query history with optional filtering and pagination.
    
    Parameters:
    - limit: Maximum number of records to return (1-500)
    - offset: Number of records to skip for pagination
    - agent: Filter by specific agent name
    - search: Search term to filter queries
    """
    try:
        items, total = get_query_history(
            limit=limit,
            offset=offset,
            agent_filter=agent,
            search=search
        )
        
        history_items = [HistoryItem(**item) for item in items]
        
        return HistoryResponse(
            total=total,
            items=history_items,
            limit=limit,
            offset=offset
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve history: {str(e)}"
        )

@history_router.get("/history/stats", response_model=StatsResponse)
async def get_stats():
    """Get query statistics and analytics"""
    try:
        stats = get_statistics()
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )

@history_router.delete("/history/{query_id}")
async def delete_query_endpoint(query_id: int = Path(..., gt=0)):
    """Delete a specific query from history"""
    try:
        deleted = delete_query(query_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Query not found")
        return {"message": "Query deleted successfully", "query_id": query_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete query: {str(e)}"
        )

@history_router.delete("/history")
async def clear_history_endpoint(confirm: bool = Query(False, description="Confirm deletion")):
    """Clear all query history (requires confirmation)"""
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Set confirm=true to clear all history"
        )
    
    try:
        deleted_count = clear_history()
        return {
            "message": "History cleared successfully",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear history: {str(e)}"
        )