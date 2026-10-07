# Chilean Fantasy — Documentación del Proyecto

---

## Resumen Ejecutivo

### Visión del Proyecto

**Chilean Fantasy** es una aplicación web dinámica e interactiva enfocada en la liga de fútbol chileno. Su objetivo principal es ofrecer una experiencia estratégica donde los usuarios administran su propio presupuesto, compiten en el mercado de fichajes en tiempo real, arman plantillas competitivas y acumulan puntos jornada a jornada.

### Mecánicas Core del Juego

1. **Mercado de Fichajes y Agentes Libres:** Lista balanceada de jugadores agrupados por posición (2 Arqueros, 3 Defensas, 3 Mediocampistas, 2 Delanteros). Sistema de pujas para adquirir futbolistas sin propietario.
2. **Clausulazo:** Permite a un manager "arrebatar" de forma inmediata a un futbolista que pertenezca a un rival pagando su cláusula de rescisión fija. El monto pagado se descuenta automáticamente del comprador y se abona al dueño anterior.
3. **Blindar Clausula:** Los managers pueden reinvertir parte de su saldo disponible en su propia plantilla para elevar la cláusula de un jugador y evitar que otros rivales se lo quiten con un clausulazo.

### Estado Actual del Proyecto

| Area | Estado |
|---|---|
| Backend / Servidor | FastAPI con 17 endpoints (10 protegidos, 7 públicos). Rutas de usuarios, jugadores, mercado, ligas, jornadas y ranking configuradas. |
| Autenticación | Login + JWT con `SECRET_KEY` desde `.env`. Dependency `get_current_user` protege todas las rutas sensibles. |
| Capa API (Frontend) | Módulo `api.js` con `request()` que inyecta `Authorization: Bearer` automáticamente. |
| UI - Mercado y Plantilla | Algoritmo de distribución por posiciones en `ui.js`. Renderizado diferencial de estados (Agente Libre, Rival, Propio). |
| Eventos y Métodos | `app.js` refactorizado con control centralizado de tabs, `recargarTodo()` y controladores de pujas, blindajes y clausulazos. |
| Motor de Puntuación | `scoring_engine.py` funcional con reglas completas de fantasy football. |
| Sincronización API externa | `sync_jornada.py` operativo para ingestar datos de SportAPI7, con **caché de temporada** (`metadatos`) e **idempotencia por evento** (`eventos_sincronizados`) para minimizar el consumo de la cuota. |
| Ajuste de precios | `market_engine.py` ajusta precio/cláusula ±10% según puntos por jornada. |
| Base de Datos | Schema unificado (`schema.sql`) con monedero `saldo` único, precios alineados y constraints de integridad. Pendiente ejecutar en Supabase. |

### Estado del Código (Issues Detectados)

| Issue | Archivo | Severidad | Estado |
|---|---|---|---|
| Router no registrado | `main.py` | Media | ✅ Resuelto |
| Import faltante (`market_engine`) | `routers/jornadas.py` | Alta | ✅ Resuelto (creado `market_engine.py`) |
| Script incompleto | `sync_pendientes.py` | Baja | ✅ Resuelto |
| Endpoint obsoleto `POST /usuarios` | `routers/usuarios.py` | Baja | ✅ Eliminado |
| JWT emitido pero nunca verificado | `mercado.py`, `ligas.py`, etc. | Alta | ✅ Resuelto (`deps.py` + protected routes) |
| Doble concepto `presupuesto`/`saldo` | `usuarios`, `auth.py`, `validators.py` | Alta | ✅ Resuelto (solo `saldo`) |
| `precio_base` vs `precio` (columna real) | `jugadores.py`, `mercado.py`, `market_engine.py` | Alta | ✅ Resuelto |
| `es_capitan` vs `es_titular` (columna real) | `ranking.py`, `ligas.py` | Alta | ✅ Resuelto |
| `RETURNING id` sin columna `id` en `jornadas` | `routers/jornadas.py` | Alta | ✅ Resuelto (`RETURNING numero`) |
| `row["id"]` KeyError en `guardar_alineacion` | `routers/plantillas.py` | Alta | ✅ Resuelto (acceso por `row["id"]` con RealDictCursor) |
| `obtener_plantilla` devolvía nombres de columnas en vez de datos | `routers/plantillas.py` | Alta | ✅ Resuelto (usar `cursor.fetchall()` directo con RealDictCursor) |
| `mercado_pujas` duplicada (sin uso) | schema de BD | Baja | ✅ Eliminada en `schema.sql` |
| `fetch_data.py` quemaba 1 request al importar (nivel de módulo) | `fetch_data.py` | Media | ✅ Eliminado |
| Re-sincronizar una fecha re-fetchaba lineups ya guardados | `sync_jornada.py` | Alta | ✅ Resuelto (idempotencia vía `eventos_sincronizados`) |
| `/seasons` consultado en cada corrida de sync | `sync_jornada.py` | Media | ✅ Resuelto (caché `metadatos`) |
| `sync_pendientes.py` recorría 1..30 sin saltar nada | `sync_pendientes.py` | Alta | ✅ Resuelto (salta `FINALIZADA`, rango `--desde/--hasta`) |
| Endpoint marcaba `FINALIZADA` aunque quedaran partidos en juego | `routers/jornadas.py` | Alta | ✅ Resuelto (según resumen de la jornada; si no, queda `EN_PROGRESO`) |
| `jornadas` vacía → 404 al sincronizar/marcar estado | BD | Alta | ✅ Resuelto (seed 1..30 en `schema.sql` + `seed_jornadas.py`) |
| `validar_reglas_plantilla` existía pero nunca se llamaba | `validators.py`, `routers/plantillas.py` | Alta | ✅ Resuelto (conectado a `guardar_alineacion`; sin saldo, formación por `posicion_campo`, lineup lock por jornada activa) |

