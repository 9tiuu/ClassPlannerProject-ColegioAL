const divPlan = document.getElementById("plan-div");
const crearPlan = document.getElementById("crear-plan");
const errorClasses = "bg-red-100 dark:bg-red-900 p-4 mb-4 text-sm text-red-700 rounded-lg dark:text-red-300 transition duration-200";
const getPlanForms = () => document.querySelectorAll("#plan-form > form");
const getCheckedAsignaturas = () => {
    const asignaturasSelect = document.getElementById("asignaturas-select");
    return asignaturasSelect
    ? asignaturasSelect.querySelectorAll('input[type="checkbox"]:checked')
    : [];
};
const setAsignaturas = () => {
    const asignaturas = document.getElementsByName("hrs_asignatura");
    asignaturas.forEach((input) => {
        if (input.value === "") {
            input.value = 0;
        }});
}
const setBtnDeleteState = (enabled) => {
    getPlanForms().forEach(form => { // Borrar curso
        const button = form.querySelector("[name='btn-delete-form']");
        if (!button) return;
        
        button.disabled = !enabled;
    });
};
const setBtnCrearState = (enabled) => {
    const btnSubmitAll = document.getElementById("submit-all");
    // Crear plan
    btnSubmitAll.disabled = !enabled;
};

const setErrors = (error) => { // ver posibilidad de crear lista para mostrar +1 error
    const p = document.createElement("p");
    p.textContent = error;
    const errorBox = document.querySelector("[name='div-errors']");
    if (!errorBox) return;
    if (!error) {
        errorBox.className = ""
    } else {
        console.log("!errorBox.querySelector(p): ",!errorBox.querySelector("p"))
        errorBox.className = errorClasses
    }
    errorBox.replaceChildren(p);
};

let btnCrearIsDisabled = true;
const inputTrigger = () => {
    const planForms = Array.from(getPlanForms());
    const checkedAsignaturas = getCheckedAsignaturas();
    setBtnDeleteState(planForms.length > 1);
    
    if (planForms.length != 0) {
        planForms.forEach(form => {
            const horasInputs = Array.from(form.querySelectorAll("[name='hrs_asignatura']"));
            let total = 0
            horasInputs.some(ipt => {
                const num = isNaN(ipt.valueAsNumber) ? 0 : ipt.valueAsNumber
                total = total + num
            })
            
            const cursoSelect = form.querySelector("[name='curso_id']");
            const selectedOption = cursoSelect?.selectedOptions[0];
            const horasCurso = Number(selectedOption?.dataset.horasPlanTotal ?? 0);
            const horasForm = total;
            const horasSpanCurso = selectedOption?.value
                ? Math.floor(selectedOption.dataset.horasPlanTotal) ?? ""
                : 0;
            const horasSpanForm = total !== 0 ? total : 0;
            const createDivider = () => {
                const divider = document.createElement("span");
                divider.className = "w-4 shrink-0 flex-grow border-t border-slate-300 dark:border-slate-600 sm:w-8";
                return divider;
            };
            const configureSummary = (container, name, labelText, value) => {
                container.setAttribute("name", name);
                container.className = "flex w-full min-w-0 items-center gap-2";

                const label = document.createElement("span");
                label.setAttribute("name", `${name}-label`);
                label.className = "shrink-0 whitespace-nowrap mr-2 py-2 w-[5.5rem] text-sm font-medium text-slate-700 dark:text-[#a8b2d2]";
                label.textContent = labelText;

                const valueSpan = document.createElement("span");
                valueSpan.setAttribute("name", `${name}-value`);
                valueSpan.className = "shrink-0 whitespace-nowrap mr-2 py-2 text-sm font-medium text-slate-700 dark:text-[#a8b2d2]";
                valueSpan.textContent = value;

                container.replaceChildren(label, createDivider(), valueSpan);
            };

            const cursoDiv = document.createElement("div");
            configureSummary(cursoDiv, "curso-div", "Horas Plan:", horasSpanCurso);

            const formDiv = document.createElement("div");
            configureSummary(formDiv, "hrs-totales-div", "Total:", horasSpanForm);

            const asignaturasDiv = form.querySelector("[name='hrs-asignaturas-parent']");
            let summaryContainer = form.querySelector("[name='horas-resumen']");
            if (!summaryContainer) {
                summaryContainer = document.createElement("div");
                summaryContainer.setAttribute("name", "horas-resumen");
                summaryContainer.className = "mt-2 flex w-full flex-col gap-1 border-t border-slate-200 pt-2 dark:border-slate-700";
                summaryContainer.append(cursoDiv, formDiv);
                (asignaturasDiv || form).append(summaryContainer);
            } else {
                const cursoDivElem = summaryContainer.querySelector("[name='curso-div']");
                const formDivElem = summaryContainer.querySelector("[name='hrs-totales-div']");
                const horasSpanCursoValue = cursoDivElem?.querySelector("[name='curso-div-value']");
                const horasSpanFormValue = formDivElem?.querySelector("[name='hrs-totales-div-value']");

                if (horasSpanCursoValue) {
                    horasSpanCursoValue.textContent = horasSpanCurso;
                }
                if (horasSpanFormValue) {
                    horasSpanFormValue.textContent = horasSpanForm;
                }
            }
            
            // Compara horas ingresadas y totales de plan
            if (horasForm > horasCurso) {
                summaryContainer.querySelectorAll("[name$='-label'], [name$='-value']").forEach(span => {
                    span.classList.add("text-red-700", "dark:text-red-300");
                });
            } else {
                summaryContainer.querySelectorAll("[name$='-label'], [name$='-value']").forEach(span => {
                    span.classList.remove("text-red-700", "dark:text-red-300");
                });
            }
        });
    } else {}

    if (planForms.length === 0) {
        btnCrearIsDisabled = true;
    } else if (checkedAsignaturas.length === 0) {
        setErrors("Seleccione al menos una asignatura");
        btnCrearIsDisabled = true;
    } else if (planForms.some(form => !form.querySelector("[name='curso_id']")?.value)) {
        setErrors("Seleccione cursos");
        btnCrearIsDisabled = true;
    } else if (planForms.some(form => {
        const horasInputs = Array.from(form.querySelectorAll("[name='hrs_asignatura']"));
        return horasInputs.length !== checkedAsignaturas.length
        || horasInputs.some(input => input.value === "");
    })) {    
        setErrors("Existen asignaturas sin horas asignadas");
        btnCrearIsDisabled = true;
    } else {
        planForms.some(form => {
            const horasInputs = Array.from(form.querySelectorAll("[name='hrs_asignatura']"));
            let total = 0
            horasInputs.some(ipt => {
                const num = isNaN(ipt.valueAsNumber) ? 0 : ipt.valueAsNumber
                total = total + num
            })
            const cursoSelect = form.querySelector("[name='curso_id']");
            const selectedOption = cursoSelect?.selectedOptions[0];
            const horasCurso = Number(selectedOption?.dataset.horasPlanTotal ?? 0);
            const horasForm = total;
            if (horasForm === 0) {
                setErrors("El total de horas semanales no puede ser 0");
                return btnCrearIsDisabled = true;
            } else if (horasForm > horasCurso) {
                console.log("horasForm:",horasForm,horasCurso)
                setErrors("El total excede el límite de horas del plan");
                return btnCrearIsDisabled = true;
            } else {
                setErrors();
                btnCrearIsDisabled = false;
            }
            if (horasInputs.some(ipt => {
                return ipt.valueAsNumber > 8
            })) {
                setErrors("Una asignatura excede el límite de horas");
                return btnCrearIsDisabled = true;
            } else {
                setErrors();
                btnCrearIsDisabled = false;
            }
        });
    };

    setBtnCrearState(!btnCrearIsDisabled);
    return btnCrearIsDisabled;
}

