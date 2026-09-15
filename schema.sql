-- ============================================================
-- Chilean Fantasy — Esquema de base de datos (RESET COMPLETO)
-- Ejecutar en el SQL Editor de Supabase (esquema `public`)
-- ============================================================

-- 1. Eliminar todo el esquema público (reset total)
DROP TABLE IF EXISTS
    usuarios,
    equipos,
    jugadores,
    jornadas,
    puntos_jornada,
    pujas,
    mercado_pujas,
    plantillas_usuarios,
    ligas,
    ligas_miembros,
    transacciones
CASCADE;

DROP SEQUENCE IF EXISTS
    pujas_id_seq,
    puntos_jornada_id_seq,
    plantillas_usuarios_id_seq,
    ligas_miembros_id_seq
CASCADE;

-- ============================================================
-- 2. Crear las tablas
-- ============================================================

-- -------- Usuarios --------
-- Monedero unificado: SOLO saldo (bigint, default 100.000.000)
CREATE TABLE usuarios (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre_usuario  varchar(30)  NOT NULL UNIQUE,
    email           varchar(255) NOT NULL UNIQUE,
    password_hash   varchar(100),
    saldo           bigint       NOT NULL DEFAULT 100000000,
    creado_en       timestamptz  NOT NULL DEFAULT now()
);

-- -------- Equipos --------
CREATE TABLE equipos (
    id          integer      PRIMARY KEY,
    nombre      varchar(200) NOT NULL,
    escudo_url  text
);

-- -------- Jugadores --------
-- propietario_id NULL = agente libre
CREATE TABLE jugadores (
    id              integer      PRIMARY KEY,
    nombre          varchar(200) NOT NULL,
    posicion        varchar(10),
    equipo_id       integer      REFERENCES equipos(id),
    precio          integer      NOT NULL DEFAULT 2000000,
    clausula        bigint       NOT NULL DEFAULT 5000000,
    propietario_id  uuid         REFERENCES usuarios(id),
    foto_url        text
);

-- -------- Jornadas --------
CREATE TABLE jornadas (
    numero          integer     PRIMARY KEY,
    estado          varchar(20) NOT NULL DEFAULT 'ABIERTA'
                    CHECK (estado IN ('ABIERTA', 'EN_PROGRESO', 'FINALIZADA')),
    fecha_inicio    timestamp,
    fecha_fin       timestamp
);

-- -------- Puntos por jornada --------
-- UNIQUE (jugador_id, numero_jornada) habilita el upsert del scoring_engine
CREATE TABLE puntos_jornada (
    id                  serial  PRIMARY KEY,
    jugador_id          integer REFERENCES jugadores(id),
    numero_jornada      integer NOT NULL,
    puntos              integer DEFAULT 0,
    minutos_jugados     integer DEFAULT 0,
    goles               integer DEFAULT 0,
    asistencias         integer DEFAULT 0,
    tarjetas_amarillas  integer DEFAULT 0,
    tarjetas_rojas      integer DEFAULT 0,
    UNIQUE (jugador_id, numero_jornada)
);

-- -------- Pujas --------
-- UNIQUE (usuario_id, jugador_id, fecha) habilita el upsert del mercado
CREATE TABLE pujas (
    id          serial  PRIMARY KEY,
    usuario_id  uuid    NOT NULL REFERENCES usuarios(id),
    jugador_id  integer NOT NULL REFERENCES jugadores(id),
    monto       integer NOT NULL,
    fecha       date    DEFAULT CURRENT_DATE,
    UNIQUE (usuario_id, jugador_id, fecha)
);

-- -------- Plantillas de usuarios --------
-- Base del futuro módulo de alineación (11 titulares + banca)
CREATE TABLE plantillas_usuarios (
    id              serial      PRIMARY KEY,
    usuario_id      uuid        REFERENCES usuarios(id),
    jugador_id      integer     REFERENCES jugadores(id),
    es_titular      boolean     DEFAULT true,
    posicion_campo  varchar(10)
);

-- -------- Ligas --------
CREATE TABLE ligas (
    id                uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre            varchar(100) NOT NULL,
    codigo_invitacion varchar(6)   NOT NULL UNIQUE,
    creador_id        uuid         REFERENCES usuarios(id),
    creado_en         timestamptz  DEFAULT now()
);

CREATE TABLE ligas_miembros (
    id          serial      PRIMARY KEY,
    liga_id     uuid        REFERENCES ligas(id),
    usuario_id  uuid        REFERENCES usuarios(id),
    unido_en    timestamptz DEFAULT now()
);

-- -------- Transacciones (auditoría de mercado) --------
-- Reservada para uso futuro: deja rastro de pujas, clausulazos, blindajes y compras
CREATE TABLE transacciones (
    id            uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
    comprador_id  uuid         REFERENCES usuarios(id),
    vendedor_id   uuid         REFERENCES usuarios(id),
    jugador_id    integer      REFERENCES jugadores(id),
    monto         bigint       NOT NULL,
    tipo          varchar(20)  NOT NULL
                  CHECK (tipo IN ('PUJA', 'CLAUZULAZO', 'BLINDAJE', 'COMPRA_AGENTE')),
    fecha         timestamp    DEFAULT now()
);