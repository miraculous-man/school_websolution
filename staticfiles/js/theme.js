document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('themeToggle');
    const htmlElement = document.documentElement;
    
    function applyTheme(themeName) {
        if (themeName === 'dark') {
            htmlElement.classList.add('dark-mode');
            htmlElement.classList.remove('theme-auto');
            localStorage.setItem('theme', 'dark');
        } else if (themeName === 'light') {
            htmlElement.classList.remove('dark-mode');
            htmlElement.classList.remove('theme-auto');
            localStorage.setItem('theme', 'light');
        } else {
            htmlElement.classList.add('theme-auto');
            htmlElement.classList.remove('dark-mode');
            localStorage.setItem('theme', 'auto');
        }
    }
    
    function initializeTheme() {
        const savedTheme = localStorage.getItem('theme') || 'auto';
        applyTheme(savedTheme);
        
        if (themeToggle) {
            themeToggle.addEventListener('change', function() {
                const newTheme = this.value;
                applyTheme(newTheme);
            });
        }
    }
    
    if (themeToggle) {
        initializeTheme();
    }
});
