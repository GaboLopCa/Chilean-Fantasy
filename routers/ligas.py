import random
import string
from fastapi import APIRouter, Depends, HTTPException
from database import get_db_connection
from pydantic import BaseModel
from routers.deps import get_current_user

router = APIRouter(prefix="/ligas", tags=["Ligas"])

class CrearLigaRequest(BaseModel):
    nombre: str

class UnirseLigaRequest(BaseModel):
    codigo_invitacion: str

def generar_codigo():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@router.post("/crear")
def crear_liga(
    datos: CrearLigaRequest,
    creador_id: str = Depends(get_current_user),
):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Reintenta si el código generado ya existe (columna UNIQUE)
        codigo = None
        liga = None
        for _ in range(5):
            codigo = generar_codigo()
            cursor.execute(
                "INSERT INTO ligas (nombre, codigo_invitacion, creador_id) VALUES (%s, %s, %s) RETURNING id, nombre, codigo_invitacion;",
                (datos.nombre, codigo, creador_id)
            )
            try:
                liga = cursor.fetchone()
                break
            except Exception:
                conn.rollback()
                liga = None

        if liga is None:
            raise HTTPException(status_code=400, detail="No se pudo generar un código único. Intenta nuevamente.")

        # Unir automáticamente al creador a la liga
        cursor.execute(
            "INSERT INTO ligas_miembros (liga_id, usuario_id) VALUES (%s, %s);",
            (liga["id"], creador_id)
        )

        conn.commit()
        return {"mensaje": "Liga creada exitosamente", "liga": liga}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Error al crear liga: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@router.post("/unirse")
def unirse_a_liga(
    datos: UnirseLigaRequest,
    usuario_id: str = Depends(get_current_user),
):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM ligas WHERE codigo_invitacion = %s;", (datos.codigo_invitacion.upper(),))
        liga = cursor.fetchone()

        if not liga:
            raise HTTPException(status_code=404, detail="Código de invitación inválido.")

        cursor.execute(
            "INSERT INTO ligas_miembros (liga_id, usuario_id) VALUES (%s, %s);",
            (liga["id"], usuario_id)
        )
        conn.commit()
        return {"mensaje": "Te has unido exitosamente a la liga."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Ya perteneces a esta liga o hubo un error al unirte. {str(e)}")
    finally:
        cursor.close()
        conn.close()

@router.get("/{liga_id}/tabla")
def obtener_tabla_liga(
    liga_id: str,
    _usuario_id: str = Depends(get_current_user),
):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT
                u.id AS usuario_id,
                u.nombre_usuario,
                COALESCE(SUM(COALESCE(pj.puntos, 0)), 0) AS puntos_totales
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