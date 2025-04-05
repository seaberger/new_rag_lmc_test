# --- START OF FILE main.py ---

from fasthtml.common import *

from monsterui.all import *
import os
import re
import json  # Import the json module
import logging
from pathlib import Path  # Import Path
from contextlib import asynccontextmanager
from fastapi.responses import FileResponse

# Create images directory if it doesn't exist
images_dir = Path("./images")
# images_dir.mkdir(exist_ok=True)

# Import chat engine functions
from chat_engine import init_chat_engine

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Constants ---
SUGGESTED_QUESTIONS_FILE_LOCAL = "./suggested_questions.json"
SUGGESTED_QUESTIONS_FILE_PROD = "/app/suggested_questions.json"


# --- Lifespan context manager for startup/shutdown ---
@asynccontextmanager
async def lifespan(app: FastHTML):
    # --- Chat Engine Initialization ---
    logging.info("Application startup: Initializing chat engine...")
    try:
        app.state.chat_engine = init_chat_engine()
        logging.info("Application startup: Chat engine initialized successfully.")
    except Exception as e:
        logging.error(
            f"Application startup: FATAL error initializing chat engine: {e}",
            exc_info=True,
        )
        app.state.chat_engine = None

    # --- Load Suggested Questions ---
    logging.info("Application startup: Loading suggested questions...")
    app.state.suggested_questions = []  # Default to empty list
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
                f"Application startup: Successfully loaded {len(app.state.suggested_questions)} suggested questions."
            )
        else:
            logging.warning(
                f"Application startup: Suggested questions file not found at {questions_file_path}. Using empty list."
            )

    except json.JSONDecodeError as e:
        logging.error(
            f"Application startup: Error decoding JSON from suggested questions file: {e}",
            exc_info=True,
        )
    except Exception as e:
        logging.error(
            f"Application startup: Error loading suggested questions: {e}",
            exc_info=True,
        )

    # App runs while in the 'yield'
    yield
    # Code to run on shutdown (optional)
    logging.info("Application shutdown.")


# Helper function to set input text via JS
# set_query_script = Script(""" function setQuery(text) { /* ... same ... */ } """)
set_query_script = Script("""
function setQuery(text) {
  // Get the input field
  const textarea = document.getElementById('user-input');
  if (textarea) {
    // Set the value
    textarea.value = text;
    // Focus the textarea
    textarea.focus();
    // Optional: Move cursor to end
    textarea.setSelectionRange(textarea.value.length, textarea.value.length);
  } else {
    console.error("Could not find textarea with id 'user-input'");
  }
}
""")
# Helper script for auto-scrolling chat messages
# auto_scroll_script = Script(
#     """ document.addEventListener('htmx:afterSwap', function(event) { /* ... same ... */ }); """
# )
auto_scroll_script = Script("""
document.addEventListener('htmx:afterSwap', function(event) {
    if (event.detail.target.id === 'chat-messages') {
        setTimeout(function() {
            const chatMessages = document.getElementById('chat-messages');
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            // Make sure the reset button stays consistently positioned
            const container = document.getElementById('chat-container');
            if (container) {
                container.scrollTop = 0; // Keep the container itself at the top
            }
        }, 100);
    }
});
""")


# def simple_message_html(content, role):
#     """Generate HTML string for a message with enhanced contrast"""
#     # --- Function remains the same ---
#     is_user = role == "user"
#     content_html = ""
#     if not is_user:
#         cleaned_content = re.sub(r"```\s*\n\s*```", "", content)
#         cleaned_content = re.sub(r"```[a-z]*\s*\n\s*```", "", cleaned_content)
#         try:
#             from mistletoe import Document, HTMLRenderer


