const dropdown_user = document.getElementById('dropdown-user');
const user_buttom = document.getElementById('user-buttom');

user_buttom.addEventListener('click', function (e) {
    e.stopPropagation();
    dropdown_user.classList.toggle('hidden');
});

document.addEventListener('click', function (e) {
    if (!dropdown_user.contains(e.target) && !user_buttom.contains(e.target)) {
        dropdown_user.classList.add('hidden');
    }
});

const sidebar_buttom = document.getElementById('sidebar-buttom');
const sidebar_dropdown = document.getElementById('top-bar-sidebar');

sidebar_buttom.addEventListener('click', function (e) {
    e.stopPropagation();
    sidebar_dropdown.classList.toggle('-translate-x-full');
});

// console.log(horaactual);