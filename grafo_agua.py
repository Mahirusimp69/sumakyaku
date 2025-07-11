import pandas as pd
import networkx as nx
from geopy.distance import geodesic
import logging
import os

def cargar_datos():
    try:
        data_dir = "data"
        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"Data directory '{data_dir}' not found")
        
        embalses = pd.read_csv('data/embalses.csv')
        puntos = pd.read_csv('data/puntos_criticos.csv')
        nodos = pd.read_csv('data/nodos.csv')
        aristas = pd.read_csv('data/aristas.csv')
        
        logging.info(f"Loaded data: {len(embalses)} reservoirs, {len(puntos)} critical points, {len(nodos)} nodes, {len(aristas)} edges")
        
        return embalses, puntos, nodos, aristas
        
    except FileNotFoundError as e:
        logging.error(f"Data file not found: {e}")
        raise
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        raise

def construir_grafo(embalses, puntos, nodos, aristas):
    G = nx.DiGraph()

    for _, e in embalses.iterrows():
        nombre = e.get('Nombre', e.get('nombre', f'Embalse_{_}'))
        latitud = e.get('Latitud', e.get('latitud', 0))
        longitud = e.get('Longitud', e.get('longitud', 0))
        capacidad = e.get('Volumen_Almacenado_m3', e.get('volumen_almacenado_m3', 1000000))
        
        G.add_node(
            nombre, 
            pos=(latitud, longitud), 
            tipo='embalse', 
            capacidad=capacidad,
            estado='transitable'
        )
        logging.debug(f"Added reservoir: {nombre}")
    
    for _, p in puntos.iterrows():
        nombre = p.get('Nombre', p.get('nombre', f'PC_{_}'))
        latitud = p.get('Latitud', p.get('latitud', 0))
        longitud = p.get('Longitud', p.get('longitud', 0))
        tipo = p.get('Tipo', p.get('tipo', 'critico'))
        
        G.add_node(
            nombre, 
            pos=(latitud, longitud), 
            tipo='punto_critico',
            subtipo=tipo,
            estado='obstaculo' 
        )
        logging.debug(f"Added critical point: {nombre}")
    
    for _, n in nodos.iterrows():
        G.add_node(
            n['id_nodo'], 
            pos=(n['latitud'], n['longitud']), 
            tipo=n['tipo'], 
            estado=n['estado']
        )
        logging.debug(f"Added node: {n['id_nodo']}")
        
    edges_added = 0
    for _, a in aristas.iterrows():
        if a['origen'] in G.nodes and a['destino'] in G.nodes:
            
            origen_estado = G.nodes[a['origen']].get('estado', 'transitable')
            destino_estado = G.nodes[a['destino']].get('estado', 'transitable')

            if (origen_estado == 'obstaculo' or destino_estado == 'obstaculo' or 
                a['estado'] == 'bloqueado'):
                logging.debug(f"Skipping edge {a['origen']} -> {a['destino']} (obstacle/blocked)")
                continue
            
            pos1 = G.nodes[a['origen']]['pos']
            pos2 = G.nodes[a['destino']]['pos']

            if 'distancia' in a and pd.notna(a['distancia']) and a['distancia'] > 0:
                dist = float(a['distancia'])
            else:
                dist = geodesic(pos1, pos2).kilometers

            color = 'blue'  
            capacidad = float(a.get('capacidad', 1000))
            
            G.add_edge(
                a['origen'], 
                a['destino'], 
                weight=dist, 
                estado=a['estado'], 
                color=color,
                capacidad=capacidad,
                distancia=dist
            )
            # Agregar arista inversa si no existe
            if not G.has_edge(a['destino'], a['origen']):
                G.add_edge(
                    a['destino'],
                    a['origen'],
                    weight=dist,
                    estado=a['estado'],
                    color=color,
                    capacidad=capacidad,
                    distancia=dist
                )
            edges_added += 1
            logging.debug(f"Added edge: {a['origen']} <-> {a['destino']} (distance: {dist:.2f}km)")
    
    logging.info(f"Graph constructed with {len(G.nodes)} nodes and {edges_added} edges")
    return G

