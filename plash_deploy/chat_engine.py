# chat_engine.py

import os
import re
import pickle
import sqlite3
from typing import List
from llama_index.core.schema import NodeWithScore, TextNode, QueryBundle
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.chat_engine import ContextChatEngine
from qdrant_client import QdrantClient
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.postprocessor.cohere_rerank import CohereRerank
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings


# SQLite FTS Retriever
class SQLiteFTSRetriever:
    def __init__(self, db_path=None, top_k=5):
        if db_path is None:
            # Use different paths for local and production
            if os.environ.get("PLASH_PRODUCTION") == "1":
                self.db_path = "/app/laser_nodes.db"
            else:
                self.db_path = "./laser_nodes.db"
        else:
            self.db_path = db_path
        self.top_k = top_k

    def retrieve(self, query_str: str) -> List[NodeWithScore]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Analyze the query
        analysis = analyze_query(query_str)
        
        # Build the FTS query based on query type
        if analysis['query_type'] == 'part_number':
            # For part numbers, use exact matching and metadata
            part_numbers = analysis['detected_part_numbers']
            if part_numbers:
                # Create a query that looks for exact part numbers in both content and metadata
                query_parts = []
                for part in part_numbers:
                    # Look for exact matches with word boundaries
                    query_parts.append(f'"{part}"')
                
                fts_query = ' OR '.join(query_parts)
                
                # Execute query with exact matching
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
            else:
                # Fallback to normal search if no part numbers detected
                c.execute(
                    f"""
                    SELECT nodes.node_id, nodes.content, nodes.metadata, nodes_fts.rank
                    FROM nodes_fts 
                    JOIN nodes ON nodes_fts.rowid = nodes.rowid
                    WHERE nodes_fts MATCH ? 
                    ORDER BY nodes_fts.rank
                    LIMIT {self.top_k}
                    """,
                    (f'"{query_str}"',),
                )
        
        elif analysis['query_type'] == 'model':
            # For model names, use a combination of exact and fuzzy matching
            # This helps catch variations in model names (PM10 vs PowerMax 10)
            query_terms = query_str.lower().split()
            query_parts = []
            
            # Add exact phrase matching
            query_parts.append(f'"{query_str}"')
            
            # Add individual term matching with word boundaries
            for term in query_terms:
                if term in ['pm', 'op', 'lm']:
                    # For common prefixes, also look for expanded forms
                    if term == 'pm':
                        query_parts.append('(powermax OR "power max")')
                    elif term == 'op':
                        query_parts.append('(optical OR op)')
                    elif term == 'lm':
                        query_parts.append('(labmax OR "lab max")')
                query_parts.append(f'"{term}"')
            
            fts_query = ' OR '.join(query_parts)
            
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
        
        else:
            # For general queries, use standard FTS matching
            c.execute(
                f"""
                SELECT nodes.node_id, nodes.content, nodes.metadata, nodes_fts.rank
                FROM nodes_fts 
                JOIN nodes ON nodes_fts.rowid = nodes.rowid
                WHERE nodes_fts MATCH ? 
                ORDER BY nodes_fts.rank
                LIMIT {self.top_k}
                """,
                (f'"{query_str}"',),
            )

        results = []
        for node_id, content, metadata_blob, rank in c.fetchall():
            import json

            metadata = json.loads(metadata_blob)
            node = TextNode(text=content, metadata=metadata, id_=node_id)
            
            # Base score from rank
            score = 1.0 / (1.0 + float(rank))
            
            # Boost score based on metadata matches
            if analysis['query_type'] == 'part_number' and 'part_numbers' in metadata:
                for part_number in analysis['detected_part_numbers']:
                    if part_number in metadata['part_numbers']:
                        score *= 2.0  # Double score for metadata matches
            
            elif analysis['query_type'] == 'model' and 'product_names' in metadata:
                if any(model.lower() in query_str.lower() for model in metadata['product_names']):
                    score *= 1.5  # 50% boost for model name matches
            
            results.append(NodeWithScore(node=node, score=score))

        conn.close()
        return results


