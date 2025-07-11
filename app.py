import os
import logging
import json
import time
import pandas as pd
from flask import Flask, render_template, jsonify, request
from extensions import db  # Importa db desde extensions.py
from grafo_agua import cargar_datos, construir_grafo, calcular_rutas_y_flujos

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-for-water-system")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sumaq_yaku.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)

# Importa los modelos después de inicializar db
from models import Embalse, PuntoCritico, Nodo, Arista, Procesamiento, HistorialRuta

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    """Render the main interface for the water distribution system."""
    return render_template("index.html")

@app.route("/procesar", methods=["POST"])
def procesar():
    """Process water distribution data and calculate optimal routes and flows."""
    start_time = time.time()
    
    try:
        embalses, puntos, nodos, aristas = cargar_datos()
        
        G = construir_grafo(embalses, puntos, nodos, aristas)

        # Usar solo el primer embalse como fuente, como antes
        if len(embalses) > 0:
            fuente = embalses.iloc[0]['Nombre'] if 'Nombre' in embalses.columns else embalses.iloc[0]['nombre']
        else:
            return jsonify({"error": "No reservoirs found in data"}), 400

        rutas, flujos, rutas_destacadas = calcular_rutas_y_flujos(G, fuente)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        nodos_json = []
        for n, d in G.nodes(data=True):
            node_data = {"id": n}
            node_data.update(d)
            nodos_json.append(node_data)
        
        aristas_json = []
        for u, v, d in G.edges(data=True):
            edge_data = {"origen": u, "destino": v}
            edge_data.update(d)
            aristas_json.append(edge_data)

        total_rutas_calculadas = len([r for r in rutas.values() if r is not None])
        total_flujo_maximo = sum(flujos.values())

        try:
            procesamiento = Procesamiento(
                fuente_principal=fuente,
                total_rutas_calculadas=total_rutas_calculadas,
                total_flujo_maximo=total_flujo_maximo,
                tiempo_procesamiento_ms=processing_time_ms,
                estado='exitoso',
                detalles_json=json.dumps({
                    "rutas_optimas": rutas,
                    "flujos_maximos": flujos,
                    "nodos_count": len(nodos_json),
                    "aristas_count": len(aristas_json)
                })
            )
            db.session.add(procesamiento)
            db.session.commit()

            for destino, ruta in rutas.items():
                if ruta is not None:
                    distancia_total = 0
                    for i in range(len(ruta) - 1):
                        edge_data = G.get_edge_data(ruta[i], ruta[i+1])
                        if edge_data and 'distancia' in edge_data:
                            distancia_total += edge_data['distancia']
                    
                    historial_ruta = HistorialRuta(
                        procesamiento_id=procesamiento.id,
                        origen=fuente,
                        destino=destino,
                        ruta_json=json.dumps(ruta),
                        flujo_maximo=flujos.get(destino, 0),
                        distancia_total=distancia_total,
                        tiempo_estimado_h=distancia_total / 50.0 if distancia_total > 0 else 0  
                    )
                    db.session.add(historial_ruta)
            
            db.session.commit()
            logging.info(f"Processing results saved to database (ID: {procesamiento.id})")
            
        except Exception as db_error:
            logging.warning(f"Failed to save to database: {db_error}")
            db.session.rollback()
        
        # Solo mostrar en el panel los flujos de los destinos de rutas destacadas
        flujos_panel = {r['fin']: r['flujo_maximo'] for r in rutas_destacadas}
        rutas_panel = {r['fin']: r['ruta'] for r in rutas_destacadas}
        return jsonify({
            "rutas_optimas": rutas_panel,
            "flujos_maximos": flujos_panel,
            "nodos": nodos_json,
            "aristas": aristas_json,
            "fuente": fuente,
            "procesamiento_id": procesamiento.id if 'procesamiento' in locals() else None,
            "tiempo_procesamiento_ms": processing_time_ms,
            "rutas_destacadas": rutas_destacadas
        })
        
    except Exception as e:
        logging.error(f"Error processing water distribution data: {str(e)}")
        return jsonify({"error": f"Error processing data: {str(e)}"}), 500