def calcular_rutas_y_flujos(G, fuente):
    """Calculate optimal routes and maximum flows from source to distribution nodes."""
    rutas = {}
    flujos = {}

    # Definir límites aproximados de la ciudad de Arequipa
    LAT_MIN, LAT_MAX = -16.45, -16.30
    LON_MIN, LON_MAX = -71.60, -71.45

    def dentro_de_ciudad(pos):
        lat, lon = pos
        return LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX

    # Filtrar destinos solo dentro de la ciudad
    destinos = [
        n for n, d in G.nodes(data=True)
        if d.get("tipo") not in ["punto_critico", "embalse"]
        and d.get("estado") != "obstaculo"
        and dentro_de_ciudad(d.get("pos", (0, 0)))
    ]

    if not destinos:
        logging.warning("No accessible distribution nodes found for route calculation")
        return rutas, flujos, None

    destinos = destinos[:10]
    logging.info(f"Calculating routes from {fuente} to {len(destinos)} distribution nodes")

    G_transitable = G.copy()

    nodos_obstaculo = [n for n, d in G_transitable.nodes(data=True) 
                       if d.get("estado") == "obstaculo" or d.get("tipo") == "punto_critico"]
    G_transitable.remove_nodes_from(nodos_obstaculo)

    edges_to_remove = [(u, v) for u, v, d in G_transitable.edges(data=True) 
                      if d.get('estado') == 'bloqueado']
    G_transitable.remove_edges_from(edges_to_remove)

    for destino in destinos:
        try:
            if nx.has_path(G_transitable, fuente, destino):
                ruta = nx.dijkstra_path(G_transitable, fuente, destino, weight='weight')
                rutas[destino] = ruta
                logging.debug(f"Route to {destino}: {' -> '.join(ruta)}")
            else:
                rutas[destino] = None
                logging.warning(f"No path found from {fuente} to {destino}")
        except Exception as e:
            logging.error(f"Error calculating route to {destino}: {e}")
            rutas[destino] = None

        try:
            if nx.has_path(G_transitable, fuente, destino):
                flujo = nx.maximum_flow_value(G_transitable, fuente, destino, capacity='capacidad')
                flujos[destino] = round(flujo, 2)
                logging.debug(f"Max flow to {destino}: {flujo}")
            else:
                flujos[destino] = 0
        except Exception as e:
            logging.error(f"Error calculating flow to {destino}: {e}")
            flujos[destino] = 0

    # Seleccionar rutas conectadas entre nodos transitables más cercanos
    nodos_transitables = [n for n, d in G_transitable.nodes(data=True)
                         if d.get("estado") == "transitable" and dentro_de_ciudad(d.get("pos", (0, 0)))]
    rutas_destacadas = []
    usados = set()
    for origen in nodos_transitables:
        if origen in usados:
            continue
        pos_origen = G_transitable.nodes[origen]["pos"]
        # Buscar el nodo transitable más cercano que no haya sido usado y que esté conectado
        candidatos = [n for n in nodos_transitables if n != origen and n not in usados]
        candidatos = sorted(candidatos, key=lambda n: geodesic(pos_origen, G_transitable.nodes[n]["pos"]).meters)
        for destino in candidatos:
            try:
                if nx.has_path(G_transitable, origen, destino):
                    ruta = nx.dijkstra_path(G_transitable, origen, destino, weight='weight')
                    flujo = nx.maximum_flow_value(G_transitable, origen, destino, capacity='capacidad')
                    rutas_destacadas.append({
                        'inicio': origen,
                        'fin': destino,
                        'ruta': ruta,
                        'flujo_maximo': round(flujo, 2)
                    })
                    usados.add(origen)
                    usados.add(destino)
                    break  # Solo una ruta por origen
            except Exception as e:
                logging.error(f"Error calculating connected highlighted route {origen} -> {destino}: {e}")
                continue
        if len(rutas_destacadas) >= 5:
            break
    return rutas, flujos, rutas_destacadas

    # Rutas conectadas partiendo desde el embalse (fuente)
    rutas_destacadas = []
    usados = set([fuente])
    actual = fuente
    rutas_optimas_panel = {}
    for _ in range(3):  # Hasta 3 rutas conectadas
        pos_actual = G_transitable.nodes[actual]["pos"]
        candidatos = [n for n in nodos_transitables if n != actual and n not in usados]
        candidatos = sorted(candidatos, key=lambda n: geodesic(pos_actual, G_transitable.nodes[n]["pos"]).meters)
        encontrado = False
        for destino in candidatos:
            try:
                if nx.has_path(G_transitable, actual, destino):
                    ruta = nx.dijkstra_path(G_transitable, actual, destino, weight='weight')
                    flujo = nx.maximum_flow_value(G_transitable, actual, destino, capacity='capacidad')
                    rutas_destacadas.append({
                        'inicio': actual,
                        'fin': destino,
                        'ruta': ruta,
                        'flujo_maximo': round(flujo, 2)
                    })
                    usados.add(destino)
                    rutas_optimas_panel[destino] = ruta
                    actual = destino
                    encontrado = True
                    break
            except Exception as e:
                logging.error(f"Error calculating connected highlighted route {actual} -> {destino}: {e}")
                continue
        if not encontrado:
            break
    flujos_panel = {r['fin']: r['flujo_maximo'] for r in rutas_destacadas}
    return rutas_optimas_panel, flujos_panel, rutas_destacadas