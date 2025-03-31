from fastapi import FastAPI, HTTPException, Query
import requests

app = FastAPI()

# ⚠️ Reemplaza con tu token de Yandex Disk
YANDEX_DISK_TOKEN = "y0__xDEpMmGCBjcxzYgpNSC2BKQLw2lA21Ek-XwgjuE9SpSiJcTcA"

def get_direct_image_link(yandex_path: str) -> str:
    """
    Obtiene un enlace directo para visualizar una imagen en HTML desde Yandex Disk.
    """
    api_url = "https://cloud-api.yandex.net/v1/disk/resources/download"
    headers = {"Authorization": f"OAuth {YANDEX_DISK_TOKEN}"}
    params = {"path": yandex_path}
    
    response = requests.get(api_url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        data = data

        if not data:
            raise Exception("No se encontró 'href' en la respuesta de Yandex Disk")
        
        return data
    else:
        raise Exception(f"Error al obtener enlace directo: {response.status_code} - {response.text}")

@app.get("/image-url")
def image_url(path: str = Query(..., description="Ruta en Yandex Disk, ej: /imagenes/foto.jpg")):
    """
    Retorna un enlace directo para visualizar una imagen en HTML desde Yandex Disk.
    """
    try:
        link = get_direct_image_link(path)
        return {"image_url": link}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
