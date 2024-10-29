// Función para mostrar el formulario de agregar registro y ocultar los botones
document.getElementById('btn-agregar').addEventListener('click', function() {
    const formularioRegistro = document.getElementById('form-container');
    const buttonContainer = document.querySelector('.button-container');

    formularioRegistro.classList.remove('hidden');  // Mostrar el contenedor del formulario
    buttonContainer.classList.add('hidden');  // Ocultar los botones
});



// Mostrar el campo de búsqueda al presionar "Buscar Registro"
document.getElementById('btn-buscar').addEventListener('click', function() {
    const buscarContenedor = document.getElementById('buscar-registro');
    const buttonContainer = document.querySelector('.button-container');

    buscarContenedor.classList.remove('hidden');  // Mostrar el contenedor de búsqueda
    buttonContainer.classList.add('hidden');  // Ocultar los botones principales
});

let timeout = null;
document.getElementById('buscar-nombre').addEventListener('input', function() {
    const searchTerm = this.value.toLowerCase().trim();  // Convertimos el valor a minúsculas
    const sugerencias = document.getElementById('sugerencias');
    
    // Ajustar el ancho del contenedor de sugerencias al ancho del input
    sugerencias.style.width = this.offsetWidth + 'px';
    clearTimeout(timeout);  // Limpiar el timeout anterior
    timeout = setTimeout(() => {
    if (searchTerm.length >= 2) {  // Verificamos si hay texto después de eliminar espacios en blanco
        fetch('/buscar_registro', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ search_term: searchTerm })
        })
        .then(response => response.json())
        .then(data => {
            mostrarSugerencias(data);  // Mostramos las sugerencias
        })
        .catch(error => {
            console.error('Error:', error);
        });
    } else {
        limpiarSugerencias();  // Limpiar las sugerencias si no hay texto
    }
    }, 300);
});

// Función para mostrar las sugerencias
function mostrarSugerencias(registros) {
    const sugerencias = document.getElementById('sugerencias');
    sugerencias.innerHTML = '';  // Limpiar sugerencias previas
    if (registros.length > 0) {
        registros.forEach(registro => {
            const div = document.createElement('div');
            div.classList.add('sugerencia-item');  // Clase para estilos

            div.textContent = `${registro.nombre_apellido} - CUIL: ${registro.cuil} - Sector: ${registro.sector}`;
            
            // Agregar evento para seleccionar una sugerencia
            div.addEventListener('click', function() {
                document.getElementById('buscar-nombre').value = `${registro.nombre_apellido}`;
                limpiarSugerencias();  // Limpiar sugerencias después de seleccionar
            });

            sugerencias.appendChild(div);
        });
        sugerencias.classList.remove('hidden');  // Mostrar el contenedor de sugerencias
    } else {
        limpiarSugerencias();  // Si no hay sugerencias, ocultar el contenedor
    }
}

// Función para limpiar las sugerencias
function limpiarSugerencias() {
    const sugerencias = document.getElementById('sugerencias');
    sugerencias.innerHTML = '';  // Limpiar el contenido
    sugerencias.classList.add('hidden');  // Ocultar el contenedor
}

// Ocultar sugerencias al hacer clic fuera del input o la barra de sugerencias
document.addEventListener('click', function(event) {
    const buscarInput = document.getElementById('buscar-nombre');
    const sugerencias = document.getElementById('sugerencias');
    
    // Si el clic no fue dentro del input de búsqueda o el contenedor de sugerencias
    if (!buscarInput.contains(event.target) && !sugerencias.contains(event.target)) {
        limpiarSugerencias();  // Ocultar las sugerencias
    }
});

document.getElementById('buscar').addEventListener('click', function() {
    const searchTerm = document.getElementById('buscar-nombre').value.toLowerCase();  // Obtenemos el valor del input

    if (searchTerm) {
        fetch('/buscar_registro', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ search_term: searchTerm })
        })
        .then(response => response.json())
        .then(data => {
            
            if (data.length > 0) {
                const registro = data[0];  // Tomamos el primer resultado
                // console.log(data[[0]])
                const key = registro.key;  // Obtenemos la 'key' del registro
                mostrarRegistro(data[0], key);  // Si hay registros, mostramos el primero encontrado
            } else {
                alert('No se encontró ningún registro.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ocurrió un error en el servidor.');
        });
    } else {
        alert('Por favor, ingrese un término de búsqueda.');
    }
});

