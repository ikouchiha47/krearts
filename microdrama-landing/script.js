// GSAP Animations
gsap.registerPlugin(ScrollTrigger);

// Initialize animations when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initAnimations();
    initCTATracking();
    initFormHandling();
    initMobileMenu();
    initCarousel();
});

// GSAP Animations
function initAnimations() {
    // Hero animations
    gsap.from('.hero-title-line', {
        opacity: 0,
        y: 50,
        duration: 1,
        stagger: 0.2,
        ease: 'power3.out'
    });

    gsap.from('.hero-subtitle', {
        opacity: 0,
        y: 30,
        duration: 1,
        delay: 0.6,
        ease: 'power3.out'
    });

    gsap.from('.hero-cta', {
        opacity: 0,
        y: 30,
        duration: 1,
        delay: 0.8,
        ease: 'power3.out'
    });

    gsap.from('.hero-stats .stat', {
        opacity: 0,
        y: 30,
        duration: 1,
        delay: 1,
        stagger: 0.1,
        ease: 'power3.out'
    });

    gsap.from('.phone-mockup', {
        opacity: 0,
        x: 100,
        duration: 1.2,
        delay: 0.4,
        ease: 'power3.out'
    });

    // Feature cards animation
    gsap.from('.feature-card', {
        scrollTrigger: {
            trigger: '.features-grid',
            start: 'top 80%',
        },
        opacity: 0,
        y: 50,
        duration: 0.8,
        stagger: 0.15,
        ease: 'power3.out'
    });

    // Steps animation
    gsap.utils.toArray('.step').forEach((step, index) => {
        gsap.from(step, {
            scrollTrigger: {
                trigger: step,
                start: 'top 80%',
            },
            opacity: 0,
            x: index % 2 === 0 ? -100 : 100,
            duration: 1,
            ease: 'power3.out'
        });
    });

    // Example cards animation
    gsap.from('.example-card', {
        scrollTrigger: {
            trigger: '.examples-grid',
            start: 'top 80%',
        },
        opacity: 0,
        y: 50,
        duration: 0.8,
        stagger: 0.2,
        ease: 'power3.out'
    });

    // CTA section animation
    gsap.from('.cta-content', {
        scrollTrigger: {
            trigger: '.cta-section',
            start: 'top 80%',
        },
        opacity: 0,
        y: 50,
        duration: 1,
        ease: 'power3.out'
    });

    // Parallax effect for hero background
    gsap.to('.hero-background::before', {
        scrollTrigger: {
            trigger: '.hero',
            start: 'top top',
            end: 'bottom top',
            scrub: true,
        },
        y: 200,
        ease: 'none'
    });

}

// Carousel functionality
function initCarousel() {
    const panels = document.querySelectorAll('.carousel-panel');
    const dots = document.querySelectorAll('.carousel-dots .dot');
    let currentIndex = 0;

    function showPanel(index) {
        panels.forEach((panel, i) => {
            if (i === index) {
                panel.classList.add('active');
            } else {
                panel.classList.remove('active');
            }
        });

        dots.forEach((dot, i) => {
            if (i === index) {
                dot.classList.add('active');
            } else {
                dot.classList.remove('active');
            }
        });
    }

    // Auto-advance carousel
    setInterval(() => {
        currentIndex = (currentIndex + 1) % panels.length;
        showPanel(currentIndex);
    }, 4000);

    // Dot click handlers
    dots.forEach((dot, index) => {
        dot.addEventListener('click', () => {
            currentIndex = index;
            showPanel(currentIndex);
        });
    });
}

// CTA Click Tracking
function initCTATracking() {
    const ctaButtons = document.querySelectorAll('.cta-track');
    
    ctaButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            const ctaName = button.getAttribute('data-cta');
            trackCTAClick(ctaName);
            
            // Add visual feedback
            gsap.to(button, {
                scale: 0.95,
                duration: 0.1,
                yoyo: true,
                repeat: 1,
                ease: 'power2.inOut'
            });
        });
    });
}

function trackCTAClick(ctaName) {
    // Log to console (in production, send to analytics service)
    console.log(`CTA Clicked: ${ctaName}`);
    console.log(`Timestamp: ${new Date().toISOString()}`);
    console.log(`User Agent: ${navigator.userAgent}`);
    console.log(`Page URL: ${window.location.href}`);
    
    // Store in localStorage for demo purposes
    const clicks = JSON.parse(localStorage.getItem('ctaClicks') || '[]');
    clicks.push({
        cta: ctaName,
        timestamp: new Date().toISOString(),
        url: window.location.href
    });
    localStorage.setItem('ctaClicks', JSON.stringify(clicks));
    
    // In production, send to analytics service:
    // fetch('/api/track', {
    //     method: 'POST',
    //     headers: { 'Content-Type': 'application/json' },
    //     body: JSON.stringify({
    //         event: 'cta_click',
    //         cta: ctaName,
    //         timestamp: new Date().toISOString()
    //     })
    // });
}

