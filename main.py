import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# 1. Importar tus routers (asegúrate de que los nombres de archivo coincidan)
from routers import auth, jugadores, plantillas, usuarios, mercado 

app = FastAPI()

# 2. Registrar cada router en la aplicación
app.include_router(auth.router)
app.include_router(jugadores.router)
app.include_router(plantillas.router)
app.include_router(usuarios.router)
app.include_router(mercado.router)

# 3. Archivos estáticos y HTML principal
if os.path.exists("js"):
    app.mount("/js", StaticFiles(directory="js"), name="js")

@app.get("/")
def read_root():
    return FileResponse("index.html")