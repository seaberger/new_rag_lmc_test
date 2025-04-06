# --- START OF FILE main.py ---

from fasthtml.common import *
from fasthtml.components import Title
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

textarea_auto_grow_script = Script("""
function autoGrowTextarea(element) {
  element.style.height = 'auto'; // Temporarily shrink to measure
  // Add a small buffer (e.g., 2px) if content sometimes gets cut off
  element.style.height = (element.scrollHeight) + 'px';
}

// Function to toggle suggestions visibility with more robust handling
function toggleSuggestions() {
  console.log('Toggle suggestions called');
  const container = document.getElementById('suggestions-container');
  const toggleBtn = document.querySelector('.suggestions-toggle');
  const buttonsContainer = document.getElementById('suggestions-buttons');
  
  if (!buttonsContainer) {
    console.error('Suggestions buttons container not found');
    return;
  }
  
  if (container.classList.contains('suggestions-collapsed')) {
    // Show suggestions
    container.classList.remove('suggestions-collapsed');
    toggleBtn.textContent = 'Hide Suggestions ▲';
    toggleBtn.style.backgroundColor = '#1a73e8'; // Blue when showing
    buttonsContainer.style.display = 'block';
    console.log('Showing suggestions');
  } else {
    // Hide suggestions
    container.classList.add('suggestions-collapsed');
    toggleBtn.textContent = 'Show Suggestions ▼';
    toggleBtn.style.backgroundColor = '#1a73e8'; // Blue when hidden
    buttonsContainer.style.display = 'none';
    console.log('Hiding suggestions');
  }
}

document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.getElementById('user-input');
    if(textarea) {
        // Add class for CSS styling
        textarea.classList.add('auto-grow-textarea');
        // Add listener for input events
        textarea.addEventListener('input', function() {
            autoGrowTextarea(this);
        });
        // Initial call in case loaded with content (e.g., browser restore)
        autoGrowTextarea(textarea);
    }
    
    // Initialize mobile suggestions - more robust implementation
    const isMobile = window.matchMedia('(max-width: 600px)').matches;
    console.log('Is mobile device:', isMobile);
    
    // Apply mobile-specific setup with a slight delay to ensure DOM is fully loaded
    setTimeout(function() {
        if (isMobile) {
            const container = document.getElementById('suggestions-container');
            const toggleBtn = document.querySelector('.suggestions-toggle');
            const buttonsContainer = document.getElementById('suggestions-buttons');
            
            if (container && toggleBtn && buttonsContainer) {
                console.log('Mobile device detected, initializing suggestions toggle');
                // Ensure collapsed class is applied on mobile
                container.classList.add('suggestions-collapsed');
                toggleBtn.style.display = 'block';
                buttonsContainer.style.display = 'none';
                
                // Force visibility of the toggle button on mobile
                toggleBtn.setAttribute('style', 'display: block !important; margin: 5px auto; padding: 6px 12px; font-weight: bold;');
            } else {
                console.error('Mobile setup: One or more required elements not found');
            }
        }
    }, 100); // Short delay to ensure DOM is ready
});
// Also listen for custom events if content might be set programmatically later
document.body.addEventListener('htmx:afterSwap', function(event) {
     // If textarea content might change via OOB swap (though we clear it now)
     if (event.detail.target.id === 'user-input' || event.detail.elt.id === 'user-input') {
         const textarea = document.getElementById('user-input');
         if (textarea) autoGrowTextarea(textarea);
     }
});
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
#
custom_css = Style("""
    body {
        background-color: #f8f9fa;
        font-family: 'Google Sans', 'Segoe UI', system-ui, -apple-system, sans-serif;
        margin: 0; /* Ensure no default body margin */
    }

    /* --- HIDE FRAMEWORK-GENERATED MAIN TITLE (Just in case) --- */
    main > h1.uk-h1:first-child, h1.uk-h1 {
        display: none !important; /* Hide forcefully */
    }
    /* ------------------------------------------- */

    /* --- NEW HEADER STYLES --- */
    #main-header {
        padding: 15px 20px; /* Adjust padding as needed */
        background-color: #f8f9fa; /* Match page background */
        flex-shrink: 0; /* Prevent shrinking in the main flex container */
        border-bottom: 1px solid #e0e0e0; /* Optional separator */
    }
    .header-logo-main { /* Logo inside the new header */
        max-width: 150px;  /* Keep reduced size or adjust */
        height: auto;
        display: block;   /* Stack vertically */
        margin-bottom: 8px; /* Space between logo and title */
    }
    .main-page-title { /* The new H1 title */
        font-size: 1.3rem;  /* Adjust font size as desired */
        font-weight: bold;
        color: #202124;
        margin: 0;          /* Reset default H1 margins */
        line-height: 1.2;
    }
    /* --- END NEW HEADER STYLES --- */

    /* --- Chat Area Wrapper --- */
    #chat-area-wrapper {
        flex-grow: 1; /* Take remaining vertical space */
        padding: 20px 0; /* Add vertical padding around the chat box */
        display: flex; /* Use flex to easily center chat-container */
        justify-content: center; /* Horizontal centering */
        align-items: flex-start; /* Align chat box to the top */
        overflow: hidden; /* Prevent this wrapper from scrolling */
        min-height: 0; /* Important for flex children sizing */
    }

    /* --- Styles for elements INSIDE #chat-container --- */
    /* These styles should override or replace old centered logo/title styles */
    .logo-container { display: none; } /* Hide old centered logo container */
    .title-block { display: none; } /* Hide old internal title block */

    /* Keep text area, suggestion button, toggle, etc. styles */
    .auto-grow-textarea { resize: none; overflow-y: hidden; }
    .suggestion-btn { display: inline-block; color: #1a73e8; background-color: #f1f3f4; margin: 0.4rem; padding: 0.6rem 1rem; border: none; border-radius: 24px; cursor: pointer; font-size: 0.9rem; font-weight: 500; box-shadow: 0 1px 2px rgba(0,0,0,0.1); transition: background-color 0.2s; }
    .suggestion-btn:hover { background-color: #e8f0fe; }
    .suggestions-toggle { background-color: #1a73e8; color: white; border: none; border-radius: 20px; padding: 8px 16px; font-size: 1rem; cursor: pointer; margin: 10px auto; display: none; font-weight: bold; box-shadow: 0 2px 5px rgba(0,0,0,0.2); width: 80%; text-align: center; }
    #suggestions-container { padding: 0 1rem; text-align: center; margin-bottom: 15px; flex-shrink: 0; border-bottom: 1px solid #eee; padding-bottom: 10px; }
    #suggestions-buttons { display: flex; flex-wrap: wrap; justify-content: center; gap: 5px; margin-top: 10px; }
    .suggestions-collapsed #suggestions-buttons { display: none !important; max-height: 0 !important; overflow: hidden !important; }
    .suggestions-collapsed { padding-bottom: 0 !important; border-bottom: none !important; margin-bottom: 0 !important; }

    /* Keep message area styles */
    #chat-messages { flex: 1 1 auto; overflow-y: auto; padding: 0 15px; margin-bottom: 8px; /* Keep reduced */ border-radius: 8px; min-height: 100px; /* Ensure min height */ }

    /* Keep form/controls styles */
    .form-controls-area { flex-shrink: 0; padding-top: 6px; /* Keep reduced */ border-top: 1px solid #f0f0f0; }
    .reset-button-area { text-align: center; margin-bottom: 10px; flex-shrink: 0; }

    /* Keep Keyframes */
    @keyframes spinner-spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

    /* --- START: CSS for Enhanced Run/Stop Button --- */
    .run-button-base { min-width: 100px; background-color: #1a73e8 !important; color: white !important; border: none; border-radius: 18px; font-weight: 500; font-size: 15px; cursor: pointer; height: 36px; text-align: center; transition: background-color 0.2s; box-sizing: border-box; position: relative; display: inline-flex; align-items: center; justify-content: center; vertical-align: middle; overflow: hidden; }
    .run-button-base:hover { background-color: #185abc !important; }
    .button-inner-content { display: inline-flex; align-items: center; justify-content: center; width: 100%; height: 100%; gap: 6px; padding: 0 12px; }
    .button-text { display: none; } .run-text { display: inline; }
    .button-icon { font-size: 1.1em; opacity: 1; transition: opacity 0.2s ease-in-out; } .cmd-icon { display: inline; }
    .inline-spinner { width: 20px; height: 20px; border-radius: 50%; display: none !important; box-sizing: border-box; position: relative; flex-shrink: 0; }
    .spinner-square { position: absolute; top: 50%; left: 50%; width: 8px; height: 8px; background-color: white; transform: translate(-50%, -50%); display: block; z-index: 1; }
    .inline-spinner::before { content: ""; box-sizing: border-box; position: absolute; top: 0; left: 0; width: 100%; height: 100%; border-radius: 50%; border: 3px solid rgba(255, 255, 255, 0.3); border-top-color: #ffffff; animation: spinner-spin 0.8s linear infinite; }
    /* Styling WHEN HTMX REQUEST IS ACTIVE (Blue Background) */
    form#chat-form.htmx-request .run-button-base { /* No background change */ }
    form#chat-form.htmx-request .run-button-base:hover { /* No background change */ }
    form#chat-form.htmx-request .inline-spinner { display: inline-block !important; }
    form#chat-form.htmx-request .run-text { display: none !important; }
    form#chat-form.htmx-request .cmd-icon { display: none !important; }
    form#chat-form.htmx-request .stop-text { display: inline !important; }
    /* --- END: CSS for Enhanced Run/Stop Button --- */

    /* --- General Content Styling (Keep from original file) --- */
    pre { background-color: #f1f3f4; padding: 1rem; border-radius: 0.5rem; overflow-x: auto; font-size: 0.9rem; margin: 1rem 0; }
    code { color: #202124; font-family: 'Roboto Mono', monospace; font-size: 0.9em; }
    p { line-height: 1.5; margin: 0.5em 0; }
    h1, h2, h3, h4, h5, h6 { color: #202124; margin-top: 1.5rem; margin-bottom: 0.5rem; } /* General h tag styling */
    ul, ol { padding-left: 1.5rem; margin: 0.75rem 0; }
    li { margin-bottom: 0.5rem; }
    table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
    th, td { border: 1px solid #e0e0e0; padding: 0.5rem; text-align: left; }
    th { background-color: #f1f3f4; }
    a { color: #1a73e8; text-decoration: none; }
    a:hover { text-decoration: underline; }


    /* === MEDIA QUERY FOR MOBILE RESPONSIVENESS (max-width: 600px) === */
    @media only screen and (max-width: 600px) {
        #main-header { padding: 10px 15px; } /* Adjust header padding */
        .header-logo-main { max-width: 120px; } /* Maybe smaller logo on mobile */
        .main-page-title { font-size: 1.1rem; } /* Smaller title */

        #chat-area-wrapper { padding: 10px 0; align-items: stretch; } /* Stretch chat box vertically */
        /* #chat-container styles might need slight mobile tweaks if needed */

        pre { padding: 0.75rem; font-size: 0.8rem; }
        .suggestion-hide-mobile { display: none !important; }
        .suggestion-btn { margin: 0.3rem !important; padding: 0.5rem 0.8rem !important; font-size: 0.85rem !important; }
        #suggestions-container { padding: 0.3rem !important; margin-bottom: 8px !important; max-height: none !important; overflow-y: visible !important; border-bottom: 1px solid #eee; }
        #suggestions-buttons { display: flex; flex-wrap: wrap; justify-content: center; gap: 5px; margin-top: 10px; }
        .suggestions-toggle { display: block !important; width: 80% !important; max-width: 250px !important; margin: 10px auto !important; padding: 8px 16px !important; font-weight: bold !important; font-size: 1rem !important; border-radius: 20px !important; }
        .suggestions-collapsed #suggestions-buttons { display: none !important; max-height: 0 !important; overflow: hidden !important; }
        .suggestions-collapsed { padding-bottom: 0 !important; border-bottom: none !important; margin-bottom: 0 !important; }
    }

""")

# app, rt = fast_app(
#     hdrs=(  # Pass all headers/scripts/styles here
#         Title("Matrix Laser Technical Support"),  # Sets <title> tag
#         favicon_link,
#         custom_css,  # We will modify this below
#         textarea_auto_grow_script,
#         set_query_script,
#         auto_scroll_script,
#         submit_on_enter_script,
#         cancel_request_script,
#     ),
#     lifespan=lifespan,
# )
app, rt = fast_app(
    # Pass title directly here
    title="Matrix Laser Technical Support",
    hdrs=(
        # REMOVE Title("Matrix Laser Technical Support") from here
        favicon_link,
        custom_css,
        textarea_auto_grow_script,
        set_query_script,
        auto_scroll_script,
        submit_on_enter_script,
        cancel_request_script,
    ),
    lifespan=lifespan,
)


def simple_message_html(content, role):
    """Generate HTML string for a message without avatars"""
    is_user = role == "user"

    # Message processing
    if not is_user:
        # Process markdown for assistant messages
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

    # Determine container alignment
    container_margin = "margin-left: auto;" if not is_user else ""
    # Optional extra style
    bubble_extra_style = ""

    # Return the formatted message HTML
    return f"""
    <div style="display: flex; gap: 1rem; padding: 1rem; margin-bottom: 1rem; max-width: 85%; {container_margin}">
        <div style="background-color: {"#f1f3f4" if not is_user else "white"}; padding: 12px 16px; border-radius: 18px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); flex-grow: 1;{bubble_extra_style}">
            <div style="color: #202124; font-size: 15px;">
                {content_html}
            </div>
        </div>
    </div>
    """


# --- chat_interface function (MODIFIED) ---
def chat_interface(request: Request):
    """Create the main chat interface components."""
    # Access chat engine safely from request state
    chat_engine = getattr(request.app.state, "chat_engine", None)
    suggested_questions = getattr(request.app.state, "suggested_questions", [])

    # --- Check if chat engine loaded ---
    if chat_engine is None:
        logging.error("Chat engine is None when rendering chat_interface.")
        return Div(
            H1("Error", style="color: red;"),
            P("The Chat Engine failed to initialize or is not available..."),
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
        Div(
            *suggestion_buttons,
            id="suggestions-buttons",
        ),
        id="suggestions-container",
        # Removed cls="suggestions-collapsed" here, JS/CSS manage state
        style="padding: 0 1rem; text-align: center; margin-bottom: 15px; flex-shrink: 0; border-bottom: 1px solid #eee; padding-bottom: 10px;",
    )

    # --- REMOVED Internal Title Block ---

    # --- Main Chat Container ---
    # This Div is the actual chat box UI
    return Div(
        # --- Top Section ---
        # REMOVED title_block
        suggestions_div,  # Suggestions appear at the top inside the chat box
        # --- Middle Scrolling Section ---
        Div(  # Chat messages area
            Safe(
                simple_message_html(
                    "Welcome! How can I assist you with Matrix lasers today?",
                    "assistant",
                )
            ),
            id="chat-messages",
            style="flex: 1 1 auto; overflow-y: auto; padding: 0 15px; margin-bottom: 8px; border-radius: 8px;",  # Reduced margin
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
                    Button(  # Run/Stop button
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
                ),
                id="chat-form",
                hx_post="/send-message",
                hx_target="#chat-messages",
                hx_swap="beforeend",
                hx_indicator="#chat-form",
            ),
            Div(  # Reset button container
                Button(
                    "Reset Chat",
                    hx_post="/reset-chat",
                    hx_target="#chat-container",
                    hx_swap="innerHTML",
                    hx_confirm="Are you sure?",
                    style="background-color: #f1f3f4; color: #5f6368; border: none; padding: 8px 20px; border-radius: 20px; cursor: pointer; font-weight: 500; height: 36px; line-height: 20px;",
                ),
                # Add class for easier targeting if needed later
                cls="reset-button-area",
                style="text-align: center; margin-bottom: 10px;",
            ),
            # Add class for easier targeting
            cls="form-controls-area",
            style="flex-shrink: 0; padding-top: 6px; border-top: 1px solid #f0f0f0;",  # Reduced padding
        ),
        # --- Style for the main chat container itself ---
        style=(
            "max-width: 900px; margin: 0 auto;"  # Centered within #chat-area-wrapper
            " background-color: white; border-radius: 12px;"
            " box-shadow: 0 2px 8px rgba(0,0,0,0.05);"
            " display: flex; flex-direction: column;"
            " width: 100%; height: 100%;"  # Fill the parent wrapper
            " overflow: hidden;"  # Internal scroll handled by #chat-messages
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


@rt("/")
def get(request: Request):
    return Div(  # Main page container
        # --- NEW HEADER SECTION ---
        Header(
            Img(
                src="/images/Coherent_logo_blue.png",
                alt="Coherent Logo",
                cls="header-logo-main",
            ),  # New class
            H1(
                "Matrix Laser Technical Support", cls="main-page-title"
            ),  # New visible title + class
            id="main-header",  # ID for styling
        ),
        # --- Chat Interface Section ---
        # This div will now hold the chat interface and fill remaining space
        Div(
            chat_interface(request=request),
            id="chat-area-wrapper",  # ID for styling
        ),
        # --- Style for the main page container ---
        # This outer div still uses flex to position header and chat area
        style="display: flex; flex-direction: column; height: 100dvh; background-color: #f8f9fa;",
        # Removed overflow: hidden here, let child handle it
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
# if __name__ == "__main__":
#     in_production = os.environ.get("PLASH_PRODUCTION") == "1"
#     reload_status = not in_production
#     print("\n--- Starting Server ---")
#     print(f"Production Mode: {in_production}")
#     print(f"Uvicorn Reload: {reload_status}")
#     serve(reload=reload_status)

# --- Server Start ---
if __name__ == "__main__":
    in_production = os.environ.get("PLASH_PRODUCTION") == "1"
    reload_status = not in_production
    port = 5001  # Keep consistent port
    host = "127.0.0.1"
    print("\n--- Starting Server ---")
    print(f"Production Mode: {in_production}")
    print(f"Uvicorn Reload: {reload_status}")
    print(f"Access URL: http://{host}:{port}")

    # Use fasthtml's serve() which wraps uvicorn correctly
    serve(host=host, port=port, reload=reload_status)
