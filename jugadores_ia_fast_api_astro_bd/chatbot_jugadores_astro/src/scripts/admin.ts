import { adminApi, imagenJugador } from './admin-api';

const toast = document.querySelector<HTMLElement>('#admin-toast');
function notify(message: string) {
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add('visible');
  window.setTimeout(() => toast.classList.remove('visible'), 3200);
}
function el<K extends keyof HTMLElementTagNameMap>(tag: K, className = '', text = ''): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}
function cell(row: HTMLTableRowElement, value: unknown) {
  const td = el('td', '', value === null || value === undefined || value === '' ? '—' : String(value));
  row.append(td);
  return td;
}
function errorPage(error: unknown) {
  const panel = document.querySelector<HTMLElement>('[data-error-target]');
  if (panel) panel.textContent = (error as Error).message || 'No fue posible cargar la información.';
}
function mostrarResultadoGuardado(tipo: 'club' | 'jugador') {
  const result = new URLSearchParams(window.location.search).get('resultado');
  const messages: Record<string, string> = {
    'club-creado': 'Club registrado correctamente.',
    'club-actualizado': 'Club actualizado correctamente.',
    'jugador-creado': 'Jugador registrado correctamente.',
    'jugador-actualizado': 'Jugador actualizado correctamente.',
  };
  if (result && result.startsWith(tipo + '-') && messages[result]) {
    notify(messages[result]);
    window.history.replaceState({}, '', window.location.pathname);
  }
}
function mostrarDetalle(titulo: string, datos: Record<string, unknown>) {
  const dialog = document.querySelector<HTMLDialogElement>('#record-dialog');
  const title = document.querySelector<HTMLElement>('#record-dialog-title');
  const content = document.querySelector<HTMLElement>('#record-dialog-content');
  if (!dialog || !title || !content) return;
  title.textContent = titulo;
  content.replaceChildren();
  const labels: Record<string, string> = {
    id_club: 'ID del club', id_jugador: 'ID del jugador', nombre: 'Nombre', apellido: 'Apellido',
    pais: 'País', liga: 'Liga', estadio: 'Estadio', anio_fundacion: 'Año de fundación',
    edad: 'Edad', nacionalidad: 'Nacionalidad', posicion: 'Posición', numero_camiseta: 'Número',
    valor_mercado: 'Valor de mercado (€ M)', altura: 'Altura (m)', peso: 'Peso (kg)',
    pie_dominante: 'Pie dominante', club: 'Club', imagen: 'Imagen', cantidad_jugadores: 'Jugadores registrados',
  };
  Object.entries(datos).forEach(([key, value]) => {
    if (key === 'imagen' && value) {
      const image = el('img', 'detail-image');
      image.src = imagenJugador(String(value)) || '/images/player-placeholder.svg';
      image.alt = `Imagen de ${String(datos.nombre || 'jugador')}`;
      content.append(image);
      return;
    }
    const row = el('div', 'detail-item');
    row.append(el('span', 'detail-label', labels[key] || key), el('span', 'detail-value', value == null || value === '' ? '—' : String(value)));
    content.append(row);
  });
  dialog.showModal();
}
document.querySelectorAll<HTMLButtonElement>('[data-close-dialog]').forEach(button => {
  button.addEventListener('click', () => button.closest('dialog')?.close());
});
function chart(container: HTMLElement | null, entries: Array<[string, number | null]>) {
  if (!container) return;
  container.replaceChildren();
  if (!entries.length) {
    container.append(el('p', 'empty-row', 'Sin datos disponibles.'));
    return;
  }
  const max = Math.max(...entries.map(([, value]) => value ?? 0), 1);
  entries.forEach(([label, value]) => {
    const row = el('div', 'bar-row');
    const name = el('span', '', label);
    const track = el('div', 'bar-track');
    const fill = el('div', 'bar-fill');
    fill.style.width = `${Math.max(2, (value ?? 0) / max * 100)}%`;
    track.append(fill);
    const shown = value == null ? '—' : Number.isInteger(value) ? String(value) : value.toFixed(1);
    row.append(name, track, el('strong', 'bar-value', shown));
    container.append(row);
  });
}

