# --- START OF FILE main.py ---

from fasthtml.common import *

from fasthtml import FastHTML
from fastapi import Request, Response
from monsterui.all import *
from fastapi.responses import FileResponse
import os
import re
import json
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# Create images directory if it doesn't exist
images_dir = Path("./images")
images_dir.mkdir(exist_ok=True)  # Ensure it exists

favicon_link = Link(
    rel="icon", type="image/png", href="/images/coherent_atom_symbol.png"
)

# Import chat engine functions
from chat_engine import init_chat_engine

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Constants ---
SUGGESTED_QUESTIONS_FILE_LOCAL = "./suggested_questions.json"
SUGGESTED_QUESTIONS_FILE_PROD = "/app/suggested_questions.json"


# --- Lifespan context manager for startup/shutdown (no changes needed here) ---
@asynccontextmanager
async def lifespan(app: FastHTML):
    logging.info("Application startup: Initializing chat engine...")
    try:
        # Use app instance passed to lifespan
        app.state.chat_engine = init_chat_engine()
        logging.info("Application startup: Chat engine initialized successfully.")
    except Exception as e:
        logging.error(
            f"Application startup: FATAL error initializing chat engine: {e}",
            exc_info=True,  # Log traceback on error
        )
        app.state.chat_engine = None  # Set to None on failure
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
    logging.info("Application shutdown.")


# --- JavaScript Snippets (no changes needed) ---
set_query_script = Script("""
function setQuery(text) {
  const textarea = document.getElementById('user-input');
  if (textarea) {
    textarea.value = text;
    textarea.focus();
    textarea.setSelectionRange(textarea.value.length, textarea.value.length);
  } else { console.error("Could not find textarea with id 'user-input'"); }
}
""")

auto_scroll_script = Script("""
document.addEventListener('htmx:afterSwap', function(event) {
    if (event.detail.target.id === 'chat-messages' || event.detail.target.closest('#chat-messages')) {
        setTimeout(function() {
            const chatMessages = document.getElementById('chat-messages');
            if (chatMessages) { chatMessages.scrollTop = chatMessages.scrollHeight; }
        }, 100);
    }
});
""")

submit_on_enter_script = Script("""
document.addEventListener('DOMContentLoaded', function() {
    console.log("[Cmd+Enter] DOM loaded. Setting up listener on BODY."); // Log 1

    // Attach listener to the body, but only act if the event originated from our textarea
    document.body.addEventListener('keydown', function(event) {
        // Check if the event target is the textarea we care about
        if (event.target.id !== 'user-input') {
            return; // Not our textarea, ignore
        }

        const chatForm = document.getElementById('chat-form'); // Still need the form
        const textarea = event.target; // Already have the textarea from event.target

        // console.log("[Cmd+Enter] Keydown on #user-input:", event.key, "Meta:", event.metaKey, "Ctrl:", event.ctrlKey); // Log 3

        if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
            console.log("[Cmd+Enter] Cmd/Ctrl+Enter DETECTED on #user-input!"); // Log 4
            event.preventDefault(); // Prevent newline

            if (!chatForm) {
                console.error("[Cmd+Enter] Form with id 'chat-form' not found when trying to submit!");
                return;
            }

            if (window.htmx && typeof window.htmx.trigger === 'function') {
               console.log("[Cmd+Enter] Triggering HTMX submit on form."); // Log 5
               try {
                   htmx.trigger(chatForm, 'submit');
               } catch (e) {
                   console.error("[Cmd+Enter] Error during htmx.trigger:", e);
               }
            } else {
               console.log("[Cmd+Enter] HTMX trigger not found, using requestSubmit."); // Log 6
               try {
                  chatForm.requestSubmit();
               } catch (e) {
                  console.error("[Cmd+Enter] Error during requestSubmit:", e);
               }
            }
        }
    }); // End of body keydown listener

}); // End of DOMContentLoaded listener
""")

