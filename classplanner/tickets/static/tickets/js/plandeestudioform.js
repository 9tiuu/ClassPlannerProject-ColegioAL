const divPlan = document.getElementById("plan-div");
const errorClasses = "bg-red-100 dark:bg-red-900 p-4 mb-4 text-sm text-red-700 rounded-lg dark:text-red-300";
const btnSubmitAll = document.getElementById("submit-all");
const errorBox = document.getElementById("error-msg");

const getPlanForms = () => document.querySelectorAll("#plan-form > form");
const getCheckedAsignaturas = () => {
    const selectAsignaturas = document.getElementById("asignaturas-select");
    return selectAsignaturas
        ? selectAsignaturas.querySelectorAll('input[type="checkbox"]:checked')
        : [];
};

const setFormInputsState = (enabled) => {
    const planForms = getPlanForms();
    const btnGetForm = document.getElementById("agregar-curso");

    if (btnGetForm) {
        btnGetForm.disabled = !enabled;
    }

    planForms.forEach((form) => {
        const cursoInput = form.querySelector("[name='curso_id']");
        const horasInputs = form.querySelectorAll("[name='hrs_asignatura']");
        const btnDelete = form.querySelector("[name='btn-delete-form']");

        if (cursoInput) cursoInput.disabled = !enabled;
        horasInputs.forEach((input) => {
            input.disabled = !enabled;
        });

        if (btnDelete) {
            btnDelete.disabled = !enabled;
            btnDelete.className = enabled
                ? "ml-2 my-2 w-10 h-10 text-red-700 dark:text-red-300 rounded bg-red-100 hover:bg-red-300 dark:bg-red-900 dark:text-white border border-red-300 dark:border-slate-700 flex items-center justify-center"
                : "ml-2 my-2 w-10 h-10 text-red-300 dark:text-red-100 rounded bg-red-100 dark:bg-red-900 dark:text-white border border-red-200 dark:border-slate-700 flex items-center justify-center";
        }
    });
};

const inputTrigger = () => {
    const planForms = getPlanForms();
    const checkedAsignaturas = getCheckedAsignaturas();

    if (!btnSubmitAll || !errorBox) return;

    const hasAsignaturasChecked = checkedAsignaturas.length > 0;
    setFormInputsState(hasAsignaturasChecked);

    if (!hasAsignaturasChecked) {
        btnSubmitAll.disabled = true;
        errorBox.textContent = "Seleccione asignaturas";
        errorBox.className = errorClasses;
        return;
    }

    btnSubmitAll.disabled = planForms.length === 0;

    const cursos = Array.from(planForms)
        .map(planForm => planForm.querySelector("[name='curso_id']")?.value)
        .filter((cursoValue, index, arr) => cursoValue && arr.indexOf(cursoValue) !== index);
    const cursosRepetidos = Array.from(cursos);
    const DivErrorForm = document.querySelectorAll("#error-msg-form > div");

    if (DivErrorForm.length != 0) {
        DivErrorForm.forEach(e => e.remove());
    }

    let errorMessage = "";

    planForms.forEach((planForm, formIndex) => {
        const cursoInput = planForm.querySelector("[name='curso_id']");
        const horasInputs = planForm.querySelectorAll("[name='hrs_asignatura']");
        const divHrs = planForm.querySelector(".hrs-crear-plan")
            || planForm.querySelector("#hrs-crear-plan");
        const horasAsignadas = Array.from(horasInputs).reduce((total, input) => {
            return total + (input.value === "" ? 0 : parseFloat(input.value));
        }, 0);
        const SobreHorasMax = Array.from(horasInputs).some(input => parseFloat(input.value) > 8);
        const cursoVacio = !cursoInput || cursoInput.value === "";
        const asignaturaVacia = horasInputs.length === 0
            || Array.from(horasInputs).some(input => input.value === "");

        if (!divHrs) return;

        let totalInput = divHrs.querySelector("[name='hrs_asignadas']");
        if (!totalInput) {
            const totalLabel = document.createElement("label");
            totalLabel.htmlFor = `hrs-asignadas-${formIndex}`;
            totalLabel.textContent = "Horas asignadas:";
            totalInput = document.createElement("input");
            totalInput.type = "number";
            totalInput.name = "hrs_asignadas";
            totalInput.id = `hrs-asignadas-${formIndex}`;
            totalInput.disabled = true;
            divHrs.append(totalLabel, totalInput);
        }
        totalInput.value = horasAsignadas;

        let totalRef = divHrs.querySelector("[name='hrs_totales']");
        if (!totalRef) {
            const totalRefLabel = document.createElement("label");
            totalRefLabel.htmlFor = `hrs-totales-${formIndex}`;
            totalRefLabel.textContent = "Horas totales:";
            totalRef = document.createElement("input");
            totalRef.type = "number";
            totalRef.name = "hrs_totales";
            totalRef.id = `hrs-totales-${formIndex}`;
            totalRef.disabled = true;
            divHrs.append(totalRefLabel, totalRef);
        }
        totalRef.value = "30";

        if (cursoInput && cursosRepetidos.includes(cursoInput.value)) {
            errorMessage = "Hay cursos repetidos";
        } else if (!errorMessage && (cursoVacio || asignaturaVacia) && !(horasInputs.length == 0)) {
            errorMessage = "Por favor, complete todos los campos";
        } else if (!errorMessage && SobreHorasMax) {
            errorMessage = "Hay asignaturas que superan las horas máximas";
        }
    });

    btnSubmitAll.disabled = planForms.length === 0 || Boolean(errorMessage);
    errorBox.textContent = errorMessage;
    errorBox.className = errorMessage ? errorClasses : "";
};

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

if (divPlan) {
    ['input', 'submit'].forEach(eventType => {
        divPlan.addEventListener(eventType, inputTrigger);
    });
}