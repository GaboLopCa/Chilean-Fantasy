from fastapi import APIRouter, HTTPException
from database import get_db_connection
from schemas import CrearUsuarioRequest
import psycopg2
import psycopg2.extras

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@router.post("")
def crear_usuario(usuario: CrearUsuarioRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO usuarios (nombre_usuario, email) VALUES (%s, %s) RETURNING id, nombre_usuario, presupuesto;",
            (usuario.nombre_usuario, usuario.email),
        )
        nuevo_usuario = cursor.fetchone()
        conn.commit()
        return nuevo_usuario
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Error al crear usuario: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.get("/{usuario_id}")
def obtener_usuario(usuario_id: str):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cursor.execute(
            "SELECT id, nombre_usuario, presupuesto FROM usuarios WHERE id = %s", 
            (usuario_id,)
        )
        usuario = cursor.fetchone()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return usuario
    finally:
        cursor.close()
        conn.close()