cancel_request_script = Script("""
document.addEventListener('click', function(event) {
    const button = event.target.closest('#run-stop-button');
    if (!button) return;

    const form = button.closest('form');
    const stopTextElement = button.querySelector('.stop-text');
    const isStopVisible = stopTextElement && window.getComputedStyle(stopTextElement).display !== 'none';

    if (isStopVisible && form && form.classList.contains('htmx-request')) {
        console.log('Stop button clicked (Stop visible). Form has htmx-request. Attempting DIRECT abort.');

        // --- New Approach: Find and abort the XHR directly ---
        let xhr = null;
        // HTMX might store request info on the triggering element or the target
        // Check the form first (common for hx-indicator target)
        if (form.htmx && form.htmx.xhr) { // Check if API exists and xhr property is there
            xhr = form.htmx.xhr;
            console.log('Found XHR on form element.');
        }
        // Fallback: Check the button (less likely but possible)
        else if (button.htmx && button.htmx.xhr) {
             xhr = button.htmx.xhr;
             console.log('Found XHR on button element.');
        }
        // Fallback: Look for related elements (htmx sometimes adds data attributes)
        // This part is more speculative and might need inspection in dev tools
        else {
             const relatedTarget = document.querySelector(form.getAttribute('hx-target'));
             if (relatedTarget && relatedTarget.htmx && relatedTarget.htmx.xhr) {
                 xhr = relatedTarget.htmx.xhr;
                 console.log('Found XHR on target element:', form.getAttribute('hx-target'));
             }
        }


        if (xhr && typeof xhr.abort === 'function') {
            console.log('Calling xhr.abort() directly.');
            xhr.abort(); // Directly abort the XMLHttpRequest
            // Note: Manually removing the htmx-request class might be needed
            // as direct XHR abort might not trigger all HTMX cleanup automatically.
            // form.classList.remove('htmx-request'); // Uncomment if button state doesn't reset
            event.preventDefault();
            event.stopPropagation();
        } else {
             console.warn('Could not find active XHR object to abort directly. Trying htmx:abort event as fallback.');
             // Fallback to triggering the event if direct abort failed
             if (window.htmx && typeof window.htmx.trigger === 'function') {
                  window.htmx.trigger(form, 'htmx:abort');
                  event.preventDefault();
                  event.stopPropagation();
             } else {
                 console.error("Neither direct XHR abort nor htmx:abort trigger is possible.");
             }
        }
        const textarea = document.getElementById('user-input');
if (textarea) {
    // textarea.value = ''; // If you decided to clear it
    textarea.focus(); // Bring focus back to input
}
        // --- End New Approach ---

    }
}, true);
""")
# --- End JavaScript Snippets ---


# --- CSS Styles (no changes needed in the CSS content itself) ---
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

    /* --- Keyframes for Spinners --- */
    @keyframes spinner-spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    /* --- External Spinner (If Used Elsewhere) --- */
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
        box-sizing: border-box;
        border: 4px solid rgba(0, 0, 0, 0.1);
        border-left-color: #1a73e8;
        border-radius: 50%;
    }
    #spinner.htmx-request {
        opacity: 1;
        animation: spinner-spin 1s linear infinite;
    }


    /* --- START: CSS for Enhanced Run/Stop Button --- */

    /* Base Button Styles (with Debugging Flags) */
    .run-button-base {
        min-width: 100px;
        background-color: #1a73e8 !important; /* DEBUG: Force blue */
        color: white !important; /* DEBUG: Force white */
        border: none;
        border-radius: 18px;
        font-weight: 500;
        font-size: 15px;
        cursor: pointer;
        height: 36px;
        text-align: center;
        transition: background-color 0.2s;
        box-sizing: border-box;
        position: relative;
        display: inline-flex; /* Button is flex container */
        align-items: center; /* Vertical centering */
        justify-content: center; /* Horizontal centering */
        vertical-align: middle;
        overflow: hidden;
    }
    /* Comment out hover during debug if needed */
    .run-button-base:hover {
        background-color: #185abc !important; /* DEBUG: Force darker blue */
    }

    /* Inner Content Container */
    .button-inner-content {
        display: inline-flex; /* Contents are also flex */
        align-items: center;
        justify-content: center;
        width: 100%;
        height: 100%;
        gap: 6px;
        padding: 0 12px; /* Padding inside */
    }

    /* Default Visibility for Text/Icons */
    .button-text { display: none; } /* Hide all text spans by default */
    .run-text { display: inline; }  /* Show Run text */
    /* .stop-text is covered by .button-text default */

    .button-icon { font-size: 1.1em; opacity: 1; transition: opacity 0.2s ease-in-out; }
    .cmd-icon { display: inline; } /* Show Cmd icon */

    /* Spinner Default Visibility & Style */
    .inline-spinner {
    width: 20px;
    height: 20px;
    /* Remove border properties from the container */
    /* border: 3px solid rgba(255, 255, 255, 0.3); */
    /* border-left-color: #ffffff; */
    border-radius: 50%;
    display: none !important; /* DEBUG: Keep hidden default */
    box-sizing: border-box;
    position: relative; /* Still needed for pseudo-element and square */
    flex-shrink: 0;
    /* Remove animation from the container */
    /* animation: spinner-spin 0.8s linear infinite; */
}

