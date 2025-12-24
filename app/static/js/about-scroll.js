/**
 * Advanced Scroll-Based Trajectory Animations
 * Elements follow predefined paths based on scroll position
 * Creates immersive, reversible animations
 */

(function() {
    'use strict';

    // Initialize AOS library
    AOS.init({
        duration: 1000,
        offset: 100,
        once: false,  // Allow animations to play multiple times (reversible)
        easing: 'ease-in-out-cubic',
        disable: false,
        startEvent: 'DOMContentLoaded',
        animatedClassName: 'aos-animate'
    });

    /**
     * Advanced scroll trajectory engine
     * Calculates element positions based on scroll progress
     */
    class ScrollTrajectoryEngine {
        constructor() {
            this.elements = [];
            this.scrollProgress = 0;
            this.ticking = false;
            this.init();
        }

        init() {
            // Register all animated elements with trajectories
            this.registerTrajectories();
            
            // Attach scroll listener
            window.addEventListener('scroll', () => this.onScroll(), { passive: true });
            
            // Initial position calculation
            this.updateTrajectories();
        }

        registerTrajectories() {
            // Section-specific trajectory configurations
            const trajectories = [
                // Hero section trajectories
                { selector: '.blob-1', trajectory: 'floating-blob', intensity: 1.2 },
                { selector: '.blob-2', trajectory: 'floating-blob', intensity: 0.9 },
                { selector: '.blob-3', trajectory: 'floating-blob', intensity: 1 },
                
                // University cards - staggered rise
                { selector: '.uni-card:nth-child(1)', trajectory: 'staggered-rise', delay: 0 },
                { selector: '.uni-card:nth-child(2)', trajectory: 'staggered-rise', delay: 100 },
                { selector: '.uni-card:nth-child(3)', trajectory: 'staggered-rise', delay: 200 },
                
                // Developer cards - rotating orbit
                { selector: '.developer-card', trajectory: 'orbit-animation', intensity: 0.8 },
                
                // Feature cards - wave motion
                { selector: '.feature-card', trajectory: 'wave-motion', intensity: 1 }
            ];

            trajectories.forEach(config => {
                const elements = document.querySelectorAll(config.selector);
                elements.forEach((element, index) => {
                    this.elements.push({
                        element,
                        ...config,
                        index,
                        baseX: element.offsetLeft,
                        baseY: element.offsetTop
                    });
                });
            });
        }

        /**
         * Handle scroll events with trajectory updates
         */
        onScroll() {
            if (!this.ticking) {
                window.requestAnimationFrame(() => {
                    this.updateTrajectories();
                    this.ticking = false;
                });
                this.ticking = true;
            }
        }

        /**
         * Calculate scroll progress (0 to 1)
         */
        getScrollProgress() {
            const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
            return Math.max(0, Math.min(1, window.scrollY / totalHeight));
        }

        /**
         * Update all element trajectories
         */
        updateTrajectories() {
            const scrollProgress = this.getScrollProgress();
            const scrollY = window.scrollY;

            this.elements.forEach(config => {
                const { element, trajectory, intensity = 1, index = 0, delay = 0 } = config;

                // Calculate trajectory based on type
                let transform = this.calculateTrajectory(
                    trajectory,
                    scrollProgress,
                    scrollY,
                    intensity,
                    index,
                    delay
                );

                // Apply transform
                element.style.transform = transform;
                element.style.willChange = 'transform';
            });
        }

        /**
         * Calculate trajectory based on animation type
         */
        calculateTrajectory(type, progress, scrollY, intensity, index, delay) {
            switch(type) {
                case 'floating-blob':
                    return this.floatingBlobTrajectory(progress, intensity);
                
                case 'staggered-rise':
                    return this.staggeredRiseTrajectory(progress, index, delay);
                
                case 'orbit-animation':
                    return this.orbitTrajectory(progress, index, intensity);
                
                case 'wave-motion':
                    return this.waveTrajectory(progress, index, intensity);
                
                default:
                    return 'translate(0, 0) scale(1)';
            }
        }

        /**
         * Floating blob animation
         * Elements gently float up and down with rotation
         */
        floatingBlobTrajectory(progress, intensity) {
            const offsetY = Math.sin(progress * Math.PI * 4) * 40 * intensity;
            const offsetX = Math.cos(progress * Math.PI * 3) * 30 * intensity;
            const rotation = progress * 360 * intensity;
            const scale = 1 + Math.sin(progress * Math.PI * 2) * 0.2 * intensity;
            
            return `translate(${offsetX}px, ${offsetY}px) rotate(${rotation}deg) scale(${scale})`;
        }

        /**
         * Staggered rise animation
         * Elements move upward with staggered timing
         */
        staggeredRiseTrajectory(progress, index, delay) {
            // Adjust progress for stagger effect
            const adjustedProgress = Math.max(0, progress - (delay / 2000));
            const normalizedProgress = Math.min(1, adjustedProgress * 1.5);
            
            const offsetY = -normalizedProgress * 100;
            const rotation = normalizedProgress * 10;
            const opacity = Math.max(0, Math.min(1, normalizedProgress));
            const scale = 0.8 + normalizedProgress * 0.2;
            
            return `translateY(${offsetY}px) rotateX(${rotation}deg) scale(${scale})`;
        }

        /**
         * Orbit animation
         * Elements move in circular orbits
         */
        orbitTrajectory(progress, index, intensity) {
            const angle = progress * Math.PI * 4 + (index * Math.PI / 3);
            const radius = 50 * intensity;
            const offsetX = Math.cos(angle) * radius;
            const offsetY = Math.sin(angle) * radius * 0.5;
            const scale = 1 + Math.sin(angle) * 0.15;
            const rotation = angle * 180 / Math.PI;
            
            return `translate(${offsetX}px, ${offsetY}px) rotate(${rotation}deg) scale(${scale})`;
        }

        /**
         * Wave motion animation
         * Elements move in wave patterns (horizontal)
         */
        waveTrajectory(progress, index, intensity) {
            const waveOffset = Math.sin((progress * Math.PI * 4) + (index * Math.PI / 3)) * 60 * intensity;
            const verticalOffset = Math.cos((progress * Math.PI * 2) + index) * 30 * intensity;
            const skewX = Math.sin(progress * Math.PI * 2) * 5;
            const scale = 1 + Math.abs(Math.sin(progress * Math.PI * 2)) * 0.1;
            
            return `translateX(${waveOffset}px) translateY(${verticalOffset}px) skewX(${skewX}deg) scale(${scale})`;
        }
    }

    /**
     * Color shifting animation engine
     * Elements change colors based on scroll position
     */
    class ColorShiftEngine {
        constructor() {
            this.init();
        }

        init() {
            window.addEventListener('scroll', () => this.updateColors(), { passive: true });
        }

        updateColors() {
            const scrollProgress = window.scrollY / (document.documentElement.scrollHeight - window.innerHeight);
            const cards = document.querySelectorAll('.uni-card, .feature-card');
            
            cards.forEach((card, index) => {
                const hue = (scrollProgress * 360 + index * 30) % 360;
                const saturation = 60 + Math.sin(scrollProgress * Math.PI * 2) * 20;
                const lightness = 50 + Math.cos((scrollProgress * Math.PI * 2) + index) * 10;
                
                // Apply color shift to card accents
                const accentColor = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
                card.style.setProperty('--accent-color', accentColor);
            });
        }
    }

    /**
     * Parallax depth effect
     * Different layers move at different speeds
     */
    class ParallaxEngine {
        constructor() {
            this.init();
        }

        init() {
            window.addEventListener('scroll', () => this.updateParallax(), { passive: true });
        }

        updateParallax() {
            const scrollY = window.scrollY;
            
            // Hero background parallax
            const heroBackground = document.querySelector('.hero-background');
            if (heroBackground) {
                heroBackground.style.transform = `translateY(${scrollY * 0.5}px)`;
            }

            // Section backgrounds
            const sections = document.querySelectorAll('section');
            sections.forEach(section => {
                const rect = section.getBoundingClientRect();
                const sectionProgress = 1 - (rect.top / window.innerHeight);
                const parallaxValue = Math.max(-50, Math.min(50, sectionProgress * 30));
                
                section.style.backgroundPosition = `0 ${parallaxValue}px`;
            });
        }
    }

    /**
     * Text reveal animation
     * Text animates character by character on scroll
     */
    function setupTextReveal() {
        const titles = document.querySelectorAll('h1, h2, h3');
        
        titles.forEach(title => {
            // Skip if already processed
            if (title.classList.contains('text-revealed')) return;
            
            const text = title.textContent;
            const chars = text.split('');
            
            title.innerHTML = chars
                .map((char, i) => `<span class="char" style="--char-index: ${i}">${char}</span>`)
                .join('');
            
            title.classList.add('text-revealed');
        });
    }

    /**
     * Mouse move parallax for hero section
     * Adds interactivity on mouse movement
     */
    function setupMouseParallax() {
        const heroSection = document.querySelector('.section-hero');
        if (!heroSection) return;

        document.addEventListener('mousemove', (e) => {
            const x = (e.clientX / window.innerWidth) - 0.5;
            const y = (e.clientY / window.innerHeight) - 0.5;
            
            const blobs = heroSection.querySelectorAll('.blob');
            blobs.forEach((blob, index) => {
                const intensity = (index + 1) * 20;
                blob.style.transform = `translate(${x * intensity}px, ${y * intensity}px)`;
            });
        });
    }

    /**
     * Refresh AOS on load
     */
    function refreshAOS() {
        if (typeof AOS !== 'undefined') {
            setTimeout(() => {
                AOS.refresh();
            }, 200);
        }
    }

    /**
     * Initialize all systems
     */
    function init() {
        // Wait for DOM and AOS library to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                setupTextReveal();
                setupMouseParallax();
                new ScrollTrajectoryEngine();
                new ParallaxEngine();
                new ColorShiftEngine();
                refreshAOS();
            });
        } else {
            setupTextReveal();
            setupMouseParallax();
            new ScrollTrajectoryEngine();
            new ParallaxEngine();
            new ColorShiftEngine();
            refreshAOS();
        }
    }

    // Initialize on script load
    init();

})();
