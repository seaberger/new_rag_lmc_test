# --- START OF FILE chat_engine.py ---
# --- Imports for LlamaIndex components ---
import os
import re
import pickle
import sqlite3
import json
import logging
from typing import List, Dict, AsyncGenerator, Optional
from pathlib import Path

from dotenv import load_dotenv
from llama_index.core import (
    Settings,
    VectorStoreIndex,
)
from llama_index.core.schema import NodeWithScore, TextNode, QueryBundle
from llama_index.core.chat_engine.types import (
    BaseChatEngine,
    StreamingAgentChatResponse,
)
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.llms.openai import OpenAI
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.postprocessor.cohere_rerank import CohereRerank
from llama_index.core.retrievers import BaseRetriever
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from langfuse.llama_index import LlamaIndexCallbackHandler
from langfuse.llama_index import LlamaIndexInstrumentor  # Add new import
from llama_index.core.callbacks import CallbackManager
from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)
load_dotenv()

# --- Constants ---
# General
APP_NAME = "Matrix Chatbot"
APP_VERSION = "1.0.0"
MAX_TOKENS = 4096
TEMPERATURE = 0.1
DEFAULT_PROMPT = (
    "You are a helpful AI assistant knowledgeable about Matrix Laser products."
)

# Models
LLM_MODEL = "gpt-4o"
EMBED_MODEL = "text-embedding-3-large"
EMBED_DIM = 3072
RERANK_MODEL = "rerank-english-v3.0"

# Database Paths (Now using Qdrant and SQLite)
NODE_PICKLE_FILE = "matrix_nodes.pkl"
SQLITE_DB_NAME_LOCAL = "matrix_nodes.db"
SQLITE_DB_NAME_PROD = "/app/matrix_nodes.db"
QDRANT_COLLECTION_NAME = "matrix_docs"
QDRANT_PATH_LOCAL = "./qdrant_db"
QDRANT_PATH_PROD = "/app/qdrant_db"

# Retriever Settings
VECTOR_SIMILARITY_TOP_K = 10
KEYWORD_SIMILARITY_TOP_K = 5
RERANK_TOP_N = 5
HYBRID_RETRIEVER_MODE = "relative_score"

# --- Helper Classes ---


