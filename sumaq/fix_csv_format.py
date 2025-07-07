import pandas as pd

def fix_csv_formats():
    try:
        puntos = pd.read_csv('data/puntos_criticos.csv')
        puntos_fixed = puntos.rename(columns={
            'nombre': 'Nombre',
            'latitud': 'Latitud', 
            'longitud': 'Longitud',
            'tipo': 'Tipo',
            'prioridad': 'Prioridad',
            'poblacion_afectada': 'Poblacion_Afectada'
        })
        
        puntos_fixed.to_csv('data/puntos_criticos.csv', index=False)
        print(f"✓ Fixed puntos_criticos.csv: {len(puntos_fixed)} rows")
        
    except Exception as e:
        print(f"Error fixing puntos_criticos.csv: {e}")
    
    # Verificar que embalses.csv esté en el formato correcto
    try:
        embalses = pd.read_csv('data/embalses.csv')
        print(f"✓ embalses.csv format OK: {len(embalses)} rows")
        print(f"  Columns: {list(embalses.columns)}")
        
    except Exception as e:
        print(f"Error checking embalses.csv: {e}")
    
    # Verificar nodos.csv
    try:
        nodos = pd.read_csv('data/nodos.csv')
        print(f"✓ nodos.csv format OK: {len(nodos)} rows")
        print(f"  Columns: {list(nodos.columns)}")
        
    except Exception as e:
        print(f"Error checking nodos.csv: {e}")
    
    # Verificar aristas.csv
    try:
        aristas = pd.read_csv('data/aristas.csv')
        print(f"✓ aristas.csv format OK: {len(aristas)} rows")
        print(f"  Columns: {list(aristas.columns)}")
        
    except Exception as e:
        print(f"Error checking aristas.csv: {e}")

if __name__ == "__main__":
    fix_csv_formats()