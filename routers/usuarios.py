from fastapi import APIRouter, Depends, HTTPException, status
from database import get_db_connection
import psycopg2.extras
from routers.deps import get_current_user

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@router.get("/{usuario_id}")
def obtener_usuario(
    usuario_id: str,
    current_user_id: str = Depends(get_current_user),
):
    if usuario_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver los datos de otro usuario.",
        )

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cursor.execute(
            "SELECT id, nombre_usuario, saldo FROM usuarios WHERE id = %s",
            (usuario_id,)
        )
        usuario = cursor.fetchone()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return usuario
    finally:
        cursor.close()
        conn.close()