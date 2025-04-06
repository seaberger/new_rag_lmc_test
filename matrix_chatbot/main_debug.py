# --- START OF FILE main.py (Simplified for Debugging) ---

# --- Use Wildcard Imports ---
from fasthtml.common import *
from monsterui.all import *  # Keep this for now to match working repo

# --- Other necessary imports ---
import os
import re

# import json # Not needed for this simplified version
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from chat_engine import init_chat_engine

try:
    from mistletoe import Document, HTMLRenderer
except ImportError:
    Document = None
    HTMLRenderer = None
    logging.warning("Mistletoe not found.")

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Constants for suggested questions - REMOVED for now ---
# SUGGESTED_QUESTIONS_FILE_LOCAL = ...
# SUGGESTED_QUESTIONS_FILE_PROD = ...


# --- Lifespan context manager (Keep for engine init) ---
@asynccontextmanager
async def lifespan(app: FastHTML):
    logging.info("Application startup: Initializing chat engine...")
    try:
        app.state.chat_engine = init_chat_engine()
        logging.info("... Chat engine initialized.")
    except Exception as e:
        logging.error(f"... FATAL error initializing chat engine: {e}", exc_info=True)
        app.state.chat_engine = None
    # --- REMOVED suggested questions loading ---
    # logging.info("Application startup: Loading suggested questions...")
    # app.state.suggested_questions = []
    # try: ...
    # except Exception as e: ...
    yield
    logging.info("Application shutdown.")


# --- REMOVED Helper JS scripts for now ---
# set_query_script = Script(...)
# auto_scroll_script = Script(...)


# simple_message_html (remains the same)
def simple_message_html(content, role):
    # ... (same implementation as before) ...
    is_user = role == "user"
    content_html = ""
    if not is_user:
        cleaned_content = re.sub(r"```\s*\n\s*```", "", content)
        cleaned_content = re.sub(r"```[a-z]*\s*\n\s*```", "", cleaned_content)
        try:
            if not Document or not HTMLRenderer:
                raise ImportError("Mistletoe missing")
            doc = Document(cleaned_content)
            renderer = HTMLRenderer()
            content_html = renderer.render(doc)
            content_html = re.sub(
                r"<pre>\s*<code>\s*</code>\s*</pre>", "", content_html
            )
        except Exception as e:
            logging.warning(f"Markdown failed ({e}).", exc_info=False)
            content_html = markdown(cleaned_content)
    else:
        content_html = f"<p>{content}</p>"
    enhanced_content = f"""<div style="flex: 1; color: #000000; font-family: system-ui, sans-serif;"><div style="color: #000000;">{content_html}</div></div>"""
    return f"""<div style="display: flex; gap: 1rem; padding: 1rem; background-color: {"#f0f0f0" if not is_user else "white"}; border-radius: 0.5rem; margin-bottom: 1rem; border: 1px solid #d0d0d0;"><div style="width: 2rem; height: 2rem; background-color: #d0d0d0; border-radius: 9999px; display: flex; align-items: center; justify-content: center;">{"👤" if is_user else "🤖"}</div>{enhanced_content}</div>"""


# Custom CSS (remains the same)
custom_css = Style(""" body { ... } /* Keep existing styles */ """)

# Initialize FastHTML app - Use lifespan
app, rt = fast_app(
    # --- REMOVED helper scripts from headers ---
    hdrs=(Title("Matrix Laser Technical Support"), Theme.blue.headers(), custom_css),
    lifespan=lifespan,
)


