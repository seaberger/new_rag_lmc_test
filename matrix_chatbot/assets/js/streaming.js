// Variables to manage streaming state
let currentStreamTarget = null;
let isNewStream = true;
let accumulatedMarkdown = ""; // Add accumulator for raw text

// --- Stream Initialization (Reset State) ---
function startStream() {
    // Only reset state variables, target is created on first chunk
    isNewStream = false;
    accumulatedMarkdown = "";
    console.log('Stream state reset.');
}

// --- Append Chunk to Stream ---
function appendToStream(chunk) {
    // Cannot append if stream ended prematurely or never started correctly
    if (isNewStream) {
        console.error('Stream not initialized or already ended');
        return;
    }

    // Check for the [DONE] signal from the backend
    if (chunk === '[DONE]') {
        endStream();
        return;
    }

    // --- First Chunk Logic: Create Bubble --- 
    if (currentStreamTarget === null) {
        console.log("First chunk received, creating assistant bubble.");
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) {
            console.error("CRITICAL: chat-messages container not found!");
            endStream(); // Abort if we can't add the message
            return;
        }
        const assistantMessageId = `assistant-msg-${Date.now()}`;
        const assistantBubbleId = `assistant-bubble-${assistantMessageId}`; // ID for the outer bubble div
        const streamContentId = `stream-content-${assistantMessageId}`; // ID for the inner content div
        const assistantMessageHtml = `
            <div id="${assistantBubbleId}" style="display: flex; gap: 1rem; padding: 1rem; margin-bottom: 1rem; max-width: 85%; margin-right: auto;">
                <img src="/images/coherent_atom_symbol.png" alt="AI" style="width: 32px; height: 32px; border-radius: 50%; align-self: flex-start;">
                <div style="background-color: #f1f3f4; padding: 12px 16px; border-radius: 18px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); flex-grow: 1;">
                    <div style="color: #202124; font-size: 15px; width: 100%; overflow-wrap: break-word; white-space: pre-wrap;" id="${streamContentId}"></div>
                </div>
            </div>`;
        chatMessages.insertAdjacentHTML('beforeend', assistantMessageHtml);
        currentStreamTarget = document.getElementById(streamContentId); // Get the inner div for content
        const assistantBubbleElement = document.getElementById(assistantBubbleId); // Get the outer bubble
        
        if (!currentStreamTarget || !assistantBubbleElement) {
             console.error("CRITICAL: Could not find newly created assistant bubble elements!");
             endStream(); // Abort
             return;
        }
        // Scroll the new bubble into view, aligning to top/nearest
        assistantBubbleElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    // --- End First Chunk Logic ---

    // Accumulate the raw text chunk
    accumulatedMarkdown += chunk;

    // Display the raw text chunk directly using textContent
    currentStreamTarget.textContent += chunk; 
}

// --- End Stream ---
function endStream() {
    const chatForm = document.getElementById('chat-form');
    if (chatForm) {
        chatForm.classList.remove('streaming'); // Remove class for button state
    }
    
    if (!currentStreamTarget && !isNewStream) {
        // Stream might have ended before first chunk (e.g., error on backend start)
        console.warn('endStream called, but no target was ever created (no chunks received?).');
    } else if (!currentStreamTarget && isNewStream) {
        // Called unnecessarily or after already ended
        console.log('endStream called when stream was not active.');
        return;
    } else {
        // Normal end: Format the accumulated text
        console.log('Stream ended. Final accumulated text:', accumulatedMarkdown);
        if (accumulatedMarkdown) {
            const formattedText = accumulatedMarkdown
                .replace(/\n\n/g, '</p><p>')  // Double newlines -> paragraph breaks
                .replace(/\n/g, '<br>');      // Single newlines -> line breaks
            currentStreamTarget.innerHTML = `<p>${formattedText}</p>`; // Set final formatted HTML
        } else {
             currentStreamTarget.innerHTML = `<p style="font-style: italic; color: #888;">No response content received.</p>`;
        }
    }

    // Re-enable input and hide loading indicator (if applicable)
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('run-stop-button'); // Corrected ID
    // const loadingIndicator = document.getElementById('loading-indicator'); // If you add one

    if (userInput) userInput.disabled = false;
    if (sendButton) sendButton.disabled = false;
    // if (loadingIndicator) loadingIndicator.style.display = 'none'; 

    // Reset state variables AFTER potentially using them
    currentStreamTarget = null; 
    isNewStream = true;         
    accumulatedMarkdown = "";   

    console.log('Stream processing complete and UI elements reset.');
}

