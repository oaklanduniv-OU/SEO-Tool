// Get the theme link and toggle button
const themeLink = document.getElementById('theme-link');
const toggleIcon = document.getElementById('theme-toggle-btn');

// Check localStorage for stored theme preference
const savedTheme = localStorage.getItem('theme');
if (savedTheme) {
  themeLink.setAttribute('href', savedTheme);

  if (savedTheme === '/static/css/dark-mode.css') {
    toggleIcon.style.color = '#ffcc00'; // Lightbulb color for dark mode
  } else {
    toggleIcon.style.color = '#333'; // Lightbulb color for light mode
  }
} else {
  // Default theme (dark mode)
  themeLink.setAttribute('href', '/static/css/dark-mode.css');
  document.body.className = "dark-theme"
  toggleIcon.style.color = '#ffcc00'; // Lightbulb color for dark mode

}

// Toggle theme on button click
toggleIcon.addEventListener('click', () => {
  if (themeLink.getAttribute('href') === '/static/css/dark-mode.css') {
    themeLink.setAttribute('href', '/static/css/light-mode.css');
    document.body.className = ""
    localStorage.setItem('theme', '/static/css/light-mode.css');
    toggleIcon.style.color = '#333'; // Change to light mode color
  } else {
    themeLink.setAttribute('href', '/static/css/dark-mode.css');
    document.body.className = "dark-theme"
    localStorage.setItem('theme', '/static/css/dark-mode.css');
    
    toggleIcon.style.color = '#ffcc00'; // Change to dark mode color
  }
});
