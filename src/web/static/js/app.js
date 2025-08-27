/**
 * Personal Password Manager - Web Interface JavaScript
 * ===================================================
 * 
 * Main JavaScript functionality for the web interface including:
 * - Theme management
 * - Modal handling
 * - AJAX interactions
 * - UI enhancements
 * - Mobile navigation
 * 
 * Author: Personal Password Manager
 * Version: 1.0.0
 */

// Global application state
const App = {
    currentTheme: 'dark',
    isLoading: false,
    modals: {}
};

/**
 * Initialize the application
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    initializeModals();
    initializeMobileNav();
    initializeTooltips();
    initializeClipboard();
    setupKeyboardShortcuts();
    
    console.log('Password Manager Web Interface initialized');
});

/**
 * Theme Management
 */
function initializeTheme() {
    // Load theme from localStorage or default to dark
    const savedTheme = localStorage.getItem('password-manager-theme') || 'dark';
    setTheme(savedTheme);
}

function toggleTheme() {
    const newTheme = App.currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

function setTheme(theme) {
    App.currentTheme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('password-manager-theme', theme);
    
    // Update theme toggle button text if it exists
    const themeButton = document.querySelector('[onclick="toggleTheme()"]');
    if (themeButton) {
        const icon = themeButton.querySelector('i');
        const text = themeButton.querySelector('span') || themeButton.childNodes[2];
        
        if (theme === 'dark') {
            if (icon) icon.className = 'fas fa-sun';
            if (text) text.textContent = ' Light Theme';
        } else {
            if (icon) icon.className = 'fas fa-moon';
            if (text) text.textContent = ' Dark Theme';
        }
    }
}

/**
 * Modal Management
 */
function initializeModals() {
    // Close modals when clicking outside
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            closeModal(e.target.id);
        }
    });
    
    // Close modals with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                closeModal(openModal.id);
            }
        }
    });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
        
        // Focus first input or button
        const firstFocusable = modal.querySelector('input, button, textarea, select');
        if (firstFocusable) {
            setTimeout(() => firstFocusable.focus(), 100);
        }
        
        App.modals[modalId] = true;
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
        delete App.modals[modalId];
        
        // Return focus to trigger element if available
        const trigger = document.querySelector(`[onclick*="${modalId}"]`);
        if (trigger) {
            trigger.focus();
        }
    }
}

function showSecurityInfo() {
    openModal('securityModal');
}

function showAbout() {
    openModal('aboutModal');
}

/**
 * Mobile Navigation
 */
function initializeMobileNav() {
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', toggleMobileMenu);
        
        // Close mobile menu when clicking on nav links
        navMenu.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('active');
                updateNavToggle(false);
            });
        });
    }
}

function toggleMobileMenu() {
    const navMenu = document.querySelector('.nav-menu');
    const isActive = navMenu.classList.toggle('active');
    updateNavToggle(isActive);
}

function updateNavToggle(isActive) {
    const navToggle = document.querySelector('.nav-toggle');
    const spans = navToggle.querySelectorAll('span');
    
    if (isActive) {
        spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
        spans[1].style.opacity = '0';
        spans[2].style.transform = 'rotate(-45deg) translate(7px, -6px)';
        navToggle.setAttribute('aria-expanded', 'true');
    } else {
        spans[0].style.transform = '';
        spans[1].style.opacity = '1';
        spans[2].style.transform = '';
        navToggle.setAttribute('aria-expanded', 'false');
    }
}

/**
 * Loading States
 */
function showLoading(message = 'Loading...') {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        const text = overlay.querySelector('p');
        if (text) text.textContent = message;
        overlay.style.display = 'flex';
        App.isLoading = true;
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
        App.isLoading = false;
    }
}

/**
 * Toast Notifications
 */
function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icon = getToastIcon(type);
    toast.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Remove after duration
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, duration);
}

function getToastIcon(type) {
    switch (type) {
        case 'success': return 'check';
        case 'error': return 'times';
        case 'warning': return 'exclamation-triangle';
        default: return 'info';
    }
}

/**
 * Clipboard Operations
 */
function initializeClipboard() {
    // Check if clipboard API is available
    if (!navigator.clipboard) {
        console.warn('Clipboard API not available');
        return;
    }
}

async function copyToClipboard(text, successMessage = 'Copied to clipboard!') {
    try {
        await navigator.clipboard.writeText(text);
        showToast(successMessage, 'success');
        return true;
    } catch (err) {
        console.error('Failed to copy to clipboard:', err);
        
        // Fallback for older browsers
        if (fallbackCopyToClipboard(text)) {
            showToast(successMessage, 'success');
            return true;
        } else {
            showToast('Failed to copy to clipboard', 'error');
            return false;
        }
    }
}

function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        document.body.removeChild(textArea);
        return successful;
    } catch (err) {
        document.body.removeChild(textArea);
        return false;
    }
}

/**
 * Form Enhancements
 */
