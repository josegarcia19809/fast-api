const API_URL = (import.meta.env.PUBLIC_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

export interface Club {
  id_club: number;
  nombre: string;
  pais: string;
  liga: string;
  estadio: string | null;
  anio_fundacion: number | null;
}

export interface Jugador {
  id_jugador: number;
  nombre: string;
  apellido: string;
  edad: number | null;
  nacionalidad: string | null;
  posicion: string | null;
  numero_camiseta: number | null;
  valor_mercado: number | null;
  altura: number | null;
  peso: number | null;
  pie_dominante: string | null;
  imagen: string | null;
  id_club: number;
  club: string;
}

interface Page<T> { items: T[]; total: number; limite: number; desplazamiento: number }

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { Accept: 'application/json', 'Content-Type': 'application/json', ...init.headers },
    });
  } catch {
    throw new Error('No se pudo conectar con FastAPI. Revisa que el backend esté en ejecución.');
  }
  const data = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data?.detail;
    if (typeof detail === 'string') throw new Error(detail);
    if (Array.isArray(detail)) {
      const messages = detail.map(item => item?.msg).filter(Boolean);
      throw new Error(messages.join(' ') || `La solicitud falló (HTTP ${response.status}).`);
    }
    throw new Error(`La solicitud falló (HTTP ${response.status}).`);
  }
  return data as T;
}

export const adminApi = {
  clubes: () => request<Club[]>('/clubes/administracion'),
  obtenerClub: (id: number) => request<Club>(`/clubes/${id}`),
  club: (id: number) => request<Club>(`/clubes/${id}`),
  crearClub: (data: Omit<Club, 'id_club'>) => request<Club>('/clubes/', { method: 'POST', body: JSON.stringify(data) }),
  actualizarClub: (id: number, data: Omit<Club, 'id_club'>) => request<Club>(`/clubes/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  eliminarClub: (id: number) => request<void>(`/clubes/${id}`, { method: 'DELETE' }),
  jugadores: (filtros: { nombre?: string; posicion?: string; nacionalidad?: string; id_club?: number; desplazamiento?: number } = {}) => {
    const params = new URLSearchParams({ limite: '100', desplazamiento: String(filtros.desplazamiento || 0) });
    if (filtros.nombre) params.set('nombre', filtros.nombre);
    if (filtros.posicion) params.set('posicion', filtros.posicion);
    if (filtros.nacionalidad) params.set('nacionalidad', filtros.nacionalidad);
    if (filtros.id_club) params.set('id_club', String(filtros.id_club));
    return request<Page<Jugador>>(`/jugadores/administracion?${params}`);
  },
  obtenerJugador: (id: number) => request<Jugador>(`/jugadores/detalle/${id}`),
  todosJugadores: async () => {
    const first = await adminApi.jugadores();
    const all = [...first.items];
    for (let offset = first.limite; offset < first.total; offset += first.limite) {
      all.push(...(await adminApi.jugadores({ desplazamiento: offset })).items);
    }
    return all;
  },
  crearJugador: (data: Omit<Jugador, 'id_jugador' | 'club'>) => request<Jugador>('/jugadores/', { method: 'POST', body: JSON.stringify(data) }),
  actualizarJugador: (id: number, data: Omit<Jugador, 'id_jugador' | 'club'>) => request<Jugador>(`/jugadores/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  eliminarJugador: (id: number) => request<void>(`/jugadores/${id}`, { method: 'DELETE' }),
  estadisticasJugadores: () => request<Record<string, any>>('/jugadores/estadisticas'),
  estadisticasPorPosicion: () => request<Array<Record<string, any>>>('/jugadores/cantidad-por-posicion'),
  estadisticasClubes: () => request<Array<Record<string, any>>>('/clubes/estadisticas'),
  jugadoresClub: (id: number) => request<Jugador[]>(`/clubes/${id}/jugadores`),
};

export function imagenJugador(valor?: string | null): string | null {
  const imagen = valor?.trim();
  if (!imagen) return null;
  if (/^https?:\/\//i.test(imagen)) return imagen;
  const archivo = imagen.replace(/^\/+/, '').replace(/^static\/retratos\//, '');
  if (!/^[\w-]+(?:\.png)?$/i.test(archivo)) return null;
  return `${API_URL}/static/retratos/${archivo.toLowerCase().endsWith('.png') ? archivo : `${archivo}.png`}`;
}
