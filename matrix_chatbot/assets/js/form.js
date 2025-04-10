document.addEventListener('DOMContentLoaded', function() {
    console.log("[Cmd+Enter] DOM loaded. Setting up listener on BODY.");

    document.body.addEventListener('keydown', function(event) {
        if (event.target.id !== 'user-input') {
            return;
        }

        const chatForm = document.getElementById('chat-form');
        const textarea = event.target;

        if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
            console.log("[Cmd+Enter] Cmd/Ctrl+Enter DETECTED on #user-input!");
            event.preventDefault();

            if (!chatForm) {
                console.error("[Cmd+Enter] Form with id 'chat-form' not found when trying to submit!");
                return;
            }

            if (window.htmx && typeof window.htmx.trigger === 'function') {
               console.log("[Cmd+Enter] Triggering HTMX submit on form.");
               try {
                   htmx.trigger(chatForm, 'submit');
               } catch (e) {
                   console.error("[Cmd+Enter] Error during htmx.trigger:", e);
               }
            } else {
               console.log("[Cmd+Enter] HTMX trigger not found, using requestSubmit.");
               try {
                  chatForm.requestSubmit();
               } catch (e) {
                  console.error("[Cmd+Enter] Error during requestSubmit:", e);
               }
            }
        }
    });
});

document.addEventListener('click', function(event) {
    const button = event.target.closest('#run-stop-button');
    if (!button) return;

    const form = button.closest('form');
    const stopTextElement = button.querySelector('.stop-text');
    const isStopVisible = stopTextElement && window.getComputedStyle(stopTextElement).display !== 'none';

    if (isStopVisible && form && form.classList.contains('htmx-request')) {
        console.log('Stop button clicked (Stop visible). Form has htmx-request. Attempting DIRECT abort.');

        let xhr = null;
        if (form.htmx && form.htmx.xhr) {
            xhr = form.htmx.xhr;
            console.log('Found XHR on form element.');
        } else if (button.htmx && button.htmx.xhr) {
             xhr = button.htmx.xhr;
             console.log('Found XHR on button element.');
        } else {
             const relatedTarget = document.querySelector(form.getAttribute('hx-target'));
             if (relatedTarget && relatedTarget.htmx && relatedTarget.htmx.xhr) {
                 xhr = relatedTarget.htmx.xhr;
                 console.log('Found XHR on target element:', form.getAttribute('hx-target'));
             }
        }

        if (xhr && typeof xhr.abort === 'function') {
            console.log('Calling xhr.abort() directly.');
            xhr.abort();
            event.preventDefault();
            event.stopPropagation();
        } else {
             console.warn('Could not find active XHR object to abort directly. Trying htmx:abort event as fallback.');
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
            textarea.focus();
        }
    }
}, true);