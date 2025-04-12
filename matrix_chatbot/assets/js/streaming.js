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
    // This is sent manually by the Python backend for the "done" type
    if (chunk === '[DONE]') {
        endStream();
        return;
    }
    
    // The backend now sends text chunks directly without JSON structure
    // The formatting is handled server-side

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

    // --- Render incrementally for visual streaming --- 
    if (currentStreamTarget) {
        // 1. Convert Markdown bold to HTML strong tags
        let formattedText = accumulatedMarkdown.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // 2. Convert newlines to paragraphs/breaks (simplified for streaming)
        //    Using <br> for all newlines during streaming is visually okay.
        //    We could refine paragraph logic here if needed, but <br> is simpler.
        formattedText = formattedText.replace(/\n/g, '<br>'); 
        
        // Update the innerHTML with the processed content so far
        currentStreamTarget.innerHTML = formattedText; 
        
        // Optional: Keep scrolled to bottom if needed
        // currentStreamTarget.parentElement.parentElement.scrollIntoView({ behavior: 'smooth', block: 'end' }); 
    }
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
        // Normal end: Formatting is now done incrementally in appendToStream.
        // We can log the final accumulated text for debugging if needed.
        console.log('Stream ended. Final accumulated text (raw):', accumulatedMarkdown);
        // Optional: Could do a final, more robust formatting pass here if the incremental one is imperfect.
        // e.g., ensure it's wrapped in <p> tags properly if needed based on final content.
        if (currentStreamTarget && !currentStreamTarget.innerHTML.startsWith('<p>')) {
             // Basic check: Wrap if not already in a paragraph
             // Note: The incremental rendering might already handle this implicitly
             // currentStreamTarget.innerHTML = `<p>${currentStreamTarget.innerHTML}</p>`; 
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
    const sendButton = document.getElementById('run-stop-button');
    const chatMessages = document.getElementById('chat-messages');
    const chatContainer = document.getElementById('chat-container');
    // Find the reset button using its ID instead of HTMX attributes
    const resetButton = document.getElementById('reset-chat-button');
    
    // --- Set up manual reset button handling to completely bypass HTMX ---
    if (resetButton) {
        console.log('Reset button found, setting up manual click handler...');
        
        resetButton.addEventListener('click', function(event) {
            event.preventDefault(); // Prevent default button action
            console.log('Reset button clicked. Manual handling engaged.');

            // Handle confirmation dialog
            if (!confirm("Are you sure you want to reset the chat and start over?")) {
                console.log('Reset cancelled by user.');
                return; // Stop if user cancels
            }
            console.log('User confirmed reset.');

            // 1. Disable form inputs immediately
            userInput.disabled = true;
            sendButton.disabled = true;
            resetButton.disabled = true;
            // Add visual indicator
            resetButton.textContent = 'Resetting...';

            // 2. Clear URL Query Parameters BEFORE fetch
            const currentUrl = new URL(window.location.href);
            if (currentUrl.search !== '') {
                console.log('Current URL has query parameters:', currentUrl.search);
                console.log('Clearing query parameters from browser history before fetch...');
                history.replaceState(null, '', currentUrl.pathname);
                console.log('Browser history URL state replaced with:', currentUrl.pathname);
            } else {
                console.log('No query parameters to clear.');
            }
            
            // 3. Clear Frontend Chat State Storage
            console.log("Clearing potential chat history from localStorage/sessionStorage...");
            try {
                // Clear any stored chat messages or state
                localStorage.clear();  // Clears ALL localStorage for this origin
                sessionStorage.clear(); // Clears ALL sessionStorage for this origin
                
                // Also directly clear the chat-messages div for immediate visual feedback
                if (chatMessages) {
                    console.log("Clearing chat messages from DOM before fetch...");
                    // Keep only the welcome message (or clear completely and let the reload handle it)
                    chatMessages.innerHTML = '';
                }
                
                console.log("Cleared localStorage, sessionStorage, and current chat messages.");
            } catch (e) {
                console.error("Error clearing storage:", e);
            }

            // 4. Manually Fetch the Reset Endpoint
            console.log('Making fetch POST to /reset-chat...');
            fetch('/reset-chat', {
                method: 'POST',
                headers: {
                    'Accept': '*/*',
                }
            })
            .then(response => {
                console.log('Reset response received. Status:', response.status);
                // Check for HX-Refresh header
                const hxRefresh = response.headers.get('HX-Refresh');
                console.log('HX-Refresh header value:', hxRefresh);
                
                if (hxRefresh === 'true') {
                    console.log('HX-Refresh: true header detected. Manually reloading page.');
                    // Manually trigger reload
                    window.location.reload();
                    return; // Execution stops due to reload
                } else {
                    // Handle unexpected response
                    console.warn('Reset request completed but did not trigger refresh. Status:', response.status);
                    // Re-enable form
                    resetButton.textContent = 'Reset Chat';
                    resetButton.disabled = false;
                    userInput.disabled = false;
                    sendButton.disabled = false;
                    return response.text(); // Process body if needed
                }
            })
            .then(text => { // Only runs if no reload happened
                if (text) {
                    console.log("Response body (no reload):", text);
                }
            })
            .catch(error => {
                console.error('Fetch error during reset request:', error);
                alert('An error occurred during the reset request. Please try again.');
                // Re-enable form on error
                resetButton.textContent = 'Reset Chat';
                resetButton.disabled = false;
                userInput.disabled = false;
                sendButton.disabled = false;
            });

        }); // End of click listener
        
        console.log('Reset button manual handler configured successfully.');
    } else {
        console.error("Could not find reset button with ID='reset-chat-button'");
    }

    if (chatForm && userInput && sendButton && chatMessages) {
        // --- Temporarily Disable Form Elements to Prevent Race Condition on Page Load ---
        console.log("Disabling form inputs briefly during initialization...");
        userInput.disabled = true;
        sendButton.disabled = true;
        
        // Re-enable after a short delay to ensure HTMX has fully initialized
        setTimeout(() => {
            console.log("Re-enabling form inputs.");
            userInput.disabled = false;
            sendButton.disabled = false;
            
            // Optional: Re-focus the input if it had autofocus
            if (userInput.hasAttribute('autofocus')) {
                userInput.focus();
            }
        }, 200); // Short delay to allow all JavaScript and HTMX to initialize
        
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