# --- SIMPLIFIED chat_interface ---
def chat_interface(request: Request):
    chat_engine = (
        request.app.state.chat_engine
        if hasattr(request.app.state, "chat_engine")
        else None
    )

    # --- Add Debug Prints ---
    print(f"--- [DEBUG] Inside chat_interface ---")
    print(f"--- [DEBUG] Type of P object: {type(P)} ---")  # Check P
    print(f"--- [DEBUG] Value of P object: {P} ---")
    print(f"--- [DEBUG] Type of Div object: {type(Div)} ---")  # Check Div
    print(f"--- [DEBUG] Type of H1 object: {type(H1)} ---")  # Check H1
    print(
        f"--- [DEBUG] Type of TextArea object: {type(TextArea)} ---"
    )  # Check TextArea
    # --- End Debug Prints ---

    if chat_engine is None:
        print("--- [DEBUG] chat_engine is None ---")
        return Div(H1("Error"), P("Chat Engine failed..."))  # Use P, Div, H1

    # --- Return a simplified structure - NO suggestions/reset ---
    print(f"--- [DEBUG] Building simplified interface ---")
    try:
        # Use component names as found by wildcard (P, Div, H1, TextArea)
        interface = Div(
            Div(  # Header
                H1("Matrix Laser Technical Support (Debug)"),
                P("Ask questions about Matrix laser products"),
                style="border-bottom: 2px solid #000; padding-bottom: 1rem; margin-bottom: 1rem;",
            ),
            Div(  # Chat messages container
                Safe(simple_message_html("Welcome (Debug Mode)", "assistant")),
                id="chat-messages",
                style="max-height: 60vh; overflow-y: auto;",
            ),
            Form(  # Input form
                Div(
                    TextArea(
                        placeholder="Ask...",
                        id="user-input",
                        name="query",
                        rows=2,
                        style="...",
                    ),
                    Button(
                        "Send",
                        type="submit",
                        style="...",
                    ),
                    style="position: relative; margin-top: 1rem;",
                ),
                hx_post="/send-message",
                hx_target="#chat-messages",
                hx_swap="beforeend",
                hx_indicator="#spinner",
                style="margin-top: 1rem; border-top: 2px solid #000; padding-top: 1rem;",
            ),
            Loading(cls=(LoadingT.spinner, ...), htmx_indicator=True, id="spinner"),
            id="chat-container",
            style="max-width: 800px; margin: 20px auto; ...",
        )
        print(f"--- [DEBUG] Simplified interface built successfully ---")
        return interface
    except Exception as e:
        print(f"--- [DEBUG] ERROR building simplified interface: {e} ---")
        import traceback

        traceback.print_exc()
        # Return very basic error
        return P(f"Error building interface: {e}")


# --- Route Handlers (Keep request argument) ---
@rt("/")
def get(request: Request):
    print(f"--- [DEBUG] Handling GET / ---")
    # Use Titled
    return Titled("Matrix Debug", chat_interface(request=request))


# --- Inside main.py ---


@rt("/send-message", methods=["POST"])
def send_message(request: Request, query: str):
    chat_engine = (
        request.app.state.chat_engine
        if hasattr(request.app.state, "chat_engine")
        else None
    )
    if chat_engine is None:
        return Safe(simple_message_html("Engine unavailable.", "assistant"))

    query = query.strip()
    if not query:
        return ""

    user_message_html = simple_message_html(query, "user")  # Use Safe implicitly

    try:
        response = chat_engine.chat(query)
        assistant_message_html = simple_message_html(response.response, "assistant")

        # --- FIX THIS CALL ---
        # Ensure ALL arguments have keywords
        clear_input = TextArea(
            id="user-input",  # keyword
            name="query",  # keyword
            rows=2,  # keyword
            autofocus=True,  # keyword
            placeholder="Ask...",  # keyword (make sure placeholder= is present)
            # Make sure style= is present
            style="width: 100%; padding: 0.75rem; border: 2px solid #000000; border-radius: 0.375rem; min-height: 80px; color: #000000; font-family: system-ui, sans-serif; font-weight: 500;",
            hx_swap_oob="true",  # keyword
        )
        # --- END FIX ---

        return Safe(user_message_html), Safe(assistant_message_html), clear_input

    except Exception as e:
        logging.error(
            f"Error processing chat query: {e}", exc_info=True
        )  # Added logging
        error_message = simple_message_html(
            f"Sorry, an error occurred: {str(e)}", "assistant"
        )
        return Safe(user_message_html), Safe(error_message)


# --- REMOVE Reset route for now ---
# @rt("/reset-chat", methods=["POST"])
# def reset_chat(request: Request): ...


# --- Server Start (Keep reload logic) ---
if __name__ == "__main__":
    in_production = os.environ.get("PLASH_PRODUCTION") == "1"
    reload_status = not in_production
    print("\n--- Starting Server ---")
    print(f"Production Mode: {in_production}")
    print(f"Uvicorn Reload: {reload_status}")
    serve(reload=reload_status)

# --- END OF FILE main.py ---
