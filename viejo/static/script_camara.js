var socket = io.connect('http://127.0.0.1:5000');
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const captureButton = document.getElementById('capture');
const context = canvas.getContext('2d');

// Activar la cámara
navigator.mediaDevices.getUserMedia({ video: true })
    .then(function(stream) {
        video.srcObject = stream;
    })
    .catch(function(err) {
        console.log("Error al acceder a la cámara: ", err);
    });

// Capturar la imagen
captureButton.addEventListener('click', function() {
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageData = canvas.toDataURL('image/png');

    // Enviar la imagen al servidor para realizar el reconocimiento facial
    fetch('/submit_image', {
        method: 'POST',
        body: JSON.stringify({ image: imageData }),
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    // .then(data => {
    //     if (data.cuil) {

    //         alert(`Empleado identificado: ${data.nombre_apellido}, DNI: ${data.dni}`);

    //         // // Abrir la vista /generalfood en una nueva pestaña
    //         // const nuevaVentana = window.open('/generalfood', '_blank');

    //         // // Emitir el DNI a través de Socket.IO
    //         // socket.emit('cuil_detected', { ciul: data.cuil });

    //         // // Esperar a que la nueva ventana cargue y enviar el DNI al input de la vista /generalfood
    //         // nuevaVentana.onload = function() {
    //         //     nuevaVentana.document.getElementById('buscar-nombre').value = data.cuil;
    //         //     nuevaVentana.document.getElementById('buscar-nombre').dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
    //         // };
    //     } else {
    //         alert("No se encontró ninguna coincidencia.");
    //     }
    // })
    .catch(error => {
        console.error("Error en el reconocimiento facial:", error);
    });
});