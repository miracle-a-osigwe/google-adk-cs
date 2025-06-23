// This assumes you are using a modern browser with support for ES Modules.
// You would typically use a bundler like Vite or Webpack to manage this.
import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';

// --- Configuration ---
// IMPORTANT: These should be loaded from environment variables in a real app
const SUPABASE_URL = 'https://qinhihvbpvabhbgxmsci.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFpbmhpaHZicHZhYmhiZ3htc2NpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAyMDMxNzcsImV4cCI6MjA2NTc3OTE3N30.2Bc2Sag-RWKx30hK3VAsGjOI23QJcdpWGKX4eHejFTY';

// Initialize the Supabase client
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// --- Helper function to display messages ---
function showMessage(type, title, text) {
    const display = document.getElementById('messageDisplay') || document.getElementById('errorMessage');
    const titleEl = document.getElementById('messageTitle') || document.getElementById('errorText');
    const textEl = document.getElementById('messageText') || document.getElementById('errorText');

    if (!display || !titleEl || !textEl) {
        console.error('Message display elements not found');
        return;
    }

    if (type === 'error') {
        display.className = 'bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative';
        titleEl.textContent = title;
    } else {
        display.className = 'bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative';
        titleEl.textContent = title;
    }
    textEl.textContent = text;
    display.classList.remove('hidden');
}

// --- Login Form Logic ---
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitButton = document.getElementById('submitButton');
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Signing in...';

        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        const { data, error } = await supabase.auth.signInWithPassword({
            email: email,
            password: password,
        });

        if (error) {
            showMessage('error', 'Login Failed!', error.message);
            submitButton.disabled = false;
            submitButton.innerHTML = 'Sign in';
        } else {
            // Successful login
            localStorage.setItem('supabase.auth.token', data.session.access_token);
            
            // Set cookie for server-side auth
            document.cookie = `supabase-auth-token=${data.session.access_token}; path=/; max-age=${60*60*24*7}; SameSite=Lax`;
            
            // Add token to all future fetch requests
            const originalFetch = window.fetch;
            window.fetch = function(url, options = {}) {
                options.headers = options.headers || {};
                options.headers['X-Supabase-Auth'] = data.session.access_token;
                return originalFetch(url, options);
            };

            // Redirect to the customer home page
            window.location.href = '/customer/';
        }
    });
}

// --- Signup Form Logic ---
const signupForm = document.getElementById('signupForm');
if (signupForm) {
    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitButton = document.getElementById('submitButton');
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Creating account...';

        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm-password').value;

        if (password !== confirmPassword) {
            showMessage('error', 'Error!', 'Passwords do not match.');
            submitButton.disabled = false;
            submitButton.innerHTML = 'Sign up';
            return;
        }

        const { data, error } = await supabase.auth.signUp({
            email: email,
            password: password,
        });

        if (error) {
            showMessage('error', 'Signup Failed!', error.message);
            submitButton.disabled = false;
            submitButton.innerHTML = 'Sign up';
        } else {
            // IMPORTANT: If you have "Email confirmation" enabled in Supabase, the user is not yet logged in.
            showMessage('success', 'Success!', 'Please check your email to verify your account.');
            // We don't redirect here, just show the message.
            submitButton.innerHTML = 'Sign up'; // Keep the button text, maybe disable it permanently
        }
    });
}

// --- Check if user is already logged in ---
async function checkAuthStatus() {
    const { data: { session } } = await supabase.auth.getSession();
    
    if (session) {
        // User is logged in
        console.log('User is logged in:', session.user.email);
        
        // Add the token to localStorage for easy access
        localStorage.setItem('supabase.auth.token', session.access_token);
        
        // Set cookie for server-side auth
        document.cookie = `supabase-auth-token=${session.access_token}; path=/; max-age=${60*60*24*7}; SameSite=Lax`;
        
        // Add token to all future fetch requests
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            options.headers = options.headers || {};
            options.headers['X-Supabase-Auth'] = session.access_token;
            return originalFetch(url, options);
        };

        // If we're on the login or signup page, redirect to home
        if (window.location.pathname === '/customer/login' || window.location.pathname === '/customer/signup') {
            window.location.href = '/customer/';
        }
        
        // Update UI to show logged-in state
        updateUIForLoggedInUser(session.user);
    } else {
        // User is not logged in
        console.log('No active session found');
        
        // If we're on a protected page, redirect to login
        const protectedPaths = ['/customer/tickets', '/customer/profile'];
        if (protectedPaths.some(path => window.location.pathname.startsWith(path))) {
            window.location.href = '/customer/login?redirect=' + encodeURIComponent(window.location.pathname);
        }
    }
}

function updateUIForLoggedInUser(user) {
    // Find all sign-in buttons and replace them with user info
    const signInButtons = document.querySelectorAll('.sign-in-button');
    signInButtons.forEach(button => {
        const userMenu = document.createElement('div');
        userMenu.className = 'relative';
        userMenu.innerHTML = `
            <button id="userMenuButton" class="flex items-center text-sm font-medium text-gray-700 hover:text-gray-800">
                <span class="mr-2">${user.email}</span>
                <i class="fas fa-chevron-down"></i>
            </button>
            <div id="userMenuDropdown" class="hidden absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-10">
                <a href="/customer/profile" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Your Profile</a>
                <a href="/customer/tickets" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Your Tickets</a>
                <button id="signOutButton" class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Sign out</button>
            </div>
        `;
        button.replaceWith(userMenu);
        
        // Add event listeners for dropdown
        const menuButton = document.getElementById('userMenuButton');
        const menuDropdown = document.getElementById('userMenuDropdown');
        if (menuButton && menuDropdown) {
            menuButton.addEventListener('click', () => {
                menuDropdown.classList.toggle('hidden');
            });
            
            // Close when clicking outside
            document.addEventListener('click', (e) => {
                if (!menuButton.contains(e.target) && !menuDropdown.contains(e.target)) {
                    menuDropdown.classList.add('hidden');
                }
            });
        }
        
        // Add sign out functionality
        const signOutButton = document.getElementById('signOutButton');
        if (signOutButton) {
            signOutButton.addEventListener('click', async () => {
                await supabase.auth.signOut();
                localStorage.removeItem('supabase.auth.token');
                
                // Clear the auth cookie
                document.cookie = 'supabase-auth-token=; path=/; max-age=0; SameSite=Lax';
                
                window.location.href = '/customer/login';
            });
        }
    });
}

// Run auth check when the page loads
document.addEventListener('DOMContentLoaded', checkAuthStatus);

// Export the supabase client and auth functions for use in other scripts
export { supabase, showMessage };