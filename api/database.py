from typing import Optional, List, Tuple, Dict, Any

from Database.mongodb import (
    save_query_document,
    get_query_document_by_id,
    get_query_documents,
    get_statistics_documents,
    delete_query_document,
    clear_history_documents,
    init_mongo_indexes,
)


def init_db() -> None:
    """
    Initialize MongoDB indexes.

    This can be called on application startup to ensure indexes exist.
    """
    init_mongo_indexes()


def save_query(
    query: str,
    agent: str,
    response: str,
    execution_time: float,
    adjustments: Optional[List[Dict[str, Any]]] = None,
) -> int:
    """
    Save a query to MongoDB.

    Returns:
        query_id (str): The MongoDB ObjectId as a string.
    """
    return save_query_document(
        query=query,
        agent=agent,
        response=response,
        execution_time=execution_time,
        adjustments=adjustments,
    )


def get_query_by_id(query_id: int) -> Optional[dict]:
    """Retrieve a specific query by its 3-digit integer ID."""
    return get_query_document_by_id(query_id)


def get_query_history(
    limit: int = 50,
    offset: int = 0,
    agent_filter: Optional[str] = None,
    search: Optional[str] = None,
) -> Tuple[List[dict], int]:
    """Retrieve query history with filtering and pagination from MongoDB."""
    return get_query_documents(
        limit=limit,
        offset=offset,
        agent_filter=agent_filter,
        search=search,
    )


def get_statistics() -> dict:
    """Get query statistics from MongoDB."""
    return get_statistics_documents()


def delete_query(query_id: int) -> bool:
    """Delete a specific query document from MongoDB by its 3-digit ID."""
    return delete_query_document(query_id)


def clear_history() -> int:
    """Clear all query history documents from MongoDB."""
    return clear_history_documents()