/* Spinner Square (Centered inside container) */
.spinner-square {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 8px;
    height: 8px;
    background-color: white;
    transform: translate(-50%, -50%);
    display: block; /* Keep block */
    z-index: 1; /* Ensure square is above the spinning border */
}

/* Spinning Border using ::before Pseudo-element */
.inline-spinner::before {
    content: "";
    box-sizing: border-box;
    position: absolute;
    top: 0;
    left: 0;
    width: 100%; /* Match parent size */
    height: 100%; /* Match parent size */
    border-radius: 50%; /* Make it round */
    /* Apply border styles HERE */
    border: 3px solid rgba(255, 255, 255, 0.3); /* Light track */
    border-top-color: #ffffff; /* Spinning segment (use border-top/left/right/bottom) */
    /* Apply animation HERE */
    animation: spinner-spin 0.8s linear infinite;
}

/* STYLING WHEN HTMX REQUEST IS ACTIVE */
form#chat-form.htmx-request .inline-spinner {
    display: inline-block !important; /* DEBUG: Force show container */
}
    form#chat-form.htmx-request .button-inner-content {
        /* justify-content: center; /* Keep centered */
    }
    form#chat-form.htmx-request .inline-spinner {
        display: inline-block !important; /* DEBUG: Force show spinner */
    }
    form#chat-form.htmx-request .run-text {
        display: none !important; /* DEBUG: Force hide Run */
    }
    form#chat-form.htmx-request .cmd-icon {
        display: none !important; /* DEBUG: Force hide Cmd icon */
    }
    form#chat-form.htmx-request .stop-text {
        display: inline !important; /* DEBUG: Force show Stop */
    }
    /* --- END: CSS for Enhanced Run/Stop Button --- */

""")


# --- Initialize FastHTML app using fast_app helper ---
# This combines app creation, route setup, headers, and lifespan integration
app, rt = fast_app(
    hdrs=(  # Pass all headers/scripts/styles here
        # No need for Titled() here, handle in route if needed
        favicon_link,
        custom_css,
        set_query_script,
        auto_scroll_script,
        submit_on_enter_script,
        cancel_request_script,
    ),
    lifespan=lifespan,  # Pass the lifespan manager
)
# Now `app` is the configured FastHTML instance and `rt` is its route decorator


# def simple_message_html(content, role):
#     """Generate HTML string for a message (no changes needed)"""
#     is_user = role == "user"
#     avatar = "👤" if is_user else "🤖"
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
#     # Return the formatted message HTML
#     return f"""
#     <div style="display: flex; gap: 1rem; padding: 1rem; margin-bottom: 1rem; max-width: 85%; {"margin-left: auto;" if not is_user else ""}">
#         <div style="width: 32px; height: 32px; background-color: {"#4285f4" if not is_user else "#5f6368"}; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; flex-shrink: 0;">{avatar}</div>
#         <div style="background-color: {"#f1f3f4" if not is_user else "white"}; padding: 12px 16px; border-radius: 18px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); flex-grow: 1;"><div style="color: #202124; font-size: 15px;">{content_html}</div></div>
#     </div>"""
def simple_message_html(content, role):
    """Generate HTML string for a message without avatars"""
    is_user = role == "user"

    # Message processing
    if not is_user:
        # (Keep your markdown processing logic here)
        cleaned_content = re.sub(r"```\s*\n\s*```", "", content)  # Example
        cleaned_content = re.sub(
            r"```[a-z]*\s*\n\s*```", "", cleaned_content
        )  # Example
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
    # Optional extra style (e.g., margin-right for assistant bubble)
    bubble_extra_style = ""  # Or ' margin-right: 32px;' if not is_user else ''

    # --- Corrected f-string (INVALID COMMENTS REMOVED) ---
    return f"""
    <div style="display: flex; gap: 1rem; padding: 1rem; margin-bottom: 1rem; max-width: 85%; {container_margin}">
        <div style="background-color: {"#f1f3f4" if not is_user else "white"}; padding: 12px 16px; border-radius: 18px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); flex-grow: 1;{bubble_extra_style}">
            <div style="color: #202124; font-size: 15px;">
                {content_html}
            </div>
        </div>
    </div>
    """
    # --- END Correction ---


