# Project Summary: Technical Support Chatbot for Laser Measurement Products

## Goal
To create an intelligent chatbot that can accurately answer technical questions about laser power meters, energy meters, and beam diagnostics products by leveraging information directly from product datasheets.

## Core Technology
Retrieval-Augmented Generation (RAG) using LlamaIndex, LlamaParse, OpenAI, Cohere, Qdrant, SQLite, and FastHTML.

## Workflow Overview

The project follows a multi-stage pipeline to transform raw PDF datasheets into an interactive, context-aware chatbot:

### Phase 1: Data Ingestion & Preparation

#### Stage 1: Advanced PDF Parsing & Initial Extraction (`parse.py`)
*   **Input:** Directory of PDF product datasheets.
*   **Process:**
    *   Utilizes LlamaParse (a specialized cloud service) for robust parsing of complex PDFs, handling text, tables, and potentially images.
    *   Employs a detailed custom `user_prompt` combined with `auto_mode=True` settings. This specific combination proved crucial through testing to instruct LlamaParse to:
        *   Extract clean Markdown representation of the datasheet content (including tables with filled cells).
        *   Identify and extract (`model_name`, `part_number`) pairs, appending them in a structured `Metadata: {pairs: ...}` block within the parsed text output.
    *   Runs parsing jobs in parallel using `asyncio` for efficiency.
    *   Implements a post-processing step after LlamaParse:
        *   Uses regex and `ast.literal_eval` to reliably find the `Metadata: {pairs: ...}` block in the text.
        *   Parses the pairs.
        *   Transforms pairs into a `List[Dict[str, str]]` format (`[{'model_name': ..., 'part_number': ...}]`) for better downstream querying.
        *   Adds this structured list to the `Document.metadata` field under the key `'pairs'`.
        *   Safely removes the original `Metadata: {...}` block from the `Document.text` using `set_content()`, only if the block isn't the entire content of that chunk (preventing accidental data loss).
*   **Output:** A Python pickle file (`parsed_docs.pkl`) containing a list of `llama_index.core.Document` objects. Each object represents a section of a PDF with clean text content and structured pairs metadata.
*   **Benefits:** Overcomes limitations of standard PDF text extraction; accurately handles datasheet tables; extracts critical structured data (model/part pairs); provides clean text ready for chunking. The iterative debugging revealed the necessity of the specific `user_prompt`/`auto_mode` combination for LlamaParse.

#### Stage 2: Node Creation & Contextual Enhancement (`metadata.py`)
*   **Input:** `parsed_docs.pkl` (output from Stage 1).
*   **Process:**
    *   Loads the `Document` objects.
    *   Uses `llama_index.core.node_parser.SentenceSplitter` to break down the documents into smaller, more manageable `TextNode` chunks suitable for retrieval (e.g., 2048 characters with overlap). Metadata (including the structured pairs list, source file info) is automatically propagated from the parent `Document` to the child `TextNodes`.
    *   For each `TextNode`, calls the OpenAI API (using `gpt-4o-mini` for cost-effectiveness) with a specific prompt to generate concise context keywords and phrases summarizing the node's content. Pronouns are replaced for clarity.
    *   Appends this generated `Context: ...` string directly to the `TextNode.text` content.
*   **Output:** A Python pickle file (`enhanced_laser_nodes.pkl`) containing a list of `llama_index.core.schema.TextNode` objects, each enriched with context and carrying relevant metadata.
*   **Benefits:** Creates appropriately sized chunks for effective retrieval; enriches nodes with explicit semantic context, aiding both vector and keyword search; prepares data specifically for indexing.

---

### Phase 2: Indexing & Retrieval Strategy

