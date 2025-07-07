import osmnx as ox
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)

def generar_red_arequipa():
    """Generate road network data for Arequipa, Peru."""
    try:
        place_name = "Arequipa, Peru"
        logging.info(f"Downloading road network data for {place_name}")

        G = ox.graph_from_place(place_name, network_type='drive')
        G = ox.simplify_graph(G)
        
        logging.info(f"Downloaded network with {len(G.nodes)} nodes and {len(G.edges)} edges")

        nodos = []
        aristas = []

        id_map = {}
        for i, (node, data) in enumerate(G.nodes(data=True)):
            node_id = f"N{i+1:05}"
            id_map[node] = node_id
            nodos.append({
                "id_nodo": node_id,
                "latitud": data['y'],
                "longitud": data['x'],
                "tipo": "tubo",
                "estado": "transitable"
            })
        
        for u, v, data in G.edges(data=True):
            aristas.append({
                "origen": id_map[u],
                "destino": id_map[v],
                "distancia": round(data.get('length', 0), 2),
                "estado": "transitable"
            })

        nodos_df = pd.DataFrame(nodos)
        aristas_df = pd.DataFrame(aristas)
        
        nodos_df.to_csv("data/nodos_arequipa.csv", index=False)
        aristas_df.to_csv("data/aristas_arequipa.csv", index=False)
        
        logging.info("✅ Nodes and edges generated successfully.")
        logging.info(f"Generated {len(nodos)} nodes and {len(aristas)} edges")
        
        return nodos_df, aristas_df
        
    except Exception as e:
        logging.error(f"Error generating network data: {e}")
        raise

if __name__ == "__main__":
    generar_red_arequipa()