# def chat_interface(request: Request):
#     """Create the main chat interface components."""
#     # Access chat engine safely from request state
#     chat_engine = getattr(request.app.state, "chat_engine", None)
#     suggested_questions = getattr(request.app.state, "suggested_questions", [])

#     # --- Check if chat engine loaded ---
#     if chat_engine is None:
#         logging.error("Chat engine is None when rendering chat_interface.")
#         return Div(
#             H1("Error", style="color: red;"),
#             P(
#                 "The Chat Engine failed to initialize or is not available. Please check server logs."
#             ),
#             style="max-width: 800px; margin: 40px auto; padding: 20px; background-color: #fff; border: 1px solid red; border-radius: 8px;",
#         )

#     # --- Build Suggested Questions ---
#     suggestion_buttons = []
#     if suggested_questions:
#         for q in suggested_questions:
#             safe_q = q.replace("'", "\\'")
#             suggestion_buttons.append(
#                 Button(
#                     q,
#                     onclick=f"setQuery('{safe_q}')",
#                     style="color: #1a73e8; background-color: #f1f3f4; margin: 0.4rem; padding: 0.6rem 1rem; border: none; border-radius: 24px; cursor: pointer; font-size: 0.9rem; display: inline-block; font-weight: 500; box-shadow: 0 1px 2px rgba(0,0,0,0.1); transition: background-color 0.2s;",
#                 )
#             )
#     else:
#         suggestion_buttons.append(
#             P("No suggestions available.", style="font-style: italic; color: #666;")
#         )
#     suggestions_div = Div(
#         *suggestion_buttons,
#         style="padding: 1rem; text-align: center; margin: 20px 0 30px 0;",
#     )

#     # --- Internal Title Block ---
#     title_block = Div(
#         P(
#             "Ask technical questions about Matrix laser products",
#             style="font-size: 1.3rem; color: #5f6368; margin-top: 0.5rem; font-weight: bold; font-style: italic;",
#         ),
#         style="text-align: center; margin-bottom: 40px; padding-bottom: 1rem;",
#     )


