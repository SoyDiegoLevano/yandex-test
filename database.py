# database.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.sql import func

from config import DB_URL

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Pedido(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True, index=True)
    client_info = Column(String, nullable=True)
    fecha = Column(DateTime, server_default=func.now())  # Se asigna la fecha automáticamente con func.now()
    estado = Column(String, default="nuevo")
    original_path = Column(String, nullable=False)  # Ruta remota en Yandex Disk
    original_cache_path = Column(String, nullable=True)  # URL de la previsualización en la nube (Yandex)
    original_cache_path_minio = Column(String, nullable=True) # Ruta de la previsualización en MinIO (opcional)
    original_cache_url_minio = Column(String, nullable=True) # URL de la previsualización en MinIO

    disenos = relationship("Diseno", back_populates="pedido")

class Diseno(Base):
    __tablename__ = "disenos"
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"))
    design_path = Column(String, nullable=False)  # Ruta del diseño final en Yandex Disk
    design_cache_path = Column(String, nullable=True)  # URL de la previsualización en la nube (Yandex)
    design_cache_path_minio = Column(String, nullable=True) # Ruta de la previsualización en MinIO (opcional)
    design_cache_url_minio = Column(String, nullable=True) # URL de la previsualización en MinIO
    converted_path = Column(String, nullable=True)  # Ruta del archivo convertido para impresión
    estado = Column(String, default="diseño completado")
    fecha = Column(DateTime, server_default=func.now())  # Se asigna la fecha automáticamente

    pedido = relationship("Pedido", back_populates="disenos")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()