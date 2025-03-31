# config.py
import os
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()
print(os.getenv("UPLOAD_FOLDER"))

# Carpetas de subida y caché
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")
CACHE_ORIGINAL_DIR = os.getenv("CACHE_ORIGINAL_DIR")
CACHE_DESIGN_DIR = os.getenv("CACHE_DESIGN_DIR")
YANDEX_DISK_TOKEN = os.getenv("YANDEX_DISK_TOKEN")

# Tiempo de expiración para la caché en segundos (24 horas por defecto)
CACHE_EXPIRATION_SECONDS = int(os.getenv("CACHE_EXPIRATION_SECONDS", 86400))

# Configuración de la base de datos
DB_URL = os.getenv("DB_URL")

# Configuración de Rclone para Yandex Disk
RCLONE_REMOTE = os.getenv("RCLONE_REMOTE")

# Variable para habilitar o restringir previsualizaciones
PREVIEW_ENABLED = os.getenv("PREVIEW_ENABLED", "false").lower() == "true"

# Configuración de MinIO
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "dikals")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "dikals123")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "preview-cache")

# Asegurarse de que las carpetas necesarias existan
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CACHE_ORIGINAL_DIR, exist_ok=True)
os.makedirs(CACHE_DESIGN_DIR, exist_ok=True)