#     # --- Main Chat Container ---
#     return Div(
#         title_block,
#         Div(  # Chat messages area
#             Safe(
#                 simple_message_html(
#                     "Welcome! How can I assist you with Matrix lasers today?",
#                     "assistant",
#                 )
#             ),
#             suggestions_div,
#             id="chat-messages",
#             style="max-height: 60vh; overflow-y: auto; padding-right: 10px; margin-bottom: 30px;",
#         ),
#         Div(  # Form and controls area
#             Form(
#                 Div(  # Input Row
#                     TextArea(
#                         placeholder="Ask a question about Matrix lasers...",
#                         id="user-input",
#                         name="query",
#                         rows=1,
#                         autofocus=True,
#                         style="width: 100%; box-sizing: border-box; padding: 14px 110px 14px 16px; font-size: 16px; color: #202124; border: 1px solid #dfe1e5; border-radius: 24px; resize: none; outline: none; box-shadow: none; height: 52px; margin: 0;",
#                     ),
#                     # --- Corrected Button Structure with Commas ---
#                     Button(
#                         Span(  # Start of outer Span arguments
#                             # Positional arguments for the outer Span come FIRST:
#                             # 1.1 Spinner Span
#                             Span(  # Outer Spinner Span call
#                                 # Positional Argument(s) first:
#                                 Span(cls="spinner-square"),  # The inner square Span
#                                 # Keyword Argument(s) last:
#                                 cls="inline-spinner",
#                             ),  # Comma still needed between positional args
#                             # 1.2 Run Text Span
#                             Span(
#                                 "Run", cls="button-text run-text"
#                             ),  # Positional then KWD is fine here
#                             # Comma still needed between positional args
#                             # 1.3 Stop Text Span
#                             Span(
#                                 "Stop", cls="button-text stop-text"
#                             ),  # Positional then KWD is fine here
#                             # Comma still needed between positional args
#                             # 1.4 Icon Span
#                             Span(
#                                 " ⌘⏎", cls="button-icon cmd-icon"
#                             ),  # Positional then KWD is fine here
#                             # Keyword arguments for the outer Span come LAST:
#                             cls="button-inner-content",  # Moved cls keyword arg to the end
#                         ),
#                         # Span(cls="button-inner-content", # Inner content wrapper
#                         #     Span(cls="inline-spinner", Span(cls="spinner-square")), # 1. Spinner
#                         #     Span("Run", cls="button-text run-text"), # 2. Run Text
#                         #     Span("Stop", cls="button-text stop-text"), # 3. Stop Text
#                         #     Span(" ⌘⏎", cls="button-icon cmd-icon"), # 4. Icon
#                         # ), # <-- End of main Span (Positional Arg 1)
#                         # Keyword arguments for Button:
#                         type="submit",
#                         id="run-stop-button",
#                         cls="run-button-base",
#                         style="position: absolute; right: 6px; top: 50%; transform: translateY(-50%); overflow: hidden;",
#                         title="Submit query (⌘+⏎ or Ctrl+Enter)"
#                     ),
#                     # --- End Corrected Button ---
#                     style="position: relative; display: block; margin-bottom: 24px; min-height: 52px;",
#                 ),
#                 hx_post="/send-message",
#                 hx_target="#chat-messages",
#                 hx_swap="beforeend",
#                 hx_indicator="#chat-form",
#                 id="chat-form",
#             ),
#             # Reset button
#             Div(
#                 Button(
#                     "Reset Chat",
#                     hx_post="/reset-chat",
#                     hx_target="#chat-container",
#                     hx_swap="innerHTML",
#                     hx_confirm="Are you sure?",
#                     style="background-color: #f1f3f4; color: #5f6368; border: none; padding: 8px 20px; border-radius: 20px; cursor: pointer; font-weight: 500; height: 36px; line-height: 20px;",
#                 ),
#                 style="text-align: center; margin-bottom: 24px;",
#             ),
#             style="margin-top: 1rem; position: sticky; bottom: 0; background-color: white; padding-top: 12px; border-top: 1px solid #f0f0f0;",
#         ),
#         # No external spinner Div needed as it's inside the button now
#         id="chat-container",
#         style="max-width: 900px; margin: 40px auto; padding: 30px; font-family: 'Google Sans', 'Segoe UI', system-ui, sans-serif; background-color: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); position: relative;",
#     )
def chat_interface(request: Request):
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
        for q in suggested_questions:
            safe_q = q.replace("'", "\\'")
            suggestion_buttons.append(
                Button(
                    q,
                    onclick=f"setQuery('{safe_q}')",
                    style="color: #1a73e8; background-color: #f1f3f4; margin: 0.4rem; padding: 0.6rem 1rem; border: none; border-radius: 24px; cursor: pointer; font-size: 0.9rem; display: inline-block; font-weight: 500; box-shadow: 0 1px 2px rgba(0,0,0,0.1); transition: background-color 0.2s;",
                )
            )
    else:
        suggestion_buttons.append(
            P("No suggestions available.", style="font-style: italic; color: #666;")
        )
    # --- Suggestions Div (will be part of non-scrolling top area) ---
    suggestions_div = Div(
        *suggestion_buttons,
        style="padding: 0 1rem; text-align: center; margin-bottom: 15px; flex-shrink: 0;",  # Don't shrink
    )

    # --- Internal Title Block (will be part of non-scrolling top area) ---
    title_block = Div(
        P(
            "Ask technical questions about Matrix laser products",
            style="font-size: 1.3rem; color: #5f6368; margin-top: 0; margin-bottom: 0; font-weight: bold; font-style: italic;",
        ),
        style="text-align: center; margin-bottom: 15px; padding: 10px 0; flex-shrink: 0;",  # Don't shrink
    )

    # --- Main Chat Container - Flex Column, Fills Space, Manages Internal Overflow ---
    return Div(  # id="chat-container"
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
            # Messages appended here
            id="chat-messages",
            # Style: Grow/shrink within parent flex, enable Y scrolling
            style="flex: 1 1 auto; overflow-y: auto; padding: 0 15px; margin-bottom: 15px; /* border: 1px solid #eee; */ border-radius: 8px;",
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
                        style="width: 100%; box-sizing: border-box; padding: 14px 110px 14px 16px; font-size: 16px; color: #202124; border: 1px solid #dfe1e5; border-radius: 24px; resize: none; outline: none; box-shadow: none; height: 52px; margin: 0;",
                    ),
                    # --- Button using correct syntax ---
                    Button(
                        Span(  # Outer Span (button-inner-content)
                            Span(
                                Span(cls="spinner-square"), cls="inline-spinner"
                            ),  # Spinner Span
                            Span("Run", cls="button-text run-text"),  # Run Text Span
                            Span("Stop", cls="button-text stop-text"),  # Stop Text Span
                            Span(" ⌘⏎", cls="button-icon cmd-icon"),  # Icon Span
                            cls="button-inner-content",  # Keyword arg last
                        ),  # End Outer Span
                        type="submit",
                        id="run-stop-button",
                        cls="run-button-base",
                        style="position: absolute; right: 6px; top: 50%; transform: translateY(-50%); overflow: hidden;",
                        title="Submit query (⌘+⏎ or Ctrl+Enter)",  # Tooltip added
                    ),
                    # --- End Button ---
                    style="position: relative; display: block; margin-bottom: 10px; min-height: 52px;",
                ),  # End Input Row Div
                hx_post="/send-message",
                hx_target="#chat-messages",
                hx_swap="beforeend",
                hx_indicator="#chat-form",
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
            # Style: Don't shrink, add padding/border
            style="flex-shrink: 0; padding-top: 10px; border-top: 1px solid #f0f0f0;",
        ),  # End Form/Controls Area Div
        # --- Style for the main chat container itself ---
        style=(
            "max-width: 900px; margin: 0 auto 20px auto;"  # Horizontal centering, bottom margin
            " padding: 20px; background-color: white; border-radius: 12px;"
            " box-shadow: 0 2px 8px rgba(0,0,0,0.05);"
            " display: flex; flex-direction: column;"  # Use flex column for internal layout
            " flex: 1 1 auto;"  # ★★★ Key: Grow/shrink to fill space from parent flex container ★★★
            " overflow: hidden;"  # Hide overflow on this container, scroll happens in #chat-messages
            # " border: 2px solid red;" # DEBUG: Uncomment to see container bounds
        ),
        id="chat-container",
    )


