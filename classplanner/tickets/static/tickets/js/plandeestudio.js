const formPlan = document.getElementById("plan-form")
function ipt_asignatura() {
    const selectAsignaturas = document.getElementById("asignaturas-select")
    if (!formPlan || !selectAsignaturas) return

    const checkedAsignaturas = selectAsignaturas.querySelectorAll(
        'input[type="checkbox"]:checked'
    )

    formPlan.querySelectorAll("form").forEach((form, formIndex) => {
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
            const asignaturaInput = document.createElement("input")
            const input = document.createElement("input")

            asignaturaInput.type = "hidden"
            asignaturaInput.name = "asignatura_id"
            asignaturaInput.value = checkbox.value

            input.id = `hrs-${formIndex}-${checkbox.value}`
            input.type = "number"
            input.name = "hrs_asignatura"
            input.min = "0"
            input.max = "8"
            input.step = "0.5"
            input.required = true
            input.value = valoresGuardados.get(checkbox.value) ?? ""
            input.className = "w-full rounded border mt-2 out-of-range:border-red-500 px-3 py-2"
            
    
            wrapper.append(asignaturaInput, input)
            divAsignaturas.append(wrapper)
        })
    })
}

document.body.addEventListener("htmx:afterSwap", event => {
    if (event.detail.target === formPlan) ipt_asignatura()
})