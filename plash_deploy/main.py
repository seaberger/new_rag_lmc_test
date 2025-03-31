from fasthtml.common import *
from monsterui.all import *
import os
import re
from typing import List

# Import chat engine functions
from chat_engine import init_chat_engine

# Initialize the chat engine
chat_engine = init_chat_engine()


def simple_message_html(content, role):
    """Generate HTML string for a message with enhanced contrast"""
    is_user = role == "user"

    if not is_user:
        # Use regex to remove empty code blocks but preserve code blocks with content
        # This pattern matches code blocks with only whitespace between the backticks
        cleaned_content = re.sub(r"```\s*\n\s*```", "", content)

        # Also handle the case where there might be a language specifier
        cleaned_content = re.sub(r"```[a-z]*\s*\n\s*```", "", cleaned_content)

        # Custom rendering to avoid the empty code block issue
        try:
            from mistletoe import Document, HTMLRenderer

            doc = Document(cleaned_content)
            renderer = HTMLRenderer()
            content_html = renderer.render(doc)
            # Additional cleanup - remove any empty pre/code tags that might remain
            content_html = re.sub(
                r"<pre>\s*<code>\s*</code>\s*</pre>", "", content_html
            )
        except Exception as e:
            # Fallback to standard markdown if custom rendering fails
            print(f"Using fallback markdown due to: {str(e)}")
            content_html = markdown(cleaned_content)
    else:
        content_html = f"<p>{content}</p>"

    # Add stronger contrast for the content text
    enhanced_content = f"""
    <div style="flex: 1; color: #000000; font-family: system-ui, sans-serif;">
        <div style="color: #000000;">
            {content_html}
        </div>
    </div>
    """

    return f"""
    <div style="display: flex; gap: 1rem; padding: 1rem; background-color: {"#f0f0f0" if not is_user else "white"}; border-radius: 0.5rem; margin-bottom: 1rem; border: 1px solid #d0d0d0;">
        <div style="width: 2rem; height: 2rem; background-color: #d0d0d0; border-radius: 9999px; display: flex; align-items: center; justify-content: center;">
            {"👤" if is_user else "🤖"}
        </div>
        {enhanced_content}
    </div>
    """


# Custom CSS for a cleaner interface with high contrast
custom_css = Style("""
    body {
        background-color: #f9fafb;
    }
    
    #chat-messages {
        min-height: 300px;
    }
    
    pre {
        background-color: #f1f1f1;
        padding: 1rem;
        border-radius: 0.5rem;
        overflow-x: auto;
        border: 1px solid #d0d0d0;
    }
    
    code {
        color: #000000;
        font-family: monospace;
    }
    
    #user-input:focus {
        box-shadow: none;
        border-color: #000000;
    }
    
    /* Improve the typography */
    p {
        line-height: 1.6;
        color: #000000;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #000000;
        font-weight: bold;
    }
    
    /* Strong contrast for all elements */
    * {
        color: #000000;
    }
""")

# Initialize FastHTML app
app, rt = fast_app(hdrs=(Theme.blue.headers(), custom_css))


def chat_interface():
    """Create a clean, high-contrast chat interface"""
    return Div(
        # Header
        Div(
            H1(
                "Laser Measurement Assistant",
                style="font-size: 1.75rem; font-weight: bold; color: #000000;",
            ),
            P(
                "Ask questions about laser measurement technology",
                style="color: #000000; font-size: 1rem; font-weight: 500;",
            ),
            style="border-bottom: 2px solid #000000; padding-bottom: 1rem; margin-bottom: 1rem;",
        ),
        # Chat messages container
        Div(
            # Initial welcome message as HTML
            Safe(
                simple_message_html(
                    "Welcome to the Laser Measurement Assistant. How can I help you today?",
                    "assistant",
                )
            ),
            id="chat-messages",
            style="max-height: 60vh; overflow-y: auto;",
        ),
        # Input form
        Form(
            Div(
                # Text input
                TextArea(
                    placeholder="Ask a question about laser measurement...",
                    id="user-input",
                    name="query",
                    rows=2,
                    style="width: 100%; padding: 0.75rem; border: 2px solid #000000; border-radius: 0.375rem; min-height: 80px; color: #000000; font-family: system-ui, sans-serif; font-weight: 500;",
                ),
                # Submit button
                Button(
                    "Send",
                    type="submit",
                    style="position: absolute; right: 0.75rem; bottom: 0.75rem; background-color: #0047AB; color: white; padding: 0.5rem 1rem; border-radius: 0.375rem; font-weight: bold; border: none; cursor: pointer;",
                ),
                style="position: relative; margin-top: 1rem;",
            ),
            hx_post="/send-message",
            hx_target="#chat-messages",
            hx_swap="beforeend",
            hx_indicator="#spinner",
            style="margin-top: 1rem; border-top: 2px solid #000000; padding-top: 1rem;",
        ),
        # Loading indicator
        Loading(
            cls=(LoadingT.spinner, "fixed bottom-4 right-4 opacity-0"),
            htmx_indicator=True,
            id="spinner",
        ),
        style="max-width: 800px; margin: 0 auto; padding: 20px; font-family: system-ui, sans-serif; background-color: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);",
    )


# Main route
@rt("/")
def get():
    return Titled("Laser Measurement Assistant", chat_interface())


# Add route to handle message sending
@rt("/send-message", methods=["POST"])
def send_message(query: str):
    """Handle user message and get response"""
    if not query.strip():
        return ""

    # Create user message HTML
    user_message = Safe(simple_message_html(query, "user"))

    try:
        # Get response from chat engine
        response = chat_engine.chat(query)

        # Create assistant message HTML
        assistant_message = Safe(simple_message_html(response.response, "assistant"))

        # Clear input via OOB swap
        clear_input = TextArea(
            placeholder="Ask a question about laser measurement...",
            id="user-input",
            name="query",
            rows=2,
            style="width: 100%; padding: 0.75rem; border: 2px solid #000000; border-radius: 0.375rem; min-height: 80px; color: #000000; font-family: system-ui, sans-serif; font-weight: 500;",
            hx_swap_oob="true",
        )

        return user_message, assistant_message, clear_input

    except Exception as e:
        # Return error message
        error_message = Safe(
            simple_message_html(f"Sorry, an error occurred: {str(e)}", "assistant")
        )
        return user_message, error_message


# Start the server
if __name__ == "__main__":
    serve()
