import os
import requests
from dotenv import load_dotenv

load_dotenv()

headers = {
    "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
    "x-rapidapi-host": os.getenv("RAPIDAPI_HOST"),
}

# ID estático de la categoría Chile
CHILE_CATEGORY_ID = 49

# Petición directa a los torneos chilenos
url = f"https://sportapi7.p.rapidapi.com/api/v1/category/{CHILE_CATEGORY_ID}/unique-tournaments"
respuesta = requests.get(url, headers=headers)

print(f"Estado HTTP: {respuesta.status_code}")
datos = respuesta.json()
print(datos)