import pandas as pd
import numpy as np
import random
from geopy.distance import geodesic

def generar_coordenadas_arequipa():
    """Genera coordenadas dentro del área urbana de Arequipa"""
    lat_min, lat_max = -16.45, -16.35
    lng_min, lng_max = -71.60, -71.50
    return random.uniform(lat_min, lat_max), random.uniform(lng_min, lng_max)

def calcular_distancia(coord1, coord2):
    """Calcula distancia en km entre dos coordenadas"""
    return geodesic(coord1, coord2).kilometers

def generar_nodos_distribucion(num_nodos=500):
    """Genera nodos de distribución de agua por toda Arequipa"""
    nodos = []
    tipos_distribucion = ['tubo', 'bomba', 'valvula']
    estados = ['transitable', 'transitable', 'transitable', 'obstaculo'] 

    for i in range(1, num_nodos + 1):
        lat, lng = generar_coordenadas_arequipa()
        nodo = {
            'id_nodo': f'D{i:04d}', 
            'latitud': round(lat, 6),
            'longitud': round(lng, 6),
            'tipo': random.choice(tipos_distribucion),
            'estado': random.choice(estados)
        }
        nodos.append(nodo)

    return nodos

def generar_puntos_criticos_obstaculos(num_puntos=250):
    """Genera puntos críticos que actúan como obstáculos donde NO puede pasar el agua"""
    puntos = []
    tipos_obstaculo = ['inundacion', 'deslizamiento', 'hundimiento', 'obra', 'contaminacion']
    prioridades = ['alta', 'media', 'baja']

    for i in range(1, num_puntos + 1):
        lat, lng = generar_coordenadas_arequipa()
        punto = {
            'nombre': f'PC_{i:04d}',
            'latitud': round(lat, 6),
            'longitud': round(lng, 6),
            'tipo': random.choice(tipos_obstaculo),
            'prioridad': random.choice(prioridades),
            'poblacion_afectada': random.randint(100, 5000)
        }
        puntos.append(punto)

    return puntos

def generar_aristas_red(nodos_existentes, nodos_nuevos, puntos_criticos):
    """Genera aristas conectando toda la red, evitando puntos críticos"""
    aristas = []
    todos_nodos = nodos_existentes + nodos_nuevos

    coords_nodos = {
        nodo['id_nodo']: (nodo['latitud'], nodo['longitud']) for nodo in todos_nodos
    }

    embalses = [
        {'id': 'Embalse_Chilina', 'coords': (-16.3969, -71.5375)},
        {'id': 'Embalse_Aguada_Blanca', 'coords': (-16.4091, -71.5875)},
        {'id': 'Embalse_Aguada_Pillones', 'coords': (-16.3969, -71.5175)},
        {'id': 'Embalse_Aguada_Chalhuanca', 'coords': (-16.4291, -71.5275)},
        {'id': 'Embalse_El_Frayle', 'coords': (-16.4191, -71.5675)}
    ]

    for embalse in embalses:
        coords_nodos[embalse['id']] = embalse['coords']

    for nodo in todos_nodos:
        if nodo['estado'] == 'obstaculo':
            continue

        nodo_coords = (nodo['latitud'], nodo['longitud'])
        nodo_id = nodo['id_nodo']

        distancias = [
            (otro_id, calcular_distancia(nodo_coords, otras_coords))
            for otro_id, otras_coords in coords_nodos.items()
            if otro_id != nodo_id and calcular_distancia(nodo_coords, otras_coords) < 5.0
        ]

        distancias.sort(key=lambda x: x[1])
        num_conexiones = min(random.randint(3, 5), len(distancias))

        for i in range(num_conexiones):
            destino_id, distancia = distancias[i]

            if destino_id in [n['id_nodo'] for n in todos_nodos if n['estado'] == 'obstaculo']:
                continue

            pasa_por_critico = any(
                min(calcular_distancia(nodo_coords, (pc['latitud'], pc['longitud'])),
                    calcular_distancia(coords_nodos[destino_id], (pc['latitud'], pc['longitud']))) < 0.5
                for pc in puntos_criticos
            )

            if pasa_por_critico:
                continue

            estado_arista = 'transitable'
            capacidad = 1000

            if random.random() < 0.1:
                estado_arista = 'bloqueado'
                capacidad = 0

            aristas.append({
                'origen': nodo_id,
                'destino': destino_id,
                'distancia': round(distancia, 2),
                'estado': estado_arista,
                'capacidad': capacidad
            })

    return aristas

def main():
    print("🚰 Generando red de distribución de agua para Arequipa...")

    try:
        nodos_existentes = pd.read_csv('data/nodos.csv').to_dict('records')
        print(f"✓ Cargados {len(nodos_existentes)} nodos existentes")
    except FileNotFoundError:
        nodos_existentes = []
        print("✓ No hay nodos existentes, se empezará desde cero")

    print("📍 Generando 500 nodos de distribución nuevos...")
    nodos_nuevos = generar_nodos_distribucion(500)

    print("⚠️ Generando 250 puntos críticos...")
    puntos_criticos = generar_puntos_criticos_obstaculos(250)

    print("🔗 Generando conexiones (aristas)...")
    aristas = generar_aristas_red(nodos_existentes, nodos_nuevos, puntos_criticos)

    print("💾 Guardando archivos CSV...")
    pd.DataFrame(nodos_existentes + nodos_nuevos).to_csv('data/nodos.csv', index=False)
    pd.DataFrame(puntos_criticos).to_csv('data/puntos_criticos.csv', index=False)
    pd.DataFrame(aristas).to_csv('data/aristas.csv', index=False)

    print("\n🎉 ¡Red generada exitosamente!")
    print(f"📊 Total nodos: {len(nodos_existentes + nodos_nuevos)}")
    print(f"📊 Puntos críticos: {len(puntos_criticos)}")
    print(f"📊 Aristas generadas: {len(aristas)}")

if __name__ == "__main__":
    main()
