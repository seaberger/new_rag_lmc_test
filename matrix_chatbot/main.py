# --- START OF FILE main.py ---

# --- Import section for main.py ---
from fasthtml.common import *

from fasthtml import FastHTML
from fastapi import Request, Response
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from monsterui.all import *
import os
import re
import json
import logging
import asyncio
from uuid import uuid4
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List

# Import chat engine functions
from chat_engine import init_chat_engine, generate_streaming_response

# Create images directory if it doesn't exist
images_dir = Path("./images")
images_dir.mkdir(exist_ok=True)  # Ensure it exists

# Create assets directories if they don't exist
assets_dir = Path("./assets")
css_dir = assets_dir / "css"
js_dir = assets_dir / "js"
css_dir.mkdir(parents=True, exist_ok=True)
js_dir.mkdir(parents=True, exist_ok=True)

favicon_link = Link(
    rel="icon", type="image/png", href="/images/coherent_atom_symbol.png"
)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Constants ---
SUGGESTED_QUESTIONS_FILE_LOCAL = "./suggested_questions.json"
SUGGESTED_QUESTIONS_FILE_PROD = "/app/suggested_questions.json"
APP_VERSION = "1.0.0"  # Update this when you make significant changes


# --- Lifespan context manager for startup/shutdown ---
@asynccontextmanager
async def lifespan(app: FastHTML):
    logging.info(f"Application startup: Matrix Chatbot v{APP_VERSION}")

    try:
        # Initialize chat engine components
        chat_components = init_chat_engine()
        app.state.chat_engine = chat_components["chat_engine"]
        app.state.langfuse_instrumentor = chat_components.get("langfuse_instrumentor")

        # Store session ID for tracking
        app.state.session_id = f"session-{uuid4()}"

        logging.info("Application startup: Chat engine initialized successfully.")
    except Exception as e:
        logging.error(
            f"Application startup: FATAL error initializing chat engine: {e}",
            exc_info=True,
        )
        app.state.chat_engine = None  # Set to None on failure
        app.state.langfuse_instrumentor = None

    logging.info("Application startup: Loading suggested questions...")
    app.state.suggested_questions = []
    try:
        in_production = os.environ.get("PLASH_PRODUCTION") == "1"
        questions_file_path = Path(
            SUGGESTED_QUESTIONS_FILE_PROD
            if in_production
            else SUGGESTED_QUESTIONS_FILE_LOCAL
        )
        if questions_file_path.exists():
            with open(questions_file_path, "r") as f:
                app.state.suggested_questions = json.load(f)
            logging.info(
                f"Successfully loaded {len(app.state.suggested_questions)} questions."
            )
        else:
            logging.warning(
                f"Suggested questions file not found: {questions_file_path}"
            )
    except Exception as e:
        logging.error(f"Error loading suggested questions: {e}", exc_info=True)

    yield

    # Application shutdown: Clean up Langfuse instrumentor
    if hasattr(app.state, "langfuse_instrumentor") and app.state.langfuse_instrumentor:
        try:
            logging.info("Flushing Langfuse events on shutdown...")
            app.state.langfuse_instrumentor.flush()
        except Exception as e:
            logging.error(f"Error flushing Langfuse events: {e}")

    logging.info("Application shutdown.")


# --- Initialize FastHTML app ---
app, rt = fast_app(
    hdrs=(
        favicon_link,
        Link(rel="stylesheet", href="/assets/css/main.css"),
        Script(src="/assets/js/ui.js"),
        Script(src="/assets/js/form.js"),
        Script(src="/assets/js/streaming.js"),
    ),
    lifespan=lifespan,
)

# Mount static files directory after app is created
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


def simple_message_html(content, role):
    """Generate HTML string for a message without avatars"""
    is_user = role == "user"

    # Message processing
    if not is_user:
        # Process markdown for assistant messages
        cleaned_content = content  # Initialize cleaned_content first
        cleaned_content = re.sub(r"```\s*\n\s*```", "", cleaned_content)
        cleaned_content = re.sub(r"```[a-z]*\s*\n\s*```", "", cleaned_content)
        try:
            from mistletoe import Document, HTMLRenderer

            doc = Document(cleaned_content)
            renderer = HTMLRenderer()
            content_html = renderer.render(doc)
            content_html = re.sub(
                r"<pre>\s*<code>\s*</code>\s*</pre>", "", content_html
            )
        except Exception as e:
            logging.warning(f"Markdown failed: {e}.", exc_info=False)
            content_html = f"<p>{content}</p>"
    else:
        content_html = f"<p>{content}</p>"

    # Determine container alignment
    container_margin = "margin-left: auto;" if not is_user else ""
    # Optional extra style
    bubble_extra_style = ""

    # Return the formatted message HTML
    return f"""
    <div style="display: flex; gap: 1rem; padding: 1rem; margin-bottom: 1rem; max-width: 85%; {container_margin}">
        <div style="background-color: {"#f1f3f4" if not is_user else "white"}; padding: 12px 16px; border-radius: 18px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); flex-grow: 1;{bubble_extra_style}">
            <div style="color: #202124; font-size: 15px; width: 100%; overflow-wrap: break-word;">
                {content_html}
            </div>
        </div>
    </div>
    """


