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
import asyncio  # Add back for async streaming
from uuid import uuid4
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List, AsyncGenerator

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
APP_VERSION = "1.0.1"  # Incremented version for theme feature


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
            logging.info("Shutting down Langfuse instrumentor on exit...")
            # Use shutdown instead of flush for cleaner exit
            app.state.langfuse_instrumentor.shutdown(timeout=5)
            logging.info("Langfuse instrumentor shut down.")
        except Exception as e:
            logging.error(f"Error shutting down Langfuse instrumentor: {e}")

    logging.info("Application shutdown.")


# --- Initialize FastHTML app ---
app, rt = fast_app(
    hdrs=(
        favicon_link,
        Link(rel="stylesheet", href="/assets/css/main.css"),
        Script(src="/assets/js/ui.js"),
        Script(src="/assets/js/form.js"),
        Script(src="/assets/js/streaming.js"),
        Script(src="/assets/js/theme-switcher.js"),
    ),
    lifespan=lifespan,
)

# Mount static files directory after app is created
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


def simple_message_html(content, role):
    """Generate HTML string for a message using CSS classes."""
    is_user = role == "user"
    role_class = "user" if is_user else "assistant"
    
    # Identify if this is the welcome message
    is_welcome = role == "assistant" and "Welcome! How can I assist" in str(content)

    # Process markdown for assistant messages
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
            import html
            content_html = f"<p>{html.escape(content)}</p>"
    else:
        # User message: Escape HTML and wrap in <p>
        import html
        content_html = f"<p>{html.escape(content)}</p>"

    # Return None or empty string if no content to display
    if not content_html:
        return ""

    # Use CSS classes instead of inline styles
    if role_class == "assistant":
        # Add the special class for welcome message
        container_extra_class = " welcome-message-container" if is_welcome else ""
        # Add the atom icon for assistant messages
        return f"""
        <div class="message-container {role_class}{container_extra_class}">
            <div class="atom-icon">
                <img src="/images/coherent_atom_symbol.png" alt="Coherent" width="24" height="24">
            </div>
            <div class="message-bubble">
                <div class="message-content">
                    {content_html}
                </div>
            </div>
        </div>
        """
    else:
        # User message without icon
        return f"""
        <div class="message-container {role_class}">
            <div class="message-bubble">
                <div class="message-content">
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
                        title="Submit query (⌘+⏎ or Ctrl+Enter)",
                    ),
                    cls="input-row",
                ),  # End Input Row Div
                # Use JavaScript-based streaming instead of HTMX
                id="chat-form",
            ),  # End Form
            Div(  # Reset button container
                Button(
                    "Reset Chat",
                    id="reset-chat-button", # Use ID instead of HTMX attributes
                    # HTMX attributes removed - will use manual JavaScript handling
                    cls="reset-button",
                ),
                cls="reset-button-container",
            ),  # End Reset Div
            id="chat-form-area",
        ),  # End Form/Controls Area Div
        # Use ID instead of inline styles for the main chat container
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
    # --- Header Controls Component ---
    header_controls = Div(
        # Theme toggle button
        Button(
            "🌓",  # Moon/sun emoji as a simple toggle icon
            id="theme-toggle", 
            cls="theme-toggle icon-button", 
            title="Toggle Light/Dark Theme"
        ),
        # Menu toggle button (hamburger)
        Button(
            Span(cls="hamburger-bar"),
            Span(cls="hamburger-bar"),
            Span(cls="hamburger-bar"),
            id="menu-toggle",
            cls="menu-toggle icon-button",
            title="Open Menu"
        ),
        # The Dropdown Menu (hidden by default)
        Nav(
            Ul(
                Li(A("System Theme", href="#", cls="theme-menu-item", data_theme_value="system")),
                Li(A("Light Theme", href="#", cls="theme-menu-item", data_theme_value="light")),
                Li(A("Dark Theme", href="#", cls="theme-menu-item", data_theme_value="dark")),
                # Future menu items can be added here
            ),
            id="settings-menu",
            cls="settings-menu hidden" # Start hidden
        ),
        cls="header-controls" # Class for the right-side group
    )

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
                header_controls,  # Add the header controls here
                cls="logo-container",
            ),
            # --- 2. Chat Interface Section ---
            await chat_interface(request=request),
            # Theme toggle now moved to header_controls
            id="main-content-area",
            # Use CSS variables for styling
            style="display: flex; flex-direction: column; height: 100dvh; background-color: var(--bg-color); overflow: hidden;",
        ),
    )


# Streaming endpoint
@rt("/stream-message")
async def stream_message(request: Request):
    """Stream a response to a query using token-by-token streaming"""
    # ---> START DEBUG LOGGING <---
    request_id = str(uuid4())  # Unique ID for this specific request
    logging.info(f"[{request_id}] ===> Received request for /stream-message (Streaming Mode)")
    logging.info(f"[{request_id}] Headers: {dict(request.headers)}")
    logging.info(f"[{request_id}] Query Params: {dict(request.query_params)}")

    query = request.query_params.get("query", "").strip()
    logging.info(f"[{request_id}] Extracted Query: '{query}' (Length: {len(query)})")

    # Check app state immediately
    chat_engine = getattr(request.app.state, "chat_engine", None)
    instrumentor = getattr(request.app.state, "langfuse_instrumentor", None)
    session_id = getattr(request.app.state, "session_id", "UNKNOWN")

    logging.info(f"[{request_id}] App State Check:")
    logging.info(f"[{request_id}]   Chat Engine Instance: {id(chat_engine) if chat_engine else 'None'}")
    logging.info(f"[{request_id}]   Instrumentor Instance: {id(instrumentor) if instrumentor else 'None'}")
    logging.info(f"[{request_id}]   Current Session ID: {session_id}")
    # ---> END DEBUG LOGGING <---
    
    if not query:
        logging.warning(f"[{request_id}] Query is empty, returning error stream.")
        async def error_stream_no_query():
            yield json.dumps({"type": "error", "content": "Query is required."}) + "\n"
            yield json.dumps({"type": "done", "content": ""}) + "\n"
        return StreamingResponse(error_stream_no_query(), media_type="application/x-ndjson", status_code=400)

    if chat_engine is None:
        logging.error(f"[{request_id}] Chat engine not available in app state, returning error stream.")
        async def error_stream_no_engine():
            yield json.dumps({"type": "error", "content": "Chat engine not available."}) + "\n"
            yield json.dumps({"type": "done", "content": ""}) + "\n"
        return StreamingResponse(error_stream_no_engine(), media_type="application/x-ndjson", status_code=503)

    # Define the event stream generator that calls the async streaming function
    async def event_stream_generator() -> AsyncGenerator[str, None]:
        try:
            logging.info(f"[{request_id}] Calling generate_streaming_response...")
            async for chunk_dict in generate_streaming_response(
                query=query,
                chat_engine=chat_engine,
                instrumentor=instrumentor  # Pass instrumentor from app state
            ):
                yield json.dumps(chunk_dict) + "\n"  # Format as NDJSON line
                await asyncio.sleep(0.005)  # Yield control briefly
            logging.info(f"[{request_id}] Finished streaming response from generator.")
        except Exception as e:
            logging.error(f"[{request_id}] Error generating streaming event stream: {e}", exc_info=True)
            try:
                # Try to yield a final error message if the stream breaks
                error_payload = {"type": "error", "content": f"Stream generation error: {e}"}
                yield json.dumps(error_payload) + "\n"
                done_payload = {"type": "done", "content": ""}
                yield json.dumps(done_payload) + "\n"
            except Exception as final_err:
                logging.error(f"[{request_id}] Failed to yield final error message to stream: {final_err}")

    # Return the StreamingResponse with proper headers
    logging.info(f"[{request_id}] Returning StreamingResponse with media_type application/x-ndjson.")
    headers = {
        "Content-Type": "application/x-ndjson",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive", # Useful for some proxy/server setups
        "X-Accel-Buffering": "no", # Often needed for Nginx to disable buffering
    }
    return StreamingResponse(event_stream_generator(), media_type="application/x-ndjson", headers=headers)


# Reset chat route - now async with more thorough state cleanup
@rt("/reset-chat", methods=["POST"])
async def reset_chat(request: Request):
    # ---> START DEBUG LOGGING <---
    reset_id = str(uuid4())  # Unique ID for this specific reset operation
    logging.info(f"[{reset_id}] ===> Received request for /reset-chat")
    logging.info(f"[{reset_id}] Headers: {dict(request.headers)}")
    
    # Log initial app state
    chat_engine = getattr(request.app.state, "chat_engine", None)
    instrumentor = getattr(request.app.state, "langfuse_instrumentor", None)
    previous_session_id = getattr(request.app.state, "session_id", "UNKNOWN")
    
    logging.info(f"[{reset_id}] Initial App State Before Reset:")
    logging.info(f"[{reset_id}]   Chat Engine Instance: {id(chat_engine) if chat_engine else 'None'}")
    logging.info(f"[{reset_id}]   Instrumentor Instance: {id(instrumentor) if instrumentor else 'None'}")
    logging.info(f"[{reset_id}]   Current Session ID: {previous_session_id}")
    # ---> END DEBUG LOGGING <---

    engine_reset = False
    trace_reset = False

    # 1. Reset Chat Engine Memory
    if chat_engine:
        try:
            logging.info(f"[{reset_id}] Resetting chat engine memory...")
            
            # Log the type of reset we're doing (async or sync)
            if hasattr(chat_engine, "areset"):
                logging.info(f"[{reset_id}] Using async reset (areset)")
                await chat_engine.areset()
            else:
                logging.info(f"[{reset_id}] Using sync reset (reset)")
                chat_engine.reset()
                
            logging.info(f"[{reset_id}] Chat engine memory reset successfully.")
            engine_reset = True
        except Exception as e:
            logging.error(f"[{reset_id}] Error resetting chat engine: {e}", exc_info=True)
    else:
        logging.warning(f"[{reset_id}] Reset attempted, but chat engine not available.")

    # 2. Flush Langfuse Context (SIMPLIFIED)
    #    Just ensure any data from the *previous* session is sent.
    #    DO NOT try to manually clear internal state like _current_trace.
    if instrumentor:
        try:
            logging.info(f"[{reset_id}] Flushing Langfuse instrumentor during reset...")
            if hasattr(instrumentor, "flush"):
                instrumentor.flush()
                logging.info(f"[{reset_id}] Langfuse flush during reset completed.")
                trace_reset = True
            else:
                logging.warning(f"[{reset_id}] Instrumentor has no flush method!")
        except Exception as e:
            logging.error(f"[{reset_id}] Error flushing Langfuse instrumentor during reset: {e}", exc_info=True)
    else:
        logging.warning(f"[{reset_id}] Reset attempted, but Langfuse instrumentor not available.")

    # Update session ID regardless to get a fresh trace context for future operations
    new_session_id = f"session-{uuid4()}"
    request.app.state.session_id = new_session_id
    logging.info(f"[{reset_id}] Session ID changed from {previous_session_id} to {new_session_id}")
    
    # Reset any pending state flags
    if hasattr(request.app.state, "processing_query"):
        old_value = request.app.state.processing_query
        request.app.state.processing_query = False
        logging.info(f"[{reset_id}] Reset processing_query flag from {old_value} to False")
    else:
        logging.info(f"[{reset_id}] No processing_query flag found in app state")
        
    # Log final app state after reset
    logging.info(f"[{reset_id}] Final App State After Reset:")
    logging.info(f"[{reset_id}]   Chat Engine Instance: {id(chat_engine) if chat_engine else 'None'}")
    logging.info(f"[{reset_id}]   Instrumentor Instance: {id(instrumentor) if instrumentor else 'None'}")
    logging.info(f"[{reset_id}]   New Session ID: {new_session_id}")

    # Base success primarily on the engine reset status

    logging.info(f"[{reset_id}] Reset completed - Engine Reset: {engine_reset}, Trace Reset: {trace_reset}, New Session: {new_session_id}")

    # Redirect to force clean page load
    # Use 303 See Other with HX-Refresh to ensure HTMX triggers a full page reload
    from starlette.responses import RedirectResponse
    
    # Create headers with HX-Refresh to instruct HTMX to refresh the page
    headers = {"HX-Refresh": "true"}
    
    logging.info(f"[{reset_id}] Sending 303 Redirect with HX-Refresh header to force HTMX to reload the page")
    return RedirectResponse(url="/", status_code=303, headers=headers)


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
