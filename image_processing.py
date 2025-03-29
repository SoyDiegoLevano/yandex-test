import io
import os
import tempfile
import subprocess
from PIL import Image
from fastapi import HTTPException

def generate_preview(image_path: str) -> bytes:
    """
    Abre la imagen desde 'image_path', la convierte a WebP y la comprime.
    Si el archivo es CDR, lo convierte primero a PNG usando Inkscape.
    Retorna los bytes de la imagen en formato WebP.
    """
    try:
        # Verificar si el archivo es un CDR
        if image_path.lower().endswith('.cdr'):
            # Crear un archivo temporal para guardar la conversión a PNG
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_filename = tmp.name
            # Convertir el CDR a PNG usando Inkscape
            command = ["inkscape", image_path, "--export-type=png", "--export-filename", tmp_filename]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                os.remove(tmp_filename)
                raise Exception(f"Inkscape falló: {result.stderr}")
            # Abrir la imagen convertida
            with Image.open(tmp_filename) as img:
                output = io.BytesIO()
                img.save(output, format="WEBP", quality=75)
            os.remove(tmp_filename)
            return output.getvalue()
        else:
            # Procesamiento normal para otros formatos
            with Image.open(image_path) as img:
                output = io.BytesIO()
                img.save(output, format="WEBP", quality=75)
                return output.getvalue()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar previsualización: {str(e)}")