---

## Tabla de Contenidos

1. [Stack Tecnológico](#stack-tecnológico)
2. [Estructura del Proyecto](#estructura-del-proyecto)
3. [Base de Datos](#base-de-datos)
4. [Autenticación y Seguridad](#autenticación-y-seguridad)
5. [API REST (Backend)](#api-rest-backend)
6. [Motor de Puntuación](#motor-de-puntuación)
7. [Sincronización de Datos Externos](#sincronización-de-datos-externos)
8. [Frontend](#frontend)
9. [Variables de Entorno](#variables-de-entorno)
10. [Scripts de Población Inicial](#scripts-de-población-inicial)
11. [Ejecución del Proyecto](#ejecución-del-proyecto)
12. [Roadmap — Próximos Pasos](#roadmap--próximos-pasos)
13. [Notas Conocidas](#notas-conocidas)

---

## Stack Tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Python 3.11+ con FastAPI |
| Base de datos | PostgreSQL (Supabase) |
| ORM / Driver | psycopg2 (sin ORM) |
| Autenticación | JWT (PyJWT) + bcrypt |
| Validación | Pydantic v2 |
| Frontend | HTML vanilla + Tailwind CSS (CDN) + JavaScript ES6 modules |
| API externa | RapidAPI - SportAPI7 (datos de fútbol chileno) |

---

## Estructura del Proyecto

```
Chilean_Fantasy/
├── main.py                  # Punto de entrada FastAPI, registro de routers
├── database.py              # Conexión a PostgreSQL (psycopg2 + RealDictCursor)
├── schemas.py               # Modelos Pydantic para requests
├── security.py              # Hash de contraseñas (bcrypt) + JWT + SECRET_KEY de .env
├── validators.py            # Validación de reglas de plantilla (alineación)
├── scoring_engine.py        # Cálculo y persistencia de puntos por jornada
├── market_engine.py         # Ajuste automático de precios/cláusulas por jornada
├── schema.sql               # Schema de la BD (reset completo) — se ejecuta en Supabase
├── sportapi.py              # Cliente único de SportAPI7: headers, errores tipados (cuota/5xx),
│                            #   caché de temporada en `metadatos` y verificación de tablas de sync
├── sync_jornada.py          # Sincroniza una jornada desde la API (con idempotencia por evento)
├── sync_pendientes.py       # Sincroniza fechas pendientes (--desde/--hasta), salta las FINALIZADAS
├── seed_jornadas.py         # Pobla la tabla `jornadas` (fechas 1..30) sin reset
├── populate_teams.py        # Pobla la tabla `equipos` desde la API
├── populate_players.py      # Pobla la tabla `jugadores` desde la API
├── index.html               # SPA principal (único archivo HTML)
├── .env                     # Variables de entorno (no versionado)
├── .gitignore
├── js/
│   ├── app.js               # Controlador principal del frontend
│   ├── api.js               # Capa de comunicación con la API REST (Auth header)
│   └── ui.js                # Renderizado del DOM (plantilla, mercado, usuario)
└── routers/
    ├── __init__.py          # Marca `routers` como paquete Python
    ├── deps.py              # Dependency get_current_user (valida JWT)
    ├── auth.py              # Registro y login de usuarios (público)
    ├── usuarios.py          # Datos de usuario (protegido, solo dueño)
    ├── jugadores.py         # Listado de jugadores (público)
    ├── plantillas.py        # Consulta de plantilla por usuario (protegido)
    ├── mercado.py           # Compra, pujas, cláusulas y clausulazos (protegido)
    ├── jornadas.py          # Gestión de estado de jornadas (protegido)
    ├── ligas.py             # Creación, unión y ranking de ligas (protegido)
    └── ranking.py           # Ranking global de jugadores (protegido)
```

---

## Base de Datos

Conexión gestionada en `database.py` mediante `psycopg2` con `RealDictCursor` para devolver resultados como diccionarios.

### Tablas Principales

#### `usuarios`
| Campo | Tipo | Descripción |
|---|---|---|
| id | UUID (PK) | Identificador único del usuario |
| nombre_usuario | VARCHAR | Nombre visible en la app (único) |
| email | VARCHAR | Correo electrónico (único) |
| password_hash | VARCHAR | Contraseña hasheada con bcrypt |
| saldo | BIGINT | Monedero único (default 100,000,000). Sustituye al antiguo `presupuesto`. |

#### `equipos`
| Campo | Tipo | Descripción |
|---|---|---|
| id | INT (PK) | ID del equipo en la API externa |
| nombre | VARCHAR | Nombre del club |
| escudo_url | VARCHAR | URL del escudo (generada dinámicamente) |

#### `jugadores`
| Campo | Tipo | Descripción |
|---|---|---|
| id | INT (PK) | ID del jugador en la API externa |
| nombre | VARCHAR | Nombre completo |
| posicion | VARCHAR | Posición: G (portero), D (defensa), M (mediocampo), F (delantero) |
| equipo_id | INT (FK) | Referencia a equipos |
| precio | INT | Precio del jugador (default 2,000,000) |
| clausula | BIGINT | Valor de cláusula de rescisión (default 5,000,000) |
| propietario_id | UUID (FK) | Usuario propietario (NULL = agente libre) |
| foto_url | VARCHAR | URL de la foto del jugador |

#### `plantillas_usuarios`
| Campo | Tipo | Descripción |
|---|---|---|
| usuario_id | UUID (FK) | Referencia a usuarios |
| jugador_id | INT (FK) | Referencia a jugadores |
| es_titular | BOOLEAN | Indica si es titular (default true) |
| posicion_campo | VARCHAR | Posición en la formación (futuro módulo de alineación) |

#### `jornadas`
| Campo | Tipo | Descripción |
|---|---|---|
| numero | INT (PK) | Número de fecha (1-30) |
| estado | VARCHAR | ABIERTA / EN_PROGRESO / FINALIZADA (CHECK constraint) |
| fecha_inicio | TIMESTAMP | Inicio de la jornada |
| fecha_fin | TIMESTAMP | Fin de la jornada |

#### `puntos_jornada`
| Campo | Tipo | Descripción |
|---|---|---|
| jugador_id | INT (FK) | Referencia a jugadores |
| numero_jornada | INT | Número de fecha |
| puntos | INT | Puntos calculados |
| minutos_jugados | INT | Minutos en cancha |
| goles | INT | Goles anotados |
| asistencias | INT | Asistencias |
| tarjetas_amarillas | INT | Amarillas recibidas |
| tarjetas_rojas | INT | Rojas recibidas |

> Constraint unique: `(jugador_id, numero_jornada)` con upsert (ON CONFLICT DO UPDATE).

#### `pujas`
| Campo | Tipo | Descripción |
|---|---|---|
| usuario_id | UUID (FK) | Usuario que puja |
| jugador_id | INT (FK) | Jugador pujado |
| monto | INT | Monto de la puja |
| fecha | DATE | Fecha de la puja |

> Constraint unique: `(usuario_id, jugador_id, fecha)` - un usuario solo puede pujar una vez por día por jugador.

#### `ligas`
| Campo | Tipo | Descripción |
|---|---|---|
| id | UUID (PK) | ID de la liga |
| nombre | VARCHAR | Nombre de la liga |
| codigo_invitacion | VARCHAR | Código de 6 caracteres para unirse |
| creador_id | UUID (FK) | Usuario creador |

#### `ligas_miembros`
| Campo | Tipo | Descripción |
|---|---|---|
| liga_id | UUID (FK) | Referencia a ligas |
| usuario_id | UUID (FK) | Referencia a usuarios |
| unido_en | TIMESTAMPTZ | Fecha de ingreso |

#### `transacciones` (auditoría, reservada para uso futuro)
| Campo | Tipo | Descripción |
|---|---|---|
| id | UUID (PK) | Identificador |
| comprador_id | UUID (FK) | Usuario que compra |
| vendedor_id | UUID (FK) | Usuario que vende |
| jugador_id | INT (FK) | Jugador transferido |
| monto | BIGINT | Monto de la operación |
| tipo | VARCHAR | PUJA / CLAUSULAZO / BLINDAJE / COMPRA_AGENTE |
| fecha | TIMESTAMP | Fecha de la operación |

> Tabla `mercado_pujas` (duplicada) **eliminada** del schema. El schema real se define en `schema.sql` y se replica ejecutándolo en el SQL Editor de Supabase.

---

## Autenticación y Seguridad

**Archivos:** `security.py` + `routers/deps.py`

- **Contraseñas:** Hasheadas con `bcrypt` (truncadas a 72 bytes UTF-8 como máximo).
- **Tokens JWT:** Firmados con algoritmo HS256, expiración de 7 días.
- **`SECRET_KEY`:** Se lee de `.env` (`SECRET_KEY`). Si falta o es menor a 32 caracteres, la app **no arranca** (fail-fast). No hay secretos en el código.
- **Protección de rutas:** `routers/deps.py` define `get_current_user` (dependency `OAuth2PasswordBearer`). Valida el JWT y devuelve el `usuario_id`. El usuario se identifica **por el token**, nunca por campos del body.
- **Flujo de login:** El usuario envía email/nombre_usuario + contraseña → se verifica con `bcrypt.checkpw` → se retorna un `access_token` JWT.

**Endpoints de auth** (`routers/auth.py`) — públicos:

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/auth/registro` | Registra usuario, retorna token + id + nombre |
| POST | `/auth/login` | Login con email o nombre de usuario, retorna token |

---

## API REST (Backend)

### Endpoints por Router

> **PUB** = público (sin token). **LOCK** = requiere `Authorization: Bearer <token>`.

#### Auth (`/auth`) — todos **PUB**
- `POST /auth/registro` — Registro de usuario, retorna token
- `POST /auth/login` — Inicio de sesión, retorna token

#### Usuarios (`/usuarios`) — todos **LOCK**
- `GET /usuarios/{usuario_id}` — Datos del usuario (nombre, saldo). Solo el dueño (403 si ajeno).

#### Jugadores (`/jugadores`) — **PUB**
- `GET /jugadores?posicion=&limite=50` — Listar jugadores con filtro por posición y límite

#### Plantilla (`/plantilla`) — **LOCK**
- `GET /plantilla/{usuario_id}` — Jugadores asignados a un usuario. Solo el dueño (403 si ajeno).

#### Mercado (`/mercado`) — todos **LOCK**
- `GET /mercado/agentes-libres` — 2 jugadores aleatorios por posición sin propietario
- `POST /mercado/comprar-agente` — Comprar agente libre al precio base
- `POST /mercado/pujar` — Registrar puja diaria por un jugador
- `POST /mercado/procesar-pujas-diarias` — Procesa pujas del día (mayor puja gana)
- `POST /mercado/pagar-clausula` — Ejecutar clausulazo (comprar jugador con cláusula)
- `POST /mercado/subir-clausula` — Aumentar cláusula de rescisión (blindar)

> El `usuario_id`/`comprador_id` de las operaciones de mercado sale del token; no se acepta en el body.

#### Jornadas (`/jornadas`) — **LOCK**
- `PUT /jornadas/{numero_jornada}/estado` — Cambiar estado (ABIERTA → EN_PROGRESO → FINALIZADA). Al pasar a FINALIZADA se ejecuta el ajuste automático de precios.
- `POST /jornadas/{numero_jornada}/sincronizar` — Sincroniza stats de la jornada desde SportAPI7, calcula puntos (`puntos_jornada`), marca FINALIZADA y ajusta precios (`market_engine`). (~35s sync + ~19s precios).

#### Ligas (`/ligas`) — **LOCK**
- `POST /ligas/crear` — Crear liga privada con código de invitación (el creador sale del token)
- `POST /ligas/unirse` — Unirse a liga mediante código (el usuario sale del token)
- `GET /ligas/{liga_id}/tabla` — Tabla de posiciones de la liga (puntos totales)

#### Ranking (`/ranking`) — **LOCK**
- `GET /ranking` — Ranking global de todos los usuarios

### Modelos Pydantic (schemas.py)

| Modelo | Campos |
|---|---|
| `UsuarioRegistro` | nombre_usuario (3-30 chars), email (EmailStr), password (6-50 chars) |
| `Token` | access_token, token_type, usuario_id, nombre_usuario |
| `GuardarPlantillaRequest` | jugador_ids (list), capitan_id |
| `ActualizarEstadoJornadaRequest` | estado |
| `PujaRequest` | jugador_id, monto (>0) |
| `PagarClausulaRequest` | jugador_id |
| `AumentarClausulaRequest` | jugador_id, monto_incremento (>0) |
| `ComprarAgenteRequest` | jugador_id |

---

## Motor de Puntuación

**Archivo:** `scoring_engine.py`

Calcula puntos por jornada basado en estadísticas reales de los jugadores. Reglas de puntuación:

### Tabla de Puntos

| Acción | Puntos | Condición |
|---|---|---|
| Minutos jugados | +2 (≥60 min), +1 (1-59 min) | Siempre |
| Gol anotado (Delantero) | +4 | |
| Gol anotado (Mediocampista) | +5 | |
| Gol anotado (Defensa) | +6 | |
| Gol anotado (Portero) | +6 | |
| Asistencia | +3 | |
| Portería a cero (GK/DEF) | +4 | Si jugó ≥60 min y no recibió goles |
| Portería a cero (MED) | +1 | Si jugó ≥60 min y no recibió goles |
| Goles encajados (GK/DEF) | -1 por cada 2 goles | |
| Penalti parado | +5 | |
| Penalti provocado | +2 | |
| Penalti fallado | -2 | |
| Penalti cometido | -2 | |
| Autogol | -2 | |
| Tarjeta amarilla | -1 | |
| Tarjeta roja | -3 | |

### Funciones

- `calcular_puntos(stats, posicion)` — Calcula puntos totales desde un diccionario de estadísticas
- `guardar_puntos_jornada(jugador_id, numero_jornada, stats, posicion, nombre, equipo_id)` — Calcula puntos y los guarda/upsert en `puntos_jornada`. Si se provee nombre y equipo_id, también inserta el jugador en la tabla `jugadores` si no existe.

---

## Sincronización de Datos Externos

**API:** SportAPI7 vía RapidAPI (Torneo ID: 11653 = Primera División de Chile)

### `sync_jornada.py`

Sincroniza las estadísticas de todos los jugadores de una jornada específica:

1. Obtiene la temporada actual **desde la caché `metadatos`** (solo consulta `/seasons` si no está cacheada)
2. Consulta los eventos (partidos) de la jornada
3. Filtra solo partidos con estado `finished`
4. **Salta (0 requests)** los eventos ya registrados en `eventos_sincronizados` (idempotencia)
5. Para cada evento nuevo, obtiene los lineups y procesa las estadísticas de cada jugador
6. Llama a `guardar_puntos_jornada` para calcular y persistir puntos

Devuelve un resumen: `partidos_total`, `partidos_procesados`, `partidos_pendientes` (en juego/no programados) y `partidos_reutilizados`.

**Ejecución:** `python sync_jornada.py` (modificar `numero_jornada` en `____main__`)

También se puede disparar desde la API con `POST /jornadas/{numero_jornada}/sincronizar` (requiere token):
- **Todos los partidos terminados** → marca `FINALIZADA` y ejecuta el ajuste de precios.
- **Quedan pendientes** → queda en `EN_PROGRESO` y se puede re-invocar sin costo para los eventos ya importados.
- Si la API externa responde `429`, el endpoint retorna `429` (`CuotaAgotada`) y la jornada **no** se marca finalizada.

### `sync_pendientes.py`

Itera un rango de fechas sincronizando solo las que **no** están en estado `FINALIZADA` (las omite sin gastar requests). Rango configurable: `python sync_pendientes.py --desde 1 --hasta 5`.

### `seed_jornadas.py`

Puebla la tabla `jornadas` con las fechas 1..30 (idempotente, no duplica). **Necesario** para que el endpoint `PUT /jornadas/{n}/estado` y el ciclo de sync funcionen (sin fila, devuelven 404). Si ya existe el `schema.sql` completo con el seed, no hace falta.

### Presupuesto de Requests (plan Basic)

> ⚠️ El plan **Basic de RapidAPI** tiene un **límite mensual de uso** (cuota). Al superarlo, la API responde `429` y la app lo propaga desde `/jornadas/{n}/sincronizar`. El código **no** marca la jornada `FINALIZADA` en ese caso.

| Operación | Requests (antes) | Requests (ahora) | Detalle de la optimización |
|---|---|---|---|
| `populate_teams.py` | 2 | 1–2 | `/seasons` cacheado en `metadatos` |
| `populate_players.py` | ~16 (1 por equipo) | ~16 | igual (16 clubes, pausa 0.2s) |
| `sync_jornada.py` (1.ª vez) | ~11–12 | ~9–10 | solo 1 eventos + 1 lineup por partido |
| `sync_jornada.py` (re-ejecución) | ~11–12 | **1** | eventos ya sync → 0 lineup requests |
| `sync_pendientes.py` (30 fechas) | ~330 | ~**280–300** | salta fechas `FINALIZADA` (0 requests) |

**Caché de temporada (`metadatos`):** la tabla `season_id`/`season_name` solo se consulta la primera vez que se corre `populate_teams` o `sync_jornada`; después se reutiliza (ahorra ~1 request por corrida).

**Idempotencia por evento (`eventos_sincronizados`):** cada partido (`event_id`) se registra al importarlo; re-sincronizar una fecha con eventos ya importados **no** pide lineups de nuevo.

> 💡 `sportapi.py` centraliza headers, el manejo de `429`/`5xx` y un reintento con backoff para errores de red. No reintenta ante cuota agotada (evita quemar requests inútiles).

### Checklist pendiente (cuota renovada)

Pasos manuales pendientes de validar cuando la cuota mensual de RapidAPI se renueve:

1. Ejecutar `POST /jornadas/1/sincronizar` hasta obtener **200 + `estado: FINALIZADA` + precios ajustados** (antes bloqueado por 429).
2. Repoblar con `populate_teams.py` → `populate_players.py` para refrescar equipos/plantillas (si la API cambió datos).
3. Verificar el **mapeo de posiciones** devuelto por la API (`G/D/M/F`) contra `calcular_puntos` de `scoring_engine.py`.
4. Confirmar que la cuota mensual sigue vigente antes de cada corrida de `sync_pendientes.py` (mide con `GET https://...` o revisa el dashboard de RapidAPI).

### Endpoints disponibles sin usar (roadmap futuro)

| Endpoint | Idea de feature |
|---|---|
| `GET /event/{id}/incidents` | Validar goles/tarjetas/sustituciones contra el scoring |
| `GET /event/{id}/statistics` | Stats avanzadas para un visual de partido |
| `GET /unique-tournament/{id}/season/{id}/standings/total` | Tabla de posiciones real de la liga chilena |
| `GET /event/{id}/h2h` | Cara a cara entre equipos |
| `GET /players/search` | Búsqueda/descubrimiento de futbolistas |
| `GET /transfer/*` | Módulo de transferencias históricas |
| `GET /sport/football/{fecha}/{tz}/categories` | Próximos partidos/fechas del fixture |

---

## Frontend

### Arquitectura

SPA de una sola página (`index.html`) con JavaScript ES6 modules. Sin frameworks — vanilla JS con Tailwind CSS vía CDN.

### Componentes

#### `js/api.js`
Capa de comunicación con el backend. Función genérica `request()` que centraliza fetch, parseo JSON y manejo de errores, e **inyecta automáticamente el header `Authorization: Bearer <token>`** desde `localStorage`.

Endpoints disponibles en el cliente:
- `API.login(username, password)`
- `API.obtenerUsuario(usuarioId)`
- `API.obtenerPlantilla(usuarioId)`
- `API.obtenerJugadores()`
- `API.pujar(jugadorId, monto)`
- `API.pagarClausula(jugadorId)`
- `API.subirClausula(jugadorId, montoIncremento)`
- `API.obtenerAgentesLibres()`
- `API.comprarAgenteLibre(jugadorId)`

#### `js/ui.js`
Renderizado del DOM:
- `UI.renderUsuario(nombre, saldo)` — Actualiza barra de navegación
- `UI.renderPlantilla(data)` — Renderiza cards de jugadores propios con botón "Blindar Cláusula"
- `UI.renderMercado(jugadores, usuarioId)` — Renderiza mercado filtrado (2 porteros, 3 defensas, 3 mediocampistas, 2 delanteros aleatorios) con botones de puja/clausulazo según propiedad

#### `js/app.js`
Controlador principal:
- **Login:** Maneja formulario, almacena token/id/usuario en `localStorage`
- **Tabs:** Mi Plantilla, Mercado de Fichajes, Clasificación
- **Acciones Mercado:** Pujas (prompt), Clausulazos (confirm)
- **Acciones Plantilla:** Blindar cláusula (modal con input de monto)
- **Sesión:** Cierre de sesión limpia `localStorage`

### Flujo de Datos del Frontend

```
Login → API.login() → localStorage (token, usuario_id, usuario)
  ↓
recargarTodo() → Promise.all([
  API.obtenerUsuario() → UI.renderUsuario(),
  API.obtenerPlantilla() → UI.renderPlantilla(),
  API.obtenerJugadores() → UI.renderMercado()
])
```

### Persistencia del Cliente

| Clave | Valor |
|---|---|
| `token` | JWT de autenticación |
| `usuario` | Nombre de usuario |
| `usuario_id` | UUID del usuario |

---

## Variables de Entorno

**Archivo:** `.env`

| Variable | Descripción |
|---|---|
| `DB_HOST` | Host de PostgreSQL (Supabase) |
| `DB_NAME` | Nombre de la base de datos |
| `DB_USER` | Usuario de la base de datos |
| `DB_PASS` | Contraseña de la base de datos |
| `DB_PORT` | Puerto de PostgreSQL |
| `RAPIDAPI_KEY` | API key de RapidAPI (plan Basic, cuota mensual → puede dar `429`) |
| `RAPIDAPI_HOST` | Host de la API SportAPI7 (`sportapi7.p.rapidapi.com`) |
| `SECRET_KEY` | Clave para firmar JWT (mínimo 32 caracteres, validado al arrancar) |

---

## Scripts de Población Inicial

### `populate_teams.py`

Obtiene todos los equipos de la temporada actual del campeonato chileno y los inserta en la tabla `equipos` con upsert (ON CONFLICT DO UPDATE).

**Ejecución:** `python populate_teams.py`

### `populate_players.py`

Para cada equipo en la BD, consulta la API por su plantilla de jugadores y los inserta en `jugadores` con upsert. Incluye pausa de 0.2s entre requests para no saturar la API.

**Dependencia:** Requiere que `populate_teams.py` se haya ejecutado primero.

**Ejecución:** `python populate_players.py`

---

## Reglas de Validación de Plantilla

**Archivo:** `validators.py` → `validar_reglas_plantilla(cursor, titulares)`, llamado desde `routers/plantillas.py::guardar_alineacion`.

Al guardar una alineación se validan los **11 titulares** (la banca no entra en estas reglas):

1. **Lineup Lock:** la jornada activa (menor número no finalizada) debe estar `ABIERTA`. Si está `EN_PROGRESO` o no quedan jornadas por jugar, se rechazan los cambios.
2. **Cantidad:** exactamente 11 titulares (sin duplicados).
3. **Existencia:** los 11 IDs deben existir en la BD (y ser del usuario; el ownership lo valida el router).
4. **Posiciones** (según el `posicion_campo` declarado en el payload):
   - 1 Portero (G)
   - 3-5 Defensores (D)
   - 3-5 Mediocampistas (M)
   - 1-3 Delanteros (F)
5. **Límite por equipo:** máximo 5 jugadores del mismo club (según `equipo_id` real).

> **Sin validación de saldo:** comprar en el mercado ya descuenta; re-alinear no gasta dinero.

---

## Ejecución del Proyecto

```bash
# 1. Instalar dependencias
pip install fastapi uvicorn psycopg2-binary python-dotenv bcrypt PyJWT pydantic[email]

# 2. Configurar .env con las credenciales

# 3. Poblar datos iniciales
python populate_teams.py
python populate_players.py

# 4. Sincronizar jornadas (opcional)
python sync_jornada.py

# 5. Iniciar el servidor
uvicorn main:app --reload
```

El frontend estará disponible en `http://127.0.0.1:8000`.

---

## Roadmap — Próximos Pasos

### Fase 1 — Seguridad (JWT real) ✅ Completado

- `SECRET_KEY` desde `.env` con fail-fast en `security.py`
- Dependency `get_current_user` en `routers/deps.py` (OAuth2PasswordBearer)
- Rutas de mercado, jornadas, plantilla, ligas, ranking, usuarios → protegidas con token
- `usuario_id`/`comprador_id` eliminados de los bodies (la identidad sale del token)
- Frontend inyecta `Authorization: Bearer <token>` en cada request
- Rutas públicas: `/`, `/auth/*`, `/jugadores`

### Fase 2 — Unificar monedero a `saldo` + Reset de BD ✅ Completado (código)

- `schema.sql` con el nuevo diseño (solo `saldo`, uniques, `transacciones`, sin `mercado_pujas`)
- Código alineado al schema real: `precio`, `es_titular`, `RETURNING numero`, `saldo`
- **⚠️ Pendiente (manual):** ejecutar `schema.sql` en el SQL Editor de Supabase y repoblar con `populate_teams.py` + `populate_players.py`

### Paso 3 — Tabla de Clasificación / Ranking (Pestaña Ranking) ✅ Completado

- El endpoint `GET /ranking` ya existía (protegido) y ordena a los managers por puntos totales desde `puntos_jornada`.
- Frontend: `API.obtenerRanking()`, `UI.renderRanking()` (tabla con medallas 🥇🥈🥉, fila del usuario resaltada) y `cargarRanking()` llamada al abrir la pestaña `Clasificación`.

### Paso 4 — Módulo de Alineación (11 Titulares)

- Permitir al manager seleccionar su formación táctica (ej: 4-3-3, 4-4-2) y definir quiénes van al 11 titular y quiénes quedan en banca.

### Paso 5 — Motor de Puntuación (Fechas de la Liga) ✅ Completado

- `POST /jornadas/{numero_jornada}/sincronizar`: sincroniza stats desde SportAPI7, calcula y persiste puntos en `puntos_jornada` (`scoring_engine.py`), marca la jornada `FINALIZADA` **solo si todos los partidos terminaron** (si quedan pendientes queda `EN_PROGRESO` y se puede re-invocar sin costo) y ajusta precios/cláusulas (`market_engine.py`, ±10% según puntos).
- Ranking y tablas de liga leen `puntos_jornada` vía `plantillas_usuarios`: el E2E confirmó 16 pts reales de jornada 1 para un titular alineado.
- ✅ La jornada ya no requiere insert manual: `schema.sql` siembra las fechas 1..30 (y `seed_jornadas.py` las crea sin reset). El cuadro de `429` se maneja con `CuotaAgotada` → `429` en el endpoint.

---

## Notas Conocidas

- La `SECRET_KEY` actual tiene 43 caracteres (cumple el fail-fast de 32; sin advertencias de PyJWT).
- El frontend apunta a `http://127.0.0.1:8000` en `js/api.js:1`
- `ranking.py` suma `puntos_jornada` usando la alineación **actual** (`plantillas_usuarios`): editar la alineación después de finalizada una jornada altera el histórico. Un snapshot por jornada quedaría para una fase futura.
- `mercado.py::comprar-agente` no valida el límite de 5 jugadores por club al comprar: la regla se aplica solo al alinear. Comprar de más es posible, alinearlos no.
- Los ranking/ligas leen `plantillas_usuarios`: devuelven puntos en cero para usuarios sin alineación guardada.
- `routers/plantillas.py` fue corregido para usar `RealDictCursor` correctamente: `guardar_alineacion` accede con `row["id"]` y `obtener_plantilla` devuelve `fetchall()` directo (antes devolvía los nombres de columnas).
