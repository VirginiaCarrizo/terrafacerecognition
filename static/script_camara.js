var socket = io({path: '/terrarrhh/socket.io'});
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const captureButton = document.getElementById('capture');
const context = canvas.getContext('2d');

socket.on('connect', function() {
    console.log('Conectado al servidor');
    socket.emit('mi_evento', {data: 'Hola servidor'});
});

let activeSpinner = null;

function spinner(){
    if (!activeSpinner) {
        activeSpinner = document.createElement('div');
        activeSpinner.id = 'loading';
        activeSpinner.style.position = 'fixed';
        activeSpinner.style.top = '0';
        activeSpinner.style.left = '0';
        activeSpinner.style.width = '100%';
        activeSpinner.style.height = '100%';
        activeSpinner.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
        activeSpinner.style.display = 'flex';
        activeSpinner.style.alignItems = 'center';
        activeSpinner.style.justifyContent = 'center';
        activeSpinner.style.fontSize = '20px';
        activeSpinner.style.zIndex = '9999';
        activeSpinner.textContent = 'Cargando...';

        document.body.appendChild(activeSpinner);
    }

    // Devuelve una función para quitar el spinner
    return function removeSpinner() {
        if (activeSpinner) {
            document.body.removeChild(activeSpinner);
            activeSpinner = null; // Resetear el spinner
        }
    };
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
        modal.classList.remove('hidden'); // Mostrar el modal

        // Limpiar el input y enfocarlo automáticamente
        inputElement.value = '';
        inputElement.focus();

        // Manejar clic en "Aceptar"
        const handleOk = () => {
            const inputValue = inputElement.value.trim();
            modal.classList.add('hidden'); // Ocultar modal
            cleanup(); // Limpiar eventos
            resolve(inputValue || null); // Resolver con el valor ingresado o null
        };

        // Manejar clic en "Cancelar"
        const handleCancel = () => {
            modal.classList.add('hidden'); // Ocultar modal
            cleanup(); // Limpiar eventos
            resolve(null); // Resolver con null
        };

        // Manejar "Enter" dentro del input
        const handleKeyPress = (event) => {
            if (event.key === 'Enter') {
                handleOk();
            }
        };

        // Limpieza de eventos
        const cleanup = () => {
            okButton.removeEventListener('click', handleOk);
            cancelButton.removeEventListener('click', handleCancel);
            inputElement.removeEventListener('keypress', handleKeyPress);
        };

        okButton.addEventListener('click', handleOk);
        cancelButton.addEventListener('click', handleCancel);
        inputElement.addEventListener('keypress', handleKeyPress);
    });
}

// Capturar la imagen
captureButton.addEventListener('click', function() {
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageData = canvas.toDataURL('image/png');
    // Mostrar spinner
    const removeSpinner1 = spinner();
    console.log('mostrar spinner 1')
    // Enviar la imagen al servidor para realizar el reconocimiento facial
    fetch('/terrarrhh/submit_image', {
        method: 'POST',
        body: JSON.stringify({ image: imageData }),
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(async data => {
        console.log(data.status)
        removeSpinner1();
        console.log('remover spinner 1')
        if (data.status === 'success') {
            let dni = data.dni;
            const cuil = data.employeeInfoCompletaBD['cuil'];
            const nombre_completo = data.employeeInfoCompletaBD['nombre_apellido'];    
            const confirmed = await customConfirm(`DNI detectado: ${dni} para ${nombre_completo}\n¿Es correcto?`);
            if (confirmed) {
                // Mostrar spinner nuevamente mientras se procesa la confirmación
                const removeSpinner2 = spinner();
                console.log('mostrar spinner 2')
                socket.emit('confirm_dni_response', { cuil: cuil, dni: null, confirmed: true });
                removeSpinner2(); // Quitar el spinner después de la confirmación
                console.log('remover spinner 2')
            } else {
                const dni = await customPrompt("Por favor, ingrese el DNI manualmente.");
                if (dni !== null){
                    // Mostrar spinner nuevamente mientras se procesa el nuevo DNI
                    const removeSpinner3 = spinner();
                    console.log('mostrar spinner 3')
                    socket.emit('confirm_dni_response', { cuil: null, dni: dni, confirmed: true });
                    removeSpinner3(); // Quitar el spinner después de procesar el DNI manual
                    console.log('remover spinner 3')
                } else {
                    socket.emit('confirm_dni_response', { cuil: null, dni: 0, confirmed: false })
                }
            }
        } else if (data.status === 'no_match') {
            // Mostrar popup para ingresar DNI manualmente
            const dni = await customPrompt("Por favor, ingrese el DNI manualmente.");
            
            if (dni !== null) {
                // Mostrar spinner nuevamente mientras se procesa el nuevo DNI
                const removeSpinner4 = spinner();
                console.log('mostrar spinner 4')
                socket.emit('confirm_dni_response', { cuil: null, dni: dni, confirmed: true });
                removeSpinner4(); // Quitar el spinner después de procesar el DNI manual
                console.log('remover spinner 4')
            } else {
                socket.emit('confirm_dni_response', { cuil: null, dni: 0, confirmed: false });
            }
            
        }
    })
    .catch(error => {
        console.error("Error en el reconocimiento facial:", error);
    })
});



socket.on('alertas', function(data) {
    const removeSpinner5 = spinner(); // Mostrar spinner al inicio de la interacción
    console.log('mostrar spinner 5')
    if (data.actualizacion === 'pedido') {
        console.log('pedido')
        removeSpinner5()
        console.log('remover spinner 5')
        // location.reload();
    } else if (data.actualizacion === 'registrado'){
        console.log('registrado')
        removeSpinner5()
        console.log('remover spinner 5 bis')
    } else if (data.actualizacion === 'nomach'){
        alert('No se encuentra en la base de datos. Contáctese con el administrador')
        // location.reload();
    } else if (data.actualizacion === ''){
        alert('DNI no confirmado. Intente nuevamente')
        // location.reload();
    }
});
