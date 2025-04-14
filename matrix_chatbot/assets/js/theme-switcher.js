/**
 * Theme Switcher
 * Manages theme preferences between light, dark, and system settings.
 */

// Define the possible theme values
const THEMES = {
  LIGHT: 'light',
  DARK: 'dark',
  SYSTEM: 'system'
};

// Initialize theme from localStorage or default to system
function initTheme() {
  // Get stored theme from localStorage or use system as default
  const storedTheme = localStorage.getItem('theme') || THEMES.SYSTEM;
  setTheme(storedTheme);
  
  // Set up menu and toggle interactions
  setupMenuInteractions();
  
  // Initial icon update on load
  updateMoonIcon();
  
  // Listen for system preference changes
  if (window.matchMedia) {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Add listener for system preference changes
    try {
      // Chrome & Firefox
      mediaQuery.addEventListener('change', ({ matches }) => {
        // Only update if the theme is set to "system"
        if (document.documentElement.getAttribute('data-theme') === THEMES.SYSTEM) {
          updateThemeClass(matches ? THEMES.DARK : THEMES.LIGHT);
          updateMoonIcon(); // Update icon when system preference changes
        }
      });
    } catch (e) {
      // Safari fallback (older versions)
      mediaQuery.addListener(({ matches }) => {
        if (document.documentElement.getAttribute('data-theme') === THEMES.SYSTEM) {
          updateThemeClass(matches ? THEMES.DARK : THEMES.LIGHT);
          updateMoonIcon(); // Update icon when system preference changes
        }
      });
    }
  }
}

// Set theme and update UI
function setTheme(theme) {
  if (!Object.values(THEMES).includes(theme)) {
    console.error('Invalid theme value:', theme);
    theme = THEMES.SYSTEM;
  }
  
  // Store in localStorage
  localStorage.setItem('theme', theme);
  
  // Set data-theme attribute on the html element
  document.documentElement.setAttribute('data-theme', theme);
  
  // Update menu items to show active state
  updateActiveMenuItem(theme);
  
  // Update the moon/sun icon
  updateMoonIcon();
  
  // If using system theme, determine if it's dark or light
  if (theme === THEMES.SYSTEM) {
    const systemPrefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    updateThemeClass(systemPrefersDark ? THEMES.DARK : THEMES.LIGHT);
  } else {
    // Otherwise use the explicitly set theme
    updateThemeClass(theme);
  }
  
  // Trigger minimal layout refresh if needed
  refreshLayout();
}

// Update menu items to show active state
function updateActiveMenuItem(theme) {
  // Get all theme menu items
  const menuItems = document.querySelectorAll('.theme-menu-item');
  
  // Set the matching one as active
  menuItems.forEach(item => {
    if (item.getAttribute('data-theme-value') === theme) {
      item.classList.add('active-theme');
    } else {
      item.classList.remove('active-theme');
    }
  });
}

