function setQuery(text) {
    const textarea = document.getElementById('user-input');
    if (textarea) {
      textarea.value = text;
      textarea.focus();
      textarea.setSelectionRange(textarea.value.length, textarea.value.length);
    } else { 
      console.error("Could not find textarea with id 'user-input'"); 
    }
  }
  
  function autoGrowTextarea(element) {
    element.style.height = 'auto';
    element.style.height = (element.scrollHeight) + 'px';
  }
  
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
      toggleBtn.style.backgroundColor = '#1a73e8';
      buttonsContainer.style.display = 'block';
      console.log('Showing suggestions');
    } else {
      // Hide suggestions
      container.classList.add('suggestions-collapsed');
      toggleBtn.textContent = 'Show Suggestions ▼';
      toggleBtn.style.backgroundColor = '#1a73e8';
      buttonsContainer.style.display = 'none';
      console.log('Hiding suggestions');
    }
  }
  
  document.addEventListener('DOMContentLoaded', function() {
      const textarea = document.getElementById('user-input');
      if(textarea) {
          textarea.classList.add('auto-grow-textarea');
          textarea.addEventListener('input', function() {
              autoGrowTextarea(this);
          });
          autoGrowTextarea(textarea);
      }
      
      // Initialize mobile suggestions
      const isMobile = window.matchMedia('(max-width: 600px)').matches;
      console.log('Is mobile device:', isMobile);
      
      setTimeout(function() {
          if (isMobile) {
              const container = document.getElementById('suggestions-container');
              const toggleBtn = document.querySelector('.suggestions-toggle');
              const buttonsContainer = document.getElementById('suggestions-buttons');
              
              if (container && toggleBtn && buttonsContainer) {
                  console.log('Mobile device detected, initializing suggestions toggle');
                  container.classList.add('suggestions-collapsed');
                  toggleBtn.style.display = 'block';
                  buttonsContainer.style.display = 'none';
                  toggleBtn.setAttribute('style', 'display: block !important; margin: 5px auto; padding: 6px 12px; font-weight: bold;');
              } else {
                  console.error('Mobile setup: One or more required elements not found');
              }
          }
      }, 100);
      
      // Attach HTMX event listeners after DOM is ready
      if (document.body) { 
          document.body.addEventListener('htmx:afterSwap', function(event) {
               if (event.detail.target.id === 'user-input' || event.detail.elt.id === 'user-input') {
                   const textarea = document.getElementById('user-input');
                   if (textarea) autoGrowTextarea(textarea);
               }
          });
      } else {
          console.error("document.body not available even after DOMContentLoaded?");
      }

      document.addEventListener('htmx:afterSwap', function(event) {
          if (event.detail.target.id === 'chat-messages' || event.detail.target.closest('#chat-messages')) {
              setTimeout(function() {
                  const chatMessages = document.getElementById('chat-messages');
                  if (chatMessages) { chatMessages.scrollTop = chatMessages.scrollHeight; }
              }, 100);
          }
      });
  });