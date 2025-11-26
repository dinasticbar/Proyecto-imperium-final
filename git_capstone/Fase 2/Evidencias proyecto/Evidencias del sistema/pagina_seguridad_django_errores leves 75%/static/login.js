document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const messageDiv = document.getElementById('loginMessage');

    if (username === 'admin' && password === '1234') {
        messageDiv.textContent = '¡Login exitoso!';
        messageDiv.style.color = 'green';
    } else {
        messageDiv.textContent = 'Usuario o contraseña incorrectos.';
        messageDiv.style.color = 'red';
    }
});
