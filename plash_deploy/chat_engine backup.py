import os
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
    def __init__(self, db_path="./enhanced_laser_nodes.db", top_k=5):
        self.db_path = db_path
        self.top_k = top_k

    def retrieve(self, query_str: str) -> List[NodeWithScore]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        escaped_query = f'"{query_str}"'
        c.execute(
            f"""
            SELECT nodes.node_id, nodes.content, nodes.metadata, nodes_fts.rank
            FROM nodes_fts 
            JOIN nodes ON nodes_fts.rowid = nodes.rowid
            WHERE nodes_fts MATCH ? 
            ORDER BY nodes_fts.rank
            LIMIT {self.top_k}
            """,
            (escaped_query,),
        )

        results = []
        for node_id, content, metadata_blob, rank in c.fetchall():
            import json

            metadata = json.loads(metadata_blob)
            node = TextNode(text=content, metadata=metadata, id_=node_id)
            score = 1.0 / (1.0 + float(rank))
            results.append(NodeWithScore(node=node, score=score))

        conn.close()
        return results


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
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        self.initial_top_k = initial_top_k
        super().__init__()

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        query_str = query_bundle.query_str

        # Get results from both retrievers
        vector_results = self.vector_retriever.retrieve(query_str)
        keyword_results = self.keyword_retriever.retrieve(query_str)

        # Combine scores
        node_scores = {}
        for i, result in enumerate(vector_results):
            node_id = result.node.node_id
            score = self.vector_weight * (1.0 / (i + 1))
            node_scores[node_id] = {"node": result.node, "score": score}

        for i, result in enumerate(keyword_results):
            node_id = result.node.node_id
            keyword_score = self.keyword_weight * (1.0 / (i + 1))
            if node_id in node_scores:
                node_scores[node_id]["score"] += keyword_score
            else:
                node_scores[node_id] = {"node": result.node, "score": keyword_score}

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
        reranked_nodes = self.reranker.postprocess_nodes(initial_results, query_bundle)

        return reranked_nodes


def create_or_load_vector_store(nodes_path, qdrant_save_path):
    """Create Qdrant vector store if it doesn't exist, or load existing one"""

    # Always recreate from nodes to ensure consistency
    print(f"Creating new Qdrant vector store from nodes in {nodes_path}")

    # Load nodes
    with open(nodes_path, "rb") as f:
        nodes = pickle.load(f)

    # Explicitly embed the nodes
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

    if qdrant_client.collection_exists(collection_name):
        qdrant_client.delete_collection(collection_name)

    # Create collection with the proper configuration - explicitly set to 3072 dimensions
    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config={"size": 3072, "distance": "Cosine"},
    )

    # Create vector store
    vector_store = QdrantVectorStore(
        client=qdrant_client, collection_name=collection_name
    )

    # Create storage context and index with pre-embedded nodes
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex(nodes, storage_context=storage_context, embed_model=None)

    # Get points from the collection
    points = qdrant_client.scroll(collection_name=collection_name, limit=10000)[0]

    # Create collection data for saving
    collection_data = {
        "collection_name": collection_name,
        "vector_size": 3072,
        "points": points,
    }

    # Save to disk
    with open(qdrant_save_path, "wb") as f:
        pickle.dump(collection_data, f)
    print(f"Saved Qdrant vector store to {qdrant_save_path}")

    return collection_data


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


def create_retriever(cohere_api_key, collection_data=None):
    # Load SQLite retriever
    sqlite_retriever = SQLiteFTSRetriever()

    try:
        # Create Qdrant client
        qdrant_client = QdrantClient(":memory:")
        collection_name = "laser_docs"  # Use a consistent name

        if collection_data is None:
            # Load nodes and create from scratch
            nodes_path = "./enhanced_laser_nodes.pkl"
            with open(nodes_path, "rb") as f:
                nodes = pickle.load(f)

            # Ensure nodes are embedded with consistent dimensions
            embed_model = Settings.embed_model
            for node in nodes:
                if not hasattr(node, "embedding") or node.embedding is None:
                    print(f"Embedding node {node.node_id}...")
                    node.embedding = embed_model.get_text_embedding(
                        node.get_content(metadata_mode="all")
                    )

            # Create collection with the proper configuration - explicitly set to 3072
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

            # Create storage context and index with pre-embedded nodes
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            index = VectorStoreIndex(
                nodes, storage_context=storage_context, embed_model=None
            )
        else:
            # Use provided collection data
            if qdrant_client.collection_exists(collection_name):
                qdrant_client.delete_collection(collection_name)

            # Create collection with the proper configuration
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    "size": collection_data["vector_size"],
                    "distance": "Cosine",
                },
            )

            # Upsert points if available
            if collection_data["points"] and len(collection_data["points"]) > 0:
                try:
                    qdrant_client.upsert(
                        collection_name=collection_name,
                        points=collection_data["points"],
                    )
                except Exception as e:
                    print(f"Error upserting points: {e}")
                    print("Recreating index from nodes...")

                    # If upserting fails, recreate the index from nodes
                    nodes_path = "./enhanced_laser_nodes.pkl"
                    with open(nodes_path, "rb") as f:
                        nodes = pickle.load(f)

                    # Ensure nodes are embedded
                    embed_model = Settings.embed_model
                    for node in nodes:
                        if not hasattr(node, "embedding") or node.embedding is None:
                            node.embedding = embed_model.get_text_embedding(
                                node.get_content(metadata_mode="all")
                            )

                    # Create vector store and index with pre-embedded nodes
                    vector_store = QdrantVectorStore(
                        client=qdrant_client, collection_name=collection_name
                    )

                    storage_context = StorageContext.from_defaults(
                        vector_store=vector_store
                    )
                    index = VectorStoreIndex(
                        nodes, storage_context=storage_context, embed_model=None
                    )

        # Create vector retriever
        vector_store = QdrantVectorStore(
            client=qdrant_client, collection_name=collection_name
        )

        index = VectorStoreIndex.from_vector_store(vector_store)
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
    qdrant_save_path = "./laser_qdrant.pkl"
    sqlite_db_path = "./laser_nodes.db"

    # Create or load vector store
    collection_data = create_or_load_vector_store(nodes_path, qdrant_save_path)

    # Create or load SQLite database
    create_or_load_sqlite_db(nodes_path, sqlite_db_path)

    # Create retrievers and chat engine
    retriever = create_retriever(cohere_api_key, collection_data)
    return create_chat_engine(retriever)
