import uvicorn
from fastapi import FastAPI
from endpoints import router as api_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="API de Gestión de Pedidos y Diseños")

# Habilitar CORS para permitir solicitudes de cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Puedes restringir a dominios específicos en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

if __name__ == "__main__":
    # En entorno de desarrollo:
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    
    # Para producción, puedes usar múltiples workers:
    # uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=4, reload=True)