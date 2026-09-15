const API_URL = "http://127.0.0.1:8000";

// Función auxiliar privada para abstraer y limpiar las peticiones Fetch
async function request(endpoint, options = {}) {
    const token = localStorage.getItem("token");

    const config = {
        headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...options.headers
        },
        ...options
    };

    const res = await fetch(`${API_URL}${endpoint}`, config);

    // Manejo seguro del cuerpo de la respuesta en caso de ser JSON o texto vacío
    let data;
    try {
        data = await res.json();
    } catch {
        data = null;
    }

    if (!res.ok) {
        const errorMsg = data?.detail || `Error en la petición: ${res.statusText}`;
        throw new Error(errorMsg);
    }

    return data;
}

export const API = {
    // Autenticación
    login(username, password) {
        const formData = new URLSearchParams({ username, password });
        return request("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: formData
        });
    },

    registro(nombre_usuario, email, password) {
        return request("/auth/registro", {
            method: "POST",
            body: JSON.stringify({ nombre_usuario, email, password })
        });
    },

    // Usuarios y Plantillas
    obtenerUsuario(usuarioId) {
        return request(`/usuarios/${usuarioId}`);
    },

    async obtenerPlantilla(usuarioId) {
        try {
            return await request(`/plantilla/${usuarioId}`);
        } catch {
            return null; // Retorna null si no existe plantilla para evitar detener el flujo
        }
    },

    guardarAlineacion(usuarioId, alineacion) {
        return request(`/plantilla/${usuarioId}`, {
            method: "PUT",
            body: JSON.stringify({ jugadores: alineacion })
        });
    },

    // Mercado de Jugadores
    obtenerJugadores() {
        return request("/jugadores/");
    },

    pujar(jugadorId, monto) {
        return request("/mercado/pujar", {
            method: "POST",
            body: JSON.stringify({ jugador_id: jugadorId, monto })
        });
    },

    pagarClausula(jugadorId) {
        return request("/mercado/pagar-clausula", {
            method: "POST",
            body: JSON.stringify({ jugador_id: jugadorId })
        });
    },

    subirClausula(jugadorId, montoIncremento) {
        return request("/mercado/subir-clausula", {
            method: "POST",
            body: JSON.stringify({
                jugador_id: jugadorId,
                monto_incremento: montoIncremento
            })
        });
    },

    // Agentes Libres
    obtenerAgentesLibres() {
        return request("/mercado/agentes-libres");
    },

    comprarAgenteLibre(jugadorId) {
        return request("/mercado/comprar-agente", {
            method: "POST",
            body: JSON.stringify({ jugador_id: jugadorId })
        });
    },

    obtenerRanking() {
        return request("/ranking");
    }
};