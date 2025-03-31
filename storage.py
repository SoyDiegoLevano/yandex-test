import os
import subprocess
from config import RCLONE_REMOTE, MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET_NAME
from minio import Minio
from minio.error import S3Error
from datetime import timedelta

def upload_to_cloud(local_path: str, filename: str) -> str:
    """
    Sube el archivo localizado en 'local_path' a Yandex Disk usando Rclone.
    Retorna la ruta remota (string) en Yandex Disk.
    """
    remote_path = os.path.join(RCLONE_REMOTE, filename)
    command = ["rclone", "copy", local_path, remote_path]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Rclone falló: {result.stderr}")
    return remote_path

def download_from_cloud(remote_path: str, local_path: str):
    """
    Descarga el archivo desde Yandex Disk (ruta remota) a 'local_path' usando Rclone.
    """
    command = ["rclone", "copy", remote_path, os.path.dirname(local_path)]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Rclone falló al descargar: {result.stderr}")

def delete_from_cloud(remote_path: str):
    """
    Borra el archivo localizado en 'remote_path' de Yandex Disk usando Rclone.
    """
    command = ["rclone", "delete", remote_path]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Rclone falló al borrar: {result.stderr}")

def upload_to_minio(file_path: str, object_name: str):
    """Sube un archivo a MinIO.

    Args:
        file_path (str): La ruta local del archivo a subir.
        object_name (str): El nombre con el que se guardará el objeto en MinIO.

    Returns:
        str: La ruta del objeto en MinIO (formato: minio://bucket_name/object_name).

    Raises:
        Exception: Si ocurre un error al subir el archivo a MinIO.
    """
    try:
        minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False  # Establecer en True si tu servidor MinIO usa HTTPS
        )
        found = minio_client.bucket_exists(MINIO_BUCKET_NAME)
        if not found:
            minio_client.make_bucket(MINIO_BUCKET_NAME)
        else:
            print(f"El bucket '{MINIO_BUCKET_NAME}' ya existe")

        minio_client.fput_object(MINIO_BUCKET_NAME, object_name, file_path)
        return f"minio://{MINIO_BUCKET_NAME}/{object_name}"
    except S3Error as e:
        raise Exception(f"Error al subir a MinIO: {e}")

def generate_minio_presigned_url(object_path: str, expiry_seconds: int = 60 * 60 * 24): # Expira en 24 horas por defecto
    """Genera una URL presignada para un objeto en MinIO.

    Args:
        object_path (str): La ruta del objeto en MinIO (formato: minio://bucket_name/object_name).
        expiry_seconds (int): El tiempo de expiración de la URL en segundos (por defecto: 24 horas).

    Returns:
        str: La URL presignada para acceder al objeto.

    Raises:
        Exception: Si ocurre un error al generar la URL presignada.
    """
    try:
        minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )
        bucket_name, object_name = object_path[len("minio://"):].split("/", 1)
        url = minio_client.get_presigned_url(
            "GET",
            bucket_name,
            object_name,
            expires=timedelta(seconds=expiry_seconds)
        )
        return url
    except S3Error as e:
        raise Exception(f"Error al generar la URL presignada de MinIO: {e}")