# --- Routes ---


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


# Main page route
# @rt("/")
# def get(request: Request):
#     return Titled(  # Use Titled for browser tab and main H1 (default behavior)
#         "Matrix Laser Technical Support",  # Title text
#         # Main page content container
#         Div(
#             # Logo Section
#             Div(
#                 Img(
#                     src="/images/Coherent_logo_blue.png",
#                     alt="Coherent Logo",
#                     style="height: 60px; width: auto; display: block; margin-left: 40px; margin-bottom: 10px; margin-top: 20px;",
#                 ),
#                 style="margin-bottom: 30px;",  # Spacing below logo area
#             ),
#             # Chat Interface Section
#             chat_interface(request=request),  # Render the chat UI
#         ),
#     )
@rt("/")
def get(request: Request):
    return Titled(
        "Matrix Laser Technical Support",  # Browser tab title
        # --- Main Page Container - Flex Column, STRICT Full Height ---
        Div(
            # --- 1. Fixed Header Section ---
            Div(  # Container for Logo
                Img(
                    src="/images/Coherent_logo_blue.png",
                    alt="Coherent Logo",
                    style="height: 60px; width: auto; display: block; margin-left: 40px; margin-bottom: 10px; margin-top: 20px;",
                ),
                # Prevent shrinking, give defined bottom margin
                style="flex-shrink: 0; background-color: #f8f9fa;",  # Match body background
            ),  # --- End Header Section ---
            # --- 2. Chat Interface Section (Will be forced into remaining space) ---
            chat_interface(request=request),
            # Style for the main page container
            style="display: flex; flex-direction: column; height: 100vh; background-color: #f8f9fa; overflow: hidden;",  # STRICT height: 100vh, overflow hidden
        ),  # --- End Main Page Container ---
    )