// Función para mostrar el registro y ocultar el input de búsqueda
function mostrarRegistro(registro, key) {
    const buscarContenedor = document.getElementById('buscar-registro');
    const resultadoContenedor = document.getElementById('resultado-registro');
    const buttonContainer = document.querySelector('.button-container');  // Seleccionar el contenedor de los botones
 
    // Ocultar el contenedor de búsqueda
    buscarContenedor.classList.add('hidden');
    // Ocultar el contenedor de botones
    buttonContainer.classList.add('hidden');

    // Llenar los campos con los datos del registro
    document.getElementById('modificar-legajo').value = registro.legajo;
    document.getElementById('modificar-nombre').value = registro.nombre_apellido;
    document.getElementById('modificar-cuil').value = registro.cuil;
    document.getElementById('modificar-fecha-nacimiento').value = registro.fecha_nacimiento || 'No disponible';
    document.getElementById('modificar-empresa').value = registro.empresa || 'No disponible';
    document.getElementById('modificar-rol').value = registro.rol || 'No disponible';
    document.getElementById('modificar-sector').value = registro.sector || 'No disponible';
    
    // Mostrar la foto si existe
    const fotoElement  = document.getElementById('foto-busqueda');

    if (registro.foto) {
        // Verifica si el dato 'foto' está en formato base64 o es una URL pública
        fotoElement.src = `data:image/png;base64,${registro.foto}`;

        fotoElement.alt = `Foto de ${registro.nombre_apellido}`;
    } else {
        fotoElement.src = '';  // Si no hay foto, dejamos el src vacío
        fotoElement.alt = 'Sin foto disponible';
    }

    resultadoContenedor.classList.remove('hidden');
}

// Agregar funcionalidad para modificar el registro
document.getElementById('modificar-registro').addEventListener('click', function() {
    modificarRegistro();
});

// Funcionalidad para eliminar el registro
document.getElementById('eliminar-registro').addEventListener('click', function() {
    if (confirm(`¿Estás seguro de que deseas eliminar el registro?`)) {
        eliminarRegistro();
    }
});

// Agregar un botón para volver a buscar
document.getElementById('volver-buscar').addEventListener('click', function() {
    const buscarContenedor = document.getElementById('buscar-registro');
    const resultadoContenedor = document.getElementById('resultado-registro');
    const sugerencias = document.getElementById('sugerencias');
    const buscarInput = document.getElementById('buscar-nombre');
    
    // Ocultar el contenedor de resultados y mostrar el contenedor de búsqueda
    resultadoContenedor.classList.add('hidden');
    buscarContenedor.classList.remove('hidden');
    
    // Limpiar el campo de búsqueda y las sugerencias previas
    buscarInput.value = '';
    sugerencias.innerHTML = '';
    sugerencias.classList.add('hidden');
    
    // Opcional: Limpia también los campos de resultado si es necesario
    document.getElementById('modificar-legajo').value = '';
    document.getElementById('modificar-nombre').value = '';
    document.getElementById('modificar-cuil').value = '';
    document.getElementById('modificar-fecha-nacimiento').value = '';
    document.getElementById('modificar-empresa').value = '';
    document.getElementById('modificar-rol').value = '';
    document.getElementById('modificar-sector').value = '';
    document.getElementById('foto-busqueda').src = '';
    document.getElementById('foto-busqueda').alt = 'Sin foto disponible';
});