# --- chat_interface function ---
async def chat_interface(request: Request):
    """Create the main chat interface components with internal scrolling."""
    # Access chat engine safely from request state
    chat_engine = getattr(request.app.state, "chat_engine", None)
    suggested_questions = getattr(request.app.state, "suggested_questions", [])

    # --- Check if chat engine loaded ---
    if chat_engine is None:
        logging.error("Chat engine is None when rendering chat_interface.")
        return Div(
            H1("Error", style="color: red;"),
            P(
                "The Chat Engine failed to initialize or is not available. Please check server logs."
            ),
            style="max-width: 800px; margin: 40px auto; padding: 20px; background-color: #fff; border: 1px solid red; border-radius: 8px;",
        )

    # --- Build Suggested Questions ---
    suggestion_buttons = []
    if suggested_questions:
        for i, q in enumerate(suggested_questions):
            safe_q = q.replace("'", "\\'")
            mobile_hide_class = " suggestion-hide-mobile" if i >= 2 else ""
            suggestion_buttons.append(
                Button(
                    q,
                    onclick=f"setQuery('{safe_q}')",
                    cls=f"suggestion-btn{mobile_hide_class}",
                )
            )
    else:
        suggestion_buttons.append(
            P("No suggestions available.", style="font-style: italic; color: #666;")
        )

    # Create toggle button for mobile
    toggle_button = Button(
        "Show Suggestions ▼",
        cls="suggestions-toggle",
        onclick="toggleSuggestions()",
    )

    # --- Suggestions Div ---
    suggestions_div = Div(
        toggle_button,
        Div(  # Container for the actual buttons
            *suggestion_buttons,
            id="suggestions-buttons",
        ),
        id="suggestions-container",
        cls="suggestions-collapsed",
        style="padding: 0 1rem; text-align: center; margin-bottom: 15px; flex-shrink: 0;",
    )

    # --- Internal Title Block ---
    title_block = Div(
        P(
            "Ask technical questions about Matrix laser products",
            cls="page-title",
        ),
        cls="title-block",
    )

    # --- Main Chat Container ---
    return Div(
        # --- Top Fixed Section ---
        title_block,
        suggestions_div,
        # --- Middle Scrolling Section ---
        Div(  # Chat messages area
            Safe(
                simple_message_html(
                    "Welcome! How can I assist you with Matrix lasers today?",
                    "assistant",
                )
            ),
            id="chat-messages",
            style="flex: 1 1 auto; overflow-y: auto; padding: 0 15px; margin-bottom: 8px; border-radius: 8px;",
        ),
        # --- Bottom Fixed Section ---
        Div(  # Form and controls area
            Form(
                Div(  # Input Row
                    TextArea(
                        placeholder="Ask a question about Matrix lasers...",
                        id="user-input",
                        name="query",
                        rows=1,
                        autofocus=True,
                        cls="auto-grow-textarea",
                        style="width: 100%; box-sizing: border-box; padding: 14px 110px 14px 16px; font-size: 16px; color: #202124; border: 1px solid #dfe1e5; border-radius: 24px; resize: none; outline: none; box-shadow: none; margin: 0; overflow-y: hidden;",
                    ),
                    # --- Run/Stop Button ---
                    Button(
                        Span(
                            Span(Span(cls="spinner-square"), cls="inline-spinner"),
                            Span("Run", cls="button-text run-text"),
                            Span("Stop", cls="button-text stop-text"),
                            Span(" ⌘⏎", cls="button-icon cmd-icon"),
                            cls="button-inner-content",
                        ),
                        type="submit",
                        id="run-stop-button",
                        cls="run-button-base",
                        style="position: absolute; right: 6px; bottom: 8px; transform: none; overflow: hidden;",
                        title="Submit query (⌘+⏎ or Ctrl+Enter)",
                    ),
                    style="position: relative; display: block; margin-bottom: 10px; min-height: 52px;",
                ),  # End Input Row Div
                # Use JavaScript-based streaming instead of HTMX
                id="chat-form",
            ),  # End Form
            Div(  # Reset button container
                Button(
                    "Reset Chat",
                    hx_post="/reset-chat",
                    hx_target="#chat-container",
                    hx_swap="innerHTML",
                    hx_confirm="Are you sure?",
                    style="background-color: #f1f3f4; color: #5f6368; border: none; padding: 8px 20px; border-radius: 20px; cursor: pointer; font-weight: 500; height: 36px; line-height: 20px;",
                ),
                style="text-align: center; margin-bottom: 10px;",
            ),  # End Reset Div
            style="flex-shrink: 0; padding-top: 6px; border-top: 1px solid #f0f0f0;",
        ),  # End Form/Controls Area Div
        # --- Style for the main chat container itself ---
        style=(
            "max-width: 900px; margin: 0 auto 20px auto;"
            " padding: 20px; background-color: white; border-radius: 12px;"
            " box-shadow: 0 2px 8px rgba(0,0,0,0.05);"
            " display: flex; flex-direction: column;"
            " flex: 1 1 auto;"
            " overflow: hidden;"
        ),
        id="chat-container",
    )


