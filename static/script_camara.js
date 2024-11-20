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

// Función para abrir una ventana, escuchar Enter, manejar impresión y cerrar
function openAndHandlePrint(url) {
    const newWindow = window.open(url, "_blank");
    console.log(url);

    if (newWindow) {
        // Escuchar la tecla Enter en la nueva ventana
        // newWindow.addEventListener("keydown", function (event) {
        //     if (event.key === "Enter") {
        //         console.log("Tecla Enter detectada. Mostrando opción de imprimir.");
        //         newWindow.print();
        //     }
        // });

        // Manejar evento antes de imprimir
        newWindow.addEventListener("beforeprint", function () {
            console.log("Se inició la impresión en la nueva ventana.");
        });

        // Manejar evento después de imprimir
        newWindow.addEventListener("afterprint", function () {
            console.log("Se terminó la impresión. Cerrando la ventana.");
            newWindow.close();
        });

        // Fallback para navegadores sin soporte de eventos de impresión
        newWindow.onbeforeunload = function () {
            console.log("La ventana ha sido cerrada.");
        };
    } else {
        console.error("No se pudo abrir la nueva ventana.");
    }
}

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
            openAndHandlePrint("https://generalfoodargentina.movizen.com/pwa/inicio");
            // openAndHandlePrint("https://terragene.life/terrarrhh/generalfood");
        } else if (data.status === 'confirmation_pending') {
            // El servidor indica que el DNI está pendiente de confirmación.

            socket.once('confirm_dni', function(confirmData) {

                const dni = confirmData.dni;
                const dni_modificado = confirmData.dni_modificado;
                const nombre = confirmData.nombre_apellido;
                
                // Mostrar mensaje de confirmación al usuario
                const confirmed = window.confirm(`DNI detectado: ${dni_modificado} para ${nombre}\n¿Es correcto?`);

                if (confirmed) {
                    // Si el usuario confirma, envía la respuesta positiva al servidor
                    socket.emit('confirm_dni_response', { dni: dni, confirmed: true });
                } else {
                    // Si el usuario cancela, pide que ingrese el DNI manualmente y abre la web
                    alert("Por favor, ingrese el DNI manualmente.");
                    openAndHandlePrint("https://generalfoodargentina.movizen.com/pwa/inicio");
                    // openAndHandlePrint("https://terragene.life/terrarrhh/generalfood");
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
        // Abre la página y espera a que cargue para completar el DNIi
        console.log('llegue hasta aca')
        const newWindow = window.open("https://generalfoodargentina.movizen.com/pwa/inicio", "_blank");

        // const newWindow = window.open("https://terragene.life/terrarrhh/generalfood", "_blank");
        if (!newWindow) {
            console.error("No se pudo abrir la nueva ventana. Asegúrate de permitir ventanas emergentes.");
            return;
        }
        // Espera a que la nueva página cargue antes de ejecutar el script
        const checkWindowLoaded = setInterval(function() {
            try {
                // Verifica si el documento está completamente cargado
                if (newWindow.document && newWindow.document.readyState === 'complete') {
                    clearInterval(checkWindowLoaded);

                    console.log("La nueva ventana cargó correctamente.");
                // Selecciona el primer campo de entrada que encuentre
                // const dniField = newWindow.document.getElementById("ion-input-0");
                // const x = 162; // Coordenada x
                // const y = 392.125; // Coordenada y
                const x = 526.5; // Coordenada x
                const y = 440.45001220; // Coordenada y
                const dniField = newWindow.document.elementFromPoint(x, y);
                console.log('dniField')
                console.log(dniField)
                // const dniField = newWindow.document.getElementById("ion-input-0");
                
                if (dniField) {
                    let dni = String(data.dni);
                    let dni_modif = dni.slice(2, 10);
                    console.log(dni_modif);
                    dniField.click(); // Enfoca el campo para asegurarse de que esté activo
                    dniField.focus(); // Enfoca el campo para asegurarse de que esté activo
                    dniField.value = dni_modif; // Autocompleta el DNI

                    // Dispara el evento 'input' para asegurar que el valor sea reconocido
                    dniField.dispatchEvent(new Event('input'));

                    // Simula la tecla 'Enter' para enviar el formulario
                    dniField.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));

                    // Intenta simular el envío (si el evento 'keydown' no funciona)
                    setTimeout(() => {
                        // Si hay un formulario, envíalo directamente
                        const form = dniField.closest('form');
                        if (form) {
                            form.submit();
                        } else {
                            // Simula la tecla 'Enter'
                            dniField.dispatchEvent(new KeyboardEvent('keydown', {
                                key: 'Enter',
                                bubbles: true,
                                cancelable: true
                            }));
                        }
                    }, 100); // Tiempo para permitir que los cambios se procesen
                }
                console.log('se presiono enter')
                // newWindow.addEventListener("keydown", function (event) {
                //     if (event.key === "Enter") {
                //         console.log("Tecla Enter detectada. Mostrando opción de imprimir.");
                //         newWindow.print();
                //     }
                // });
        
                // Manejar evento antes de imprimir
                newWindow.addEventListener("beforeprint", function () {
                    console.log("Se inició la impresión en la nueva ventana.");
                });
        
                // Manejar evento después de imprimir
                newWindow.addEventListener("afterprint", function () {
                    console.log("Se terminó la impresión. Cerrando la ventana.");
                    newWindow.close();
                });
        
                // Fallback para navegadores sin soporte de eventos de impresión
                newWindow.onbeforeunload = function () {
                    console.log("La ventana ha sido cerrada.");
                };
            }
            } catch (e) {
                console.error("Error verificando el estado de la nueva ventana:", e);
            }
        }, 100);
    }
});
