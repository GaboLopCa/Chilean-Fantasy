import { API } from './api.js';
import { UI } from './ui.js';

let jugadorABlindarId = null;

document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("token");
    if (token) {
        mostrarPanelJuego();
    }

    document.getElementById("formLogin")?.addEventListener("submit", handleLogin);
    document.getElementById("btnConfirmarBlindar")?.addEventListener("click", ejecutarBlindaje);
    document.getElementById("btnCancelarBlindar")?.addEventListener("click", cerrarModalBlindar);
    document.getElementById("btnCerrarSesion")?.addEventListener("click", cerrarSesion);

    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const tab = e.currentTarget.dataset.tab;
            if (tab) cambiarTab(tab);
        });
    });

    document.getElementById("contenedorMercado")?.addEventListener("click", handleAccionesMercado);
    document.getElementById("contenedorPlantilla")?.addEventListener("click", handleAccionesPlantilla);
});

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById("txtUsername")?.value;
    const password = document.getElementById("txtPassword")?.value;
    const lblError = document.getElementById("authError");

    if (lblError) lblError.classList.add("hidden");

    try {
        const data = await API.login(email, password);
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("usuario", data.nombre_usuario);
        localStorage.setItem("usuario_id", data.usuario_id);

        await mostrarPanelJuego();
    } catch (err) {
        if (lblError) {
            lblError.innerText = err.message || "Error al iniciar sesión.";
            lblError.classList.remove("hidden");
        }
    }
}

async function mostrarPanelJuego() {
    document.getElementById("secAuth")?.classList.add("hidden");
    document.getElementById("secApp")?.classList.remove("hidden");
    document.getElementById("userInfo")?.classList.remove("hidden");

    await recargarTodo();
}

async function cargarDatosUsuario() {
    const usuarioId = localStorage.getItem("usuario_id");
    if (!usuarioId) return;

    try {
        const usuario = await API.obtenerUsuario(usuarioId);
        const saldo = usuario.saldo ?? usuario.presupuesto ?? usuario.saldo_actual ?? 0;
        UI.renderUsuario(usuario.nombre_usuario || localStorage.getItem("usuario"), saldo);
    } catch (err) {
        console.error("Error al obtener usuario:", err);
        UI.renderUsuario(localStorage.getItem("usuario"), 0);
    }
}

async function cargarMiPlantilla() {
    const usuarioId = localStorage.getItem("usuario_id");
    if (!usuarioId) return;

    try {
        const data = await API.obtenerPlantilla(usuarioId);
        UI.renderPlantilla(data);
    } catch (err) {
        console.error("Error al cargar plantilla:", err);
    }
}

async function cargarMercado() {
    const usuarioId = localStorage.getItem("usuario_id");
    if (!usuarioId) return;

    try {
        const jugadores = await API.obtenerJugadores();
        UI.renderMercado(jugadores, usuarioId);
    } catch (err) {
        console.error("Error al cargar mercado:", err);
    }
}

async function recargarTodo() {
    await Promise.all([
        cargarDatosUsuario(),
        cargarMiPlantilla(),
        cargarMercado()
    ]);
}

async function handleAccionesMercado(e) {
    const btn = e.target.closest("button");
    if (!btn) return;

    const action = btn.dataset.action;
    const jugadorId = btn.dataset.id;
    const usuarioId = localStorage.getItem("usuario_id");

    if (!jugadorId || jugadorId === "id") {
        alert("Error: Identificador de jugador no válido.");
        return;
    }

    if (action === "pujar") {
        const monto = prompt("Ingresa el monto de tu puja ($):");
        if (!monto || isNaN(monto) || Number(monto) <= 0) return;
        try {
            const res = await API.pujar(usuarioId, jugadorId, parseInt(monto, 10));
            alert(res.mensaje || "Puja realizada con éxito.");
            await recargarTodo();
        } catch (err) { 
            alert(err.message || "Error al realizar la puja."); 
        }
    } 
    else if (action === "clausulazo") {
        if (!confirm("¿Estás seguro de ejecutar el clausulazo? Se descontará el valor de la cláusula de tu saldo.")) return;
        try {
            const res = await API.pagarClausula(usuarioId, jugadorId);
            alert(res.mensaje || "¡Clausulazo ejecutado con éxito!");
            await recargarTodo();
        } catch (err) { 
            alert(err.message || "Error al ejecutar el clausulazo."); 
        }
    }
}

function handleAccionesPlantilla(e) {
    const btn = e.target.closest("button");
    if (!btn) return;

    const action = btn.dataset.action;
    const jugadorId = btn.dataset.id;

    if (!jugadorId || jugadorId === "id") {
        alert("Error: Identificador de jugador no válido.");
        return;
    }

    if (action === "blindar") {
        abrirModalBlindar(jugadorId);
    }
}

function abrirModalBlindar(jugadorId) {
    jugadorABlindarId = jugadorId;
    const txtMonto = document.getElementById("txtMontoIncremento");
    if (txtMonto) txtMonto.value = "";
    document.getElementById("modalBlindar")?.classList.remove("hidden");
}

function cerrarModalBlindar() {
    jugadorABlindarId = null;
    document.getElementById("modalBlindar")?.classList.add("hidden");
}

async function ejecutarBlindaje() {
    const incrementoInput = document.getElementById("txtMontoIncremento")?.value;
    const incremento = parseInt(incrementoInput, 10);
    const usuarioId = localStorage.getItem("usuario_id");

    if (!incremento || isNaN(incremento) || incremento <= 0) {
        alert("Ingresa un monto de incremento válido mayor a 0.");
        return;
    }

    if (!jugadorABlindarId || !usuarioId) {
        alert("Error de datos de sesión o jugador.");
        return;
    }

    try {
        const res = await API.subirClausula(usuarioId, jugadorABlindarId, incremento);
        alert(res.mensaje || "¡Cláusula blindada con éxito!");
        cerrarModalBlindar();
        await recargarTodo();
    } catch (err) {
        alert(err.message || "Error al blindar la cláusula.");
    }
}

function cerrarSesion() {
    localStorage.clear();
    location.reload();
}

function cambiarTab(tab) {
    document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
    document.querySelectorAll(".tab-btn").forEach(el => {
        el.classList.remove("border-emerald-400", "text-emerald-400");
        el.classList.add("border-transparent", "text-gray-400");
    });

    if (tab === 'plantilla') {
        document.getElementById("tabPlantilla")?.classList.remove("hidden");
        document.getElementById("btnTabPlantilla")?.classList.add("border-emerald-400", "text-emerald-400");
        cargarMiPlantilla();
    } else if (tab === 'mercado') {
        document.getElementById("tabMercado")?.classList.remove("hidden");
        document.getElementById("btnTabMercado")?.classList.add("border-emerald-400", "text-emerald-400");
        cargarMercado();
    } else if (tab === 'ranking') {
        document.getElementById("tabRanking")?.classList.remove("hidden");
        document.getElementById("btnTabRanking")?.classList.add("border-emerald-400", "text-emerald-400");
    }
}