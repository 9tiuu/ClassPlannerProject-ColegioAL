(() => {
const planForm = document.getElementById("plan-form")
const pdeidArray = Boolean(document.querySelector("[name='hrs-asignatura-div-update']"))
    ? Array.from(document.querySelectorAll("[name='pde_id']"))
    : []
console.log("pdeidArray: ",pdeidArray.values())

function ipt_asignatura() {
    const asignaturasSelect = document.getElementById("asignaturas-select")
    if (!planForm || !asignaturasSelect) return

    const checkedAsignaturas = asignaturasSelect.querySelectorAll(
        'input[type="checkbox"]:checked'
    )

    planForm.querySelectorAll("form").forEach((form, formIndex) => {
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
        )
        
        divAsignaturas.replaceChildren()
        checkedAsignaturas.forEach(checkbox => {
            const wrapper = document.createElement("div")
            const asignaturaLabel = document.createElement("span")
            const asignaturaInput = document.createElement("input")
            const pdeInput = document.createElement("input")
            const input = document.createElement("input")
            
            asignaturaInput.type = "hidden"
            asignaturaInput.name = "asignatura_id"
            asignaturaInput.value = checkbox.value
            
            if (typeof pdeidArray !== 'undefined') {
                console.log("pdeidArray existe")
                pdeInput.type = "hidden"
                pdeInput.name = "pde_id"
                pdeInput.className = asignaturaInput.value
                const matchingPde = pdeidArray.find(asig =>
                    Number(asig.className) === Number(checkbox.value)
                )
                pdeInput.value = matchingPde?.value ?? ""
                wrapper.name = "hrs-asignatura-div-update"
            }
            
            input.id = `hrs-${formIndex}-${checkbox.value}`
            input.type = "number"
            input.name = "hrs_asignatura"
            input.min = "0"
            input.max = "8"
            input.step = "0.5"
            input.required = true
            input.value = valoresGuardados.get(checkbox.value) ?? ""
            input.className = "w-full rounded border mt-2 out-of-range:border-red-500 px-3 py-2 invalid:border-red-400 focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-300 dark:bg-slate-800 dark:text-white dark:border-slate-600 dark:focus:ring-blue-300 dark:focus:border-blue-300"
            asignaturaLabel.textContent = checkbox.parentElement.id + ":"
            asignaturaLabel.className = "mr-2 py-2 w-[5.5rem] text-sm font-medium text-slate-700 dark:text-[#a8b2d2]"
            wrapper.className = "flex gap-1 items-center"
            
            wrapper.append(
                asignaturaLabel,
                (
                    !form.querySelector("hrs-asignatura-div-update") ? pdeInput : ""
                ),
                asignaturaInput, input)
            divAsignaturas.append(wrapper)
        })
    })
}

document.body.addEventListener("htmx:afterSwap", event => {
    if (event.detail.target === planForm) ipt_asignatura()
})

window.ipt_asignatura = ipt_asignatura
})()