#### Stage 3: Hybrid Knowledge Base Creation (`chat_engine.py` - setup part)
*   **Input:** `enhanced_laser_nodes.pkl` (output from Stage 2).
*   **Process:** Builds two complementary indexes for robust retrieval:
    *   **SQLite FTS5 Index (`laser_nodes.db`):** Creates a persistent SQLite database with a Full-Text Search (FTS5) index on the node content and metadata. This allows extremely fast and efficient keyword searching, phrase matching, and prefix searching – ideal for exact part numbers or specific technical terms.
    *   **Qdrant Vector Store (In-Memory):** Creates an in-memory vector index using `QdrantClient`. Embeds each `TextNode` (using OpenAI's `text-embedding-3-large` model) and stores the vectors. This enables semantic similarity search, finding nodes with related concepts even if keywords don't match exactly. (Note: Could be configured for persistent Qdrant if needed).
*   **Output:** A populated SQLite FTS database and an in-memory Qdrant vector index.
*   **Benefits:** Leverages the distinct strengths of keyword (precision, speed for known terms) and vector (semantic understanding, concept matching) search technologies. SQLite provides persistence for the keyword index.

#### Stage 4: Advanced Hybrid Retriever Implementation (`chat_engine.py` - retriever part)
*   **Input:** The SQLite FTS database and the Qdrant Vector Store index.
*   **Process:**
    *   Implements separate retrievers: `SQLiteFTSRetriever` (custom class querying the FTS DB) and a standard `VectorIndexRetriever` (querying Qdrant).
    *   Defines `analyze_query`: A crucial function that inspects the user's query to classify it (e.g., "part_number", "model", "general").
    *   Implements `HybridRetrieverWithReranking`:
        *   Takes both base retrievers as input.
        *   Retrieves an initial set of candidates from both sources.
        *   Dynamically adjusts weights for vector vs. keyword results based on the `analyze_query` output (e.g., heavily weighting keyword results if a part number is detected).
        *   Applies score boosting based on metadata matches (e.g., boosting keyword results if the detected part number exists in the node's `'pairs'` metadata).
        *   Combines and scores results from both sources.
        *   Uses Cohere Rerank API (high-quality semantic reranker) to re-order the top combined candidates based on relevance to the original query.
*   **Output:** A highly configured `HybridRetrieverWithReranking` object.
*   **Benefits:** Optimizes retrieval by dynamically choosing the best strategy (keyword/vector bias) based on query type; significantly improves precision for part number/model queries through boosting; reranking ensures the most relevant context is passed to the LLM, reducing noise and improving answer quality.

---

### Phase 3: Chat Interface & Interaction

#### Stage 5: Contextual Chat Engine Setup (`chat_engine.py` - engine part)
*   **Input:** The `HybridRetrieverWithReranking` object.
*   **Process:**
    *   Initializes `llama_index.core.chat_engine.ContextChatEngine`.
    *   Configures the engine to use the sophisticated hybrid retriever created in Stage 4.
    *   Integrates `ChatMemoryBuffer` to allow the chatbot to remember previous turns in the conversation.
    *   Sets a `system_prompt` guiding the LLM (OpenAI `gpt-4o`) to act as a helpful laser measurement assistant and primarily use the provided context for answers.
*   **Output:** An initialized `chat_engine` ready to process user queries.
*   **Benefits:** Provides the core RAG functionality; ensures responses are grounded in retrieved datasheet information; enables multi-turn conversations; defines the chatbot's persona.

#### Stage 6: Web User Interface (`main.py`)
*   **Input:** The initialized `chat_engine`.
*   **Process:**
    *   Uses FastHTML (a Pythonic web framework leveraging HTMX) to build the user interface.
    *   Defines routes for displaying the chat page and handling user message submissions (`/send-message`).
    *   Creates a clean, high-contrast UI with distinct user/assistant messages.
    *   Uses HTMX for dynamic updates: sends user query to the backend, receives HTML fragments for user message and assistant response, and swaps them into the chat log without full page reloads.
    *   Includes custom Markdown rendering (`mistletoe`) to handle code blocks gracefully and prevent layout issues seen with standard Markdown libraries.
*   **Output:** A running web application accessible via a browser.
*   **Benefits:** Provides an intuitive and interactive user experience; leverages modern web techniques (HTMX) for responsiveness; simple Python backend integration.

---

## Key Insights & Learnings

*   **Parsing is Foundational:** High-quality parsing that handles specific document structures (like datasheets) and extracts both text and structured data is critical for RAG success. LlamaParse + careful prompting was key.
*   **Metadata is Powerful:** Extracting structured data (like model/part pairs) and storing it correctly in metadata enables advanced retrieval strategies (boosting, filtering). Formatting this metadata (`list` of `dicts`) matters.
*   **Hybrid Retrieval Excels:** Combining keyword and vector search provides superior results compared to using either alone, especially for technical domains with specific identifiers (part numbers).
*   **Query Analysis is Crucial:** Dynamically adapting the retrieval strategy based on the type of query significantly improves relevance.
*   **Reranking Adds Polish:** A high-quality reranker like Cohere is essential for refining the final context passed to the LLM, leading to better, more concise answers.
*   **Iterative Development:** Debugging API interactions (like the LlamaParse parameter behavior) and refining logic based on observed output is a necessary part of building complex pipelines.

This workflow provides a robust, adaptable foundation for building similar technical support chatbots for other product lines within the company.