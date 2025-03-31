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
    def __init__(self, db_path="enhanced_laser_nodes.db", top_k=5):
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


# Load function for vector stores and create retriever
def create_retriever(cohere_api_key):
    # Load SQLite retriever
    sqlite_retriever = SQLiteFTSRetriever()

    # Load Qdrant collection
    with open("laser_qdrant.pkl", "rb") as f:
        collection_data = pickle.load(f)

    # Create Qdrant client and collection
    qdrant_client = QdrantClient(":memory:")
    collection_name = collection_data["collection_name"]

    if qdrant_client.collection_exists(collection_name):
        qdrant_client.delete_collection(collection_name)

    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config={"size": collection_data["vector_size"], "distance": "Cosine"},
    )

    if collection_data["points"]:
        qdrant_client.upsert(
            collection_name=collection_name, points=collection_data["points"]
        )

    # Create vector store and retriever
    vector_store = QdrantVectorStore(
        client=qdrant_client, collection_name=collection_name
    )

    index = VectorStoreIndex.from_vector_store(vector_store)
    vector_retriever = index.as_retriever(similarity_top_k=10)

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

    retriever = create_retriever(cohere_api_key)
    return create_chat_engine(retriever)
