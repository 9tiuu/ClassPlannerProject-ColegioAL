const KEYS = {
    assign: 'classplanner_aulas_secciones',
    pending: 'classplanner_seccion_pendiente',
    ids: 'classplanner_aulas_anteriores',
    active: 'classplanner_seccion_activa',
};
const $ = id => document.getElementById(id);
const cards = [...document.querySelectorAll('#aulas-source [data-aula-id]')];
const sections = [...document.querySelectorAll('#plano-colegio [data-section]')];
const buttons = [...document.querySelectorAll('[data-open-section]')];
const map = $('plano-colegio');
const panel = $('section-list-panel');
const list = $('section-list');
const createButton = $('create-aula-link');
const read = (key, fallback) => {
    try {
        const value = localStorage.getItem(key);
        return value !== null ? JSON.parse(value) : fallback;
    } catch { return fallback; }
};
const write = (key, value) => { try { localStorage.setItem(key, JSON.stringify(value)); } catch {} };
const remove = key => { try { localStorage.removeItem(key); } catch {} };
const valid = value => ['1', '2', '3'].includes(String(value));
const idOf = card => String(card.dataset.aulaId);
const assignments = read(KEYS.assign, {});
const previousIds = read(KEYS.ids, []);
const currentIds = cards.map(idOf);
const pending = read(KEYS.pending, null);
if (valid(pending)) {
    currentIds.filter(id => !previousIds.includes(id)).forEach(id => assignments[id] = String(pending));
}
cards.forEach((card, i) => {
    if (!valid(assignments[idOf(card)])) assignments[idOf(card)] = String((i % 3) + 1);
});
Object.keys(assignments).forEach(id => {
    if (!currentIds.includes(id)) delete assignments[id];
});
write(KEYS.assign, assignments);
write(KEYS.ids, currentIds);
remove(KEYS.pending);
const cardsOf = sectionId => cards.filter(card => assignments[idOf(card)] === sectionId);
let active = null;
const syncUI = () => {
    buttons.forEach(button => {
        const selected = button.dataset.openSection === active;
        button.setAttribute('aria-pressed', String(selected));
        button.classList.toggle('ring-4', selected);
        button.classList.toggle('ring-slate-300', selected);
        button.classList.toggle('dark:ring-slate-500', selected);
    });
    panel.classList.toggle('hidden', !active);
    panel.classList.toggle('flex', !!active);
    panel.classList.toggle('flex-col', !!active);
    map.classList.toggle('hidden', !!active && matchMedia('(max-width: 767px)').matches);
};
const openSection = sectionId => {
    sectionId = String(sectionId);
    if (!valid(sectionId)) return;
    active = sectionId;
    const selected = cardsOf(sectionId);
    $('selected-section-title').textContent = 'Sector ' + sectionId;
    $('selected-section-subtitle').textContent = 'Aulas registradas en este sector';
    list.replaceChildren(...selected);
    $('section-list-empty').classList.toggle('hidden', selected.length > 0);
    $('section-list-scroll').scrollTop = 0;
    write(KEYS.active, sectionId);
    syncUI();
};
const closeSection = () => {
    active = null;
    remove(KEYS.active);
    syncUI();
};
sections.forEach(section => {
    const counter = section.querySelector('[data-count]');
    if (counter) counter.textContent = cardsOf(section.dataset.section).length;
});
buttons.forEach(button => button.addEventListener('click', () => openSection(button.dataset.openSection)));
$('close-section-list').addEventListener('click', closeSection);
window.addEventListener('resize', syncUI);
if (createButton) {
    createButton.addEventListener('click', event => {
        event.preventDefault();
        if (!valid(active)) return;
        write(KEYS.pending, active);
        write(KEYS.active, active);
        const url = new URL(createButton.href, location.origin);
        url.searchParams.set('seccion', active);
        location.href = url.toString();
    });
}
const toRestore = valid(pending) ? String(pending) : read(KEYS.active, null);
if (valid(toRestore)) openSection(toRestore);