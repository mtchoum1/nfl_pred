import { createUserWithEmailAndPassword, signInWithEmailAndPassword, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-auth.js";
import { auth } from './firebase.js'; // Removed unused 'database' import

const formTitle = document.getElementById('form-title');
const authForm = document.getElementById('auth-form');
const submitButton = document.getElementById('submit-button');
const toggleFormButton = document.getElementById('toggle-form');
const errorMessage = document.getElementById('error-message');
const errorText = document.getElementById('error-text');

let isLogin = true;

toggleFormButton.addEventListener('click', () => {
    isLogin = !isLogin;
    formTitle.textContent = isLogin ? 'Login' : 'Sign Up';
    submitButton.textContent = isLogin ? 'Login' : 'Sign Up';
    toggleFormButton.textContent = isLogin ? 'Need an account? Sign up' : 'Have an account? Login';
    errorMessage.classList.add('hidden');
});

authForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = authForm.email.value;
    const password = authForm.password.value;
    errorMessage.classList.add('hidden');

    try {
        if (isLogin) {
            await signInWithEmailAndPassword(auth, email, password);
        } else {
            // Sign up now only creates the user; it no longer writes to the database.
            await createUserWithEmailAndPassword(auth, email, password);
        }
        window.location.href = '/';
    } catch (error) {
        errorText.textContent = error.message;
        errorMessage.classList.remove('hidden');
    }
});

onAuthStateChanged(auth, (user) => {
    if (user && window.location.pathname.includes('login')) {
        window.location.href = '/';
    }
});