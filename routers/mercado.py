from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import psycopg2.extras
from database import get_db_connection

router = APIRouter(prefix="/mercado", tags=["Mercado y Economía"])

# --- MODELOS PYDANTIC ---

class CompraAgenteSchema(BaseModel):
    usuario_id: str
    jugador_id: str

class PujaSchema(BaseModel):
    usuario_id: str
    jugador_id: str
    monto: int

class ClausulazoDTO(BaseModel):
    comprador_id: str
    jugador_id: str

class SubirClausulaDTO(BaseModel):
    usuario_id: str
    jugador_id: str
    monto_incremento: int


# --- ENDPOINTS ---

@router.get("/agentes-libres")
def obtener_agentes_libres():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        query = """
            WITH aleatorios AS (
                SELECT *, 
                       ROW_NUMBER() OVER (
                           PARTITION BY posicion 
                           ORDER BY md5(id::text || CURRENT_DATE::text)
                       ) as rn
                FROM jugadores
                WHERE propietario_id IS NULL
            )
            SELECT id, nombre, posicion, equipo_id, precio_base, clausula
            FROM aleatorios
            WHERE rn <= 2
            ORDER BY 
                CASE posicion 
                    WHEN 'POR' THEN 1 
                    WHEN 'DEF' THEN 2 
                    WHEN 'MED' THEN 3 
                    WHEN 'DEL' THEN 4 
                END;
        """
        cursor.execute(query)
        agentes = cursor.fetchall()
        return {"agentes": agentes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en BD: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.post("/comprar-agente")
def comprar_agente_libre(payload: CompraAgenteSchema):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        cursor.execute("SELECT id, precio_base, propietario_id FROM jugadores WHERE id = %s::uuid", (str(payload.jugador_id),))
        jugador = cursor.fetchone()
        
        if not jugador:
            raise HTTPException(status_code=404, detail="Jugador no encontrado.")
        if jugador['propietario_id'] is not None:
            raise HTTPException(status_code=400, detail="Este jugador ya tiene propietario.")

        cursor.execute("SELECT id, saldo FROM usuarios WHERE id = %s::uuid", (str(payload.usuario_id),))
        usuario = cursor.fetchone()
        
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")

        costo = jugador['precio_base']
        if usuario['saldo'] < costo:
            raise HTTPException(status_code=400, detail="Saldo insuficiente para comprar al jugador.")

        cursor.execute("UPDATE usuarios SET saldo = saldo - %s WHERE id = %s::uuid", (costo, str(payload.usuario_id)))
        cursor.execute("UPDATE jugadores SET propietario_id = %s::uuid WHERE id = %s::uuid", (str(payload.usuario_id), str(payload.jugador_id)))
        
        conn.commit()
        return {"mensaje": "Jugador fichado con éxito."}
        
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error en BD: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.post("/pujar")
def realizar_puja(payload: PujaSchema):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        cursor.execute("SELECT precio_base FROM jugadores WHERE id = %s::uuid", (str(payload.jugador_id),))
        jugador = cursor.fetchone()
        if not jugador:
            raise HTTPException(status_code=404, detail="Jugador no encontrado.")
            
        if payload.monto < jugador["precio_base"]:
            raise HTTPException(status_code=400, detail="El monto debe ser igual o mayor al precio base.")

        cursor.execute("SELECT saldo FROM usuarios WHERE id = %s::uuid", (str(payload.usuario_id),))
        usuario = cursor.fetchone()
        if not usuario or usuario["saldo"] < payload.monto:
            raise HTTPException(status_code=400, detail="No tienes suficiente saldo disponible.")

        cursor.execute(
            """
            INSERT INTO pujas (usuario_id, jugador_id, monto, fecha)
            VALUES (%s::uuid, %s::uuid, %s, CURRENT_DATE)
            ON CONFLICT (usuario_id, jugador_id, fecha)
            DO UPDATE SET monto = EXCLUDED.monto;
            """,
            (str(payload.usuario_id), str(payload.jugador_id), payload.monto)
        )
        conn.commit()
        return {"mensaje": "Puja registrada exitosamente."}

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error en BD: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.post("/procesar-pujas-diarias")
def procesar_pujas():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cursor.execute("""
            SELECT DISTINCT ON (jugador_id) jugador_id, usuario_id, monto
            FROM pujas
            WHERE fecha = CURRENT_DATE
            ORDER BY jugador_id, monto DESC;
        """)
        ganadores = cursor.fetchall()

        for g in ganadores:
            cursor.execute("UPDATE jugadores SET propietario_id = %s::uuid WHERE id = %s::uuid", (str(g["usuario_id"]), str(g["jugador_id"])))
            cursor.execute("UPDATE usuarios SET saldo = saldo - %s WHERE id = %s::uuid", (g["monto"], str(g["usuario_id"])))

        conn.commit()
        return {"mensaje": f"Procesadas {len(ganadores)} transferencias."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error en BD: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.post("/subir-clausula")
def subir_clausula(dto: SubirClausulaDTO):
    if dto.monto_incremento <= 0:
        raise HTTPException(status_code=400, detail="El monto de incremento debe ser mayor a 0.")

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        cursor.execute("SELECT id, propietario_id FROM jugadores WHERE id = %s::uuid", (str(dto.jugador_id),))
        jugador = cursor.fetchone()
        
        if not jugador:
            raise HTTPException(status_code=404, detail="Jugador no encontrado.")

        if not jugador["propietario_id"] or str(jugador["propietario_id"]) != str(dto.usuario_id):
            raise HTTPException(status_code=403, detail="El jugador no pertenece a tu plantilla.")

        cursor.execute("SELECT saldo FROM usuarios WHERE id = %s::uuid", (str(dto.usuario_id),))
        usuario = cursor.fetchone()
        
        if not usuario or usuario["saldo"] < dto.monto_incremento:
            raise HTTPException(status_code=400, detail="No tienes suficiente saldo para aumentar la cláusula.")

        cursor.execute("UPDATE usuarios SET saldo = saldo - %s WHERE id = %s::uuid", (dto.monto_incremento, str(dto.usuario_id)))
        cursor.execute("UPDATE jugadores SET clausula = COALESCE(clausula, 0) + %s WHERE id = %s::uuid", (dto.monto_incremento, str(dto.jugador_id)))

        conn.commit()
        return {"mensaje": "¡Cláusula aumentada y blindada exitosamente!"}

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error en BD: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.post("/pagar-clausula")
def pagar_clausula(dto: ClausulazoDTO):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
    try:
        cursor.execute("SELECT id, nombre, clausula, propietario_id FROM jugadores WHERE id = %s::uuid", (str(dto.jugador_id),))
        jugador = cursor.fetchone()
        
        if not jugador:
            raise HTTPException(status_code=404, detail="Jugador no encontrado.")
                
        if not jugador["propietario_id"]:
            raise HTTPException(status_code=400, detail="El jugador no pertenece a ningún rival (es agente libre).")
                
        if str(jugador["propietario_id"]) == str(dto.comprador_id):
            raise HTTPException(status_code=400, detail="No puedes aplicar un clausulazo a tu propio jugador.")

        vendedor_id = jugador["propietario_id"]
        precio_clausula = jugador["clausula"] or 0

        if precio_clausula <= 0:
            raise HTTPException(status_code=400, detail="El jugador no tiene una cláusula válida establecida.")

        cursor.execute("SELECT saldo FROM usuarios WHERE id = %s::uuid", (str(dto.comprador_id),))
        comprador = cursor.fetchone()
        
        if not comprador or comprador["saldo"] < precio_clausula:
            raise HTTPException(status_code=400, detail="Saldo insuficiente para pagar la cláusula.")

        cursor.execute("UPDATE usuarios SET saldo = saldo - %s WHERE id = %s::uuid", (precio_clausula, str(dto.comprador_id)))
        cursor.execute("UPDATE usuarios SET saldo = saldo + %s WHERE id = %s::uuid", (precio_clausula, str(vendedor_id)))
        cursor.execute("UPDATE jugadores SET propietario_id = %s::uuid WHERE id = %s::uuid", (str(dto.comprador_id), str(dto.jugador_id)))

        conn.commit()
        return {"mensaje": f"¡Clausulazo exitoso! Has fichado a {jugador['nombre']} por ${precio_clausula:,}"}

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error en BD: {str(e)}")
    finally:
        cursor.close()
        conn.close()