#             doc = Document(cleaned_content)
#             renderer = HTMLRenderer()
#             content_html = renderer.render(doc)
#             content_html = re.sub(
#                 r"<pre>\s*<code>\s*</code>\s*</pre>", "", content_html
#             )
#         except Exception as e:
#             logging.warning(f"Markdown failed: {e}.", exc_info=False)
#             content_html = f"<p>{content}</p>"
#     else:
#         content_html = f"<p>{content}</p>"
#     enhanced_content = f"""<div style="flex: 1; color: #000000; font-family: system-ui, sans-serif;"><div style="color: #000000;">{content_html}</div></div>"""
#     return f"""<div style="display: flex; gap: 1rem; padding: 1rem; background-color: {"#f0f0f0" if not is_user else "white"}; border-radius: 0.5rem; margin-bottom: 1rem; border: 1px solid #d0d0d0;"><div style="width: 2rem; height: 2rem; background-color: #d0d0d0; border-radius: 9999px; display: flex; align-items: center; justify-content: center;">{"👤" if is_user else "🤖"}</div>{enhanced_content}</div>"""
def simple_message_html(content, role):
    """Generate HTML string for a message with enhanced contrast"""
    is_user = role == "user"
    avatar = "👤" if is_user else "🤖"

    # Message processing remains the same
    if not is_user:
        cleaned_content = re.sub(r"```\s*\n\s*```", "", content)
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

    return f"""
    <div style="display: flex; gap: 1rem; padding: 1rem; margin-bottom: 1rem; max-width: 85%; {"" if is_user else "margin-left: auto;"}">
        <div style="width: 32px; height: 32px; background-color: {("#4285f4" if not is_user else "#5f6368")}; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; flex-shrink: 0;">
            {avatar}
        </div>
        <div style="background-color: {"#f1f3f4" if not is_user else "white"}; padding: 12px 16px; border-radius: 18px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); flex-grow: 1;">
            <div style="color: #202124; font-size: 15px;">
                {content_html}
            </div>
        </div>
    </div>
    """


custom_css = Style("""
    body { 
        background-color: #f8f9fa; 
        font-family: 'Google Sans', 'Segoe UI', system-ui, -apple-system, sans-serif;
    }
    
    pre {
        background-color: #f1f3f4;
        padding: 1rem;
        border-radius: 0.5rem;
        overflow-x: auto;
        font-size: 0.9rem;
        margin: 1rem 0;
    }
    
    code {
        color: #202124;
        font-family: 'Roboto Mono', monospace;
        font-size: 0.9em;
    }
    
    p {
        line-height: 1.5;
        margin: 0.5em 0;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #202124;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }
    
    ul, ol {
        padding-left: 1.5rem;
        margin: 0.75rem 0;
    }
    
    li {
        margin-bottom: 0.5rem;
    }
    
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 1rem 0;
    }
    
    th, td {
        border: 1px solid #e0e0e0;
        padding: 0.5rem;
        text-align: left;
    }
    
    th {
        background-color: #f1f3f4;
    }
    
    a {
        color: #1a73e8;
        text-decoration: none;
    }
    
    a:hover {
        text-decoration: underline;
    }
    
    .suggestion-btn:hover {
        background-color: #e8f0fe;
    }
    
    @media (max-width: 640px) {
        pre {
            padding: 0.75rem;
            font-size: 0.8rem;
        }
    }
    @keyframes spinner-spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

#spinner {
    position: absolute;
    bottom: 0;
    left: 100%;
    margin-left: 10px;
    width: 30px;
    height: 30px;
    opacity: 0;
    transition: opacity 0.2s ease-in-out;
    z-index: 100;
    box-sizing: border-box; /* Good practice */

    /* Spinner Appearance */
    border: 4px solid rgba(0, 0, 0, 0.1); /* Light grey track */
    border-left-color: #1a73e8; /* Blue segment */
    border-radius: 50%;
    /* No need for background/color overrides for a plain Div */
}

#spinner.htmx-request {
    opacity: 1;
    animation: spinner-spin 1s linear infinite;
}

""")

# Initialize FastHTML app - PASS LIFESPAN MANAGER
app, rt = fast_app(
    hdrs=(
        # Titled("Matrix Laser Support"),
        Theme.blue.headers(),
        custom_css,
        set_query_script,
        auto_scroll_script,
    ),
    lifespan=lifespan,
)