// Update the moon/sun icon based on current theme
function updateMoonIcon() {
  const themeToggle = document.getElementById('theme-toggle');
  if (!themeToggle) return;
  
  const currentTheme = localStorage.getItem('theme') || THEMES.SYSTEM;
  let isEffectivelyDark = false;
  
  if (currentTheme === THEMES.DARK) {
    isEffectivelyDark = true;
  } else if (currentTheme === THEMES.SYSTEM) {
    isEffectivelyDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  
  // Change icon based on theme
  themeToggle.textContent = isEffectivelyDark ? '☀️' : '🌓'; // Sun for dark, Moon for light
  themeToggle.setAttribute('title', isEffectivelyDark ? 'Switch to Light Theme' : 'Switch to Dark Theme');
}

// Helper function to update the class on body for theme-specific styling
function updateThemeClass(theme) {
  // Just an additional helper if needed for specific styling
  document.body.classList.remove('theme-light', 'theme-dark');
  document.body.classList.add(`theme-${theme}`);
  
  // REMOVED: No longer setting inline styles directly on HTML element
  // Let CSS handle all theme variable values based on the data-theme attribute
}

// Toggle between themes in sequence: light → dark → system → light...
function cycleTheme() {
  const currentTheme = localStorage.getItem('theme') || THEMES.SYSTEM;
  
  switch (currentTheme) {
    case THEMES.LIGHT:
      setTheme(THEMES.DARK);
      break;
    case THEMES.DARK:
      setTheme(THEMES.SYSTEM);
      break;
    case THEMES.SYSTEM:
    default:
      setTheme(THEMES.LIGHT);
      break;
  }
  
  // Trigger minimal layout refresh if needed
  refreshLayout();
}

// Simple function to refresh the page layout if needed
function refreshLayout() {
  // Only perform minimal DOM manipulation if needed
  // For example, we might need to trigger a layout recalculation
  // in certain browsers, but we'll avoid direct style manipulation
  
  // Force a layout recalculation in problematic browsers
  if (document.documentElement.offsetHeight) {
    // This read of offsetHeight forces layout recalculation
    // But doesn't manipulate any styles directly
  }
}

// Set up menu interactions for the hamburger menu and theme selection
function setupMenuInteractions() {
  const menuToggle = document.getElementById('menu-toggle');
  const settingsMenu = document.getElementById('settings-menu');
  const themeToggle = document.getElementById('theme-toggle');
  const themeMenuItems = document.querySelectorAll('.theme-menu-item');
  
  // Menu toggle logic
  if (menuToggle && settingsMenu) {
    menuToggle.addEventListener('click', (event) => {
      event.stopPropagation(); // Prevent click from closing menu immediately
      settingsMenu.classList.toggle('visible');
    });
  
    // Close menu when clicking outside
    document.addEventListener('click', (event) => {
      if (settingsMenu.classList.contains('visible') && 
          !settingsMenu.contains(event.target) && 
          !menuToggle.contains(event.target)) {
        settingsMenu.classList.remove('visible');
      }
    });
  }
  
  // Theme menu item click logic
  themeMenuItems.forEach(item => {
    item.addEventListener('click', (event) => {
      event.preventDefault();
      const selectedTheme = item.getAttribute('data-theme-value');
      if (selectedTheme) {
        console.log("Menu selected:", selectedTheme);
        setTheme(selectedTheme);
        if (settingsMenu) {
          settingsMenu.classList.remove('visible'); // Close menu
        }
      }
    });
  });
  
  // Moon/sun icon toggle logic
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const currentTheme = localStorage.getItem('theme') || THEMES.SYSTEM;
      let newTheme;
      
      if (currentTheme === THEMES.SYSTEM) {
        // If system, check effective scheme and toggle to opposite *explicit* theme
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        newTheme = systemPrefersDark ? THEMES.LIGHT : THEMES.DARK;
      } else if (currentTheme === THEMES.LIGHT) {
        newTheme = THEMES.DARK;
      } else { // DARK
        newTheme = THEMES.LIGHT;
      }
      
      console.log("Moon toggle:", newTheme);
      setTheme(newTheme);
    });
  }
}

// Function to explicitly clear any inline styles from the HTML element
function clearInlineStyles() {
  console.log('Clearing inline styles from HTML element');
  // Get current style attribute value
  const currentStyle = document.documentElement.getAttribute('style');
  if (currentStyle) {
    console.log('Found inline styles, removing:', currentStyle);
    // Remove the style attribute completely
    document.documentElement.removeAttribute('style');
  } else {
    console.log('No inline styles found on HTML element');
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  // Clear any inline styles first
  clearInlineStyles();
  
  // Initialize the theme
  initTheme();
  
  // Add a safety measure - clear inline styles again after a slight delay
  // This handles any race conditions where styles might be set after init
  setTimeout(clearInlineStyles, 100);
});
