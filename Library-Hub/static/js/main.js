document.addEventListener('DOMContentLoaded', function() {
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeToggleIcon');
    
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
        });
    }

    // Theme handling: init from localStorage or system, apply theme, and persist
    const applyTheme = function(theme) {
        // Do not alter page theme attributes for the landing page — keep landing white/blue enterprise look
        const onLanding = document.body.classList.contains('landing');
        if (theme === 'dark' && !onLanding) {
            document.documentElement.setAttribute('data-theme', 'dark');
            document.body.classList.add('dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
            document.body.classList.remove('dark');
        }
        // update accessible state and icon regardless to show user preference but visually landing will stay unchanged
        if (themeToggle) themeToggle.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
        if (themeIcon) themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    };

    const savedTheme = localStorage.getItem('dlcf_theme');
    let currentTheme = savedTheme || (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    applyTheme(currentTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
            localStorage.setItem('dlcf_theme', currentTheme);
            applyTheme(currentTheme);
        });
    }
    // Theme toggle - persisted in localStorage: (handled above by applyTheme)
    
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function(message) {
        const closeBtn = message.querySelector('.flash-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                message.style.opacity = '0';
                setTimeout(function() {
                    message.remove();
                }, 300);
            });
        }
        
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                message.remove();
            }, 300);
        }, 5000);
    });
    
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
        
        inputs.forEach(function(input) {
            input.addEventListener('blur', function() {
                validateInput(this);
            });
        });
        
        form.addEventListener('submit', function(e) {
            let isValid = true;
            
            inputs.forEach(function(input) {
                if (!validateInput(input)) {
                    isValid = false;
                }
            });
            
            const password = form.querySelector('input[name="password"]');
            const confirmPassword = form.querySelector('input[name="confirm_password"]');
            
            if (password && confirmPassword && password.value !== confirmPassword.value) {
                showInputError(confirmPassword, 'Passwords do not match');
                isValid = false;
            }
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    });
    
    function validateInput(input) {
        const value = input.value.trim();
        
        if (input.hasAttribute('required') && !value) {
            showInputError(input, 'This field is required');
            return false;
        }
        
        if (input.type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                showInputError(input, 'Please enter a valid email address');
                return false;
            }
        }
        
        if (input.name === 'password' && value && value.length < 6) {
            showInputError(input, 'Password must be at least 6 characters');
            return false;
        }
        
        clearInputError(input);
        return true;
    }
    
    function showInputError(input, message) {
        clearInputError(input);
        input.style.borderColor = '#ef4444';
        
        const error = document.createElement('span');
        error.className = 'input-error';
        error.style.color = '#ef4444';
        error.style.fontSize = '0.85rem';
        error.style.marginTop = '5px';
        error.style.display = 'block';
        error.textContent = message;
        
        input.parentNode.appendChild(error);
    }
    
    function clearInputError(input) {
        input.style.borderColor = '';
        const error = input.parentNode.querySelector('.input-error');
        if (error) {
            error.remove();
        }
    }
    
    const searchInput = document.querySelector('.nav-search input');
    if (searchInput) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            
            const query = this.value.trim();
            if (query.length >= 2) {
                searchTimeout = setTimeout(function() {
                    fetchSearchSuggestions(query);
                }, 300);
            }
        });
    }
    
    function fetchSearchSuggestions(query) {
        fetch('/api/search?q=' + encodeURIComponent(query))
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                if (data.success && data.data.length > 0) {
                    console.log('Search suggestions:', data.data);
                }
            })
            .catch(function(error) {
                console.error('Search error:', error);
            });
    }
    
    const contentCards = document.querySelectorAll('.content-card');
    contentCards.forEach(function(card) {
        card.addEventListener('click', function(e) {
            if (e.target.tagName !== 'A' && e.target.tagName !== 'BUTTON') {
                const link = card.querySelector('a');
                if (link) {
                    link.click();
                }
            }
        });
    });
    
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        const fileUpload = fileInput.closest('.file-upload');
        
        if (fileUpload) {
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(function(eventName) {
                fileUpload.addEventListener(eventName, function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                });
            });
            
            ['dragenter', 'dragover'].forEach(function(eventName) {
                fileUpload.addEventListener(eventName, function() {
                    fileUpload.style.borderColor = '#2563eb';
                    fileUpload.style.backgroundColor = '#eff6ff';
                });
            });
            
            ['dragleave', 'drop'].forEach(function(eventName) {
                fileUpload.addEventListener(eventName, function() {
                    fileUpload.style.borderColor = '';
                    fileUpload.style.backgroundColor = '';
                });
            });
            
            fileUpload.addEventListener('drop', function(e) {
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    fileInput.files = files;
                    const fileName = document.getElementById('file-name');
                    if (fileName) {
                        fileName.textContent = files[0].name;
                    }
                }
            });
        }
    }
    
    const videoPlayers = document.querySelectorAll('.video-player video');
    videoPlayers.forEach(function(video) {
        video.addEventListener('play', function() {
            console.log('Video started playing');
        });
    });
    
    const audioPlayers = document.querySelectorAll('.audio-player audio');
    audioPlayers.forEach(function(audio) {
        audio.addEventListener('play', function() {
            console.log('Audio started playing');
        });
    });
    
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    window.addEventListener('scroll', function() {
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            if (window.scrollY > 50) {
                navbar.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
            } else {
                navbar.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
            }
        }
    });

    /* --- Landing page interactions --- */
    // Screen mock tilt effect (desktop)
    const screenMock = document.querySelector('.lp-screen-mock');
    if (screenMock && window.matchMedia('(pointer:fine)').matches) {
        const boundary = screenMock.getBoundingClientRect();
        screenMock.style.transition = 'transform 300ms ease, box-shadow 300ms ease';

        screenMock.addEventListener('mousemove', function(e) {
            const rect = screenMock.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width - 0.5; // -0.5 .. 0.5
            const y = (e.clientY - rect.top) / rect.height - 0.5;
            const rotX = (y * 8) * -1; // tilt more vertically
            const rotY = x * 10;
            screenMock.style.transform = `perspective(900px) rotateX(${rotX}deg) rotateY(${rotY}deg) translateZ(6px)`;
            screenMock.style.boxShadow = '0 18px 40px rgba(2,6,23,0.5)';
        });

        screenMock.addEventListener('mouseleave', function() {
            screenMock.style.transform = '';
            screenMock.style.boxShadow = '';
        });
    }

    // Simple testimonials carousel
    const testimonials = Array.from(document.querySelectorAll('.testimonial'));
    if (testimonials.length > 1) {
        let tIndex = 0;
        testimonials.forEach((t, i) => {
            t.style.transition = 'opacity 400ms ease, transform 400ms ease';
            t.style.opacity = i === 0 ? '1' : '0';
            t.style.transform = i === 0 ? 'translateY(0)' : 'translateY(8px)';
            t.style.position = 'relative';
        });

        let carouselPaused = false;
        const nextTestimonial = function() {
            const current = testimonials[tIndex];
            const next = testimonials[(tIndex + 1) % testimonials.length];
            current.style.opacity = '0';
            current.style.transform = 'translateY(8px)';
            next.style.opacity = '1';
            next.style.transform = 'translateY(0)';
            tIndex = (tIndex + 1) % testimonials.length;
        };

        let carouselTimer = setInterval(function() {
            if (!carouselPaused) nextTestimonial();
        }, 5000);

        testimonials.forEach(t => {
            t.addEventListener('mouseenter', () => { carouselPaused = true; });
            t.addEventListener('mouseleave', () => { carouselPaused = false; });
        });
    }

    // Request Demo modal (opens when user clicks the hero 'Request Demo' button)
    function createDemoModal() {
        if (document.getElementById('demoModal')) return;

        const modal = document.createElement('div');
        modal.id = 'demoModal';
        modal.innerHTML = `
            <div class="demo-modal-backdrop" style="position:fixed;inset:0;background:rgba(2,6,23,0.6);display:flex;align-items:center;justify-content:center;z-index:2000;"> 
                <div class="demo-modal" role="dialog" aria-modal="true" style="width:min(720px,94%);background:#fff;border-radius:12px;padding:20px;max-height:90vh;overflow:auto;"> 
                    <header style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;"> 
                        <h3 style="margin:0;">Request a Demo</h3> 
                        <button id="demoClose" aria-label="Close" style="background:none;border:none;font-size:1.25rem;cursor:pointer;">&times;</button>
                    </header>
                    <form id="demoForm" action="/contact" method="POST">
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px;">
                            <input name="name" placeholder="Full name" required style="padding:10px;border:1px solid #e5e7eb;border-radius:8px;" />
                            <input name="email" type="email" placeholder="Work email" required style="padding:10px;border:1px solid #e5e7eb;border-radius:8px;" />
                        </div>
                        <div style="margin-bottom:10px;">
                            <input name="organization" placeholder="Organization" style="width:100%;padding:10px;border:1px solid #e5e7eb;border-radius:8px;" />
                        </div>
                        <div style="margin-bottom:12px;">
                            <textarea name="message" rows="4" placeholder="Tell us what you'd like to achieve" style="width:100%;padding:10px;border:1px solid #e5e7eb;border-radius:8px;"></textarea>
                        </div>
                        <div style="display:flex;gap:8px;justify-content:flex-end;">
                            <button type="button" id="demoCancel" class="btn btn-outline">Cancel</button>
                            <button type="submit" class="btn btn-primary">Request Demo</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        const previouslyFocused = document.activeElement;
        document.body.appendChild(modal);

        const backdrop = modal.querySelector('.demo-modal-backdrop');
        const closeButtons = modal.querySelectorAll('#demoClose, #demoCancel');
        closeButtons.forEach(btn => btn.addEventListener('click', () => modal.remove()));
        backdrop.addEventListener('click', function(e) {
            if (e.target === backdrop) modal.remove();
        });
        // Hide main content from screen readers while modal is open
        const mainContent = document.querySelector('main.main-content');
        if (mainContent) mainContent.setAttribute('aria-hidden', 'true');
        // Accessibility: focus trap and keyboard handling for modal
        const focusableSelectors = 'a[href], area[href], input:not([disabled]), textarea:not([disabled]), button:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';
        const focusableElements = modal.querySelectorAll(focusableSelectors);
        const firstFocusable = focusableElements[0];
        const lastFocusable = focusableElements[focusableElements.length - 1];
        if (firstFocusable) firstFocusable.focus();

        function keyHandler(e) {
            if (e.key === 'Escape') {
                modal.remove();
            }
            if (e.key === 'Tab') {
                if (focusableElements.length === 0) {
                    e.preventDefault();
                    return;
                }
                if (e.shiftKey) {
                    if (document.activeElement === firstFocusable) {
                        e.preventDefault();
                        lastFocusable.focus();
                    }
                } else {
                    if (document.activeElement === lastFocusable) {
                        e.preventDefault();
                        firstFocusable.focus();
                    }
                }
            }
        }
        modal.addEventListener('keydown', keyHandler);

        // When modal is removed, restore focus and aria-hidden
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(m) {
                m.removedNodes.forEach(function(node) {
                    if (node === modal) {
                        if (mainContent) mainContent.removeAttribute('aria-hidden');
                        if (previouslyFocused && typeof previouslyFocused.focus === 'function') previouslyFocused.focus();
                        observer.disconnect();
                    }
                });
            });
        });
        observer.observe(document.body, { childList: true });
    }

    // Attach demo modal to hero button(s)
    document.querySelectorAll('.lp-hero .btn-outline, .lp-hero .request-demo').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            // If the button is an anchor linking to another route, prevent navigation
            if (this.tagName.toLowerCase() === 'a') e.preventDefault();
            createDemoModal();
        });
    });

    /* Button ripple for clickable elements with .ripple */
    document.querySelectorAll('.ripple').forEach(function(el) {
        el.addEventListener('click', function(e) {
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            const span = document.createElement('span');
            span.className = 'ripple-anim';
            span.style.left = x + 'px';
            span.style.top = y + 'px';
            span.style.width = size + 'px';
            span.style.height = size + 'px';
            span.style.position = 'absolute';
            span.style.borderRadius = '50%';
            span.style.transform = 'scale(0)';
            span.style.opacity = '0.8';
            span.style.background = 'rgba(255,255,255,0.12)';
            span.style.pointerEvents = 'none';
            span.style.transition = 'transform .6s linear, opacity .6s linear';
            this.style.position = 'relative';
            this.appendChild(span);
            requestAnimationFrame(function() {
                span.style.transform = 'scale(20)';
                span.style.opacity = '0';
            });
            setTimeout(function() { span.remove(); }, 700);
        });
    });

    /* Horizontal drag-to-scroll for preview lists */
    document.querySelectorAll('.preview-scroll').forEach(function(scrollEl) {
        let isDown = false, startX, scrollLeft;
        scrollEl.addEventListener('mousedown', function(e) {
            isDown = true; scrollEl.classList.add('dragging'); startX = e.pageX - scrollEl.offsetLeft; scrollLeft = scrollEl.scrollLeft;
        });
        scrollEl.addEventListener('mouseup', function() { isDown = false; scrollEl.classList.remove('dragging'); });
        scrollEl.addEventListener('mouseleave', function() { isDown = false; scrollEl.classList.remove('dragging'); });
        scrollEl.addEventListener('mousemove', function(e) {
            if (!isDown) return; e.preventDefault(); const x = e.pageX - scrollEl.offsetLeft; const walk = (x - startX) * 1; scrollEl.scrollLeft = scrollLeft - walk;
        });
    });

});

function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this item?');
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = function() {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
