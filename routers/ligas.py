import random
import string
from fastapi import APIRouter, HTTPException
from database import get_db_connection
from pydantic import BaseModel

router = APIRouter(prefix="/ligas", tags=["Ligas"])

class CrearLigaRequest(BaseModel):
    nombre: str
    creador_id: str

class UnirseLigaRequest(BaseModel):
    codigo_invitacion: str
    usuario_id: str

def generar_codigo():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@router.post("/crear")
def crear_liga(datos: CrearLigaRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        codigo = generar_codigo()

        cursor.execute(
            "INSERT INTO ligas (nombre, codigo_invitacion, creador_id) VALUES (%s, %s, %s) RETURNING id, nombre, codigo_invitacion;",
            (datos.nombre, codigo, datos.creador_id)
        )
        liga = cursor.fetchone()

        # Unir automáticamente al creador a la liga
        cursor.execute(
            "INSERT INTO ligas_miembros (liga_id, usuario_id) VALUES (%s, %s);",
            (liga["id"], datos.creador_id)
        )

        conn.commit()
        return {"mensaje": "Liga creada exitosamente", "liga": liga}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Error al crear liga: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@router.post("/unirse")
def unirse_a_liga(datos: UnirseLigaRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM ligas WHERE codigo_invitacion = %s;", (datos.codigo_invitacion.upper(),))
        liga = cursor.fetchone()

        if not liga:
            raise HTTPException(status_code=404, detail="Código de invitación inválido.")

        cursor.execute(
            "INSERT INTO ligas_miembros (liga_id, usuario_id) VALUES (%s, %s);",
            (liga["id"], datos.usuario_id)
        )
        conn.commit()
        return {"mensaje": "Te has unido exitosamente a la liga."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Ya perteneces a esta liga o hubo un error al unirte.")
    finally:
        cursor.close()
        conn.close()

@router.get("/{liga_id}/tabla")
def obtener_tabla_liga(liga_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT 
                u.id AS usuario_id,
                u.nombre_usuario,
                COALESCE(SUM(
                    CASE 
                        WHEN pu.es_capitan THEN COALESCE(pj.puntos, 0) * 2 
                        ELSE COALESCE(pj.puntos, 0) 
                    END
                ), 0) AS puntos_totales
            FROM ligas_miembros lm
            JOIN usuarios u ON lm.usuario_id = u.id
            LEFT JOIN plantillas_usuarios pu ON u.id = pu.usuario_id
            LEFT JOIN puntos_jornada pj ON pu.jugador_id = pj.jugador_id
            WHERE lm.liga_id = %s
            GROUP BY u.id, u.nombre_usuario
            ORDER BY puntos_totales DESC;
        """
        cursor.execute(query, (liga_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()