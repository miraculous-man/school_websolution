document.addEventListener('DOMContentLoaded', function() {
    // --- Theme Logic ---
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

    // --- Animation Logic (Scroll Reveal & Fade In) ---
    const revealElements = document.querySelectorAll('.card, .stat-card, .table-responsive, .alert');
    
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const revealObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('reveal-visible');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    revealElements.forEach(el => {
        el.classList.add('reveal-hidden');
        revealObserver.observe(el);
    });

    // Add staggered animation to sidebar links
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    navLinks.forEach((link, index) => {
        link.style.opacity = '0';
        link.style.transform = 'translateX(-20px)';
        link.style.transition = `all 0.3s ease ${index * 0.05}s`;
        setTimeout(() => {
            link.style.opacity = '1';
            link.style.transform = 'translateX(0)';
        }, 100);
    });
});