def chat_interface(request: Request):
    """Create the main chat interface components."""
    chat_engine = (
        request.app.state.chat_engine
        if hasattr(request.app.state, "chat_engine")
        else None
    )
    # --- Get questions from app state ---
    suggested_questions = (
        request.app.state.suggested_questions
        if hasattr(request.app.state, "suggested_questions")
        else []
    )

    if chat_engine is None:
        return Div(
            H1("Error", style="color: red;"),
            P("The Chat Engine failed to initialize. Please check the server logs."),
            style="max-width: 800px; margin: 40px auto; padding: 20px; background-color: #fff; border: 1px solid red; border-radius: 8px;",
        )

    # --- Build Suggested Questions all at once ---
    suggestion_buttons = []
    if suggested_questions:
        for q in suggested_questions:
            safe_q = q.replace("'", "\\'")
            suggestion_buttons.append(
                Button(
                    q,
                    onclick=f"document.getElementById('user-input').value = '{safe_q}'; document.getElementById('user-input').focus();",
                    style="color: #1a73e8; background-color: #f1f3f4; margin: 0.4rem; padding: 0.6rem 1rem; border: none; border-radius: 24px; cursor: pointer; font-size: 0.9rem; display: inline-block; font-weight: 500; box-shadow: 0 1px 2px rgba(0,0,0,0.1); transition: background-color 0.2s;",
                )
            )
    else:
        suggestion_buttons.append(
            P("No suggestions available.", style="font-style: italic; color: #666;")
        )

    # Create div with all buttons at once
    suggestions_div = Div(
        *suggestion_buttons,
        style="padding: 1rem; text-align: center; margin: 20px 0 30px 0;",
    )

    return Div(
        Div(
            # H1(
            #     "Matrix Laser Technical Support",
            #     style="font-size: 2rem; font-weight: 500; color: #202124;",
            # ),
            P(
                "Ask technical questions about Matrix laser products",
                style="font-size: 1.3rem; color: #5f6368; margin-top: 0.5rem; font-weight: bold; font-style: italic;",
            ),
            style="text-align: center; margin-bottom: 40px; padding-bottom: 1rem;",
        ),
        Div(
            Safe(
                simple_message_html(
                    "Welcome! How can I assist you with Matrix lasers today?",
                    "assistant",
                )
            ),
            suggestions_div,  # Insert the dynamically created div
            id="chat-messages",
            style="max-height: 60vh; overflow-y: auto; padding-right: 10px; margin-bottom: 30px;",
        ),
        Div(
            # Form must contain both the input and submit button
            Form(
                Div(
                    TextArea(
                        placeholder="Ask a question about Matrix lasers...",
                        id="user-input",
                        name="query",
                        rows=1,
                        autofocus=True,
                        style="width: 100%; box-sizing: border-box; padding: 14px 80px 14px 16px; font-size: 16px; color: #202124; border: 1px solid #dfe1e5; border-radius: 24px; resize: none; outline: none; box-shadow: none; height: 52px; margin: 0;",
                    ),
                    Button(
                        "Send",
                        type="submit",
                        style="position: absolute; right: 6px; top: 50%; transform: translateY(-50%); background-color: #f1f3f4; border: none; padding: 8px 16px; border-radius: 18px; cursor: pointer; color: #5f6368; font-weight: 500; height: 36px; line-height: 20px;",
                    ),
                    style="position: relative; display: block; margin-bottom: 24px; min-height: 52px;",
                ),
                hx_post="/send-message",
                hx_target="#chat-messages",
                hx_swap="beforeend",
                hx_indicator="#spinner",
                hx_disabled_elt='button[type="submit"]',
                id="chat-form",
            ),
            # Reset button (outside the form)
            Div(
                Button(
                    "Reset Chat",
                    hx_post="/reset-chat",
                    hx_target="#chat-container",
                    hx_swap="innerHTML",
                    hx_confirm="Are you sure you want to reset the chat history?",
                    style="background-color: #f1f3f4; color: #5f6368; border: none; padding: 8px 20px; border-radius: 20px; cursor: pointer; font-weight: 500; height: 36px; line-height: 20px;",
                ),
                style="text-align: center; margin-bottom: 24px;",
            ),
            style="margin-top: 1rem; position: sticky; bottom: 0; background-color: white; padding-top: 12px; border-top: 1px solid #f0f0f0;",
        ),
        Div(id="spinner"),
        id="chat-container",
        # CAREFULLY REPLACE THE ENTIRE STYLE STRING with this:
        style="max-width: 900px; margin: 40px auto; padding: 30px; font-family: 'Google Sans', 'Segoe UI', system-ui, sans-serif; background-color: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); position: relative;",
    )


