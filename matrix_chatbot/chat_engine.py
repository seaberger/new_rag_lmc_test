# --- START OF FILE chat_engine.py ---

# chat_engine.py

import os
import re
import pickle
import sqlite3
import json
import logging  # Import logging
from typing import List
from pathlib import Path  # Import Path

from llama_index.core.schema import NodeWithScore, TextNode, QueryBundle
from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.chat_engine import ContextChatEngine
from qdrant_client import QdrantClient
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.postprocessor.cohere_rerank import CohereRerank
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings

# --- Define constants for file/db names ---
NODE_PICKLE_FILE = "matrix_nodes.pkl"  # Still needed for SQLite DB creation
SQLITE_DB_NAME_LOCAL = "matrix_nodes.db"
SQLITE_DB_NAME_PROD = "/app/matrix_nodes.db"
QDRANT_COLLECTION_NAME = "matrix_docs"  # MUST match create_vector_db.py
# --- Define Qdrant paths ---
QDRANT_PATH_LOCAL = "./qdrant_db"  # Relative path for local execution
QDRANT_PATH_PROD = "/app/qdrant_db"  # Absolute path in Plash container

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# --- SQLiteFTSRetriever (No changes needed from previous version) ---
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
        analysis = analyze_query(query_str)
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
                    "FTS table not found. DB might be initializing or empty."
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
            score = 1.0 / (1.0 + float(rank))
            results.append(NodeWithScore(node=node, score=score))
        conn.close()
        results.sort(key=lambda x: x.score, reverse=True)
        return results


# --- Analyze Query (No changes needed) ---
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


# --- Hybrid Retriever with Reranking (No changes needed) ---
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
        if analysis["query_type"] == "part_number":
            vector_weight *= 0.5
            keyword_weight *= 2.0
        elif analysis["query_type"] == "model":
            vector_weight *= 0.8
            keyword_weight *= 1.5
        vector_results = self.vector_retriever.retrieve(query_str)
        keyword_results = self.keyword_retriever.retrieve(query_str)
        node_scores = {}
        max_score = 0.0
        for result in vector_results:
            node_id = result.node.node_id
            score = result.score * vector_weight
            if node_id not in node_scores:
                node_scores[node_id] = {"node": result.node, "score": 0.0}
            node_scores[node_id]["score"] += score
            max_score = max(max_score, node_scores[node_id]["score"])
        keyword_max_rank_score = keyword_weight
        for i, result in enumerate(keyword_results):
            node_id = result.node.node_id
            keyword_score = keyword_max_rank_score * (1.0 / (i + 1))
            # Add boosting logic here if needed based on metadata
            if node_id not in node_scores:
                node_scores[node_id] = {"node": result.node, "score": 0.0}
            node_scores[node_id]["score"] += keyword_score
            max_score = max(max_score, node_scores[node_id]["score"])
        if max_score > 0:
            for node_id in node_scores:
                node_scores[node_id]["score"] /= max_score
        sorted_results = sorted(
            node_scores.values(), key=lambda x: x["score"], reverse=True
        )
        initial_results_for_rerank = [
            NodeWithScore(node=item["node"], score=item["score"])
            for item in sorted_results[: self.initial_top_k]
        ]
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
        return initial_results_for_rerank[:final_top_n]


# --- Create/Load SQLite DB (No changes needed) ---
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
    c.execute(
        "CREATE TABLE IF NOT EXISTS nodes (rowid INTEGER PRIMARY KEY, node_id TEXT UNIQUE, content TEXT, metadata TEXT)"
    )
    conn.commit()
    c.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(content, content='nodes', content_rowid='rowid', tokenize='porter unicode61')"
    )
    conn.commit()
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


