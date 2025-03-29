import os
import time
from config import CACHE_ORIGINAL_DIR, CACHE_DESIGN_DIR, CACHE_EXPIRATION_SECONDS

def get_cached_preview(pedido_id: int, tipo: str) -> str:
    """
    Retorna la ruta del archivo en caché si existe y no ha expirado.
    'tipo' debe ser 'original' o 'design'.
    """
    cache_dir = CACHE_ORIGINAL_DIR if tipo == "original" else CACHE_DESIGN_DIR
    cache_file = os.path.join(cache_dir, f"cache_{tipo}_{pedido_id}.webp")
    if os.path.exists(cache_file):
        # Verificar si el archivo ha expirado
        mod_time = os.path.getmtime(cache_file)
        if time.time() - mod_time < CACHE_EXPIRATION_SECONDS:
            return cache_file
        else:
            os.remove(cache_file)
    return None

def set_cached_preview(pedido_id: int, tipo: str, data: bytes):
    """
    Guarda la previsualización en la carpeta de caché correspondiente.
    """
    cache_dir = CACHE_ORIGINAL_DIR if tipo == "original" else CACHE_DESIGN_DIR
    cache_file = os.path.join(cache_dir, f"cache_{tipo}_{pedido_id}.webp")
    with open(cache_file, "wb") as f:
        f.write(data)
    return cache_file
