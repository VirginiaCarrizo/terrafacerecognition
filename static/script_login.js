document.getElementById("loginForm").addEventListener("submit", function(event) {
    event.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    if (username && password) {
        alert(`Bienvenido, ${username}!`);
        // Aquí puedes agregar la lógica para verificar el login.
    } else {
        alert("Por favor, complete todos los campos.");
    }
});
