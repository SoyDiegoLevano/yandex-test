from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
import requests
import uvicorn

app = FastAPI()

# Configuración de la aplicación en Yandex
CLIENT_ID = "6740f5f3b6e44c48a22131627de2226b"
CLIENT_SECRET = "8a24e106e2214e6a8e96163e4ff2eb27"
REDIRECT_URI = "http://127.0.0.1:8000/callback"  # Debe coincidir exactamente con lo configurado en Yandex
SCOPES = "cloud_api:disk.read cloud_api:disk.write cloud_api:disk.info"  # Permisos necesarios

@app.get("/")
def index():
    html_content = """
    <html>
      <head>
        <title>Autenticación Yandex Disk</title>
      </head>
      <body>
        <h1>Bienvenido</h1>
        <p>Para obtener un token de Yandex Disk, haz clic en el siguiente enlace:</p>
        <a href="/auth">Autenticar con Yandex Disk</a>
      </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/auth")
def auth():
    """
    Construye la URL de autorización y redirige al usuario a Yandex para autorizar la aplicación.
    """
    authorize_url = (
        "https://oauth.yandex.com/authorize"
        "?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPES}"
    )
    return RedirectResponse(url=authorize_url)

@app.get("/callback")
def callback(request: Request):
    """
    Captura el parámetro 'code' de la URL de callback, lo intercambia por un token de acceso
    y retorna los datos obtenidos en formato JSON.
    """
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="No se proporcionó el parámetro 'code'")
    
    token_url = "https://oauth.yandex.com/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
    }
    
    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        token_data = response.json()
        return JSONResponse(content=token_data)
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)

if __name__ == "__main__":
    # Ejecuta la aplicación en http://127.0.0.1:8000
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