async function dashboard() {
  try {
    const [clubs, totals, clubStats, positions] = await Promise.all([
      adminApi.clubes(), adminApi.estadisticasJugadores(), adminApi.estadisticasClubes(), adminApi.estadisticasPorPosicion(),
    ]);
    const cards: Array<[string, unknown, string]> = [
      ['Clubes registrados', clubs.length, 'Datos de /clubes/administracion'],
      ['Jugadores registrados', totals.total_jugadores ?? 0, 'Datos de /jugadores/estadisticas'],
      ['Edad promedio', totals.edad_promedio == null ? '—' : Number(totals.edad_promedio).toFixed(1), 'Años · registros disponibles'],
      ['Valor promedio', totals.valor_mercado_promedio == null ? '—' : `€${Number(totals.valor_mercado_promedio).toFixed(1)} M`, 'Millones de euros'],
    ];
    const cardsHost = document.querySelector<HTMLElement>('#dashboard-cards')!;
    cardsHost.replaceChildren(...cards.map(([label, value, hint]) => {
      const card = el('article', 'stat-card');
      card.append(el('small', '', label), el('strong', '', String(value)), el('span', '', hint));
      return card;
    }));
    const sortedClubs = [...clubStats].sort((a, b) => Number(b.cantidad_jugadores || 0) - Number(a.cantidad_jugadores || 0));
    const top = sortedClubs[0];
    const leader = document.querySelector<HTMLElement>('#top-club');
    if (leader) leader.textContent = top ? `${top.club} · ${top.cantidad_jugadores} jugadores` : 'Sin registros disponibles';
    chart(document.querySelector<HTMLElement>('#dashboard-positions'), positions.map((item: any) => [String(item.posicion), Number(item.cantidad_jugadores || item.cantidad || 0)]));
    chart(document.querySelector<HTMLElement>('#dashboard-clubs'), sortedClubs.slice(0, 8).map((item: any) => [String(item.club), Number(item.cantidad_jugadores || 0)]));
  } catch (error) { errorPage(error); }
}

async function clubesPage() {
  mostrarResultadoGuardado('club');
  const tbody = document.querySelector<HTMLTableSectionElement>('#clubs-body');
  if (!tbody) return;
  const result = new URLSearchParams(window.location.search).get('resultado');
  if (result === 'club-creado') notify('Club registrado correctamente.');
  if (result === 'club-actualizado') notify('Club actualizado correctamente.');
  const reload = async () => {
    tbody.replaceChildren();
    const loading = el('tr'); loading.append(el('td', 'loading', 'Cargando clubes…')); tbody.append(loading);
    try {
      const [clubs, counts] = await Promise.all([adminApi.clubes(), adminApi.estadisticasClubes()]);
      tbody.replaceChildren();
      const countById = new Map(counts.map((item: any) => [Number(item.id_club), Number(item.cantidad_jugadores || 0)]));
      clubs.forEach(club => {
        const row = el('tr');
        cell(row, club.nombre); cell(row, club.pais); cell(row, club.liga); cell(row, club.estadio); cell(row, club.anio_fundacion); cell(row, countById.get(club.id_club) ?? 0);
        const actions = el('td', 'table-actions');
        const view = el('button', 'icon-button', 'Consultar'); view.type = 'button'; view.addEventListener('click', () => mostrarDetalle(club.nombre, { ...club, cantidad_jugadores: countById.get(club.id_club) ?? 0 }));
        const players = el('a', 'icon-button', 'Jugadores'); players.setAttribute('href', `/jugadores?id_club=${club.id_club}`);
        const edit = el('a', 'icon-button', 'Editar'); edit.setAttribute('href', `/clubes/editar/${club.id_club}`);
        const del = el('button', 'danger-button', 'Eliminar'); del.type = 'button'; del.addEventListener('click', async () => {
          if (!window.confirm(`¿Eliminar el club ${club.nombre}? Los clubes con jugadores asociados no pueden eliminarse.`)) return;
          try { await adminApi.eliminarClub(club.id_club); notify('Club eliminado.'); await reload(); }
          catch (error) { notify((error as Error).message); }
        });
        actions.append(view, players, edit, del); row.append(actions); tbody.append(row);
      });
      if (!clubs.length) { const row = el('tr'); const empty = el('td', 'empty-row', 'No hay clubes registrados.'); empty.colSpan = 7; row.append(empty); tbody.append(row); }
    } catch (error) { errorPage(error); }
  };
  await reload();
}

