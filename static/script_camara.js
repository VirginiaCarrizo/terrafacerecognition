var socket = io({path: '/terrarrhh/socket.io'});
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const captureButton = document.getElementById('capture');
const context = canvas.getContext('2d');

socket.on('connect', function() {
    console.log('Conectado al servidor');
    socket.emit('mi_evento', {data: 'Hola servidor'});
});

function spinner(time){
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
    }, time); // Simula 3 segundos de carga
}
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

function customConfirm(message) {
    return new Promise((resolve) => {
        const modal = document.getElementById('custom-confirm');
        const messageElement = document.getElementById('custom-confirm-message');
        const yesButton = document.getElementById('custom-confirm-yes');
        const noButton = document.getElementById('custom-confirm-no');

        // Configurar el mensaje
        messageElement.textContent = message;

        // Mostrar el modal
        modal.classList.remove('hidden');

        // Manejar clic en "Sí"
        yesButton.onclick = () => {
            modal.classList.add('hidden');
            resolve(true); // Resuelve con `true` si el usuario acepta
        };

        // Manejar clic en "No"
        noButton.onclick = () => {
            modal.classList.add('hidden');
            resolve(false); // Resuelve con `false` si el usuario cancela
        };
    });
}

function customPrompt(message) {
    return new Promise((resolve) => {
        const modal = document.getElementById('custom-prompt');
        const messageElement = document.getElementById('custom-prompt-message');
        const inputElement = document.getElementById('custom-prompt-input');
        const okButton = document.getElementById('custom-prompt-ok');
        const cancelButton = document.getElementById('custom-prompt-cancel');

        // Configurar el mensaje y mostrar el modal
        messageElement.textContent = message;
        modal.classList.remove('hidden');

        // Limpiar el input y enfocarlo automáticamente
        inputElement.value = '';
        inputElement.focus();

        // Manejar clic en "Aceptar"
        okButton.onclick = () => {
            const inputValue = inputElement.value.trim(); // Elimina espacios adicionales
            modal.classList.add('hidden');
            resolve(inputValue || null); // Si el campo está vacío, resolver con null
        };

        // Manejar clic en "Cancelar"
        cancelButton.onclick = () => {
            modal.classList.add('hidden');
            resolve(null); // Resuelve con null si se cancela
        };

        // Manejar "Enter" dentro del input
        const onKeyPress = (event) => {
            if (event.key === 'Enter') {
                okButton.click();
            }
        };

        inputElement.addEventListener('keypress', onKeyPress);

        // Limpiar eventos al cerrar el modal
        const cleanup = () => {
            okButton.onclick = null;
            cancelButton.onclick = null;
            inputElement.removeEventListener('keypress', onKeyPress);
        };

        // Agregar cleanup cuando el modal se oculta
        modal.addEventListener('transitionend', cleanup, { once: true });
    });
}


// Capturar la imagen
captureButton.addEventListener('click', function() {
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageData = canvas.toDataURL('image/png');
    spinner(1500)
    // Enviar la imagen al servidor para realizar el reconocimiento facial
    fetch('/terrarrhh/submit_image', {
        method: 'POST',
        body: JSON.stringify({ image: imageData }),
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(async data => {
        console.log('llegue al fetch')
        console.log(data.status)
        if (data.status === 'success') {
            let dni = data.dni;
            const cuil = data.employeeInfoCompletaBD['cuil'];
            const nombre_completo = data.employeeInfoCompletaBD['nombre_apellido'];
            
            const confirmed = await customConfirm(`DNI detectado: ${dni} para ${nombre_completo}\n¿Es correcto?`);

            if (confirmed) {
                socket.emit('confirm_dni_response', { cuil: cuil, dni: null, confirmed: true });
            } else {
                const dni = await customPrompt("Por favor, ingrese el DNI manualmente.");
                if (dni !== null){
                    socket.emit('confirm_dni_response', { cuil: null, dni: dni, confirmed: true });
                } else {
                    socket.emit('confirm_dni_response', { cuil: null, dni: 0, confirmed: false })
                }
            }
        } else if (data.status === 'no_match') {
            const dni = await customPrompt("Por favor, ingrese el DNI manualmente.");
            if (dni !== null){
                socket.emit('confirm_dni_response', { cuil: null, dni: dni, confirmed: true });
            } else {
                socket.emit('confirm_dni_response', { cuil: null, dni: 0, confirmed: false })
            }

        }
    })
    .catch(error => {
        console.error("Error en el reconocimiento facial:", error);
    });
});



socket.on('alertas', function(data) {
    if (data.actualizacion === 'pedido') {
        console.log('pedido')
        spinner(7000)
        // location.reload();
    } else if (data.actualizacion === 'registrado'){
        console.log('registrado')
        spinner(7000)
    } else if (data.actualizacion === 'nomach'){
        alert('No se encuentra en la base de datos. Contáctese con el administrador')
        // location.reload();
    } else if (data.actualizacion === ''){
        alert('DNI no confirmado. Intente nuevamente')
        // location.reload();
    }
});
