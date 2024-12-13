var socket = io({path: '/terrarrhh/socket.io'});
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const captureButton = document.getElementById('capture');
const context = canvas.getContext('2d');

socket.on('connect', function() {
    console.log('Conectado al servidor');
    socket.emit('mi_evento', {data: 'Hola servidor'});
});

// Función para activar una cámara específica
function activateCamera(deviceId) {
    const constraints = {
        video: {
            deviceId: { ideal: deviceId }
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
        activateCamera(videoDevices[0].deviceId);
    })
    .catch(error => {
        console.error("Error al enumerar dispositivos:", error);
    });

// El servidor indica que el DNI está pendiente de confirmación.
socket.once('confirm_dni', function(confirmData) {
    console.log('llegue al confirm dni')
    let dni = confirmData.dni;
    const cuil = confirmData.employeeInfoCompletaBD['cuil'];
    const nombre_completo = confirmData.employeeInfoCompletaBD['nombre_apellido'];
    
    const confirmed = window.confirm(`DNI detectado: ${dni} para ${nombre_completo}\n¿Es correcto?`);

    if (confirmed) {
        // Si el usuario confirma, envía la respuesta positiva al servidor para actualizar la base de datos
        socket.emit('confirm_dni_response', { cuil: cuil, confirmed: true });
    } else {
        dni = prompt("Por favor, ingrese el DNI manualmente.");
        console.log('dni script camara:')
        console.log(dni)
        if (dni !== null){
            socket.emit('update_db', dni);
        } else {
            socket.emit('update_dni_global', 0)
        }
    }
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
        console.log('llegue al fetch')
        console.log(data.status)
        if (data.status === 'no_match') {
            const dni = prompt("No se ha reconocido a la persona. Por favor, ingrese el DNI manualmente.");
            if (dni !== null){
                socket.emit('update_db', dni);
            } else {
                socket.emit('update_dni_global', 0)
            }

        } 
    })
    .catch(error => {
        console.error("Error en el reconocimiento facial:", error);
    });
});


// Espera el evento de la impresion
socket.on('actualizacion_bd', function(data) {
    if (data.actualizacion === 'pedido') {
        alert('Ya pidió menú el día de hoy')
    } else if (data.actualizacion === 'registrado'){
        // Mostrar el indicador de carga
        const loadingElement = document.createElement('div');
        loadingElement.id = 'loading';
        loadingElement.style.position = 'fixed';
        loadingElement.style.top = '0';
        loadingElement.style.left = '0';
        loadingElement.style.width = '100%';
        loadingElement.style.height = '100%';
        loadingElement.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
        loadingElement.style.display = 'flex';
        loadingElement.style.alignItems = 'center';
        loadingElement.style.justifyContent = 'center';
        loadingElement.style.fontSize = '20px';
        loadingElement.style.zIndex = '9999';
        loadingElement.textContent = 'Cargando...';
        
        document.body.appendChild(loadingElement);

        // Simula una acción o espera antes de quitar el indicador de carga
        setTimeout(() => {
            document.body.removeChild(loadingElement);
        }, 3000); // Simula 3 segundos de carga
    } else if (data.actualizacion === 'nomach'){
        alert('No se encuentra en la base de datos. Contáctese con el administrador')
    } else if (data.actualizacion === ''){
        alert('DNI no confirmado. Cierre y vuelva a iniciar el programa')
    }
});
