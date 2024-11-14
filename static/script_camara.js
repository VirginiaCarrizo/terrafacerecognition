var socket = io({path: '/terrarrhh/socket.io'});
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const captureButton = document.getElementById('capture');
const context = canvas.getContext('2d');

socket.on('connect', function() {
    console.log('Conectado al servidor');
    socket.emit('mi_evento', {data: 'Hola servidor'});
});

socket.on('mi_respuesta', function(data) {
    console.log('Respuesta del servidor:', data);
});

// Función para activar una cámara específica
function activateCamera(deviceId) {
    const constraints = {
        video: {
            deviceId: { exact: deviceId }
        }
    };

    navigator.mediaDevices.getUserMedia(constraints)
        .then(function(stream) {
            video.srcObject = stream;  // Muestra el video en el elemento de video
        })
        .catch(function(err) {
            console.log("Error al acceder a la cámara: ", err);
        });
}
// Enumerar dispositivos y activar una cámara que no sea la predeterminada
navigator.mediaDevices.enumerateDevices()
    .then(devices => {
        const videoDevices = devices.filter(device => device.kind === 'videoinput');
        console.log(videoDevices)
        activateCamera(videoDevices[0].deviceId);
    })
    .catch(error => {
        console.error("Error al enumerar dispositivos:", error);
    });

// Capturar la imagen
captureButton.addEventListener('click', function() {
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageData = canvas.toDataURL('image/png');

    // Enviar la imagen al servidor para realizar el reconocimiento facial
    fetch('/terrarrhh/submit_image', {
        method: 'POST',
        body: JSON.stringify({ image: imageData }),
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'no_match') {
            // Alerta para indicar que no se ha reconocido a la persona
            alert("No se ha reconocido a la persona. Por favor, ingrese el DNI manualmente.");
            
            // Abrir la página una vez que el usuario presione "Aceptar"
            window.open("https://generalfoodargentina.movizen.com/pwa/inicio", "_blank");
        } else if (data.status === 'confirmation_pending') {
            // El servidor indica que el DNI está pendiente de confirmación.
            console.log('entro al elif')
            socket.once('confirm_dni', function(confirmData) {
                console.log('entro socket once')
                const dni = confirmData.dni;
                const dni_modificado = confirmData.dni_modificado;
                const nombre = confirmData.nombre_apellido;
                console.log(confirmData.dni)
                console.log(confirmData.nombre_apellido)
                
                // Mostrar mensaje de confirmación al usuario
                const confirmed = window.confirm(`DNI detectado: ${dni_modificado} para ${nombre}\n¿Es correcto?`);

                if (confirmed) {
                    // Si el usuario confirma, envía la respuesta positiva al servidor
                    socket.emit('confirm_dni_response', { dni: dni, confirmed: true });
                } else {
                    // Si el usuario cancela, pide que ingrese el DNI manualmente y abre la web
                    alert("Por favor, ingrese el DNI manualmente.");
                    window.open("https://generalfoodargentina.movizen.com/pwa/inicio", "_blank");
                }
            });
        }
    })
    .catch(error => {
        console.error("Error en el reconocimiento facial:", error);
    });
});

// Recibir el resultado de la confirmación de DNI y abrir la web automáticamente si se confirma
socket.on('dni_confirmation_result', function(data) {
    if (data.status === 'success') {
        // Abre la página y espera a que cargue para completar el DNI
        const newWindow = window.open("https://generalfoodargentina.movizen.com/pwa/inicio", "_blank");

        // Espera a que la nueva página cargue antes de ejecutar el script
        newWindow.onload = function() {
            const dniField = newWindow.document.querySelector("dni_input"); // Selecciona el input del DNI

            if (dniField) {
                dniField.value = data.dni; // Autocompleta el DNI
                dniField.focus(); // Enfoca el campo para asegurarse de que esté activo

                // Dispara el evento 'input' para asegurar que el valor sea reconocido
                dniField.dispatchEvent(new Event('input'));

                // Simula la tecla 'Enter' para enviar el formulario
                dniField.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
            } else {
                console.error("No se encontró el campo de DNI en la página.");
            }
        };
    }
});
// // Recibir el resultado de la confirmación de DNI y abrir la web automáticamente si se confirma
// socket.on('dni_confirmation_result', function(data) {
//     if (data.status === 'success') {
//         // Aquí se abre la página automáticamente y completa el DNI
//         socket.emit('open_page_and_enter_dni', { dni: data.dni });
//     }
// });