async function jugadoresPage() {
  mostrarResultadoGuardado('jugador');
  const tbody = document.querySelector<HTMLTableSectionElement>('#players-body');
  const filterClub = document.querySelector<HTMLSelectElement>('#filter-club');
  const filterForm = document.querySelector<HTMLFormElement>('#player-filters');
  const pagination = document.querySelector<HTMLElement>('#player-pagination');
  if (!tbody || !filterClub || !filterForm) return;
  let offset = 0;
  let total = 0;
  const clubs = await adminApi.clubes();
  clubs.forEach(club => { const option = el('option', '', club.nombre); option.value = String(club.id_club); filterClub.append(option); });
  const clubFromUrl = new URLSearchParams(window.location.search).get('id_club');
  if (clubFromUrl && clubs.some(club => String(club.id_club) === clubFromUrl)) filterClub.value = clubFromUrl;
  const reload = async () => {
    const data = new FormData(filterForm);
    tbody.replaceChildren();
    try {
      const page = await adminApi.jugadores({ nombre: String(data.get('nombre') || '').trim() || undefined, posicion: String(data.get('posicion') || '').trim() || undefined, nacionalidad: String(data.get('nacionalidad') || '').trim() || undefined, id_club: Number(data.get('id_club')) || undefined, desplazamiento: offset });
      total = page.total; tbody.replaceChildren();
      page.items.forEach(player => {
        const row = el('tr'); const playerCell = el('td'); const person = el('div', 'player-cell');
        const img = el('img', 'player-thumb'); img.alt = `Foto de ${player.nombre} ${player.apellido}`; img.src = imagenJugador(player.imagen) || '/images/player-placeholder.svg'; img.onerror = () => { img.onerror = null; img.src = '/images/player-placeholder.svg'; };
        person.append(img, el('span', '', `${player.nombre} ${player.apellido}`)); playerCell.append(person); row.append(playerCell);
        cell(row, player.posicion); cell(row, player.nacionalidad); cell(row, player.club); cell(row, player.edad); cell(row, player.valor_mercado == null ? '—' : `€${player.valor_mercado} M`);
        const actions = el('td', 'table-actions');
        const view = el('button', 'icon-button', 'Consultar'); view.type = 'button'; view.addEventListener('click', () => mostrarDetalle(`${player.nombre} ${player.apellido}`, { ...player }));
        const edit = el('a', 'icon-button', 'Editar'); edit.setAttribute('href', `/jugadores/editar/${player.id_jugador}`);
        const del = el('button', 'danger-button', 'Eliminar'); del.type = 'button'; del.addEventListener('click', async () => {
          if (!window.confirm(`¿Eliminar a ${player.nombre} ${player.apellido}?`)) return;
          try { await adminApi.eliminarJugador(player.id_jugador); notify('Jugador eliminado.'); await reload(); }
          catch (error) { notify((error as Error).message); }
        });
        actions.append(view, edit, del); row.append(actions); tbody.append(row);
      });
      if (!page.items.length) { const row = el('tr'); const empty = el('td', 'empty-row', 'No se encontraron jugadores.'); empty.colSpan = 7; row.append(empty); tbody.append(row); }
      if (pagination) {
        pagination.replaceChildren(el('span', '', `Mostrando ${total ? offset + 1 : 0}–${Math.min(offset + page.items.length, total)} de ${total}`));
        const prev = el('button', 'secondary-button', 'Anterior'); prev.type = 'button'; prev.disabled = offset <= 0; prev.addEventListener('click', () => { offset = Math.max(0, offset - page.limite); void reload(); });
        const next = el('button', 'secondary-button', 'Siguiente'); next.type = 'button'; next.disabled = offset + page.limite >= total; next.addEventListener('click', () => { offset += page.limite; void reload(); });
        pagination.append(prev, next);
      }
    } catch (error) { errorPage(error); }
  };
  filterForm.addEventListener('submit', event => { event.preventDefault(); offset = 0; void reload(); });
  document.querySelector('#clear-filters')?.addEventListener('click', () => { filterForm.reset(); offset = 0; void reload(); });
  await reload();
}