# Main route - No changes needed here
# @rt("/")
# def get(request: Request):
#     return Titled("Matrix Laser Technical Support", chat_interface(request=request))


# Add a route to serve the logo
@rt("/images/Coherent_logo_blue.png")
def get_logo():
    logo_path = images_dir / "Coherent_logo_blue.png"
    if logo_path.exists():
        return FileResponse(logo_path)
    else:
        return {"error": "Logo not found"}


@rt("/")
def get(request: Request):
    # Replace the previous simple return statement with this
    return Titled(  # Sets browser tab title *only*
        "Matrix Laser Technical Support",
        # Main page body container Div
        Div(
            # Empty div to "absorb" the auto-generated H1
            Div(style="display: none;"),
            # 1. Logo Image positioned in the top left corner
            #
            Div(
                Img(
                    src="/images/Coherent_logo_blue.png",
                    alt="Coherent Logo",
                    style="height: 60px; width: auto; display: block; margin-left: 40px; margin-bottom: 10px; margin-top: 20px;",
                ),
                # H1(
                #     "Matrix Laser Technical Support",
                #     style="margin-left: 40px; margin-top: 0; margin-bottom: 30px; font-size: 2.5rem; font-weight: bold; color: #202124;",
                # ),
                # Add a style to create a flex container for logo and title if desired
                style="display: flex; align-items: center; margin-bottom: 30px;",
            ),
            # 3. Chat Interface (remains unchanged)
            chat_interface(request=request),
        ),
    )


@rt("/send-message", methods=["POST"])
def send_message(request: Request, query: str):
    chat_engine = (
        request.app.state.chat_engine
        if hasattr(request.app.state, "chat_engine")
        else None
    )
    if chat_engine is None:
        return Safe(simple_message_html("Chat engine is not available.", "assistant"))
    query = query.strip()
    if not query:
        return ""
    user_message_html = simple_message_html(query, "user")
    try:
        logging.info(f"Processing query: {query}")
        response = chat_engine.chat(query)
        assistant_message_html = simple_message_html(response.response, "assistant")
        logging.info("Response generated.")
        clear_input = TextArea(
            id="user-input",
            name="query",
            rows=1,
            autofocus=True,
            placeholder="Ask a question about Matrix lasers...",
            style="width: 100%; box-sizing: border-box; padding: 14px 80px 14px 16px; font-size: 16px; color: #202124; border: 1px solid #dfe1e5; border-radius: 24px; resize: none; outline: none; box-shadow: none; height: 52px; margin: 0;",
            hx_swap_oob="true",
        )
        return Safe(user_message_html), Safe(assistant_message_html), clear_input
    except Exception as e:
        logging.error(f"Error processing chat query: {e}", exc_info=True)
        error_message = simple_message_html(
            f"Sorry, an error occurred: {str(e)}", "assistant"
        )
        return Safe(user_message_html), Safe(error_message)


# Route to handle chat reset - No changes needed here
@rt("/reset-chat", methods=["POST"])
def reset_chat(request: Request):
    chat_engine = (
        request.app.state.chat_engine
        if hasattr(request.app.state, "chat_engine")
        else None
    )
    if chat_engine:
        try:
            logging.info("Resetting chat engine memory...")
            chat_engine.reset()
            logging.info("Chat engine memory reset.")
        except Exception as e:
            logging.error(f"Error resetting chat engine: {e}", exc_info=True)
    else:
        logging.warning("Attempted reset, but chat engine is not available.")
    return chat_interface(request=request)


# Start the server - No changes needed here
if __name__ == "__main__":
    in_production = os.environ.get("PLASH_PRODUCTION") == "1"
    reload_status = not in_production
    print("\n--- Starting Server ---")
    print(f"Production Mode: {in_production}")
    print(f"Uvicorn Reload: {reload_status}")
    # serve(reload=reload_status)
    # Set the host to 127.0.0.1 explicitly
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=5001, reload=reload_status)
# --- END OF FILE main.py ---