# --- Create Retriever (MODIFIED TO LOAD PERSISTENT QDRANT) ---
def create_retriever(cohere_api_key):
    # Determine paths
    nodes_pickle_path = NODE_PICKLE_FILE  # Needed for SQLite creation check
    if os.environ.get("PLASH_PRODUCTION") == "1":
        sqlite_db_path = SQLITE_DB_NAME_PROD
        qdrant_db_path = QDRANT_PATH_PROD
        logging.info("Using PRODUCTION paths for SQLite and Qdrant.")
    else:
        sqlite_db_path = SQLITE_DB_NAME_LOCAL
        qdrant_db_path = QDRANT_PATH_LOCAL
        logging.info("Using LOCAL paths for SQLite and Qdrant.")

    # --- SQLite Retriever Setup (remains the same) ---
    # Ensure SQLite DB is ready (create_or_load called in init_chat_engine)
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
        # Connect to the existing persistent Qdrant DB
        qdrant_client = QdrantClient(path=qdrant_db_path)

        # Check if collection exists
        try:
            qdrant_client.get_collection(collection_name=QDRANT_COLLECTION_NAME)
            logging.info(f"Found Qdrant collection '{QDRANT_COLLECTION_NAME}'.")
        except Exception as e:
            # Catch specific exception if possible, e.g., collection not found
            logging.error(
                f"Qdrant collection '{QDRANT_COLLECTION_NAME}' not found in DB at {qdrant_db_path}."
            )
            logging.error(f"Qdrant client error: {e}")
            raise ValueError(
                f"Collection '{QDRANT_COLLECTION_NAME}' not found. Ensure DB was created correctly."
            )

        vector_store = QdrantVectorStore(
            client=qdrant_client, collection_name=QDRANT_COLLECTION_NAME
        )

        logging.info("Loading VectorStoreIndex FROM existing vector store...")
        # Load the index *from* the store, DO NOT pass nodes here
        # We still need the embed_model for query processing
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

    # --- Reranker and Hybrid Retriever Setup (remains the same) ---
    logging.info("Initializing Cohere Reranker...")
    try:
        # Use a recent model if available, check Cohere docs. v3 is recommended.
        reranker = CohereRerank(api_key=cohere_api_key, model="rerank-v3.5", top_n=8)
    except Exception as e:
        logging.error(
            f"Error initializing Cohere Reranker: {e}. Reranking will be disabled."
        )
        reranker = None

    logging.info("Initializing Hybrid Retriever...")
    return HybridRetrieverWithReranking(
        vector_retriever=vector_retriever,
        keyword_retriever=sqlite_retriever,
        reranker=reranker,
        vector_weight=0.7,
        keyword_weight=0.3,
        initial_top_k=20,
    )


# --- Create chat engine (No changes needed) ---
def create_chat_engine(retriever):
    memory = ChatMemoryBuffer.from_defaults(token_limit=3900)
    logging.info("Creating ContextChatEngine...")
    return ContextChatEngine.from_defaults(
        retriever=retriever,
        memory=memory,
        llm=Settings.llm,
        system_prompt="""You are a helpful technical support assistant specializing in Matrix laser products and technology.
        Use the provided context to answer questions accurately and concisely.
        If the context doesn't contain the answer, state that the information is not available in the provided documents.
        Do not make up information. Be specific when referring to product names or technical details found in the context.""",
    )


# --- Main initialization function (No changes needed, SQLite creation still happens here) ---
def init_chat_engine():
    logging.info("Initializing Chat Engine...")
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    cohere_api_key = os.environ.get("COHERE_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    if not cohere_api_key:
        raise ValueError("COHERE_API_KEY environment variable is not set")

    logging.info("Initializing OpenAI models...")
    Settings.llm = OpenAI(model="gpt-4o", api_key=openai_api_key, temperature=0.1)
    # Ensure this matches the model used in create_vector_db.py!
    Settings.embed_model = OpenAIEmbedding(
        model="text-embedding-3-large", api_key=openai_api_key
    )
    logging.info(
        f"Using LLM: {Settings.llm.model}, Embed Model: {Settings.embed_model.model_name}"
    )

    nodes_pickle_path = NODE_PICKLE_FILE  # Still needed for SQLite
    if os.environ.get("PLASH_PRODUCTION") == "1":
        sqlite_db_path = SQLITE_DB_NAME_PROD
        logging.info("Running in PLASH_PRODUCTION mode.")
    else:
        sqlite_db_path = SQLITE_DB_NAME_LOCAL
        logging.info("Running in local mode.")

    # Create or load SQLite database *before* creating retriever
    try:
        # Check if node pickle exists before attempting SQLite creation
        if not os.path.exists(nodes_pickle_path):
            logging.warning(
                f"Node pickle file '{nodes_pickle_path}' not found. Skipping SQLite DB creation/check."
            )
            # If SQLite is essential, raise error here instead.
            # raise FileNotFoundError(f"Required node file '{nodes_pickle_path}' not found for SQLite DB.")
        else:
            create_or_load_sqlite_db(nodes_pickle_path, sqlite_db_path)
    except FileNotFoundError as e:
        logging.error(f"Fatal Error during SQLite setup: {e}.")
        raise
    except Exception as e:
        logging.error(f"Error during SQLite DB creation: {e}")
        raise  # Stop execution if DB fails

    # Create retriever (will now load persistent Qdrant)
    try:
        retriever = create_retriever(cohere_api_key)
    except Exception as e:
        logging.error(f"Fatal Error: Could not create retriever: {e}")
        raise

    # Create chat engine
    try:
        chat_engine_instance = create_chat_engine(retriever)
        logging.info("Chat Engine Initialized Successfully.")
        return chat_engine_instance
    except Exception as e:
        logging.error(f"Fatal Error: Could not create chat engine: {e}")
        raise


# --- END OF FILE chat_engine.py ---