function hydrateForm(form: HTMLFormElement, values: Record<string, unknown>) {
  Object.entries(values).forEach(([key, value]) => {
    const field = form.elements.namedItem(key);
    if (field instanceof HTMLInputElement || field instanceof HTMLSelectElement) field.value = String(value ?? '');
  });
}

async function clubFormPage() {
  const form = document.querySelector<HTMLFormElement>('#club-form');
  if (!form) return;
  const recordId = form.dataset.recordId;
  const loading = document.querySelector<HTMLElement>('#club-form-loading')!;
  const status = document.querySelector<HTMLElement>('#club-form-status')!;
  const submit = document.querySelector<HTMLButtonElement>('#club-submit')!;
  if (recordId) {
    loading.hidden = false;
    try { hydrateForm(form, await adminApi.obtenerClub(Number(recordId)) as unknown as Record<string, unknown>); }
    catch (error) { status.textContent = (error as Error).message; return; }
    finally { loading.hidden = true; }
    form.hidden = false;
  }
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const data = new FormData(form);
    const payload = {
      nombre: String(data.get('nombre')).trim(), pais: String(data.get('pais')).trim(), liga: String(data.get('liga')).trim(),
      estadio: String(data.get('estadio') || '').trim() || null,
      anio_fundacion: data.get('anio_fundacion') ? Number(data.get('anio_fundacion')) : null,
    };
    if (!payload.nombre || !payload.pais || !payload.liga) { status.textContent = 'Nombre, país y liga son obligatorios.'; return; }
    submit.disabled = true; status.textContent = 'Guardando club…';
    try {
      if (recordId) await adminApi.actualizarClub(Number(recordId), payload);
      else await adminApi.crearClub(payload);
      window.location.assign('/clubes?resultado=club-' + (recordId ? 'actualizado' : 'creado'));
    } catch (error) { status.textContent = (error as Error).message; submit.disabled = false; }
  });
}

