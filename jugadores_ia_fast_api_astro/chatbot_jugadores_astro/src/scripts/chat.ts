import { api } from '../lib/api';
import type { Conversacion, Mensaje } from '../lib/types';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

const PLAYER_IMAGE_FALLBACK = '/images/player-placeholder.svg';
const list = document.querySelector<HTMLDivElement>('#conversation-list')!;
  const messages = document.querySelector<HTMLDivElement>('#messages')!;
  const welcome = document.querySelector<HTMLDivElement>('#welcome')!;
  const form = document.querySelector<HTMLFormElement>('#chat-form')!;
  const input = document.querySelector<HTMLTextAreaElement>('#message-input')!;
  const sendButton = document.querySelector<HTMLButtonElement>('#send-button')!;
  const toast = document.querySelector<HTMLDivElement>('#toast')!;
  const count = document.querySelector<HTMLSpanElement>('#history-count')!;
  const connection = document.querySelector<HTMLSpanElement>('#connection-status')!;
  let conversacionId: string | null = null;
  let enviando = false;
  let conversaciones: Conversacion[] = [];

  function aviso(texto: string) {
    toast.textContent = texto;
    toast.classList.add('visible');
    window.setTimeout(() => toast.classList.remove('visible'), 3200);
  }
  function textoSeguro(texto: string) {
    return DOMPurify.sanitize(marked.parse(texto, { async: false }) as string);
  }
  function prepararImagenesJugador(contenedor: HTMLElement) {
    contenedor.querySelectorAll<HTMLImageElement>('img').forEach(imagen => {
      imagen.classList.add('player-photo');
      imagen.dataset.playerPhoto = 'true';
      imagen.alt = imagen.alt.trim() || 'Fotografía del jugador';
      imagen.loading = 'lazy';
      imagen.decoding = 'async';
      imagen.addEventListener('error', () => {
        if (imagen.dataset.fallbackApplied === 'true') return;
        imagen.dataset.fallbackApplied = 'true';
        imagen.src = PLAYER_IMAGE_FALLBACK;
      }, { once: true });

      try {
        const url = new URL(imagen.getAttribute('src') || '', window.location.href);
        if (!['http:', 'https:'].includes(url.protocol)) throw new Error('URL de imagen no válida');
      } catch {
        imagen.dataset.fallbackApplied = 'true';
        imagen.src = PLAYER_IMAGE_FALLBACK;
      }
    });
  }
  function desplazarAbajo() {
    document.querySelector('#chat-area')?.scrollTo({ top: 999999, behavior: 'smooth' });
  }
  function mostrarBienvenida(mostrar: boolean) {
    welcome.hidden = !mostrar;
    messages.hidden = mostrar;
  }
  function renderMensaje(m: Mensaje) {
    const article = document.createElement('article');
    article.className = `message ${m.rol === 'user' ? 'user-message' : 'assistant-message'}`;
    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = m.rol === 'user' ? 'TÚ' : '⚽';
    const body = document.createElement('div');
    body.className = 'message-body';
    const label = document.createElement('div');
    label.className = 'message-label';
    label.textContent = m.rol === 'user' ? 'Tú' : 'Asistente';
    const content = document.createElement('div');
    content.className = 'markdown-content';
    if (m.rol === 'user') content.textContent = m.contenido;
    else {
      content.innerHTML = textoSeguro(m.contenido);
      prepararImagenesJugador(content);
    }
    body.append(label, content);
    article.append(avatar, body);
    messages.append(article);
  }
  function limpiarChat() {
    messages.replaceChildren();
    conversacionId = null;
    mostrarBienvenida(true);
    document.querySelectorAll('.conversation-item').forEach(el => el.classList.remove('active'));
  }
  function renderLista() {
    list.replaceChildren();
    count.textContent = String(conversaciones.length);
    if (!conversaciones.length) {
      const empty = document.createElement('p');
      empty.className = 'muted empty-history';
      empty.textContent = 'Todavía no hay conversaciones.';
      list.append(empty);
      return;
    }
    for (const c of conversaciones) {
      const item = document.createElement('div');
      item.className = `conversation-item${c.id === conversacionId ? ' active' : ''}`;
      const select = document.createElement('button');
      select.className = 'conversation-select';
      select.type = 'button';
      select.textContent = c.titulo || 'Nueva conversación';
      select.title = c.titulo;
      select.addEventListener('click', () => abrirConversacion(c.id));
      const del = document.createElement('button');
      del.className = 'delete-chat';
      del.type = 'button';
      del.textContent = '×';
      del.title = 'Eliminar conversación';
      del.setAttribute('aria-label', `Eliminar ${c.titulo}`);
      del.addEventListener('click', (event) => { event.stopPropagation(); borrarConversacion(c); });
      item.append(select, del);
      list.append(item);
    }
  }
  async function cargarConversaciones() {
    try {
      conversaciones = await api.listarConversaciones();
      renderLista();
      connection.textContent = 'FastAPI disponible';
      connection.classList.add('online');
    } catch (e) {
      connection.textContent = 'FastAPI no disponible';
      connection.classList.remove('online');
      list.innerHTML = '<p class="muted empty-history">No se pudo cargar el historial.</p>';
      aviso((e as Error).message);
    }
  }
  async function abrirConversacion(id: string) {
    try {
      const c = await api.obtenerConversacion(id);
      conversacionId = c.id;
      messages.replaceChildren();
      mostrarBienvenida(false);
      (c.mensajes || []).forEach(renderMensaje);
      renderLista();
      desplazarAbajo();
      document.querySelector('#sidebar')?.classList.remove('open');
    } catch (e) { aviso((e as Error).message); }
  }
  async function borrarConversacion(c: Conversacion) {
    if (!window.confirm(`¿Eliminar la conversación "${c.titulo}" y todos sus mensajes? Esta acción no se puede deshacer.`)) return;
    try {
      await api.eliminarConversacion(c.id);
      if (conversacionId === c.id) limpiarChat();
      conversaciones = conversaciones.filter(item => item.id !== c.id);
      renderLista();
      aviso('Conversación eliminada correctamente.');
    } catch (e) { aviso((e as Error).message); }
  }
  async function enviar(texto: string) {
    const mensaje = texto.trim();
    if (!mensaje || enviando) return;
    enviando = true;
    input.value = '';
    input.style.height = 'auto';
    mostrarBienvenida(false);
    renderMensaje({ rol: 'user', contenido: mensaje });
    const typing = document.createElement('div');
    typing.className = 'typing';
    typing.innerHTML = '<span></span><span></span><span></span><small>El asistente está pensando…</small>';
    messages.append(typing);
    sendButton.disabled = true;
    desplazarAbajo();
    try {
      const respuesta = await api.enviarMensaje(mensaje, conversacionId || undefined);
      conversacionId = respuesta.conversacion_id;
      typing.remove();
      renderMensaje({ rol: 'model', contenido: respuesta.respuesta });
      await cargarConversaciones();
      renderLista();
    } catch (e) {
      typing.remove();
      renderMensaje({ rol: 'model', contenido: `No pude completar la consulta: ${(e as Error).message}` });
      aviso((e as Error).message);
    } finally {
      enviando = false;
      sendButton.disabled = false;
      input.focus();
      desplazarAbajo();
    }
  }

  form.addEventListener('submit', e => { e.preventDefault(); void enviar(input.value); });
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); }
  });
  input.addEventListener('input', () => { input.style.height = 'auto'; input.style.height = `${Math.min(input.scrollHeight, 150)}px`; });
  document.querySelector('#new-chat')?.addEventListener('click', () => { limpiarChat(); input.focus(); document.querySelector('#sidebar')?.classList.remove('open'); });
  document.querySelectorAll<HTMLButtonElement>('.suggestion').forEach(b => b.addEventListener('click', () => void enviar(b.dataset.prompt || '')));
  document.querySelector('#mobile-menu')?.addEventListener('click', () => document.querySelector('#sidebar')?.classList.toggle('open'));

  try {
    await api.health();
    connection.textContent = 'FastAPI disponible';
    connection.classList.add('online');
  } catch {
    connection.textContent = 'FastAPI no disponible';
    connection.classList.remove('online');
  }
  await cargarConversaciones();
  mostrarBienvenida(true);
