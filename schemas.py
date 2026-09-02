from pydantic import BaseModel, EmailStr, Field

class UsuarioRegistro(BaseModel):
    nombre_usuario: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=50)

class Token(BaseModel):
    access_token: str
    token_type: str
    usuario_id: str
    nombre_usuario: str
    
class CrearUsuarioRequest(BaseModel):
    nombre_usuario: str
    email: str

class GuardarPlantillaRequest(BaseModel):
    usuario_id: str
    jugador_ids: list[int]
    capitan_id: int

class ActualizarEstadoJornadaRequest(BaseModel):
    estado: str

class PujaRequest(BaseModel):
    usuario_id: str
    jugador_id: int
    monto: int = Field(..., gt=0)

class PagarClausulaRequest(BaseModel):
    comprador_id: str
    jugador_id: int

class AumentarClausulaRequest(BaseModel):
    usuario_id: str
    jugador_id: int
    monto_incremento: int = Field(..., gt=0)