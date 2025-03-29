import os
import subprocess
from config import RCLONE_REMOTE

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