// Form Handling
function initFormHandling() {
    const form = document.getElementById('signupForm');
    const emailInput = document.getElementById('email');
    
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const email = emailInput.value.trim();
        
        if (validateEmail(email)) {
            // Track signup
            trackCTAClick('signup-submit');
            
            // Store email (in production, send to backend)
            console.log(`New signup: ${email}`);
            
            // In production, send to backend:
            // fetch('/api/signup', {
            //     method: 'POST',
            //     headers: { 'Content-Type': 'application/json' },
            //     body: JSON.stringify({ email })
            // });
            
            // Show success modal
            showSuccessModal();
            
            // Reset form
            form.reset();
        } else {
            showError('Please enter a valid email address');
        }
    });
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function showError(message) {
    const emailInput = document.getElementById('email');
    emailInput.style.borderColor = '#ef4444';
    
    // Create error message if it doesn't exist
    let errorMsg = document.querySelector('.error-message');
    if (!errorMsg) {
        errorMsg = document.createElement('p');
        errorMsg.className = 'error-message';
        errorMsg.style.color = '#ef4444';
        errorMsg.style.fontSize = '14px';
        errorMsg.style.marginTop = '10px';
        document.querySelector('.form-group').appendChild(errorMsg);
    }
    
    errorMsg.textContent = message;
    
    // Shake animation
    gsap.to(emailInput, {
        x: [-10, 10, -10, 10, 0],
        duration: 0.4,
        ease: 'power2.inOut'
    });
    
    // Reset border color after 3 seconds
    setTimeout(() => {
        emailInput.style.borderColor = '';
        if (errorMsg) errorMsg.remove();
    }, 3000);
}

function showSuccessModal() {
    const modal = document.getElementById('successModal');
    modal.classList.add('active');
    
    // Animate modal content
    gsap.from('.modal-content', {
        scale: 0.8,
        opacity: 0,
        duration: 0.3,
        ease: 'back.out(1.7)'
    });
}

function closeModal() {
    const modal = document.getElementById('successModal');
    
    gsap.to('.modal-content', {
        scale: 0.8,
        opacity: 0,
        duration: 0.2,
        ease: 'power2.in',
        onComplete: () => {
            modal.classList.remove('active');
        }
    });
}

// Close modal when clicking outside
document.getElementById('successModal').addEventListener('click', (e) => {
    if (e.target.id === 'successModal') {
        closeModal();
    }
});

// Mobile Menu
function initMobileMenu() {
    const toggle = document.querySelector('.mobile-menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    toggle.addEventListener('click', () => {
        toggle.classList.toggle('active');
        navLinks.classList.toggle('active');
        
        // Animate menu
        if (navLinks.classList.contains('active')) {
            navLinks.style.display = 'flex';
            navLinks.style.flexDirection = 'column';
            navLinks.style.position = 'absolute';
            navLinks.style.top = '80px';
            navLinks.style.left = '0';
            navLinks.style.right = '0';
            navLinks.style.background = 'white';
            navLinks.style.padding = '20px';
            navLinks.style.boxShadow = '0 10px 30px rgba(0,0,0,0.1)';
            
            gsap.from(navLinks, {
                opacity: 0,
                y: -20,
                duration: 0.3,
                ease: 'power2.out'
            });
        } else {
            gsap.to(navLinks, {
                opacity: 0,
                y: -20,
                duration: 0.2,
                ease: 'power2.in',
                onComplete: () => {
                    navLinks.style.display = '';
                }
            });
        }
    });
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        
        if (target) {
            gsap.to(window, {
                duration: 1,
                scrollTo: {
                    y: target,
                    offsetY: 80
                },
                ease: 'power3.inOut'
            });
        }
    });
});

// Navbar scroll effect
let lastScroll = 0;
const nav = document.querySelector('.nav');

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;
    
    if (currentScroll > 100) {
        nav.style.padding = '15px 0';
        nav.style.boxShadow = '0 2px 30px rgba(0, 0, 0, 0.1)';
    } else {
        nav.style.padding = '20px 0';
        nav.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.05)';
    }
    
    lastScroll = currentScroll;
});

// Add hover effects to showcase panels
document.querySelectorAll('.showcase-panel').forEach(panel => {
    panel.addEventListener('mouseenter', () => {
        gsap.to(panel, {
            y: -10,
            duration: 0.3,
            ease: 'power2.out'
        });
    });
    
    panel.addEventListener('mouseleave', () => {
        gsap.to(panel, {
            y: 0,
            duration: 0.3,
            ease: 'power2.out'
        });
    });
});

// Add pulse animation to CTA buttons
setInterval(() => {
    const primaryButtons = document.querySelectorAll('.btn-primary');
    primaryButtons.forEach(button => {
        gsap.to(button, {
            boxShadow: '0 6px 40px rgba(99, 102, 241, 0.5)',
            duration: 0.5,
            yoyo: true,
            repeat: 1,
            ease: 'power2.inOut'
        });
    });
}, 3000);

// Log analytics data (for demo purposes)
console.log('=== MicroDrama Analytics ===');
console.log('Page loaded:', new Date().toISOString());
console.log('Stored CTA clicks:', JSON.parse(localStorage.getItem('ctaClicks') || '[]'));
console.log('===========================');

// Export tracking function for external use
window.trackCTAClick = trackCTAClick;
