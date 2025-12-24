/**
 * Simple and Reliable AOS Initialization
 * Based on working examples from production websites
 */

(function() {
    'use strict';

    /**
     * Initialize AOS with proven settings
     * Only use basic, well-tested configuration
     */
    function initAOS() {
        if (typeof AOS === 'undefined') {
            console.warn('AOS library not loaded');
            return;
        }

        // Initialize with minimal, proven settings
        AOS.init({
            duration: 800,        // Animation duration in ms
            offset: 120,          // Offset in px when to trigger animation
            once: false,          // Allow animations on scroll both ways
            easing: 'ease-in-out-cubic',  // Smooth easing
            disable: false,       // Don't disable on mobile
            startEvent: 'DOMContentLoaded',
            animatedClassName: 'aos-animate',
            initClassName: 'aos-init'
        });

        // Refresh AOS after init to catch all elements
        setTimeout(() => {
            AOS.refresh();
        }, 100);
    }

    /**
     * Refresh AOS on window load
     * This ensures all images are loaded before AOS calculates positions
     */
    function refreshOnLoad() {
        window.addEventListener('load', function() {
            if (typeof AOS !== 'undefined') {
                AOS.refresh();
            }
        });
    }

    /**
     * Handle dynamic content - refresh AOS periodically
     * In case new elements are added dynamically
     */
    function handleDynamicContent() {
        // Refresh on resize (for responsive designs)
        let resizeTimer;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(function() {
                if (typeof AOS !== 'undefined') {
                    AOS.refresh();
                }
            }, 250);
        });
    }

    /**
     * Add optional smooth scroll behavior
     * for anchor links
     */
    function smoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                if (href !== '#' && document.querySelector(href)) {
                    e.preventDefault();
                    const target = document.querySelector(href);
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
    }

    /**
     * Main initialization function
     * Called when DOM is ready
     */
    function init() {
        console.log('Initializing AOS...');
        
        // Ensure we wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                initAOS();
                refreshOnLoad();
                handleDynamicContent();
                smoothScroll();
            });
        } else {
            // DOM is already loaded
            initAOS();
            refreshOnLoad();
            handleDynamicContent();
            smoothScroll();
        }
    }

    // Start initialization
    init();

    // Also refresh on visible change (when tab comes back to focus)
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden && typeof AOS !== 'undefined') {
            AOS.refresh();
        }
    });

})();
