import io
from PIL import Image
from fastapi import HTTPException

def generate_preview(image_path: str) -> bytes:
    """
    Abre la imagen desde 'image_path', la convierte a WebP y la comprime.
    Retorna los bytes de la imagen en formato WebP.
    """
    try:
        print(image_path)
        with Image.open(image_path) as img:
            output = io.BytesIO()
            img.save(output, format="WEBP", quality=75)
            return output.getvalue()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar previsualización: {str(e)}")
