import os
import io
import asyncio
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from config import UPLOAD_FOLDER, PREVIEW_ENABLED, CACHE_EXPIRATION_SECONDS, CACHE_ORIGINAL_DIR, CACHE_DESIGN_DIR
from database import Pedido, Diseno, get_db
from storage import upload_to_cloud, download_from_cloud, delete_from_cloud
from image_processing import generate_preview
from preview_cache import get_cached_preview, set_cached_preview

router = APIRouter()

def upload_preview_and_update_db(cache_file: str, preview_filename: str, pedido_obj, tipo: str):
    """
    Función auxiliar que se ejecuta en background para subir la previsualización a la nube
    y actualizar el registro en la base de datos.
    """
    try:
        cloud_cache_path = upload_to_cloud(cache_file, preview_filename)
        # Obtener una nueva sesión llamando a get_db() manualmente
        db = next(get_db())
        # Buscar el pedido con la nueva sesión (usando el id)
        pedido = db.query(Pedido).get(pedido_obj.id)
        if pedido is None:
            print("No se encontró el pedido en la base de datos con la nueva sesión")
            db.close()
            return

        if tipo == "original":
            pedido.original_cache_path = cloud_cache_path
            print("Se subió a original bd: ", pedido, cloud_cache_path)
        else:  # tipo == "design"
            pedido.design_cache_path = cloud_cache_path

        db.commit()
        db.close()
    except Exception as e:
        # Aquí se podría registrar el error con logging
        print(f"Error en upload_preview_and_update_db: {e}")