@app.route("/status")
def status():
    """Check system status and data availability."""
    try:
        embalses, puntos, nodos, aristas = cargar_datos()

        db_status = "ok"
        db_counts = {}
        try:
            db_counts = {
                "procesamientos": Procesamiento.query.count(),
                "historial_rutas": HistorialRuta.query.count()
            }
        except Exception as db_error:
            db_status = f"Database error: {db_error}"
        
        return jsonify({
            "status": "ok",
            "data_summary": {
                "embalses": len(embalses),
                "puntos_criticos": len(puntos),
                "nodos": len(nodos),
                "aristas": len(aristas)
            },
            "database_status": db_status,
            "database_counts": db_counts
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/api/procesamientos")
def get_procesamientos():
    """Get all processing history records."""
    try:
        procesamientos = Procesamiento.query.order_by(Procesamiento.fecha_procesamiento.desc()).limit(10).all()
        return jsonify({
            "procesamientos": [p.to_dict() for p in procesamientos]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/procesamiento/<int:procesamiento_id>/rutas")
def get_rutas_procesamiento(procesamiento_id):
    """Get route details for a specific processing run."""
    try:
        procesamiento = Procesamiento.query.get_or_404(procesamiento_id)
        rutas = HistorialRuta.query.filter_by(procesamiento_id=procesamiento_id).all()
        
        return jsonify({
            "procesamiento": procesamiento.to_dict(),
            "rutas": [r.to_dict() for r in rutas]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/data/import", methods=["POST"])
def import_csv_to_db():
    """Import CSV data to database tables."""
    try:
        embalses, puntos, nodos, aristas = cargar_datos()

        for _, row in embalses.iterrows():
            embalse = Embalse.query.filter_by(nombre=row['Nombre']).first()
            if not embalse:
                embalse = Embalse(
                    nombre=row['Nombre'],
                    latitud=row['Latitud'],
                    longitud=row['Longitud'],
                    volumen_almacenado_m3=row['Volumen_Almacenado_m3']
                )
                db.session.add(embalse)
        
        for _, row in puntos.iterrows():
            punto = PuntoCritico.query.filter_by(nombre=row['Nombre']).first()
            if not punto:
                punto = PuntoCritico(
                    nombre=row['Nombre'],
                    latitud=row['Latitud'],
                    longitud=row['Longitud'],
                    tipo=row['Tipo']
                )
                db.session.add(punto)
                
        for _, row in nodos.iterrows():
            nodo = Nodo.query.filter_by(id_nodo=row['id_nodo']).first()
            if not nodo:
                nodo = Nodo(
                    id_nodo=row['id_nodo'],
                    latitud=row['latitud'],
                    longitud=row['longitud'],
                    tipo=row['tipo'],
                    estado=row['estado']
                )
                db.session.add(nodo)

        for _, row in aristas.iterrows():
            arista = Arista.query.filter_by(origen=row['origen'], destino=row['destino']).first()
            if not arista:
                arista = Arista(
                    origen=row['origen'],
                    destino=row['destino'],
                    distancia=row['distancia'],
                    estado=row['estado']
                )
                db.session.add(arista)
        
        db.session.commit()

        counts = {
            "embalses": Embalse.query.count(),
            "puntos_criticos": PuntoCritico.query.count(),
            "nodos": Nodo.query.count(),
            "aristas": Arista.query.count()
        }
        
        return jsonify({
            "status": "success",
            "message": "CSV data imported successfully",
            "counts": counts
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error importing CSV data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/agregar-nodo", methods=["POST"])
def agregar_nodo():
    """Agregar un nuevo nodo al archivo CSV."""
    try:
        data = request.get_json()
        
        required_fields = ['id_nodo', 'latitud', 'longitud', 'tipo', 'estado']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Campo requerido faltante: {field}"}), 400

        try:
            nodos_df = pd.read_csv('data/nodos.csv')
            if data['id_nodo'] in nodos_df['id_nodo'].values:
                return jsonify({"error": f"El ID {data['id_nodo']} ya existe"}), 400
        except FileNotFoundError:
            nodos_df = pd.DataFrame(columns=['id_nodo', 'latitud', 'longitud', 'tipo', 'estado'])

        nuevo_nodo = {
            'id_nodo': data['id_nodo'],
            'latitud': float(data['latitud']),
            'longitud': float(data['longitud']),
            'tipo': data['tipo'],
            'estado': data['estado']
        }

        nuevo_nodo_df = pd.DataFrame([nuevo_nodo])
        nodos_actualizado = pd.concat([nodos_df, nuevo_nodo_df], ignore_index=True)

        nodos_actualizado.to_csv('data/nodos.csv', index=False)
        
        logging.info(f"Nuevo nodo agregado: {data['id_nodo']} en ({data['latitud']}, {data['longitud']})")
        
        return jsonify({
            "status": "success",
            "message": f"Nodo {data['id_nodo']} agregado exitosamente",
            "nodo": nuevo_nodo
        })
        
    except Exception as e:
        logging.error(f"Error agregando nodo: {str(e)}")
        return jsonify({"error": f"Error agregando nodo: {str(e)}"}), 500

@app.route("/api/agregar-punto-critico", methods=["POST"])
def agregar_punto_critico():
    """Agregar un nuevo punto crítico al archivo CSV."""
    try:
        data = request.get_json()

        required_fields = ['nombre', 'latitud', 'longitud', 'tipo', 'prioridad']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Campo requerido faltante: {field}"}), 400

        try:
            puntos_df = pd.read_csv('data/puntos_criticos.csv')
            if data['nombre'] in puntos_df['nombre'].values:
                return jsonify({"error": f"El punto crítico {data['nombre']} ya existe"}), 400
        except FileNotFoundError:
            puntos_df = pd.DataFrame(columns=['nombre', 'latitud', 'longitud', 'tipo', 'prioridad', 'poblacion_afectada'])

        nuevo_punto = {
            'nombre': data['nombre'],
            'latitud': float(data['latitud']),
            'longitud': float(data['longitud']),
            'tipo': data['tipo'],
            'prioridad': data['prioridad'],
            'poblacion_afectada': int(data.get('poblacion_afectada', 0))
        }
        
        nuevo_punto_df = pd.DataFrame([nuevo_punto])
        puntos_actualizado = pd.concat([puntos_df, nuevo_punto_df], ignore_index=True)

        puntos_actualizado.to_csv('data/puntos_criticos.csv', index=False)
        
        logging.info(f"Nuevo punto crítico agregado: {data['nombre']} en ({data['latitud']}, {data['longitud']})")
        
        return jsonify({
            "status": "success",
            "message": f"Punto crítico {data['nombre']} agregado exitosamente",
            "punto_critico": nuevo_punto
        })
        
    except Exception as e:
        logging.error(f"Error agregando punto crítico: {str(e)}")
        return jsonify({"error": f"Error agregando punto crítico: {str(e)}"}), 500

@app.route("/generar-red-completa", methods=["POST"])
def generar_red_completa():
    """Genera una red completa de 100+ nodos de distribución para Arequipa"""
    try:
        import subprocess

        result = subprocess.run(
            ['python', 'generar_red_completa_arequipa.py'],
            capture_output=True,
            text=True,
            cwd='.'
        )
        
        if result.returncode == 0:
            try:
                nodos_df = pd.read_csv('data/nodos.csv')
                puntos_df = pd.read_csv('data/puntos_criticos.csv')
                aristas_df = pd.read_csv('data/aristas.csv')
                
                summary = f"{len(nodos_df)} nodos, {len(puntos_df)} obstáculos, {len(aristas_df)} conexiones"
                
                logging.info(f"Red completa generada: {summary}")
                
                return jsonify({
                    "status": "success",
                    "message": "Red completa generada exitosamente",
                    "summary": summary,
                    "details": {
                        "nodos": len(nodos_df),
                        "puntos_criticos": len(puntos_df),
                        "aristas": len(aristas_df)
                    }
                })
            except Exception as e:
                return jsonify({
                    "status": "success",
                    "message": "Red generada, pero error al contar resultados",
                    "summary": "Red completa generada",
                    "error": str(e)
                })
        else:
            logging.error(f"Error ejecutando generador: {result.stderr}")
            return jsonify({
                "error": f"Error generando red: {result.stderr}"
            }), 500
            
    except Exception as e:
        logging.error(f"Error generando red completa: {str(e)}")
        return jsonify({"error": f"Error generando red completa: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)