function modificarRegistro() {
    const legajo = document.getElementById('modificar-legajo').value;
    const nombre = document.getElementById('modificar-nombre').value;
    const cuil = document.getElementById('modificar-cuil').value;
    const fecha_nacimiento = document.getElementById('modificar-fecha-nacimiento').value;
    const empresa = document.getElementById('modificar-empresa').value;
    const rol = document.getElementById('modificar-rol').value;
    const sector = document.getElementById('modificar-sector').value;

    // Crear el objeto de datos en formato JSON
    const data = {
        legajo: legajo,
        nombre_apellido: nombre,
        cuil: cuil,
        fecha_nacimiento: fecha_nacimiento,
        empresa: empresa,
        rol: rol,
        sector: sector
    };

    // Hacer la llamada fetch con el cuerpo JSON
    fetch(`/modificar_registro/${cuil}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',  // Asegurar que el contenido es JSON
        },
        body: JSON.stringify(data)  // Convertir el objeto en JSON
    })
    .then(response => response.json())  // Parsear la respuesta a JSON
    .then(data => {
        alert(data.message);  // Mostrar un mensaje de éxito
        location.reload();  // Recargar la página después de modificar
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Función para eliminar un registro utilizando la key
function eliminarRegistro() {
    const cuil = document.getElementById('modificar-cuil').value;
    fetch('/eliminar_registro', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ cuil: cuil })  // Enviamos la key en lugar del cuil
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        location.reload();  // Recargar la página después de eliminar
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Función para cerrar el formulario de agregar registro y volver a mostrar los botones
document.getElementById('close-form').addEventListener('click', function() {
    const formularioRegistro = document.getElementById('form-container');
    const buttonContainer = document.querySelector('.button-container');

    formularioRegistro.classList.add('hidden');
    buttonContainer.classList.remove('hidden');
});

// Función para cerrar el campo de búsqueda y volver a mostrar los botones
document.getElementById('close-buscar').addEventListener('click', function() {
    const buscarContenedor = document.getElementById('buscar-registro');
    const buttonContainer = document.querySelector('.button-container');

    buscarContenedor.classList.add('hidden');
    buttonContainer.classList.remove('hidden');
});

document.getElementById('close-agregado').addEventListener('click', function() {
    const vistaRegistroAgregado = document.getElementById('vista-registro-agregado');
    const buttonContainer = document.querySelector('.button-container');

    // Ocultar la vista del registro agregado
    vistaRegistroAgregado.classList.add('hidden');

    // Mostrar el contenedor de botones principales
    buttonContainer.classList.remove('hidden');
});

document.getElementById('agregar-btn').addEventListener('click', function() {
    const legajo = document.getElementById('legajo').value;
    const nombre = document.getElementById('nombre').value;
    const apellido = document.getElementById('apellido').value;
    const cuil = document.getElementById('cuil').value;
    const empresa = document.getElementById('empresa').value;
    const fecha_nacimiento = document.getElementById('fecha-nacimiento').value;
    const rol = document.getElementById('rol').value;
    const sector = document.getElementById('sector').value;
    const foto = document.getElementById('foto').files[0]; // Foto como archivo

    if (legajo && nombre && apellido && cuil && empresa && fecha_nacimiento && rol && sector && foto) {
        const formContainer = document.getElementById('form-container');
        const buttonContainer = document.querySelector('.button-container');
        const spinnerContainer = document.getElementById('spinner-container');

        // Ocultar los botones y el formulario, y mostrar el spinner
        buttonContainer.classList.add('hidden');
        formContainer.classList.add('hidden');
        spinnerContainer.classList.remove('hidden'); // MOSTRAR EL SPINNER AQUÍ

        const formData = new FormData();
        formData.append('legajo', legajo);
        formData.append('nombre', nombre);
        formData.append('apellido', apellido);
        formData.append('cuil', cuil);
        formData.append('empresa', empresa);
        formData.append('fecha-nacimiento', fecha_nacimiento);
        formData.append('rol', rol);
        formData.append('sector', sector);
        formData.append('foto', foto);

        // Leer la foto antes de subirla para mostrarla de inmediato
        const reader = new FileReader();
        reader.onload = function(e) {
            const fotoURL = e.target.result;
            // Mostrar la foto en el contenedor de resultados
            document.getElementById('foto-agregado').src = fotoURL; // Asignar la URL base64 de la foto al src del img
        };
        reader.readAsDataURL(foto); // Convertir la imagen a base64

        fetch('/agregar_registro', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                spinnerContainer.classList.add('hidden'); // OCULTAR EL SPINNER AL TENER ÉXITO
                // Llenar los campos con la información agregada
                document.getElementById('agregado-legajo').textContent = legajo;
                document.getElementById('agregado-nombre').textContent = `${nombre} ${apellido}`;
                document.getElementById('agregado-cuil').textContent = cuil;
                document.getElementById('agregado-fecha-nacimiento').textContent = fecha_nacimiento;
                document.getElementById('agregado-empresa').textContent = empresa;
                document.getElementById('agregado-rol').textContent = rol;
                document.getElementById('agregado-sector').textContent = sector;

                // Mostrar el contenedor con la vista del registro agregado
                document.getElementById('vista-registro-agregado').classList.remove('hidden');
            } else {
                console.error('Error en el servidor:', data.message);
                spinnerContainer.classList.add('hidden'); // OCULTAR EL SPINNER EN CASO DE ERROR
            }
        })
        .catch(error => {
            console.error('Error:', error);
            spinnerContainer.classList.add('hidden'); // OCULTAR EL SPINNER EN CASO DE ERROR
        });
    } else {
        alert('Por favor, completa todos los campos.');
    }
});