async function playerFormPage() {
  const form = document.querySelector<HTMLFormElement>('#player-form');
  if (!form) return;
  const recordId = form.dataset.recordId;
  const loading = document.querySelector<HTMLElement>('#player-form-loading')!;
  const status = document.querySelector<HTMLElement>('#player-form-status')!;
  const submit = document.querySelector<HTMLButtonElement>('#player-submit')!;
  const clubSelect = document.querySelector<HTMLSelectElement>('#jugador-club')!;
  form.hidden = true;
  loading.hidden = false;
  try {
    const clubs = await adminApi.clubes();
    clubSelect.replaceChildren(new Option('Selecciona un club', ''));
    clubs.forEach(club => clubSelect.add(new Option(club.nombre, String(club.id_club))));
    if (!clubs.length) throw new Error('Registra al menos un club antes de crear jugadores.');
    if (recordId) hydrateForm(form, await adminApi.obtenerJugador(Number(recordId)) as unknown as Record<string, unknown>);
    loading.hidden = true;
    form.hidden = false;
  } catch (error) {
    loading.hidden = true;
    status.textContent = (error as Error).message;
    return;
  }
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const data = new FormData(form);
    const optionalNumber = (key: string) => data.get(key) === '' ? null : Number(data.get(key));
    const payload = {
      nombre: String(data.get('nombre')).trim(), apellido: String(data.get('apellido')).trim(), edad: optionalNumber('edad'),
      nacionalidad: String(data.get('nacionalidad') || '').trim() || null,
      posicion: String(data.get('posicion') || '').trim() || null, numero_camiseta: optionalNumber('numero_camiseta'),
      valor_mercado: optionalNumber('valor_mercado'), altura: optionalNumber('altura'), peso: optionalNumber('peso'),
      pie_dominante: String(data.get('pie_dominante') || '').trim() || null,
      imagen: String(data.get('imagen') || '').trim() || null, id_club: Number(data.get('id_club')),
    };
    if (!payload.nombre || !payload.apellido || !payload.id_club) { status.textContent = 'Nombre, apellido y club son obligatorios.'; return; }
    submit.disabled = true; status.textContent = 'Guardando jugador…';
    try {
      if (recordId) await adminApi.actualizarJugador(Number(recordId), payload);
      else await adminApi.crearJugador(payload);
      window.location.assign('/jugadores?resultado=jugador-' + (recordId ? 'actualizado' : 'creado'));
    } catch (error) { status.textContent = (error as Error).message; submit.disabled = false; }
  });
}

async function statsPage() {
  try {
    const [clubStats, positions, players] = await Promise.all([adminApi.estadisticasClubes(), adminApi.estadisticasPorPosicion(), adminApi.todosJugadores()]);
    const clubs = [...clubStats].sort((a: any, b: any) => Number(b.cantidad_jugadores || 0) - Number(a.cantidad_jugadores || 0));
    const nationalities = new Map<string, number>(); const foot = new Map<string, number>();
    players.forEach(player => { const n = player.nacionalidad || 'Sin dato'; const f = player.pie_dominante || 'Sin dato'; nationalities.set(n, (nationalities.get(n) || 0) + 1); foot.set(f, (foot.get(f) || 0) + 1); });
    chart(document.querySelector<HTMLElement>('#stat-club-count'), clubs.map((c: any) => [String(c.club), Number(c.cantidad_jugadores || 0)]));
    chart(document.querySelector<HTMLElement>('#stat-position'), positions.map((p: any) => [String(p.posicion), Number(p.cantidad_jugadores || p.cantidad || 0)]));
    chart(document.querySelector<HTMLElement>('#stat-age'), clubs.map((c: any) => [String(c.club), c.edad_promedio == null ? null : Number(c.edad_promedio)]));
    chart(document.querySelector<HTMLElement>('#stat-market'), clubs.map((c: any) => [String(c.club), c.valor_mercado_total == null ? null : Number(c.valor_mercado_total)]));
    chart(document.querySelector<HTMLElement>('#stat-nationality'), [...nationalities.entries()].sort((a, b) => b[1] - a[1]));
    chart(document.querySelector<HTMLElement>('#stat-foot'), [...foot.entries()].sort((a, b) => b[1] - a[1]));
    const leader = clubs[0]; const box = document.querySelector<HTMLElement>('#club-leader');
    if (box) box.textContent = leader ? `${leader.club} (${leader.cantidad_jugadores} jugadores)` : 'Sin datos';
  } catch (error) { errorPage(error); }
}

const page = document.querySelector<HTMLElement>('[data-admin-page]')?.dataset.adminPage;
if (page === 'dashboard') void dashboard();
if (page === 'clubes') void clubesPage();
if (page === 'jugadores') void jugadoresPage();
if (page === 'estadisticas') void statsPage();
if (page === 'club-form') void clubFormPage();
if (page === 'player-form') void playerFormPage();
