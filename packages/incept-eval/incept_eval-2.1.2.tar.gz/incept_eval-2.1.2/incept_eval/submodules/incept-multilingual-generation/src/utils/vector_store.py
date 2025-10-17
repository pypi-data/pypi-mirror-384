import os
import logging
from threading import Lock
import certifi
import ssl

from pymongo import MongoClient
from langchain_openai import OpenAIEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch

logger = logging.getLogger(__name__)

# Singleton instances + locks (thread-safe lazy init)
_vector_store_textbooks = None
_vector_store = None
_embeddings = None
_mongodb_client = None

_vector_store_lock = Lock()
_vector_store_textbooks_lock = Lock()
_embeddings_lock = Lock()
_mongodb_client_lock = Lock()


def get_mongodb_client() -> MongoClient:
    """Get MongoDB client singleton."""
    logger.debug("Starting get_mongodb_client")
    global _mongodb_client
    if _mongodb_client is None:
        logger.debug("MongoDB client is None, initializing...")
        with _mongodb_client_lock:
            if _mongodb_client is None:
                logger.debug("Acquired MongoDB client lock, checking environment...")
                mongodb_uri = os.getenv("MONGODB_URI")
                if not mongodb_uri:
                    logger.error("MONGODB_URI environment variable not set")
                    raise ValueError(
                        "MONGODB_URI environment variable not set")

                logger.debug("MONGODB_URI found, creating MongoDB client with connection pooling...")
                # Fix SSL certificate verification for MongoDB Atlas on macOS
                # Configure connection pooling for concurrent request handling
                _mongodb_client = MongoClient(
                    mongodb_uri,
                    tlsCAFile=certifi.where(),  # Use certifi's certificate bundle
                    maxPoolSize=30,  # Reduced to avoid overwhelming DNS resolver
                    minPoolSize=5,   # Keep warm connections
                    maxIdleTimeMS=300000,  # Keep connections alive 5 minutes (reduces reconnections)
                    serverSelectionTimeoutMS=5000,  # Fast fail on server selection
                    socketTimeoutMS=30000,  # 30s socket timeout
                    connectTimeoutMS=5000,  # 5s connection timeout
                    retryWrites=True,  # Retry failed writes
                    retryReads=True,   # Retry failed reads
                    directConnection=False,  # Use SRV connection for better failover
                    waitQueueTimeoutMS=2000,  # Wait max 2s for available connection
                )
                logger.info(f"MongoDB client initialized with connection pooling: maxPoolSize=30, minPoolSize=5")
                logger.debug("Successfully created MongoDB client with SSL fix and connection pooling")
    else:
        logger.debug("MongoDB client already initialized, returning existing instance")
    return _mongodb_client


def get_embeddings() -> OpenAIEmbeddings:
    """Get OpenAI embeddings singleton."""
    logger.debug("Starting get_embeddings")
    global _embeddings
    if _embeddings is None:
        logger.debug("Embeddings is None, initializing...")
        with _embeddings_lock:
            if _embeddings is None:
                logger.debug("Acquired embeddings lock, checking environment...")
                # Prefer current models: "text-embedding-3-small" or "text-embedding-ada-002"
                model = os.getenv("OPENAI_EMBEDDING_MODEL",
                                  "text-embedding-ada-002")
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    logger.error("OPENAI_API_KEY environment variable not set")
                    raise ValueError(
                        "OPENAI_API_KEY environment variable not set")

                logger.debug(f"Creating OpenAI embeddings with model: {model}")
                _embeddings = OpenAIEmbeddings(
                    model=model,
                    api_key=api_key,
                )
                logger.debug(
                    "OpenAI embeddings initialized with model=%s", model)
    else:
        logger.debug("Embeddings already initialized, returning existing instance")
    return _embeddings


def get_vector_store(
    db_name: str, coll_name: str, index_name: str, text_key: str, embedding_key: str
) -> MongoDBAtlasVectorSearch:
    """Get MongoDB Atlas Vector Search singleton."""
    logger.debug(f"Starting get_vector_store: db={db_name}, coll={coll_name}, index={index_name}")
    global _vector_store
    if _vector_store is None:
        logger.debug("Vector store is None, initializing...")
        logger.debug("Attempting to acquire vector store lock...")
        with _vector_store_lock:
            logger.debug("Successfully acquired vector store lock")
            if _vector_store is None:
                logger.debug("Acquired vector store lock, getting MongoDB client...")
                client = get_mongodb_client()
                logger.debug("MongoDB client obtained, accessing database and collection...")

                db = client[db_name]
                collection = db[coll_name]
                logger.debug(f"Database and collection accessed: {db_name}.{coll_name}")

                logger.debug("Getting embeddings...")
                embeddings = get_embeddings()
                logger.debug("Embeddings obtained, creating MongoDBAtlasVectorSearch...")

                _vector_store = MongoDBAtlasVectorSearch(
                    collection=collection,
                    embedding=embeddings,
                    index_name=index_name,
                    text_key=text_key,
                    embedding_key=embedding_key,
                )
                logger.debug(
                    "MongoDB Atlas Vector Search initialized (db=%s, coll=%s, index=%s)",
                    db_name, coll_name, index_name
                )
    else:
        logger.debug("Vector store already initialized, returning existing instance")

    return _vector_store


def get_vector_store_textbooks() -> MongoDBAtlasVectorSearch:
    """Get MongoDB Atlas Vector Search singleton."""
    logger.debug("Starting get_vector_store_textbooks initialization")
    global _vector_store_textbooks
    if _vector_store_textbooks is None:
        logger.debug("Vector store textbooks is None, initializing...")
        with _vector_store_textbooks_lock:
            if _vector_store_textbooks is None:
                logger.debug("Acquired lock, reading environment variables")

                db_name = os.getenv("MONGODB_DB", "chatter")
                coll_name = os.getenv("MONGODB_COLLECTION", "training_data")
                index_name = os.getenv("MONGODB_VECTOR_INDEX", "vector_index")
                text_key = os.getenv("MONGODB_TEXT_KEY", "text")
                embedding_key = os.getenv(
                    "MONGODB_EMBEDDING_KEY", "text_embedding")

                logger.debug(f"Environment variables: db={db_name}, coll={coll_name}, index={index_name}")
                logger.debug("Calling get_vector_store...")

                _vector_store_textbooks = get_vector_store(
                    db_name=db_name,
                    coll_name=coll_name,
                    index_name=index_name,
                    text_key=text_key,
                    embedding_key=embedding_key,
                )
                logger.debug(
                    "MongoDB Atlas Vector Search for textbooks initialized (db=%s, coll=%s, index=%s)",
                    db_name, coll_name, index_name
                )
    else:
        logger.debug("Vector store textbooks already initialized, returning existing instance")

    return _vector_store_textbooks