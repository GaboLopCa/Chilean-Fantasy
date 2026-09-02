export const UI = {
    renderUsuario(nombre, saldo) {
        const lblUsuario = document.getElementById("lblUsuario");
        const lblSaldo = document.getElementById("lblSaldo");

        if (lblUsuario) lblUsuario.innerText = nombre || "Usuario";
        if (lblSaldo) lblSaldo.innerText = `$${Number(saldo || 0).toLocaleString()}`;
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

        let cardsHTML = jugadores.map(j => {
            const jugadorId = j.jugador_id || j.id;
            if (!jugadorId) return '';

            return `
            <div class="bg-gray-800 border border-gray-700 p-4 rounded-xl flex flex-col justify-between shadow-lg">
                <div>
                    <div class="flex justify-between items-start mb-2">
                        <h4 class="font-bold text-lg text-white">${j.nombre || 'Jugador'}</h4>
                        <span class="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-900 text-emerald-300 border border-emerald-700">${j.posicion || 'N/A'}</span>
                    </div>
                    <p class="text-sm text-gray-400">Club: <span class="text-gray-200">${j.equipo || j.equipo_id || 'Sin club'}</span></p>
                    <p class="text-sm text-gray-400">Cláusula: <span class="text-yellow-400 font-semibold">$${Number(j.clausula || 0).toLocaleString()}</span></p>
                </div>
                <div class="mt-4 pt-3 border-t border-gray-700">
                    <button data-action="blindar" data-id="${jugadorId}" class="w-full bg-blue-600 hover:bg-blue-500 text-xs font-bold py-2 rounded transition cursor-pointer">
                        🛡️ Blindar Cláusula
                    </button>
                </div>
            </div>`;
        }).join('');

        cont.innerHTML = `<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">${cardsHTML}</div>`;
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
                    <p class="text-sm text-gray-400">Precio/Cláusula: <span class="text-yellow-400 font-semibold">$${Number(j.clausula || j.precio_base || 5000000).toLocaleString()}</span></p>
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
    }
};