# Endpoint 1: Recepción del Pedido (Fase 1)
@router.post("/pedido", response_model=dict)
async def create_pedido(client_info: str = None, file: UploadFile = File(...), db: Session = Depends(get_db)):
    upload_path = None
    cloud_path = None
    try:
        # 1. Crear el pedido inicialmente sin la ruta definitiva
        nuevo_pedido = Pedido(client_info=client_info, original_path="")  # valor provisional
        db.add(nuevo_pedido)
        db.commit()       # Se confirma para generar el ID
        db.refresh(nuevo_pedido)
        
        # 2. Guardar el archivo temporalmente utilizando el ID en el nombre, preservando la extensión original
        ext = os.path.splitext(file.filename)[1]  # extrae la extensión (incluye el punto)
        filename_with_id = f"original_{nuevo_pedido.id}{ext}"
        upload_path = os.path.join(UPLOAD_FOLDER, filename_with_id)
        with open(upload_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 3. Subir el archivo a la nube
        try:
            cloud_path = upload_to_cloud(upload_path, filename_with_id)
        except Exception as e:
            # Si falla la subida a la nube, eliminar el pedido de la BD y propagar el error
            db.delete(nuevo_pedido)
            db.commit()
            raise HTTPException(status_code=500, detail=f"Error subiendo a Yandex Disk: {str(e)}")
        
        # 4. Actualizar el pedido con la ruta del archivo en la nube
        nuevo_pedido.original_path = cloud_path
        try:
            db.commit()
        except Exception as e:
            # Si falla el commit, eliminar el pedido de la BD y borrar el archivo de la nube
            db.delete(nuevo_pedido)
            db.commit()
            try:
                delete_from_cloud(cloud_path)  # Función para borrar el archivo de la nube
            except Exception as del_err:
                # Se podría registrar el error, pero se propaga el error original
                pass
            raise HTTPException(status_code=500, detail=f"Error actualizando el pedido en la base de datos: {str(e)}")
        
        return {"pedido_id": nuevo_pedido.id, "estado": nuevo_pedido.estado}
    
    except Exception as general_error:
        db.rollback()  # Revertir cualquier cambio pendiente en la BD
        raise HTTPException(status_code=500, detail=f"Error en la creación del pedido: {str(general_error)}")
    
    finally:
        # Eliminar el archivo temporal de disco, si existe
        if upload_path and os.path.exists(upload_path):
            try:
                os.remove(upload_path)
            except Exception as file_err:
                # Se podría registrar el error de eliminación
                pass

# Endpoint 2: Previsualización de la imagen original (Fase 1)
@router.get("/preview/original/{pedido_id}")
async def preview_original(
    pedido_id: int, 
    db: Session = Depends(get_db), 
    background_tasks: BackgroundTasks = None
):
    if not PREVIEW_ENABLED:
        raise HTTPException(status_code=403, detail="Previsualización no habilitada para este usuario")
    
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    # 1. Buscar en caché local
    cache_file = get_cached_preview(pedido_id, "original")
    if cache_file:
        return StreamingResponse(open(cache_file, "rb"), media_type="image/webp")
    
    # 2. Revisar si la previsualización ya está en la nube
    if pedido.original_cache_path:
        print("ENTRO A PASO 2")
        # Usar un nombre de archivo por defecto en el directorio de caché
        cache_file = os.path.join(CACHE_ORIGINAL_DIR, f"cache_original_{pedido_id}.webp")
        try:
            download_from_cloud(pedido.original_cache_path, cache_file)
            return StreamingResponse(open(cache_file, "rb"), media_type="image/webp")
        except Exception as e:
            # Si falla la descarga, se continúa con la generación de la previsualización
            pass
    
    # 3. Descargar el archivo original desde la nube y generar la previsualización

    original_filename = os.path.basename(pedido.original_path)
    print(original_filename)
    temp_download = os.path.join(UPLOAD_FOLDER, f"{original_filename}")
    print(UPLOAD_FOLDER)
    try:
        download_from_cloud(pedido.original_path, temp_download)
        print("SE DESCARGO EL ARCHIVO")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al descargar archivo: {str(e)}")
    
    # Ejecutar la conversión en un thread para evitar bloquear el event loop
    preview_bytes = await asyncio.to_thread(generate_preview, temp_download)
    cache_file = set_cached_preview(pedido_id, "original", preview_bytes)
    os.remove(temp_download)
    
    # 4. Subir la previsualización a la nube en background para no retrasar la respuesta
    preview_filename = f"cache_original_{pedido_id}.webp"
    if background_tasks:
        background_tasks.add_task(upload_preview_and_update_db, cache_file, preview_filename, pedido, "original")
    
    return StreamingResponse(io.BytesIO(preview_bytes), media_type="image/webp")


# Endpoint 3: Creación y registro del diseño final (Fase 2)
@router.post("/design/{pedido_id}", response_model=dict)
async def upload_design(pedido_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    # Extraer la extensión del archivo original y renombrar usando el id
    ext = os.path.splitext(file.filename)[1]
    new_filename = f"{pedido_id}_design{ext}"
    upload_path = os.path.join(UPLOAD_FOLDER, new_filename)
    
    with open(upload_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    try:
        cloud_path = upload_to_cloud(upload_path, new_filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error subiendo a Yandex Disk: {str(e)}")
    
    nuevo_diseno = Diseno(pedido_id=pedido_id, design_path=cloud_path)
    db.add(nuevo_diseno)
    db.commit()
    db.refresh(nuevo_diseno)
    
    return {"design_id": nuevo_diseno.id, "estado": nuevo_diseno.estado}

# Endpoint 4: Previsualización del diseño final (Fase 2)
@router.get("/preview/design/{pedido_id}")
async def preview_design(pedido_id: int, db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    if not PREVIEW_ENABLED:
        raise HTTPException(status_code=403, detail="Previsualización no habilitada para este usuario")
    
    diseno = db.query(Diseno).filter(Diseno.pedido_id == pedido_id).first()
    if not diseno:
        raise HTTPException(status_code=404, detail="Diseño no encontrado para el pedido")
    
    # 1. Buscar en caché local
    cache_file = get_cached_preview(pedido_id, "design")
    if cache_file:
        return StreamingResponse(open(cache_file, "rb"), media_type="image/webp")
    
    # 2. Revisar si la previsualización ya está en la nube
    if diseno.design_cache_path:
        local_cache = os.path.join(UPLOAD_FOLDER, f"{pedido_id}_design.webp")
        try:
            download_from_cloud(diseno.design_cache_path, local_cache)
            with open(local_cache, "rb") as f:
                data = f.read()
            cache_file = set_cached_preview(pedido_id, "design", data)
            os.remove(local_cache)
            return StreamingResponse(open(cache_file, "rb"), media_type="image/webp")
        except Exception as e:
            pass
    
    # 3. Descargar el archivo de diseño y generar la previsualización
    temp_download = os.path.join(UPLOAD_FOLDER, f"temp_{pedido_id}_design")
    try:
        download_from_cloud(diseno.design_path, temp_download)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al descargar archivo: {str(e)}")
    
    preview_bytes = await asyncio.to_thread(generate_preview, temp_download)
    cache_file = set_cached_preview(pedido_id, "design", preview_bytes)
    os.remove(temp_download)
    
    # 4. Subir la previsualización a la nube en background y actualizar la DB
    preview_filename = f"cache_design_{pedido_id}.webp"
    if background_tasks:
        background_tasks.add_task(upload_preview_and_update_db, cache_file, preview_filename, db, diseno, "design")
    
    return StreamingResponse(io.BytesIO(preview_bytes), media_type="image/webp")

# Endpoint 5: Conversión para impresión (Fase 3)
@router.post("/convert/{pedido_id}", response_model=dict)
def convert_design(pedido_id: int, db: Session = Depends(get_db)):
    diseno = db.query(Diseno).filter(Diseno.pedido_id == pedido_id).first()
    if not diseno:
        raise HTTPException(status_code=404, detail="Diseño no encontrado para el pedido")
    
    # Conversión a JPEG optimizado (ejemplo)
    try:
        from PIL import Image
        import io
        # Se asume que la ruta de diseño es un archivo local o se debe descargar previamente;
        # aquí se simplifica la lógica usando directamente la ruta
        with Image.open(diseno.design_path) as img:
            output = io.BytesIO()
            img.save(output, format="JPEG", quality=90)
            converted_bytes = output.getvalue()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en conversión: {str(e)}")
    
    converted_filename = f"converted_{os.path.basename(diseno.design_path).split('.')[0]}.jpg"
    converted_path = os.path.join(UPLOAD_FOLDER, converted_filename)
    with open(converted_path, "wb") as f:
        f.write(converted_bytes)
    
    try:
        cloud_converted_path = upload_to_cloud(converted_path, converted_filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error subiendo archivo convertido a Yandex Disk: {str(e)}")
    
    diseno.converted_path = cloud_converted_path
    db.commit()
    
    return {"converted_path": cloud_converted_path, "estado": "convertido"}

# Endpoint 6: Consulta del estado del pedido (Historial y Seguimiento)
@router.get("/pedido/{pedido_id}", response_model=dict)
def get_pedido(pedido_id: int, db: Session = Depends(get_db)):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    diseno = db.query(Diseno).filter(Diseno.pedido_id == pedido_id).first()
    return {
        "pedido_id": pedido.id,
        "client_info": pedido.client_info,
        "fecha": pedido.fecha,
        "estado": pedido.estado,
        "original_path": pedido.original_path,
        "design": {
            "design_path": diseno.design_path if diseno else None,
            "converted_path": diseno.converted_path if diseno else None,
            "estado": diseno.estado if diseno else None,
        }
    }