// --- Read Chunks from Response Stream ---
async function readChunks(response) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                console.log('Reader finished.');
                // Ensure endStream is called IF it hasn't been already by a [DONE] marker
                if (!isNewStream) {
                    endStream(); 
                }
                break;
            }
            const chunk = decoder.decode(value, { stream: true });
            // appendToStream handles the [DONE] marker internally now
            appendToStream(chunk); 
        }
    } catch (error) {
        console.error('Error reading stream:', error);
        appendToStream(`\n\n<p class="error">Error reading stream response.</p>`);
        if (!isNewStream) {
           endStream(); // Ensure UI resets on read error
        }
    }
}

// Connect to streaming when submit is clicked or Ctrl/Cmd+Enter is pressed
document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('run-stop-button'); // Corrected ID
    const chatMessages = document.getElementById('chat-messages');
    // const loadingIndicator = document.getElementById('loading-indicator'); // If you add one

    if (chatForm && userInput && sendButton && chatMessages) {
        
        // --- Form Submit Handler ---
        chatForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const query = userInput.value.trim();
            if (!query) return;

            // Disable input and show loading indicator
            userInput.disabled = true;
            sendButton.disabled = true;
            chatForm.classList.add('streaming'); // Add class for button style
            // if (loadingIndicator) loadingIndicator.style.display = 'inline-block';

            // --- Create User Message Bubble ---
            const userMessageHtml = `
                <div style="display: flex; justify-content: flex-end; margin-bottom: 1rem;">
                    <div style="max-width: 75%; background-color: #d1e7ff; color: #0d6efd; padding: 10px 15px; border-radius: 18px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); order: 1; margin-left: auto;">
                        <div style="white-space: pre-wrap; word-wrap: break-word;">${query.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</div>
                    </div>
                </div>`;
            chatMessages.insertAdjacentHTML('beforeend', userMessageHtml);
            userInput.value = ''; // Clear input after sending
            chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll down

            // --- Assistant Bubble is created later in appendToStream --- 
            
            // --- Start Streaming Request ---
            startStream(); // Reset stream state, doesn't create target anymore
            fetch('/stream-message?query=' + encodeURIComponent(query))
                .then(response => {
                    if (!response.ok) {
                        // Handle HTTP errors (e.g., 404, 500)
                        response.text().then(text => {
                           console.error(`Streaming error: ${response.status} ${response.statusText}`, text);
                           // Create bubble manually to show error
                           appendToStream(''); // Trigger bubble creation if not already done
                           appendToStream(`\n\n<p class="error">Error: ${response.status} ${response.statusText}. Check server logs.</p>`);
                           endStream();
                        });
                    } else {
                        // Start reading the stream only if response is ok
                        readChunks(response);
                    }
                 })
                 .catch(error => {
                     console.error('Stream fetch/network error:', error);
                     // Create bubble manually to show error
                     appendToStream(''); // Trigger bubble creation if not already done
                     appendToStream(`\n\n<p class="error">Network error: Could not connect.</p>`);
                     endStream(); // Ensure UI resets on fetch error
                 });
        });

        // --- Cmd/Ctrl+Enter Shortcut --- 
        userInput.addEventListener('keydown', function(event) {
            if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
                event.preventDefault(); // Prevent default newline insertion
                chatForm.requestSubmit(); // Trigger form submission
            }
        });

    } else {
        console.error('Could not find one or more essential elements: #chat-form, #user-input, #run-stop-button, #chat-messages');
    }
});