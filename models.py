from sqlalchemy.sql import func
from datetime import datetime
from extensions import db  # Importa db desde extensions.py

# Define los modelos aquí, fuera de cualquier función
class Embalse(db.Model):
    __tablename__ = 'embalses'
        
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    latitud = db.Column(db.Float, nullable=False)
    longitud = db.Column(db.Float, nullable=False)
    volumen_almacenado_m3 = db.Column(db.BigInteger, nullable=False)
    capacidad_maxima_m3 = db.Column(db.BigInteger, nullable=True)
    estado = db.Column(db.String(20), default='operativo')
    fecha_creacion = db.Column(db.DateTime, default=func.now())
    fecha_actualizacion = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
        
    def to_dict(self):
        return {
            'id': self.id,
            'Nombre': self.nombre,
            'Latitud': self.latitud,
            'Longitud': self.longitud,
            'Volumen_Almacenado_m3': self.volumen_almacenado_m3,
            'capacidad_maxima_m3': self.capacidad_maxima_m3,
            'estado': self.estado
        }

class PuntoCritico(db.Model):
    __tablename__ = 'puntos_criticos'
        
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    latitud = db.Column(db.Float, nullable=False)
    longitud = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    prioridad = db.Column(db.String(20), default='media') 
    poblacion_afectada = db.Column(db.Integer, nullable=True)
    estado = db.Column(db.String(20), default='activo')
    fecha_creacion = db.Column(db.DateTime, default=func.now())
    fecha_actualizacion = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
        
    def to_dict(self):
        return {
            'id': self.id,
            'Nombre': self.nombre,
            'Latitud': self.latitud,
            'Longitud': self.longitud,
            'Tipo': self.tipo,
            'prioridad': self.prioridad,
            'poblacion_afectada': self.poblacion_afectada,
            'estado': self.estado
        }

class Nodo(db.Model):
    __tablename__ = 'nodos'
        
    id = db.Column(db.Integer, primary_key=True)
    id_nodo = db.Column(db.String(20), nullable=False, unique=True)
    latitud = db.Column(db.Float, nullable=False)
    longitud = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # tubo, cuadra, bomba, etc.
    estado = db.Column(db.String(20), default='transitable')  # transitable, obstaculo, mantenimiento
    capacidad = db.Column(db.Float, nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=func.now())
    fecha_actualizacion = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
        
    def to_dict(self):
        return {
            'id': self.id,
            'id_nodo': self.id_nodo,
            'latitud': self.latitud,
            'longitud': self.longitud,
            'tipo': self.tipo,
            'estado': self.estado,
            'capacidad': self.capacidad
        }

class Arista(db.Model):
    __tablename__ = 'aristas'
        
    id = db.Column(db.Integer, primary_key=True)
    origen = db.Column(db.String(100), nullable=False)
    destino = db.Column(db.String(100), nullable=False)
    distancia = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), default='transitable')  # transitable, bloqueado, mantenimiento
    capacidad = db.Column(db.Float, default=1000.0)
    tipo_tuberia = db.Column(db.String(50), nullable=True)
    diametro_mm = db.Column(db.Float, nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=func.now())
    fecha_actualizacion = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
        
    def to_dict(self):
        return {
            'id': self.id,
            'origen': self.origen,
            'destino': self.destino,
            'distancia': self.distancia,
            'estado': self.estado,
            'capacidad': self.capacidad,
            'tipo_tuberia': self.tipo_tuberia,
            'diametro_mm': self.diametro_mm
        }

class Procesamiento(db.Model):
    __tablename__ = 'procesamientos'
        
    id = db.Column(db.Integer, primary_key=True)
    fecha_procesamiento = db.Column(db.DateTime, default=func.now())
    fuente_principal = db.Column(db.String(100), nullable=False)
    total_rutas_calculadas = db.Column(db.Integer, nullable=False)
    total_flujo_maximo = db.Column(db.Float, nullable=False)
    tiempo_procesamiento_ms = db.Column(db.Integer, nullable=True)
    estado = db.Column(db.String(20), default='exitoso')
    detalles_json = db.Column(db.Text, nullable=True) 
        
    def to_dict(self):
        return {
            'id': self.id,
            'fecha_procesamiento': self.fecha_procesamiento.isoformat() if self.fecha_procesamiento else None,
            'fuente_principal': self.fuente_principal,
            'total_rutas_calculadas': self.total_rutas_calculadas,
            'total_flujo_maximo': self.total_flujo_maximo,
            'tiempo_procesamiento_ms': self.tiempo_procesamiento_ms,
            'estado': self.estado
        }

class HistorialRuta(db.Model):
    __tablename__ = 'historial_rutas'
        
    id = db.Column(db.Integer, primary_key=True)
    procesamiento_id = db.Column(db.Integer, db.ForeignKey('procesamientos.id'), nullable=False)
    origen = db.Column(db.String(100), nullable=False)
    destino = db.Column(db.String(100), nullable=False)
    ruta_json = db.Column(db.Text, nullable=True) 
    flujo_maximo = db.Column(db.Float, nullable=False, default=0.0)
    distancia_total = db.Column(db.Float, nullable=True)
    tiempo_estimado_h = db.Column(db.Float, nullable=True)

    procesamiento = db.relationship('Procesamiento', backref=db.backref('rutas', lazy=True))
        
    def to_dict(self):
        return {
            'id': self.id,
            'procesamiento_id': self.procesamiento_id,
            'origen': self.origen,
            'destino': self.destino,
            'ruta_json': self.ruta_json,
            'flujo_maximo': self.flujo_maximo,
            'distancia_total': self.distancia_total,
            'tiempo_estimado_h': self.tiempo_estimado_h
        }