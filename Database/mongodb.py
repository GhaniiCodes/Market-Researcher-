import os
import random
from datetime import datetime
from typing import Any, Dict, Optional, List, Tuple

from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection

# Ensure environment variables are loaded
load_dotenv()


def _get_mongo_uri() -> str:
    """
    Get MongoDB connection URI from environment.

    Uses MONGODB_URI if set, otherwise falls back to a local instance.
    """
    return os.getenv("MONGODB_URI", "mongodb://localhost:27017")


def _get_db_name() -> str:
    """Get MongoDB database name from environment or use default."""
    return os.getenv("MONGODB_DB_NAME", "market_researcher")


def _get_collection_name() -> str:
    """Get MongoDB collection name from environment or use default."""
    return os.getenv("MONGODB_COLLECTION_NAME", "query_history")


_client: Optional[MongoClient] = None


def get_client() -> MongoClient:
    """Get a singleton MongoDB client instance."""
    global _client
    if _client is None:
        _client = MongoClient(_get_mongo_uri())
    return _client


def get_collection() -> Collection:
    """Get the main query history collection."""
    client = get_client()
    db = client[_get_db_name()]
    collection = db[_get_collection_name()]
    return collection


def init_mongo_indexes() -> None:
    """
    Initialize indexes for the query history collection.

    - timestamp (desc)
    - agent
    - query (text/standard)
    """
    collection = get_collection()

    # Standard indexes
    collection.create_index([("timestamp", DESCENDING)])
    collection.create_index([("agent", ASCENDING)])
    collection.create_index([("query", ASCENDING)])
    # Ensure query_id is unique (our custom 3-digit id).
    # Use a partial index so old documents without query_id (or with null)
    # do not cause DuplicateKeyError when building the index.
    collection.create_index(
        [("query_id", ASCENDING)],
        unique=True,
        partialFilterExpression={"query_id": {"$exists": True}},
    )


def _generate_unique_query_id(collection: Collection) -> int:
    """
    Generate a random 3-digit integer query_id (100–999) that is not yet used.

    NOTE: There are only 900 possible values. For larger-scale use, this
    scheme will eventually exhaust or conflict, but it matches the current
    requirement of a 3-digit random ID.
    """
    for _ in range(50):
        candidate = random.randint(100, 999)
        if not collection.find_one({"query_id": candidate}):
            return candidate
    # If we somehow cannot find a free ID after several tries, raise an error
    raise RuntimeError("Unable to generate a unique 3-digit query_id")


def save_query_document(
    query: str,
    agent: str,
    response: str,
    execution_time: float,
    adjustments: Optional[List[Dict[str, Any]]] = None,
) -> int:
    """
    Insert a query document into MongoDB.

    Returns the inserted document's ID as a string (query_id).
    """
    collection = get_collection()
    if adjustments is None:
        adjustments = []

    # Generate a unique 3-digit query_id
    query_id = _generate_unique_query_id(collection)

    doc: Dict[str, Any] = {
        "query_id": query_id,
        "query": query,
        "agent": agent,
        "response": response,
        # Store "answer" as an alias of "response" for clarity
        "answer": response,
        "execution_time": float(execution_time),
        "timestamp": datetime.utcnow(),
        "adjustments": adjustments,
    }

    collection.insert_one(doc)
    return query_id


def get_query_document_by_id(query_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a single query document by its 3-digit integer query_id."""
    collection = get_collection()
    doc = collection.find_one({"query_id": query_id})
    if not doc:
        return None

    return _normalize_document(doc)


def get_query_documents(
    limit: int = 50,
    offset: int = 0,
    agent_filter: Optional[str] = None,
    search: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Fetch multiple query documents with optional filtering and pagination.

    Returns (items, total_count).
    """
    collection = get_collection()

    filter_query: Dict[str, Any] = {}
    if agent_filter:
        filter_query["agent"] = agent_filter
    if search:
        # Simple substring search on query field
        filter_query["query"] = {"$regex": search, "$options": "i"}

    total = collection.count_documents(filter_query)

    cursor = (
        collection.find(filter_query)
        .sort("timestamp", DESCENDING)
        .skip(offset)
        .limit(limit)
    )

    items = [_normalize_document(doc) for doc in cursor]
    return items, total


def get_statistics_documents() -> Dict[str, Any]:
    """Compute statistics over query documents."""
    collection = get_collection()

    total = collection.count_documents({})

    # Queries by agent
    pipeline_agent = [
        {"$group": {"_id": "$agent", "count": {"$sum": 1}}},
    ]
    queries_by_agent: Dict[str, int] = {}
    for row in collection.aggregate(pipeline_agent):
        agent = row.get("_id") or "Unknown"
        queries_by_agent[agent] = int(row.get("count", 0))

    # Average execution time
    pipeline_avg = [
        {
            "$group": {
                "_id": None,
                "avg_time": {"$avg": "$execution_time"},
            }
        }
    ]
    avg_time = 0.0
    agg_result = list(collection.aggregate(pipeline_avg))
    if agg_result:
        avg_time = float(agg_result[0].get("avg_time") or 0.0)

    # Last query time
    last_doc = collection.find_one(sort=[("timestamp", DESCENDING)])
    last_query_time: Optional[datetime] = None
    if last_doc and last_doc.get("timestamp"):
        last_query_time = last_doc["timestamp"]

    return {
        "total_queries": int(total),
        "queries_by_agent": queries_by_agent,
        "avg_execution_time": round(avg_time, 3),
        "last_query_time": last_query_time,
    }


def delete_query_document(query_id: str) -> bool:
    """Delete a single query document by its 3-digit integer query_id."""
    collection = get_collection()
    result = collection.delete_one({"query_id": query_id})
    return result.deleted_count > 0


def clear_history_documents() -> int:
    """Delete all query history documents."""
    collection = get_collection()
    result = collection.delete_many({})
    return int(result.deleted_count)


def _normalize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a raw MongoDB document to a dict compatible with the API models.

    - Convert _id to query_id (string)
    - Ensure timestamp is a datetime
    """
    normalized: Dict[str, Any] = {
        "query_id": str(doc.get("_id")),
        "query": doc.get("query", ""),
        "agent": doc.get("agent", ""),
        "response": doc.get("response", ""),
        "timestamp": doc.get("timestamp") or datetime.utcnow(),
        "execution_time": float(doc.get("execution_time") or 0.0),
        "adjustments": doc.get("adjustments", []),
    }

    return normalized


