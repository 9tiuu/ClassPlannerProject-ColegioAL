let casillaOrigen = null;

document.querySelectorAll('.casilla').forEach(casilla => {
    casilla.draggable = true;
});

// iniciar arrastre
document.addEventListener('dragstart', function (e) {
    const casilla = e.target.closest('.casilla');
    const asignatura = casilla.querySelector('.in-asignatura');
    if (!casilla) return;

    // evita arrastrar casillas vacías
    if (!asignatura || !asignatura.value) {
        e.preventDefault();
        return;
    }

    casillaOrigen = casilla;
    e.dataTransfer.setData('text/plain', 'movimiento');
    e.dataTransfer.effectAllowed = 'move';
    casilla.classList.add('opacity-40');
});

// finalizar arrastre
document.addEventListener('dragend', function (e) {
    const casilla = e.target.closest('.casilla');

        if (casilla) {
            casilla.classList.remove('opacity-40');
        }
        
    casillaOrigen = null;
});

// permite soltar sobre otras casillas
document.addEventListener('dragover', function (e) {
    const destino = e.target.closest('.casilla');
    if (!destino || !casillaOrigen || destino === casillaOrigen) return;

    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
});

// permite soltar e intercambiar
document.addEventListener('drop', function (e) {
    const destino = e.target.closest('.casilla');
    if (!destino || !casillaOrigen || destino === casillaOrigen) return;
    e.preventDefault();

    // evita movimientos entre tablas/jornadas distintas
    const tablaOrigen = casillaOrigen.closest('table');
    const tablaDestino = destino.closest('table');

    if (tablaOrigen !== tablaDestino) return;
    const datosOrigen = obtenerDatos(casillaOrigen); // obtiene los datos de origen
    const datosDestino = obtenerDatos(destino); // obtiene los datos del destino

    establecerDatos(destino, datosOrigen);
    establecerDatos(casillaOrigen, datosDestino);
});

// obtener información de la casilla
function obtenerDatos(casilla) {
    return {
        asignatura: casilla.querySelector('.in-asignatura').value,
        docente: casilla.querySelector('.in-docente').value,
        aula: casilla.querySelector('.in-aula').value,

        nombreAsignatura: casilla.querySelector('.txt-asignatura').textContent,
        nombreDocente: casilla.querySelector('.txt-docente').textContent,
        nombreAula: casilla.querySelector('.txt-aula').textContent
    };
}

// actualiza la informacion de la casilla
function establecerDatos(casilla, datos) {
    casilla.querySelector('.in-asignatura').value = datos.asignatura;
    casilla.querySelector('.in-docente').value = datos.docente;
    casilla.querySelector('.in-aula').value = datos.aula;
    casilla.querySelector('.txt-asignatura').textContent = datos.nombreAsignatura;
    casilla.querySelector('.txt-docente').textContent = datos.nombreDocente;
    casilla.querySelector('.txt-aula').textContent = datos.nombreAula;

    const vacio = casilla.querySelector('.vacio');
    const asignado = casilla.querySelector('.asignado');
    const ocupado = datos.asignatura !== '';

    vacio.classList.toggle('hidden', ocupado);
    asignado.classList.toggle('hidden', !ocupado);
}