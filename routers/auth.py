from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from database import get_db_connection
from schemas import UsuarioRegistro, Token
from security import hash_password, verify_password, crear_access_token

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/registro", response_model=Token, status_code=status.HTTP_201_CREATED)
def registrar_usuario(usuario: UsuarioRegistro):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Verificar si el email o nombre de usuario ya existe
        cursor.execute(
            "SELECT id FROM usuarios WHERE email = %s OR nombre_usuario = %s;",
            (usuario.email, usuario.nombre_usuario)
        )
        existe_user = cursor.fetchone()
        
        if existe_user:
            raise HTTPException(status_code=400, detail="El correo o el nombre de usuario ya está en uso.")

        # 2. Insertar nuevo usuario
        pwd_hashed = hash_password(usuario.password)
        cursor.execute(
            """
            INSERT INTO usuarios (nombre_usuario, email, password_hash, presupuesto)
            VALUES (%s, %s, %s, 100000000)
            RETURNING id, nombre_usuario;
            """,
            (usuario.nombre_usuario, usuario.email, pwd_hashed)
        )
        nuevo_usuario = cursor.fetchone()
        conn.commit()

        # 3. Generar token
        user_id_str = str(nuevo_usuario["id"])
        access_token = crear_access_token(data={"sub": user_id_str})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "usuario_id": user_id_str,
            "nombre_usuario": nuevo_usuario["nombre_usuario"]
        }
    except HTTPException as he:
        conn.rollback()
        raise he
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Error al registrar usuario: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@router.post("/login", response_model=Token)
def iniciar_sesion(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Permite iniciar sesión con correo o nombre de usuario
        cursor.execute(
            "SELECT id, nombre_usuario, password_hash FROM usuarios WHERE email = %s OR nombre_usuario = %s;",
            (form_data.username, form_data.username)
        )
        usuario = cursor.fetchone()

        if not usuario or not usuario.get("password_hash"):
            raise HTTPException(status_code=401, detail="Credenciales incorrectas.")

        if not verify_password(form_data.password, usuario["password_hash"]):
            raise HTTPException(status_code=401, detail="Credenciales incorrectas.")

        user_id_str = str(usuario["id"])
        access_token = crear_access_token(data={"sub": user_id_str})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "usuario_id": user_id_str,
            "nombre_usuario": usuario["nombre_usuario"]
        }
    finally:
        cursor.close()
        conn.close()