def analyze_query(query: str) -> dict:
    """Analyze query to detect if it's looking for specific part numbers or model names.
    
    Args:
        query: The query string
        
    Returns:
        Dict with query analysis results
    """
    # Common patterns in part numbers and model names
    part_number_pattern = r'\d{7}|\d{2}-\d{3}-\d{3}'  # Matches 7-digit or XX-XXX-XXX format
    model_keywords = ['model', 'pm', 'op', 'lm', 'powermax', 'labmax', 'fieldmax']
    
    analysis = {
        'has_part_number': bool(re.search(part_number_pattern, query.lower())),
        'has_model_reference': any(keyword in query.lower() for keyword in model_keywords),
        'detected_part_numbers': re.findall(part_number_pattern, query),
        'query_type': 'general'
    }
    
    # Determine query type
    if analysis['has_part_number']:
        analysis['query_type'] = 'part_number'
    elif analysis['has_model_reference']:
        analysis['query_type'] = 'model'
    
    return analysis


# Hybrid Retriever with Reranking
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
        """Retrieve nodes given query."""
        query_str = query_bundle.query_str
        
        # Analyze query to determine weights and boost factors
        analysis = analyze_query(query_str)
        
        # Adjust weights based on query type
        if analysis['query_type'] == 'part_number':
            vector_weight = self.base_vector_weight * 0.5  # Reduce vector weight
            keyword_weight = self.base_keyword_weight * 2.0  # Increase keyword weight
        elif analysis['query_type'] == 'model':
            vector_weight = self.base_vector_weight * 0.8
            keyword_weight = self.base_keyword_weight * 1.5
        else:
            vector_weight = self.base_vector_weight
            keyword_weight = self.base_keyword_weight

        # Get results from both retrievers
        vector_results = self.vector_retriever.retrieve(query_str)
        keyword_results = self.keyword_retriever.retrieve(query_str)

        # Combine scores
        node_scores = {}
        
        # Process vector results
        for i, result in enumerate(vector_results):
            node_id = result.node.node_id
            score = vector_weight * (1.0 / (i + 1))
            node_scores[node_id] = {"node": result.node, "score": score}

        # Process keyword results and apply boosting
        for i, result in enumerate(keyword_results):
            node_id = result.node.node_id
            score = keyword_weight * (1.0 / (i + 1))
            
            # Apply boosting for exact part number matches
            if analysis['query_type'] == 'part_number' and 'part_numbers' in result.node.metadata:
                for part_number in analysis['detected_part_numbers']:
                    if part_number in result.node.metadata['part_numbers']:
                        score *= 2.0  # Double the score for exact part number match
            
            # Apply boosting for model name matches
            if analysis['query_type'] == 'model' and 'product_names' in result.node.metadata:
                if any(model.lower() in query_str.lower() for model in result.node.metadata['product_names']):
                    score *= 1.5  # Boost score by 50% for model name match

            if node_id in node_scores:
                node_scores[node_id]["score"] += score
            else:
                node_scores[node_id] = {"node": result.node, "score": score}

        # Sort by score
        sorted_results = sorted(
            node_scores.values(), key=lambda x: x["score"], reverse=True
        )

        # Convert to NodeWithScore objects
        initial_results = [
            NodeWithScore(node=item["node"], score=item["score"])
            for item in sorted_results[: self.initial_top_k]
        ]

        # Apply reranking
        if self.reranker is not None:
            try:
                reranked_nodes = self.reranker.postprocess_nodes(initial_results, query_bundle)
                return reranked_nodes
            except Exception as e:
                print(f"Error during reranking: {e}")
                return initial_results
        
        return initial_results