# Send message route
@rt("/send-message", methods=["POST"])
def send_message(request: Request, query: str):
    chat_engine = getattr(request.app.state, "chat_engine", None)
    if chat_engine is None:
        # Ensure even error messages are Safe
        return Safe(simple_message_html("Chat engine not available.", "assistant"))
    query = query.strip()
    if not query:
        return ""

    # import time; time.sleep(3) # For testing

    # Generate HTML - Wrap in Safe() right away or when returning
    user_message_html_str = simple_message_html(query, "user")
    try:
        logging.info(f"Processing query: {query}")
        response = chat_engine.chat(query)
        # Generate HTML - Wrap in Safe() right away or when returning
        assistant_message_html_str = simple_message_html(response.response, "assistant")
        logging.info("Response generated.")

        clear_input = TextArea(
            "",
            id="user-input",
            name="query",
            hx_swap_oob="true",
            rows=1,
            autofocus=True,
            placeholder="Ask a question about Matrix lasers...",
            style="width: 100%; box-sizing: border-box; padding: 14px 110px 14px 16px; font-size: 16px; color: #202124; border: 1px solid #dfe1e5; border-radius: 24px; resize: none; outline: none; box-shadow: none; height: 52px; margin: 0;",
        )

        # --- Wrap the HTML strings in Safe() when returning ---
        return (
            Safe(user_message_html_str),
            Safe(assistant_message_html_str),
            clear_input,
        )
        # --- End Safe() wrapping ---

    except Exception as e:
        logging.error(f"Error processing chat query: {e}", exc_info=True)
        error_message_content = "Sorry, an error occurred. Please try again."
        # Generate HTML - Wrap in Safe()
        error_message_html_str = simple_message_html(error_message_content, "assistant")

        clear_input = TextArea(
            "",
            id="user-input",
            name="query",
            hx_swap_oob="true",
            rows=1,
            autofocus=True,
            placeholder="Ask a question about Matrix lasers...",
            style="width: 100%; box-sizing: border-box; padding: 14px 110px 14px 16px; font-size: 16px; color: #202124; border: 1px solid #dfe1e5; border-radius: 24px; resize: none; outline: none; box-shadow: none; height: 52px; margin: 0;",
        )
        # --- Wrap the HTML strings in Safe() when returning ---
        # Also wrap the user message string if returning it on error
        return Safe(user_message_html_str), Safe(error_message_html_str), clear_input
        # --- End Safe() wrapping ---


# Reset chat route
@rt("/reset-chat", methods=["POST"])
def reset_chat(request: Request):
    chat_engine = getattr(request.app.state, "chat_engine", None)
    if chat_engine:
        try:
            logging.info("Resetting chat engine memory...")
            chat_engine.reset()
            logging.info("Chat engine memory reset.")
        except Exception as e:
            logging.error(f"Error resetting chat engine: {e}", exc_info=True)
    else:
        logging.warning("Reset attempted, but chat engine not available.")
    # Return fresh interface after reset
    return chat_interface(request=request)


# Start the server - No changes needed here
if __name__ == "__main__":
    in_production = os.environ.get("PLASH_PRODUCTION") == "1"
    reload_status = not in_production
    print("\n--- Starting Server ---")
    print(f"Production Mode: {in_production}")
    print(f"Uvicorn Reload: {reload_status}")
    serve(reload=reload_status)
    # Set the host to 127.0.0.1 explicitly
    # import uvicorn

    # uvicorn.run("main:app", host="127.0.0.1", port=5001, reload=reload_status)
# --- END OF FILE main.py ---
