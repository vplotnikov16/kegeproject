/**
 * Scroll-based animations for About page
 * Creates smooth parallax and reveal effects as user scrolls
 */

(function() {
    'use strict';

    // Configuration
    const config = {
        rootMargin: '50px 0px -100px 0px',  // Trigger before element enters viewport
        threshold: 0.1,
    };

    // Create Intersection Observer
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Add active class to trigger animation
                entry.target.classList.add('active');
                // Stop observing this element (animation only triggers once)
                observer.unobserve(entry.target);
            }
        });
    }, config);

    // Observe all elements with data-scroll attribute
    document.addEventListener('DOMContentLoaded', () => {
        const scrollElements = document.querySelectorAll('[data-scroll]');
        scrollElements.forEach(element => {
            observer.observe(element);
        });
    });

    /**
     * Parallax effect for hero section decoration
     * Moves background elements based on scroll position
     */
    function setupParallax() {
        const parallaxElements = document.querySelectorAll('[data-scroll-transform]');
        
        if (parallaxElements.length === 0) return;

        window.addEventListener('scroll', () => {
            parallaxElements.forEach(element => {
                const scrollPosition = window.scrollY;
                const elementOffset = element.offsetTop;
                const distance = scrollPosition - elementOffset;
                
                // Create parallax effect: move slower than scroll
                const parallaxValue = distance * 0.5;
                element.style.transform = `translateY(${parallaxValue}px)`;
            });
        }, { passive: true });
    }

    /**
     * Smooth scroll animation for hero hero elements
     * Creates a flowing effect as page loads
     */
    function setupHeroAnimation() {
        const heroElements = document.querySelectorAll('.about-hero [data-scroll]');
        
        heroElements.forEach((element, index) => {
            // Stagger animation for hero elements
            element.style.setProperty('--delay', `${index * 0.1}s`);
            element.classList.add('active');
        });
    }

    /**
     * Parallax effect based on mouse/scroll position
     * Creates depth sensation
     */
    function setupAdvancedParallax() {
        let ticking = false;
        let lastScrollY = 0;

        window.addEventListener('scroll', () => {
            lastScrollY = window.scrollY;
            if (!ticking) {
                window.requestAnimationFrame(() => {
                    updateParallax(lastScrollY);
                    ticking = false;
                });
                ticking = true;
            }
        }, { passive: true });
    }

    /**
     * Update parallax position based on scroll
     */
    function updateParallax(scrollY) {
        const heroDecoration = document.querySelector('.hero-decoration');
        if (heroDecoration) {
            heroDecoration.style.transform = `translateY(${scrollY * 0.3}px)`;
        }
    }

    /**
     * Smooth scroll for anchor links
     */
    function setupSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    /**
     * Add glow effect on hover for cards
     */
    function setupCardGlow() {
        const cards = document.querySelectorAll('.uni-card, .developer-card, .feature-item, .supervisor-card');
        
        cards.forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                card.style.setProperty('--mouse-x', `${x}px`);
                card.style.setProperty('--mouse-y', `${y}px`);
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.setProperty('--mouse-x', 'auto');
                card.style.setProperty('--mouse-y', 'auto');
            });
        });
    }

    /**
     * Reveal text animation - animate text appearance letter by letter
     */
    function setupTextReveal() {
        const titles = document.querySelectorAll('.section-header h2, .hero-title');
        
        titles.forEach(title => {
            const text = title.textContent;
            let innerHTML = '';
            
            // Don't split if already split or element is empty
            if (title.innerHTML === text) {
                title.innerHTML = text
                    .split('')
                    .map(char => `<span class="char">${char}</span>`)
                    .join('');
            }
        });
    }

    /**
     * Counter animation - animate numbers counting up
     */
    function animateCounter(element, target, duration = 1000) {
        let current = 0;
        const increment = target / (duration / 16);
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                element.textContent = target;
                clearInterval(timer);
            } else {
                element.textContent = Math.floor(current);
            }
        }, 16);
    }

    /**
     * Initialize all animations
     */
    function init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                setupHeroAnimation();
                setupAdvancedParallax();
                setupSmoothScroll();
                setupCardGlow();
                setupTextReveal();
            });
        } else {
            setupHeroAnimation();
            setupAdvancedParallax();
            setupSmoothScroll();
            setupCardGlow();
            setupTextReveal();
        }
    }

    // Start initialization
    init();

})();
