import { onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-auth.js";
import { auth } from './firebase.js';

const loginButton = document.getElementById('login-button');
const accountDropdown = document.getElementById('account-dropdown');
const accountButton = document.getElementById('account-button');
const usernameDisplay = document.getElementById('username-display');
const dropdownMenu = document.getElementById('dropdown-menu');
const logoutButton = document.getElementById('logout-button');
const mobileMenuButton = document.getElementById('mobile-menu-button');
const mobileMenu = document.getElementById('mobile-menu');
const mobileAuthLinks = document.getElementById('mobile-auth-links');
const mobileNavLinks = document.getElementById('mobile-nav-links');

// --- UPDATED NAVIGATION HIGHLIGHTING ---
function highlightActiveLink() {
    // Add the /leaderboard path to the map
    const pageMap = {
        '/': 'predictions',
        '/standings': 'standings',
        '/last_man_standing': 'lms',
        '/leaderboard': 'leaderboard'
    };
    const currentPath = window.location.pathname;
    let activeItem = null;

    if (currentPath === '/') {
        activeItem = pageMap['/'];
    } else if (currentPath.startsWith('/standings')) {
        activeItem = pageMap['/standings'];
    } else if (currentPath === '/last_man_standing') {
        activeItem = pageMap['/last_man_standing'];
    } else if (currentPath === '/leaderboard') { // Add the check for the leaderboard path
        activeItem = pageMap['/leaderboard'];
    }

    if (activeItem) {
        // Clear any existing active links first
        document.querySelectorAll('[data-nav-item]').forEach(el => el.classList.remove('active-nav-link'));
        document.querySelectorAll('#mobile-nav-links a').forEach(el => el.classList.remove('active-nav-link'));

        // Desktop nav
        const desktopLink = document.querySelector(`[data-nav-item="${activeItem}"]`);
        if(desktopLink) desktopLink.classList.add('active-nav-link');
        
        // Mobile nav
        // Note: this is a simple check; a more robust solution might use a data attribute
        const mobileLink = document.querySelector(`#mobile-nav-links a[href*="${Object.keys(pageMap).find(key => pageMap[key] === activeItem)}"]`);
        if (mobileLink) mobileLink.classList.add('active-nav-link');
    }
}

// --- Mobile Menu Toggle ---
mobileMenuButton.addEventListener('click', () => {
    const isExpanded = mobileMenuButton.getAttribute('aria-expanded') === 'true';
    mobileMenuButton.setAttribute('aria-expanded', !isExpanded);
    mobileMenu.classList.toggle('hidden');
    document.getElementById('hamburger-open').classList.toggle('hidden');
    document.getElementById('hamburger-close').classList.toggle('hidden');
});

// --- Auth State Logic ---
onAuthStateChanged(auth, async (user) => {
    const desktopNavLinks = document.querySelector('.hidden.md\\:block .space-x-4').cloneNode(true);
    desktopNavLinks.querySelectorAll('#login-button, #account-dropdown').forEach(el => el.remove());
    mobileNavLinks.innerHTML = '';
    desktopNavLinks.childNodes.forEach(node => {
        if (node.tagName === 'A') {
            const mobileLink = node.cloneNode(true);
            mobileLink.className = 'text-gray-500 hover:bg-gray-700 hover:text-white block px-3 py-2 rounded-md text-base font-medium';
            mobileNavLinks.appendChild(mobileLink);
        }
    });

    if (user) {
        loginButton.classList.add('hidden');
        accountDropdown.classList.remove('hidden');

        const userEmail = user.email || 'Account';
        usernameDisplay.textContent = userEmail;
        
        const welcomeMessage = document.getElementById('welcome-message');
        if (welcomeMessage) {
            welcomeMessage.textContent = `Welcome!`;
        }

        mobileAuthLinks.innerHTML = `
            <div class="px-5 pb-2">
                <div class="font-medium text-base text-gray-800">${userEmail}</div>
            </div>
            <div class="px-2 space-y-1">
                <a href="#" id="mobile-logout-button" class="block px-3 py-2 rounded-md text-base font-medium text-gray-500 hover:bg-gray-100 hover:text-gray-800">Logout</a>
            </div>`;
        document.getElementById('mobile-logout-button').addEventListener('click', () => logoutButton.click());
    } else {
        loginButton.classList.remove('hidden');
        accountDropdown.classList.add('hidden');
        const welcomeMessage = document.getElementById('welcome-message');
        if (welcomeMessage) {
            welcomeMessage.textContent = 'NFL Weekly Predictions';
        }

        mobileAuthLinks.innerHTML = `
            <div class="px-2 space-y-1">
                <a href="/login" class="block px-3 py-2 rounded-md text-base font-medium text-gray-500 hover:bg-gray-100 hover:text-gray-800">Login</a>
            </div>`;
    }
    highlightActiveLink();
});

accountButton.addEventListener('click', () => {
    dropdownMenu.classList.toggle('hidden');
});

logoutButton.addEventListener('click', async () => {
    try {
        await signOut(auth);
        window.location.href = '/login';
    } catch (error) {
        console.error('Logout error:', error);
    }
});