def create_or_load_sqlite_db(nodes_path, db_path):
    """Create SQLite FTS database if it doesn't exist, or use existing one"""

    if os.path.exists(db_path):
        print(f"Using existing SQLite database at {db_path}")
        return

    print(f"Creating new SQLite FTS database at {db_path}")
    # Load nodes
    with open(nodes_path, "rb") as f:
        nodes = pickle.load(f)

    # Create SQLite database and tables
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Create nodes table
    c.execute("""
    CREATE TABLE IF NOT EXISTS nodes (
        rowid INTEGER PRIMARY KEY,
        node_id TEXT,
        content TEXT,
        metadata TEXT
    )
    """)

    # Create FTS table
    c.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts 
    USING fts5(content, metadata, content=nodes, content_rowid=rowid)
    """)

    # Insert nodes
    for node in nodes:
        import json

        metadata_json = json.dumps(node.metadata)
        c.execute(
            "INSERT INTO nodes (node_id, content, metadata) VALUES (?, ?, ?)",
            (node.node_id, node.text, metadata_json),
        )

    # Populate FTS table
    c.execute("""
    INSERT INTO nodes_fts(rowid, content, metadata)
    SELECT rowid, content, metadata FROM nodes
    """)

    conn.commit()
    conn.close()
    print(f"Created SQLite FTS database with {len(nodes)} nodes")


def create_retriever(cohere_api_key):
    # Load SQLite retriever
    sqlite_retriever = SQLiteFTSRetriever()

    try:
        # Load nodes and create vector store directly
        nodes_path = "./enhanced_laser_nodes.pkl"
        with open(nodes_path, "rb") as f:
            nodes = pickle.load(f)

        # Ensure nodes are embedded with consistent dimensions
        embed_model = Settings.embed_model
        for node in nodes:
            if not hasattr(node, "embedding") or node.embedding is None:
                print(f"Embedding node...")
                node.embedding = embed_model.get_text_embedding(
                    node.get_content(metadata_mode="all")
                )

        # Create in-memory Qdrant client
        qdrant_client = QdrantClient(":memory:")
        collection_name = "laser_docs"

        # Create collection with explicit 3072 dimension
        if qdrant_client.collection_exists(collection_name):
            qdrant_client.delete_collection(collection_name)

        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config={"size": 3072, "distance": "Cosine"},
        )

        # Create vector store
        vector_store = QdrantVectorStore(
            client=qdrant_client, collection_name=collection_name
        )

        # Create index directly from nodes
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex(
            nodes, storage_context=storage_context, embed_model=None
        )

        # Create vector retriever
        vector_retriever = index.as_retriever(similarity_top_k=10)

    except Exception as e:
        print(f"Error creating vector retriever: {e}")
        raise

    # Create Cohere reranker
    reranker = CohereRerank(api_key=cohere_api_key, model="rerank-v3.5", top_n=5)

    # Create and return hybrid retriever with reranking
    return HybridRetrieverWithReranking(
        vector_retriever=vector_retriever,
        keyword_retriever=sqlite_retriever,
        reranker=reranker,
        vector_weight=0.7,
        keyword_weight=0.3,
        initial_top_k=20,
    )


# Create chat engine
def create_chat_engine(retriever):
    memory = ChatMemoryBuffer.from_defaults(token_limit=3900)
    return ContextChatEngine.from_defaults(
        retriever=retriever,
        memory=memory,
        system_prompt="""You are a helpful assistant specializing in laser measurement technology.
        Answer questions based on the context provided. If you don't know the answer, say so.""",
    )


# Main initialization function
def init_chat_engine():
    # Check for required API keys
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    cohere_api_key = os.environ.get("COHERE_API_KEY")

    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    if not cohere_api_key:
        raise ValueError("COHERE_API_KEY environment variable is not set")

    # Initialize LLM and embeddings
    llm = OpenAI(model="gpt-4o", api_key=openai_api_key)
    embed_model = OpenAIEmbedding(
        model="text-embedding-3-large", api_key=openai_api_key
    )
    Settings.llm = llm
    Settings.embed_model = embed_model

    # Define paths
    nodes_path = "./enhanced_laser_nodes.pkl"
    if os.environ.get("PLASH_PRODUCTION") == "1":
        sqlite_db_path = "/app/laser_nodes.db"
    else:
        sqlite_db_path = "./laser_nodes.db"

    # Create or load SQLite database
    if not os.path.exists(sqlite_db_path):
        create_or_load_sqlite_db(nodes_path, sqlite_db_path)

    # Create retriever directly (skip saving/loading Qdrant)
    retriever = create_retriever(cohere_api_key)

    return create_chat_engine(retriever)