function initializeTooltips() {
    // Add hover effects and tooltips to buttons
    const buttons = document.querySelectorAll('[title]');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = this.getAttribute('title');
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + (rect.width / 2) + 'px';
            tooltip.style.top = rect.bottom + 5 + 'px';
            
            this._tooltip = tooltip;
        });
        
        button.addEventListener('mouseleave', function() {
            if (this._tooltip) {
                this._tooltip.remove();
                this._tooltip = null;
            }
        });
    });
}

/**
 * Keyboard Shortcuts
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K - Focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('.search-input-group input');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Ctrl/Cmd + N - Add new password (if on dashboard)
        if ((e.ctrlKey || e.metaKey) && e.key === 'n' && window.location.pathname === '/dashboard') {
            e.preventDefault();
            window.location.href = '/add_password';
        }
        
        // Ctrl/Cmd + G - Generate password
        if ((e.ctrlKey || e.metaKey) && e.key === 'g') {
            e.preventDefault();
            window.location.href = '/generate_password';
        }
        
        // ESC - Close modals or clear search
        if (e.key === 'Escape') {
            const searchInput = document.querySelector('.search-input-group input');
            if (searchInput && searchInput.value) {
                searchInput.value = '';
                searchInput.dispatchEvent(new Event('input'));
            }
        }
    });
}

/**
 * API Utilities
 */
async function makeApiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, finalOptions);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

/**
 * Password Generation
 */
async function generatePassword(options = {}) {
    const defaultOptions = {
        length: 16,
        include_lowercase: true,
        include_uppercase: true,
        include_digits: true,
        include_symbols: true,
        method: 'random'
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    try {
        showLoading('Generating password...');
        
        const response = await makeApiRequest('/api/generate_password', {
            method: 'POST',
            body: JSON.stringify(finalOptions)
        });
        
        hideLoading();
        
        if (response.success) {
            return response;
        } else {
            throw new Error(response.error || 'Password generation failed');
        }
    } catch (error) {
        hideLoading();
        showToast('Failed to generate password: ' + error.message, 'error');
        throw error;
    }
}

/**
 * Password Strength Checking
 */
let strengthCheckTimeout;
async function checkPasswordStrength(password) {
    // Debounce the strength check
    clearTimeout(strengthCheckTimeout);
    
    if (!password) {
        return null;
    }
    
    return new Promise((resolve, reject) => {
        strengthCheckTimeout = setTimeout(async () => {
            try {
                const response = await makeApiRequest('/api/check_strength', {
                    method: 'POST',
                    body: JSON.stringify({ password })
                });
                
                if (response.success) {
                    resolve(response.analysis);
                } else {
                    reject(new Error(response.error || 'Strength check failed'));
                }
            } catch (error) {
                reject(error);
            }
        }, 300);
    });
}

/**
 * Form Validation
 */
function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('error');
            isValid = false;
        } else {
            field.classList.remove('error');
        }
    });
    
    return isValid;
}

/**
 * Auto-save functionality
 */
let autoSaveTimeout;
function setupAutoSave(form, saveCallback, delay = 2000) {
    const inputs = form.querySelectorAll('input, textarea, select');
    
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            clearTimeout(autoSaveTimeout);
            
            autoSaveTimeout = setTimeout(() => {
                if (validateForm(form)) {
                    saveCallback(new FormData(form));
                }
            }, delay);
        });
    });
}

/**
 * Smooth scrolling
 */
function smoothScrollTo(element, offset = 0) {
    const targetPosition = element.offsetTop - offset;
    
    window.scrollTo({
        top: targetPosition,
        behavior: 'smooth'
    });
}

/**
 * Utility Functions
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function generateRandomId(length = 8) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdebcghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

/**
 * Performance Monitoring
 */
function measurePerformance(name, func) {
    return async function(...args) {
        const start = performance.now();
        const result = await func.apply(this, args);
        const end = performance.now();
        
        console.log(`${name} took ${(end - start).toFixed(2)} milliseconds`);
        return result;
    };
}

/**
 * Error Handling
 */
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    
    // Don't show error toasts for script loading errors in production
    if (e.filename && !e.filename.includes('localhost')) {
        return;
    }
    
    showToast('An unexpected error occurred', 'error');
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    showToast('An error occurred while processing your request', 'error');
});

/**
 * Service Worker Registration (for future PWA support)
 */
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // Service worker registration would go here
        console.log('Service Worker support detected');
    });
}

// Export functions for global use
window.App = App;
window.toggleTheme = toggleTheme;
window.openModal = openModal;
window.closeModal = closeModal;
window.showSecurityInfo = showSecurityInfo;
window.showAbout = showAbout;
window.toggleMobileMenu = toggleMobileMenu;
window.showToast = showToast;
window.copyToClipboard = copyToClipboard;
window.generatePassword = generatePassword;
window.checkPasswordStrength = checkPasswordStrength;