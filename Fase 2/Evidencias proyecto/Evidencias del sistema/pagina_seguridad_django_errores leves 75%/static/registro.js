document.addEventListener('DOMContentLoaded', () => {
    const usernameInput = document.getElementById('username');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const termsCheckbox = document.getElementById('terms');
    const registerBtn = document.getElementById('registerBtn');

    // Claves de localStorage
    const DRAFT_KEY = 'registroFormDraft';
    const REGISTERED_KEY = 'registeredUser';

    function setInputError(input, isError) {
        if (isError) {
            input.style.borderColor = 'red';
        } else {
            input.style.borderColor = '';
        }
    }

    function validateForm() {
        const usernameValid = usernameInput.value.trim().length > 0 && usernameInput.value.length <= 20;
        const emailValid = /\S+@\S+\.\S+/.test(emailInput.value);
        const passwordValid = passwordInput.value.length >= 8 && passwordInput.value.length <= 10;
        const termsChecked = termsCheckbox.checked;

        setInputError(usernameInput, !usernameValid);
        setInputError(emailInput, !emailValid);
        setInputError(passwordInput, !passwordValid);

        registerBtn.disabled = !(usernameValid && emailValid && passwordValid && termsChecked);
    }

    // Guardar datos para su próximo uso (borramos la contraseña por seguridad)
    function saveDraft() {
        const draft = {
            username: usernameInput.value,
            email: emailInput.value,
            termsChecked: termsCheckbox.checked,
            savedAt: new Date().toISOString()
        };
        localStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
    }

    // Cargar borrador si existe
    function loadDraft() {
        const raw = localStorage.getItem(DRAFT_KEY);
        if (!raw) return;
        try {
            const draft = JSON.parse(raw);
            if (draft.username) usernameInput.value = draft.username;
            if (draft.email) emailInput.value = draft.email;
            if (typeof draft.termsChecked === 'boolean') termsCheckbox.checked = draft.termsChecked;
        } catch (e) {
            console.warn('No se pudo parsear el draft de localStorage', e);
        }
    }

    // Cargar usuario registrado (si quieres rellenar con datos de un registro previo)
    function loadRegisteredUser() {
        const raw = localStorage.getItem(REGISTERED_KEY);
        if (!raw) return;
        try {
            const user = JSON.parse(raw);
            // Solo rellenamos username y email por seguridad; no rellenamos password automáticamente
            if (user.username) usernameInput.value = user.username;
            if (user.email) emailInput.value = user.email;
        } catch (e) {
            console.warn('No se pudo parsear el usuario registrado', e);
        }
    }

    // Simula envío de correo (reemplazar por backend en producción)
    function sendConfirmationEmail(email) {
        alert(`Se ha enviado un correo de confirmación a: ${email}`);
    }

    // Eventos: validar y guardar borrador (no guardamos contraseña en el borrador)
    usernameInput.addEventListener('input', () => { validateForm(); saveDraft(); });
    emailInput.addEventListener('input', () => { validateForm(); saveDraft(); });
    passwordInput.addEventListener('input', validateForm);
    termsCheckbox.addEventListener('change', () => { validateForm(); saveDraft(); });

    // Acción de registro
    registerBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (registerBtn.disabled) return;

        const userData = {
            username: usernameInput.value,
            email: emailInput.value,
            password: passwordInput.value // No guardar contraseñas en texto plano en producción
        };
        // Guardamos usuario registrado
        localStorage.setItem(REGISTERED_KEY, JSON.stringify(userData));
        // Borramos el borrador ya que se completó el registro
        localStorage.removeItem(DRAFT_KEY);

        sendConfirmationEmail(emailInput.value);
        window.location.href = 'login.html';
    });


    loadDraft();
    if (!localStorage.getItem(DRAFT_KEY)) {
        loadRegisteredUser();
    }

    validateForm();
});