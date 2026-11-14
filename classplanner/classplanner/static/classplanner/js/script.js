const dropdown_user = document.getElementById('dropdown-user');
const user_button = document.getElementById('user-buttom');

user_button.addEventListener('click', function (e) {
    e.stopPropagation();
    dropdown_user.classList.toggle('hidden');
});

document.addEventListener('click', function (e) {
    if (!dropdown_user.contains(e.target) && !user_button.contains(e.target)) {
        dropdown_user.classList.add('hidden');
    }
});

const sidebar_buttom = document.getElementById('sidebar-buttom');
const sidebar_dropdown = document.getElementById('top-bar-sidebar');

sidebar_buttom.addEventListener('click', function (e) {
    e.stopPropagation();
    sidebar_dropdown.classList.toggle('-translate-x-full');
});


// barra de búsqueda https://www.html-code-generator.com/javascript/table-search
const input = document.getElementById("search-input");
const table = document.getElementById("data-table");
const rows = table.querySelectorAll("tr");

const searchTable = () => {
    const filter = input.value.toLowerCase().trim();
    // show hide input clear icon
    rows.forEach((row, index) => {
        // Skip header row
        if (index === 0) return;
        // Flag to determine if the row should be displayed
        let row_found = false;

        const cells = row.querySelectorAll("td[name='search']");
        for (let cell of cells) {
            // Check if the cell's text content matches the filter
            if (cell.textContent.toLowerCase().includes(filter)) {
                row_found = true;
                // Stop searching through cells once a match is found
                break;
            }
        }

        // Loop through each cell in the current row
        row.style.display = row_found ? '' : 'none';
    });
};

// usage

// for large table search you can use Debounce function
// Debounce the search function to improve performance
const debounce = (fn, delay) => {
    let timeoutId;
    return (...args) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => fn(...args), delay);
    };
};

const debouncedSearch = debounce(searchTable, 200);

// Add event listener to the input element
input.addEventListener("input", debouncedSearch);