class HybridRetrieverModeA(BaseRetriever):
    """Hybrid retriever that combines vector and keyword results using relative scoring."""

    def __init__(self, vector_retriever, keyword_retriever, mode="relative_score"):
        self.vector_retriever = vector_retriever
        self.keyword_retriever = keyword_retriever
        self.mode = mode
        super().__init__()

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Retrieve nodes using both vector and keyword search, then combine."""
        query_str = query_bundle.query_str
        logger.info(f"Starting hybrid retrieval for query: '{query_str}'")

        vector_nodes = self.vector_retriever.retrieve(query_bundle)
        keyword_nodes = self.keyword_retriever.retrieve(query_bundle)

        vector_ids = {n.node.node_id for n in vector_nodes}
        keyword_ids = {n.node.node_id for n in keyword_nodes}

        combined_dict = {n.node.node_id: n for n in vector_nodes}
        combined_dict.update({n.node.node_id: n for n in keyword_nodes})

        if self.mode == "relative_score":
            self._normalize_scores(vector_nodes)
            self._normalize_scores(keyword_nodes)
            for node_id, node in combined_dict.items():
                node.score = node.score or 0.0
                if node_id in vector_ids and node_id in keyword_ids:
                    v_node = next(n for n in vector_nodes if n.node.node_id == node_id)
                    k_node = next(n for n in keyword_nodes if n.node.node_id == node_id)
                    node.score = (v_node.score + k_node.score) / 2
                elif node_id in vector_ids:
                    v_node = next(n for n in vector_nodes if n.node.node_id == node_id)
                    node.score = v_node.score
                elif node_id in keyword_ids:
                    k_node = next(n for n in keyword_nodes if n.node.node_id == node_id)
                    node.score = k_node.score

        sorted_results = sorted(
            combined_dict.values(), key=lambda x: x.score or 0.0, reverse=True
        )
        logger.info(f"Hybrid retrieval found {len(sorted_results)} unique nodes.")
        return sorted_results

    def _normalize_scores(self, nodes: List[NodeWithScore]):
        """Normalize scores to be between 0 and 1."""
        scores = [node.score for node in nodes if node.score is not None]
        if not scores:
            return
        max_score = max(scores) if scores else 1.0
        min_score = min(scores) if scores else 0.0
        for node in nodes:
            if node.score is not None:
                if max_score == min_score:
                    node.score = 1.0 if max_score > 0 else 0.0
                else:
                    node.score = (node.score - min_score) / (max_score - min_score)
            else:
                node.score = 0.0


# --- Add SQLiteFTSRetriever from working file ---
class SQLiteFTSRetriever:
    def __init__(self, db_path=None, top_k=5):
        if db_path is None:
            if os.environ.get("PLASH_PRODUCTION") == "1":
                self.db_path = SQLITE_DB_NAME_PROD
            else:
                self.db_path = SQLITE_DB_NAME_LOCAL
        else:
            self.db_path = db_path
        self.top_k = top_k
        logging.info(f"SQLiteFTSRetriever initialized with DB path: {self.db_path}")

    def retrieve(self, query_str: str) -> List[NodeWithScore]:
        if not os.path.exists(self.db_path):
            logging.error(f"Error: SQLite database not found at {self.db_path}")
            return []
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        analysis = analyze_query(query_str)  # Needs analyze_query function
        fts_query = f'"{query_str}"'  # Default to phrase search (adapt if needed)
        try:
            c.execute(
                f"""
                SELECT nodes.node_id, nodes.content, nodes.metadata, nodes_fts.rank
                FROM nodes_fts
                JOIN nodes ON nodes_fts.rowid = nodes.rowid
                WHERE nodes_fts MATCH ?
                ORDER BY nodes_fts.rank
                LIMIT {self.top_k}
                """,
                (fts_query,),
            )
        except sqlite3.OperationalError as e:
            logging.error(f"SQLite Query Error: {e}. DB Path: {self.db_path}")
            if "no such table: nodes_fts" in str(e):
                logging.warning(
                    f"DB file {self.db_path} exists but FTS table is missing. Recreating."
                )
            conn.close()
            return []
        results = []
        for node_id, content, metadata_blob, rank in c.fetchall():
            try:
                metadata = json.loads(metadata_blob)
            except json.JSONDecodeError:
                metadata = {}
            node = TextNode(text=content, metadata=metadata, id_=node_id)
            score = 1.0 / (1.0 + float(rank))  # Basic rank-based scoring
            results.append(NodeWithScore(node=node, score=score))
        conn.close()
        results.sort(key=lambda x: x.score, reverse=True)
        return results


# --- Add analyze_query from working file ---
def analyze_query(query: str) -> dict:
    part_number_pattern = r"\d{7}|\d{2}-\d{3}-\d{3}"  # Example
    model_keywords = ["matrix", "model", "laser", "series"]  # Example
    analysis = {
        "has_part_number": bool(re.search(part_number_pattern, query, re.IGNORECASE)),
        "has_model_reference": any(
            keyword in query.lower() for keyword in model_keywords
        ),
        "detected_part_numbers": re.findall(part_number_pattern, query),
        "query_type": "general",
    }
    if analysis["has_part_number"]:
        analysis["query_type"] = "part_number"
    elif analysis["has_model_reference"]:
        analysis["query_type"] = "model"
    return analysis


# --- Add HybridRetrieverWithReranking from working file ---
class HybridRetrieverWithReranking(BaseRetriever):
    def __init__(
        self,
        vector_retriever,
        keyword_retriever,
        reranker,
        vector_weight=0.7,
        keyword_weight=0.3,
        initial_top_k=20,
    ):
        self.vector_retriever = vector_retriever
        self.keyword_retriever = keyword_retriever
        self.reranker = reranker
        self.base_vector_weight = vector_weight
        self.base_keyword_weight = keyword_weight
        self.initial_top_k = initial_top_k
        super().__init__()

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        query_str = query_bundle.query_str
        analysis = analyze_query(query_str)
        vector_weight = self.base_vector_weight
        keyword_weight = self.base_keyword_weight
        # --- Dynamic Weighting Logic (keep as is) ---
        if analysis["query_type"] == "part_number":
            vector_weight *= 0.5
            keyword_weight *= 2.0
        elif analysis["query_type"] == "model":
            vector_weight *= 0.8
            keyword_weight *= 1.5
        # --- Retrieve from both ---
        vector_results = self.vector_retriever.retrieve(query_str)
        keyword_results = self.keyword_retriever.retrieve(query_str)
        # --- Combine and score ---
        node_scores = {}
        max_score = 0.0
        # Process vector results
        for result in vector_results:
            node_id = result.node.node_id
            score = result.score * vector_weight
            if node_id not in node_scores:
                node_scores[node_id] = {"node": result.node, "score": 0.0}
            node_scores[node_id]["score"] += score
            max_score = max(max_score, node_scores[node_id]["score"])
        # Process keyword results (rank-based scoring)
        keyword_max_rank_score = keyword_weight
        for i, result in enumerate(keyword_results):
            node_id = result.node.node_id
            keyword_score = keyword_max_rank_score * (1.0 / (i + 1))
            # Add boosting logic here if needed based on metadata
            if node_id not in node_scores:
                node_scores[node_id] = {"node": result.node, "score": 0.0}
            node_scores[node_id]["score"] += keyword_score
            max_score = max(max_score, node_scores[node_id]["score"])
        # --- Normalize scores ---
        if max_score > 0:
            for node_id in node_scores:
                node_scores[node_id]["score"] /= max_score
        # --- Sort combined results ---
        sorted_results = sorted(
            node_scores.values(), key=lambda x: x["score"], reverse=True
        )
        # --- Prepare for Reranking ---
        initial_results_for_rerank = [
            NodeWithScore(node=item["node"], score=item["score"])
            for item in sorted_results[: self.initial_top_k]
        ]
        # --- Rerank (if applicable) ---
        final_top_n = self.reranker.top_n if self.reranker else 5
        if self.reranker is not None and initial_results_for_rerank:
            try:
                reranked_nodes = self.reranker.postprocess_nodes(
                    initial_results_for_rerank, query_bundle
                )
                return reranked_nodes[:final_top_n]
            except Exception as e:
                logging.error(
                    f"Error during reranking: {e}. Returning initial sorted results."
                )
                return initial_results_for_rerank[:final_top_n]
        # --- Return top N if no reranker or reranking failed ---
        return initial_results_for_rerank[:final_top_n]


# --- Add create_or_load_sqlite_db from working file ---
def create_or_load_sqlite_db(nodes_path, db_path):
    if os.path.exists(db_path):
        logging.info(f"Using existing SQLite database at {db_path}")
        conn_check = sqlite3.connect(db_path)
        try:
            cursor = conn_check.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='nodes_fts'"
            )
            if not cursor.fetchone():
                logging.warning(
                    f"DB file {db_path} exists but FTS table is missing. Recreating."
                )
                conn_check.close()
                os.remove(db_path)  # Remove bad file
            else:
                conn_check.close()
                return  # DB looks okay
        except Exception as e:
            logging.warning(f"Error checking existing DB {db_path}: {e}. Recreating.")
            try:
                conn_check.close()
            except:
                pass
            if os.path.exists(db_path):
                os.remove(db_path)

    logging.info(f"Creating new SQLite FTS database at {db_path}")
    if not os.path.exists(nodes_path):
        logging.error(
            f"Error: Node pickle file not found at {nodes_path}. Cannot create SQLite DB."
        )
        raise FileNotFoundError(f"Required node file not found: {nodes_path}")
    with open(nodes_path, "rb") as f:
        nodes = pickle.load(f)
    if not nodes:
        logging.warning("No nodes found in pickle file. SQLite DB will be empty.")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Create nodes table
    c.execute(
        "CREATE TABLE IF NOT EXISTS nodes (rowid INTEGER PRIMARY KEY, node_id TEXT UNIQUE, content TEXT, metadata TEXT)"
    )
    conn.commit()
    # Create FTS table
    c.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(content, content='nodes', content_rowid='rowid', tokenize='porter unicode61')"
    )
    conn.commit()
    # Insert nodes
    inserted_count = 0
    skipped_count = 0
    for node in nodes:
        try:
            metadata_json = json.dumps(node.metadata or {})
            c.execute(
                "INSERT OR IGNORE INTO nodes (node_id, content, metadata) VALUES (?, ?, ?)",
                (node.node_id, node.text, metadata_json),
            )
            if c.rowcount > 0:
                inserted_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            logging.error(
                f"Error inserting node {getattr(node, 'node_id', 'UNKNOWN')}: {e}"
            )
            skipped_count += 1
    if skipped_count > 0:
        logging.info(f"Skipped {skipped_count} nodes (likely duplicates).")
    # Populate FTS index
    if inserted_count > 0:
        logging.info(f"Populating FTS index for {inserted_count} new nodes...")
        try:
            c.execute(
                "INSERT INTO nodes_fts(rowid, content) SELECT rowid, content FROM nodes WHERE rowid NOT IN (SELECT rowid FROM nodes_fts);"
            )
            conn.commit()
            logging.info("FTS index population complete.")
        except Exception as e:
            logging.error(f"Error populating FTS index: {e}")
            conn.rollback()
    elif skipped_count == len(nodes) and skipped_count > 0:
        logging.info("No new nodes inserted, FTS index assumed up-to-date.")
    else:
        logging.info("No nodes to insert into FTS index.")
    conn.close()
    logging.info(f"Finished SQLite DB setup at {db_path}.")


# --- Global Variables ---
global_retriever_async: Optional[BaseRetriever] = (
    None  # Keep for potential direct use/debug
)

# --- Initialization Functions ---


def _init_settings():
    """Initialize global LlamaIndex settings."""
    logger.info("Initializing OpenAI models...")
    try:
        llm = OpenAI(model=LLM_MODEL, temperature=TEMPERATURE, max_tokens=MAX_TOKENS)
        embed_model = OpenAIEmbedding(model=EMBED_MODEL, dimensions=EMBED_DIM)
        Settings.llm = llm
        Settings.embed_model = embed_model
        logger.info(f"Using LLM: {LLM_MODEL}, Embed Model: {EMBED_MODEL}")
    except Exception as e:
        logger.error(f"Error initializing OpenAI models: {e}", exc_info=True)
        raise


# --- ADD _create_sync_retriever (based on working create_retriever) ---
def _create_sync_retriever(cohere_api_key: str) -> HybridRetrieverWithReranking:
    """Creates the synchronous hybrid retriever using SQLite FTS and Qdrant."""
    # Determine paths
    if os.environ.get("PLASH_PRODUCTION") == "1":
        sqlite_db_path = SQLITE_DB_NAME_PROD
        qdrant_db_path = QDRANT_PATH_PROD
        logging.info("Using PRODUCTION paths for SQLite and Qdrant.")
    else:
        sqlite_db_path = SQLITE_DB_NAME_LOCAL
        qdrant_db_path = QDRANT_PATH_LOCAL
        logging.info("Using LOCAL paths for SQLite and Qdrant.")

    # --- SQLite Retriever Setup ---
    # DB creation/check happens in init_chat_engine_async
    sqlite_retriever = SQLiteFTSRetriever(db_path=sqlite_db_path, top_k=10)

    # --- Vector Retriever Setup (LOAD from persistent Qdrant) ---
    try:
        qdrant_path_obj = Path(qdrant_db_path)
        if not qdrant_path_obj.exists() or not any(qdrant_path_obj.iterdir()):
            logging.error(
                f"Qdrant database path {qdrant_db_path} not found or is empty."
            )
            logging.error(
                "Please run 'create_vector_db.py' locally and ensure the 'qdrant_db' folder is deployed."
            )
            raise FileNotFoundError(f"Qdrant database not found at {qdrant_db_path}")

        logging.info(
            f"Connecting to persistent Qdrant client at path: {qdrant_db_path}"
        )
        # Use the imported QdrantClient class
        qdrant_client_instance = QdrantClient(path=qdrant_db_path)

        # Check if collection exists
        try:
            qdrant_client_instance.get_collection(
                collection_name=QDRANT_COLLECTION_NAME
            )
            logging.info(f"Found Qdrant collection '{QDRANT_COLLECTION_NAME}'.")
        except Exception as e:
            # Be more specific if possible, e.g., qdrant_client.http.exceptions.UnexpectedResponse
            logging.error(
                f"Qdrant collection '{QDRANT_COLLECTION_NAME}' not found in DB at {qdrant_db_path}. Error: {e}"
            )
            raise ValueError(
                f"Collection '{QDRANT_COLLECTION_NAME}' not found. Ensure DB was created correctly."
            )

        vector_store = QdrantVectorStore(
            client=qdrant_client_instance, collection_name=QDRANT_COLLECTION_NAME
        )

        logging.info("Loading VectorStoreIndex FROM existing vector store...")
        # Ensure Settings.embed_model is initialized before this call
        if Settings.embed_model is None:
            raise RuntimeError(
                "Settings.embed_model not initialized before creating vector index."
            )
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store, embed_model=Settings.embed_model
        )
        logging.info("VectorStoreIndex loaded successfully.")

        # Create vector retriever
        vector_retriever = index.as_retriever(similarity_top_k=15)

    except Exception as e:
        logging.error(f"Error creating vector retriever from persistent Qdrant: {e}")
        import traceback

        traceback.print_exc()
        raise

    # --- Reranker and Hybrid Retriever Setup ---
    logging.info("Initializing Cohere Reranker...")
    try:
        # Ensure RERANK_MODEL constant is defined or use string directly
        reranker = CohereRerank(api_key=cohere_api_key, model=RERANK_MODEL, top_n=8)
    except Exception as e:
        logging.error(
            f"Error initializing Cohere Reranker: {e}. Reranking will be disabled."
        )
        reranker = None

    logging.info("Initializing Hybrid Retriever...")
    hybrid_retriever = HybridRetrieverWithReranking(
        vector_retriever=vector_retriever,
        keyword_retriever=sqlite_retriever,
        reranker=reranker,
        vector_weight=0.7,  # Use constants if defined, e.g., VECTOR_WEIGHT
        keyword_weight=0.3,  # Use constants if defined, e.g., KEYWORD_WEIGHT
        initial_top_k=20,  # Use constants if defined, e.g., INITIAL_TOP_K
    )
    return hybrid_retriever


# --- Main initialization function MODIFIED ---
def init_chat_engine() -> Dict:
    """Initializes the chat engine components with SYNC retrieval and returns them in a dict."""
    logger.info("--- Initializing Chat Engine (Sync Retrieval) --- ")

    # 1. Initialize Settings (LLM, Embed Model)
    _init_settings()

    # 2. Get Cohere API Key (needed for retriever)
    cohere_api_key = os.environ.get("COHERE_API_KEY")
    if not cohere_api_key:
        raise ValueError("COHERE_API_KEY environment variable is not set")

    # 3. Create/Load SQLite DB *before* creating retriever
    nodes_pickle_path = NODE_PICKLE_FILE
    if os.environ.get("PLASH_PRODUCTION") == "1":
        sqlite_db_path = SQLITE_DB_NAME_PROD
        logger.info("Running in PLASH_PRODUCTION mode.")
    else:
        sqlite_db_path = SQLITE_DB_NAME_LOCAL
        logger.info("Running in local mode.")
    try:
        if not os.path.exists(nodes_pickle_path):
            logging.warning(
                f"Node pickle file '{nodes_pickle_path}' not found. Skipping SQLite DB creation/check."
            )
            # If SQLite is essential, could raise error here instead.
            # raise FileNotFoundError(f"Required node file '{nodes_pickle_path}' not found for SQLite DB.")
        else:
            create_or_load_sqlite_db(nodes_pickle_path, sqlite_db_path)
    except FileNotFoundError as e:
        logging.error(f"Fatal Error during SQLite setup: {e}.")
        raise
    except sqlite3.Error as e:  # More specific exception
        logging.error(f"Error during SQLite DB creation/check: {e}")
        raise  # Stop execution if DB fails
    except Exception as e:  # Catch other potential errors like pickle load
        logging.error(f"Unexpected error during SQLite setup: {e}")
        raise

    # 4. Create the SYNC retriever
    try:
        retriever = _create_sync_retriever(cohere_api_key)
    except Exception as e:
        logging.error(f"Fatal Error: Could not create retriever: {e}")
        raise

    # 5. Initialize Langfuse Tracing (after settings)
    langfuse_components = _init_langfuse()
    # We don't need to use the handler directly since it's already set in the callback manager
    langfuse_instrumentor = langfuse_components.get("instrumentor")

    if langfuse_instrumentor:
        logger.info("LangFuse instrumentor initialized and started")
    else:
        logger.info("LangFuse instrumentor not available")

    # 6. Create the Chat Engine (using sync retriever)
    try:
        memory = ChatMemoryBuffer.from_defaults(token_limit=3900)
        chat_engine = ContextChatEngine.from_defaults(
            retriever=retriever,
            memory=memory,
            llm=Settings.llm,
            system_prompt="""You are a helpful technical support assistant specializing in Matrix laser products and technology.
            Use the provided context to answer questions accurately and concisely.
            If the context doesn't contain the answer, state that the information is not available in the provided documents.
            Do not make up information. Be specific when referring to product names or technical details found in the context.""",
            # Ensure callback manager is used if Langfuse initialized
            callback_manager=Settings.callback_manager,
        )
        logger.info("Chat Engine Initialized Successfully.")
    except Exception as e:
        logger.error(f"Fatal Error: Could not create chat engine: {e}")
        raise

    # 7. Return components
    return {
        "chat_engine": chat_engine,
        "retriever": retriever,  # Now the sync retriever
        "langfuse_instrumentor": langfuse_instrumentor,
    }


# --- generate_streaming_response (Keep as is for async inference) ---
async def generate_streaming_response(
    query: str,
    chat_engine: BaseChatEngine,  # Accept chat_engine instance
    chat_history: Optional[List] = None,
    system_prompt: Optional[str] = None,
) -> AsyncGenerator[str, None]:  # Change return type to AsyncGenerator
    """Generates a streaming response using the provided chat engine instance."""
    if not chat_engine:
        logger.error("Received None for chat_engine instance.")
        yield "Error: Chat engine not available."
        return

    logger.info(f"Using chat engine instance: {type(chat_engine)}")

    # Set history on the passed engine instance if provided
    if chat_history:
        # Assuming chat_engine has chat_history attribute or similar mechanism
        if hasattr(chat_engine, "chat_history"):
            chat_engine.chat_history = chat_history
        else:
            logger.warning(
                "Chat engine instance does not have 'chat_history' attribute."
            )
    # If chat_engine manages history via memory buffer, this might not be needed
    # else:
    #     pass # History is managed by the engine's memory buffer

    # Pass the query string directly; history is handled by memory or set above
    try:
        response_stream: StreamingAgentChatResponse = chat_engine.stream_chat(
            query
        )  # Use synchronous stream method
        logger.info("Started streaming response from chat engine.")

        # Process the generator for text chunks
        for chunk in response_stream.response_gen:
            yield chunk

        # Optionally process source nodes if needed later
        # source_nodes = response_stream.source_nodes
        # if source_nodes:
        #     yield "\n\nSources:\n"
        #     for node in source_nodes:
        #         yield f"- {node.metadata.get('file_name', 'Unknown')}\n"

    except Exception as e:
        logger.error(f"Error during chat engine streaming: {e}", exc_info=True)
        yield f"Error: An issue occurred while processing your request."


# --- Helper function to initialize Langfuse callback handler ---
def _init_langfuse() -> Dict:
    """
    Initialize Langfuse tracing if environment variables are set.
    Returns a dictionary with both the callback handler and instrumentor.
    """
    langfuse_handler = None
    langfuse_instrumentor = None

    # Check for required Langfuse environment variables
    langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if langfuse_secret_key and langfuse_public_key:
        try:
            # 1. Initialize the callback handler for LlamaIndex operations
            langfuse_handler = LlamaIndexCallbackHandler(
                public_key=langfuse_public_key,
                secret_key=langfuse_secret_key,
                host=langfuse_host,
            )

            # Set the callback manager globally for LlamaIndex
            Settings.callback_manager = CallbackManager([langfuse_handler])

            # 2. Initialize the LlamaIndex instrumentor for automatic tracing
            langfuse_instrumentor = LlamaIndexInstrumentor(
                public_key=langfuse_public_key,
                secret_key=langfuse_secret_key,
                host=langfuse_host,
                flush_at_shutdown=True,  # Auto-flush at shutdown
                name="matrix_chatbot",  # Name for all traces created
            )

            # Start the instrumentor to track all LlamaIndex operations
            langfuse_instrumentor.start()

            logger.info("Langfuse tracing initialized successfully")
        except ImportError:
            logger.warning(
                "Langfuse requires `langfuse`. Install with `pip install langfuse`"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Langfuse: {e}")
    else:
        logger.info(
            "Langfuse environment variables not set. Skipping Langfuse integration."
        )
        # Ensure a default empty callback manager if Langfuse isn't used
        if not Settings.callback_manager:
            Settings.callback_manager = CallbackManager([])

    return {"handler": langfuse_handler, "instrumentor": langfuse_instrumentor}


if __name__ == "__main__":
    pass  # Remove asyncio test run


# --- END OF FILE chat_engine.py ---
