export const UI = {
    renderUsuario(nombre, saldo) {
        const lblUsuario = document.getElementById("lblUsuario");
        const lblSaldo = document.getElementById("lblSaldo");

        if (lblUsuario) lblUsuario.innerText = nombre || "Usuario";
        if (lblSaldo) lblSaldo.innerText = `$${Number(saldo || 0).toLocaleString()}`;
    },

    actualizarConteoAlineacion() {
        const cont = document.getElementById("contenedorPlantilla");
        if (!cont) return;

        const filas = cont.querySelectorAll('[data-action="toggle-titular"]');
        let titulares = 0;

        filas.forEach(btn => {
            if (btn.dataset.titular === "true") titulares++;
        });

        const lblTitulares = document.getElementById("lblTitulares");
        const lblBanca = document.getElementById("lblBanca");
        if (lblTitulares) lblTitulares.innerText = String(titulares);
        if (lblBanca) lblBanca.innerText = String(filas.length - titulares);
    },

    leerAlineacion() {
        const cont = document.getElementById("contenedorPlantilla");
        if (!cont) return [];

        const filas = cont.querySelectorAll('[data-action="toggle-titular"]');
        const alineacion = [];

        filas.forEach(btn => {
            const jugadorId = btn.dataset.id;
            const esTitular = btn.dataset.titular === "true";
            const selectPos = cont.querySelector(`[data-select-posicion][data-id="${jugadorId}"]`);
            const posicionCampo = selectPos?.value || "M";

            alineacion.push({ jugador_id: Number(jugadorId), posicion_campo: posicionCampo, es_titular: esTitular });
        });

        return alineacion;
    },

    renderPlantilla(data) {
        const cont = document.getElementById("contenedorPlantilla");
        if (!cont) return;

        const jugadores = data?.jugadores || (Array.isArray(data) ? data : []);

        if (jugadores.length === 0) {
            cont.innerHTML = `
                <div class="bg-gray-800 border border-gray-700 rounded-xl p-8 text-center max-w-xl mx-auto my-6 shadow-lg">
                    <div class="text-4xl mb-3">📋</div>
                    <h4 class="text-lg font-bold text-gray-200 mb-2">Sin jugadores asignados</h4>
                    <p class="text-sm text-gray-400 mb-4">Aún no cuentas con futbolistas en tu plantel. Explora el mercado para fichar tus primeros refuerzos.</p>
                </div>
            `;
            return;
        }

        const jugadoresHTML = jugadores.map(j => {
            const jugadorId = j.jugador_id || j.id;
            if (!jugadorId) return '';

            const esTitular = j.es_titular ?? true;
            const posicionCampo = j.posicion_campo || j.posicion || 'M';
            const borde = esTitular ? 'border-emerald-500' : 'border-gray-700 opacity-75';

            return `
            <div class="bg-gray-800 border ${borde} p-4 rounded-xl flex flex-col justify-between shadow-lg" data-jugador="${jugadorId}">
                <div>
                    <div class="flex justify-between items-start mb-2">
                        <h4 class="font-bold text-lg text-white">${j.nombre || 'Jugador'}</h4>
                        <span class="text-xs font-semibold px-2 py-0.5 rounded ${esTitular ? 'bg-emerald-900 text-emerald-300 border border-emerald-700' : 'bg-gray-700 text-gray-300 border border-gray-600'}">${esTitular ? 'Titular' : 'Banca'}</span>
                    </div>
                    <p class="text-sm text-gray-400">Club: <span class="text-gray-200">${j.equipo || j.equipo_id || 'Sin club'}</span></p>
                    <p class="text-sm text-gray-400">Cláusula: <span class="text-yellow-400 font-semibold">$${Number(j.clausula || 0).toLocaleString()}</span></p>
                    <label class="block mt-3 text-xs uppercase tracking-wider text-gray-400 mb-1">Posición en campo</label>
                    <select data-select-posicion data-id="${jugadorId}" class="w-full bg-gray-900 border border-gray-700 rounded p-2 text-sm text-white focus:outline-none focus:border-emerald-500">
                        ${['G','D','M','F'].map(p =>
                            `<option value="${p}" ${p === posicionCampo ? 'selected' : ''}>${p === 'G' ? 'Portero' : p === 'D' ? 'Defensa' : p === 'M' ? 'Mediocampista' : 'Delantero'}</option>`
                        ).join('')}
                    </select>
                </div>
                <div class="mt-4 pt-3 border-t border-gray-700 space-y-2">
                    <button data-action="toggle-titular" data-id="${jugadorId}" data-titular="${esTitular}" class="w-full ${esTitular ? 'bg-gray-700 hover:bg-gray-600' : 'bg-emerald-600 hover:bg-emerald-500'} text-xs font-bold py-2 rounded transition cursor-pointer">
                        ${esTitular ? '➖ Pasar a Banca' : '➕ Poner de Titular'}
                    </button>
                </div>
            </div>`;
        }).join('');

        cont.innerHTML = `
            <div class="flex justify-between items-center mb-4">
                <p class="text-sm text-gray-400"><span id="lblTitulares" class="text-emerald-400 font-bold">0</span> de 11 titulares · <span id="lblBanca" class="text-gray-300 font-bold">0</span> en banca</p>
                <button id="btnGuardarAlineacion" data-action="guardar-alineacion" class="bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm py-2 px-4 rounded transition cursor-pointer">
                    💾 Guardar Alineación
                </button>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">${jugadoresHTML}</div>
        `;

        UI.actualizarConteoAlineacion();
    },

    renderMercado(jugadores, usuarioId) {
        const cont = document.getElementById("contenedorMercado");
        if (!cont) return;

        if (!jugadores || jugadores.length === 0) {
            cont.innerHTML = `<p class="text-gray-400 text-center py-8">No hay jugadores disponibles en el mercado.</p>`;
            return;
        }

        const porteros = jugadores.filter(j => j.posicion === 'G' || j.posicion === 'POR');
        const defensas = jugadores.filter(j => j.posicion === 'D' || j.posicion === 'DEF');
        const medios = jugadores.filter(j => j.posicion === 'M' || j.posicion === 'MED');
        const delanteros = jugadores.filter(j => j.posicion === 'F' || j.posicion === 'DEL');

        const obtenerAleatorios = (arr, cantidad) => {
            const copia = [...arr].sort(() => 0.5 - Math.random());
            return copia.slice(0, cantidad);
        };

        const mercadoFiltrado = [
            ...obtenerAleatorios(porteros, 2),
            ...obtenerAleatorios(defensas, 3),
            ...obtenerAleatorios(medios, 3),
            ...obtenerAleatorios(delanteros, 2)
        ];

        const listaFinal = mercadoFiltrado.length > 0 ? mercadoFiltrado : jugadores;

        let cardsHTML = listaFinal.map(j => {
            const jugadorId = j.jugador_id || j.id;
            if (!jugadorId) return '';

            const esPropio = String(j.propietario_id) === String(usuarioId);
            const tieneDuenio = j.propietario_id !== null && j.propietario_id !== undefined;

            return `
            <div class="bg-gray-800 border border-gray-700 p-4 rounded-xl flex flex-col justify-between shadow-lg">
                <div>
                    <div class="flex justify-between items-start mb-2">
                        <h4 class="font-bold text-lg text-white">${j.nombre || 'Jugador'}</h4>
                        <span class="text-xs font-semibold px-2 py-0.5 rounded bg-blue-900 text-blue-300 border border-blue-700">${j.posicion || 'N/A'}</span>
                    </div>
                    <p class="text-sm text-gray-400">Equipo: <span class="text-gray-200">${j.equipo || 'Libre'}</span></p>
                    <p class="text-sm text-gray-400">Precio/Cláusula: <span class="text-yellow-400 font-semibold">$${Number(j.clausula || j.precio || 5000000).toLocaleString()}</span></p>
                    <p class="text-xs text-gray-500 mt-1">${tieneDuenio ? (esPropio ? '👤 Tu Jugador' : '👤 Pertenece a Rival') : '🏛️ Agente Libre'}</p>
                </div>

                <div class="mt-4 pt-3 border-t border-gray-700">
                    ${!tieneDuenio ? `
                        <button data-action="pujar" data-id="${jugadorId}" class="w-full bg-emerald-600 hover:bg-emerald-500 text-xs font-bold py-2 rounded transition cursor-pointer">
                            💵 Realizar Puja
                        </button>
                    ` : (!esPropio ? `
                        <button data-action="clausulazo" data-id="${jugadorId}" class="w-full bg-red-600 hover:bg-red-500 text-xs font-bold py-2 rounded transition cursor-pointer">
                            ⚡ Clausulazo
                        </button>
                    ` : `
                        <span class="block text-center text-xs text-emerald-400 font-semibold py-1">En tu plantilla</span>
                    `)}
                </div>
            </div>`;
        }).join('');

        cont.innerHTML = `<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">${cardsHTML}</div>`;
    },

    renderRanking(data) {
        const cont = document.getElementById("contenedorRanking");
        if (!cont) return;

        const ranking = Array.isArray(data) ? data : [];
        const miUsuarioId = localStorage.getItem("usuario_id");

        if (ranking.length === 0) {
            cont.innerHTML = `
                <div class="bg-gray-800 p-8 rounded-xl border border-gray-700 text-center shadow-lg">
                    <div class="text-4xl mb-3">🏆</div>
                    <h4 class="text-lg font-bold text-gray-200 mb-2">Aún no hay clasificación</h4>
                    <p class="text-sm text-gray-400">Los puntos aparecerán cuando se procesen las jornadas de la liga.</p>
                </div>
            `;
            return;
        }

        const medallas = ['🥇', '🥈', '🥉'];
        const filas = ranking.map((u, i) => {
            const esMiFila = String(u.usuario_id) === String(miUsuarioId);
            return `
                <tr class="border-b border-gray-700 hover:bg-gray-700/40 ${esMiFila ? 'bg-emerald-900/40' : ''}">
                    <td class="py-3 px-4 text-center font-bold text-lg">${medallas[i] || (i + 1)}</td>
                    <td class="py-3 px-4 font-semibold text-white">
                        ${u.nombre_usuario || 'Jugador'}
                        ${esMiFila ? '<span class="text-xs ml-2 px-2 py-0.5 rounded bg-emerald-600 text-white font-medium">Tú</span>' : ''}
                    </td>
                    <td class="py-3 px-4 text-center text-yellow-400 font-bold">${Number(u.puntos_totales || 0).toLocaleString('es-CL')}</td>
                </tr>
            `;
        }).join('');

        cont.innerHTML = `
            <div class="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden shadow-lg">
                <table class="w-full text-sm">
                    <thead class="bg-gray-900 text-gray-400 uppercase text-xs">
                        <tr>
                            <th class="py-3 px-4 text-center w-16">#</th>
                            <th class="py-3 px-4 text-left">Manager</th>
                            <th class="py-3 px-4 text-center">Puntos</th>
                        </tr>
                    </thead>
                    <tbody>${filas}</tbody>
                </table>
            </div>
        `;
    }
};