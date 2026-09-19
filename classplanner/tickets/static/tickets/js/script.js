const dropdown_user = document.getElementById('dropdown-user');
const user_button = document.getElementById('user-button');

function exitConfirm(button) {
    Swal.fire({
        "title": "¿Está seguro que desea salir?",
        "text": "No se guardarán los cambios.",
        "icon": "warning",
        "showCancelButton": true,
        "confirmButtonColor": "#0d6efd",
        "cancelButtonColor": '#d33',
        "confirmButtonText": 'Si, salir',
        "cancelButtonText": 'Cancelar',
    }).then((r) => {
        if (!r.isConfirmed) return;

        if (button.id != '') {
            window.location.assign(button.dataset.url);
        } else {
            window.location.assign('/home');
        }
    });
};

user_button.addEventListener('click', function (e) {
    e.stopPropagation();
    dropdown_user.classList.toggle('hidden');
});

document.addEventListener('click', function (e) {
    if (!dropdown_user.contains(e.target) && !user_button.contains(e.target)) {
        dropdown_user.classList.add('hidden');
    }
});

const sidebar_button = document.getElementById('sidebar-button');
const sidebar_dropdown = document.getElementById('top-bar-sidebar');

sidebar_button.addEventListener('click', function (e) {
    e.stopPropagation();
    sidebar_dropdown.classList.toggle('-translate-x-full');
});

// console.log(horaactual);