const checkHoras = () => {
    planForm.querySelectorAll("form").forEach((form) => {
        const divAsignaturas = form.querySelector(".hrs-asignaturas")
        if (!divAsignaturas) return

        // para que los valores de asignaturas no se eliminen al crear un nuevo formulario
        const valoresGuardados = new Map()
        divAsignaturas.querySelectorAll("input[name='asignatura_id']").forEach(
            asignaturaInput => {
                const horasInput = asignaturaInput.parentElement.querySelector(
                    "input[name='hrs_asignatura']"
                )
                valoresGuardados.set(asignaturaInput.value, horasInput?.value ?? "")
            }
        )});
}

// Event handlers
let eventPending = false;
let firstEvent;
let eventTimer;

const runActions = (event) => { // Funciones aquí
    inputTrigger(event);
};
const handlePlanEvent = (event) => {
    if (event.type === "submit") {
        clearTimeout(eventTimer);
        eventTimer = undefined;
        eventPending = false;
        firstEvent = undefined;
        runActions(event);
        return;
    }

    if (eventPending) return;

    eventPending = true;
    firstEvent = event;

    eventTimer = setTimeout(() => {
        if (!eventPending) return;

        eventPending = false;
        const eventToHandle = firstEvent;
        firstEvent = undefined;
        eventTimer = undefined;
        runActions(eventToHandle);
    }, 0);
};

if (divPlan) {
    divPlan.addEventListener("input", handlePlanEvent);
    divPlan.addEventListener("change", handlePlanEvent);
    divPlan.addEventListener("submit", handlePlanEvent);
} else {console.error("No se encontró el elemento con id 'plan-div'. No se pueden agregar los event listeners.");}

document.body.addEventListener("htmx:afterSwap", (event) => {
    if (event.detail.target.id === "plan-form") {
        inputTrigger();
    }
});

window.inputTrigger = inputTrigger;
inputTrigger();

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
window.exitConfirm = exitConfirm;