# Route to serve images
@rt("/images/{filename:path}")
async def get_image(filename: str):
    if ".." in filename or filename.startswith("/"):
        return Response("Invalid filename", status_code=400)
    file_path = images_dir / filename
    if file_path.is_file():
        return FileResponse(file_path)
    else:
        logging.warning(f"Image not found: {file_path}")
        return Response("Image not found", status_code=404)


@rt("/")
async def get(request: Request):
    return Titled(
        "Matrix Laser Technical Support",  # Browser tab title
        Div(
            # --- 1. Fixed Header Section ---
            Div(
                Img(
                    src="/images/Coherent_logo_blue.png",
                    alt="Coherent Logo",
                    cls="header-logo",
                ),
                cls="logo-container",
            ),
            # --- 2. Chat Interface Section ---
            await chat_interface(request=request),
            # Style for the main page container
            style="display: flex; flex-direction: column; height: 100dvh; background-color: #f8f9fa; overflow: hidden;",
        ),
    )


# Streaming endpoint
@rt("/stream-message")
async def stream_message(request: Request):
    """Stream a response to a query"""
    query = request.query_params.get("query", "").strip()
    if not query:
        return Response("Query is required", status_code=400)

    chat_engine = getattr(request.app.state, "chat_engine", None)

    if chat_engine is None:
        return Response("Chat engine not available", status_code=503)

    # Process chunks from markdown to HTML on the fly
    async def process_stream():
        try:
            # Process stream without complex instrumentation
            async for text_chunk in generate_streaming_response(query, chat_engine):
                # Convert markdown chunk to HTML
                try:
                    # Assuming text_chunk is a dict like {'type': 'content', 'content': '...'}
                    # or similar structure yielded by generate_streaming_response
                    if isinstance(text_chunk, dict):
                        chunk_type = text_chunk.get("type")
                        content = text_chunk.get("content", "")
                        if chunk_type == "content":
                            # Yield raw content directly as plain text
                            yield content
                        elif chunk_type == "sources":
                            # Handle sources if needed, maybe format them at the end
                            pass  # Or yield formatted source info
                        elif chunk_type == "error":
                            # Yield error message as plain text
                            yield f"Error: {content}"
                    else:
                        # Fallback for plain text chunks (if any)
                        yield str(text_chunk)

                except Exception as chunk_error:
                    logging.error(
                        f"Error processing stream chunk: {chunk_error}", exc_info=True
                    )
                    # Yield error message to the client
                    yield "Error processing part of the response."

            # Yield a minimal delay to avoid overwhelming the browser
            await asyncio.sleep(0.01)

            # Send a final [DONE] signal
            yield "[DONE]"

        except Exception as e:
            logging.error(f"Error streaming response: {e}", exc_info=True)
            # Return error message to the client
            yield f"Error processing your request: {str(e)}"
            # Also send [DONE] after an error
            yield "[DONE]"

    # Return streaming response
    return StreamingResponse(
        process_stream(),
        media_type="text/plain",
    )


# Reset chat route - now async
@rt("/reset-chat", methods=["POST"])
async def reset_chat(request: Request):
    chat_engine = getattr(request.app.state, "chat_engine", None)

    if chat_engine:
        try:
            logging.info("Resetting chat engine memory...")

            # Reset chat engine memory
            if hasattr(chat_engine, "areset"):
                await chat_engine.areset()  # Use async reset if available
            else:
                chat_engine.reset()  # Fallback to sync reset

            # Create a new session ID for future interactions
            request.app.state.session_id = f"session-{uuid4()}"

            logging.info("Chat engine memory reset.")
        except Exception as e:
            logging.error(f"Error resetting chat engine: {e}", exc_info=True)

            # No trace error

    else:
        logging.warning("Reset attempted, but chat engine not available.")

    # Return fresh interface after reset
    return await chat_interface(request=request)


# Start the server
if __name__ == "__main__":
    in_production = os.environ.get("PLASH_PRODUCTION") == "1"
    reload_status = not in_production

    print("\n--- Starting Server ---")
    print(f"Production Mode: {in_production}")
    print(f"Uvicorn Reload: {reload_status}")

    if in_production:
        # Production mode (Plash server)
        print("Running in Plash mode: calling serve()")
        serve()
    else:
        # Local development mode
        port = 5002
        host = "127.0.0.1"
        print(f"Running in Local mode: http://{host}:{port}")
        serve(host=host, port=port, reload=reload_status)

# --- Server Start ---
