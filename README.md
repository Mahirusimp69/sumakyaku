# 🌊 Sumakyaku - Sistema de Optimización de Redes de Distribución de Agua

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Descripción

**Sumakyaku** es un sistema inteligente de gestión y optimización de redes de distribución de agua que utiliza algoritmos de grafos y análisis de flujo máximo para optimizar la distribución de agua desde embalses hasta puntos de consumo. El sistema proporciona una interfaz web interactiva con visualización en tiempo real de la red de distribución.

## ✨ Características Principales

### 🗺️ Visualización Interactiva en Mapa
- **Mapa interactivo** con Leaflet.js que muestra toda la red de distribución
- **Visualización de elementos:**
  - 🏛️ Embalses (fuentes de agua)
  - 🔵 Nodos de distribución (cuadras, tubos, bombas, válvulas)
  - ⚠️ Puntos críticos (obstáculos, inundaciones, deslizamientos)
  - 🔗 Conexiones y rutas optimizadas
- **Información detallada** al hacer clic en cada elemento
- **Actualización en tiempo real** del estado de la red

### ⚙️ Panel de Control Dinámico
- **Estado del sistema** en tiempo real
- **Procesamiento de datos** con optimización automática de rutas
- **Agregar nuevos nodos** a la red con especificaciones completas
- **Registrar puntos críticos** con prioridad y población afectada
- **Resultados detallados** de flujos máximos y rutas activas

### 🧠 Algoritmos de Optimización
- **Cálculo de rutas óptimas** usando algoritmos de grafos
- **Análisis de flujo máximo** para optimizar la distribución
- **Detección de obstáculos** y reconfiguración automática de rutas
- **Priorización inteligente** basada en población afectada

## 🚀 Instalación

### Prerrequisitos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clona el repositorio**
   ```bash
   git clone https://github.com/Mahirusimp69/sumakyaku.git
   cd sumakyaku
   ```

2. **Crea un entorno virtual (recomendado)**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   

3. **Instala las dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecuta la aplicación**
   ```bash
   python app.py
   ```

5. **Abre tu navegador**
   Navega a `http://localhost:5000`

## 📁 Estructura del Proyecto

```
sumakyaku/
├── 📁 data/                    # Datos de la red de distribución
│   ├── embalses.csv           # Información de embalses
│   ├── nodos.csv              # Nodos de la red
│   ├── aristas.csv            # Conexiones entre nodos
│   └── puntos_criticos.csv    # Puntos críticos/obstáculos
├── 📁 static/                  # Archivos estáticos
│   ├── mapa.js                # Lógica de visualización del mapa
│   └── style.css              # Estilos de la interfaz
├── 📁 templates/               # Plantillas HTML
│   └── index.html             # Interfaz principal
├── 📁 instance/                # Base de datos SQLite
├── app.py                     # Aplicación principal Flask
├── main.py                    # Punto de entrada
├── models.py                  # Modelos de base de datos
├── extensions.py              # Configuración de extensiones
├── grafo_agua.py              # Algoritmos de optimización
├── requirements.txt           # Dependencias del proyecto
└── README.md                  # Este archivo
```

## 🎯 Uso del Sistema

### 1. **Verificar Estado del Sistema**
- Al cargar la aplicación, el sistema muestra automáticamente el estado actual
- Información sobre embalses, nodos, puntos críticos y conexiones

### 2. **Procesar Datos**
- Haz clic en **"Procesar Datos"** para ejecutar la optimización
- El sistema calculará rutas óptimas y flujos máximos
- Los resultados se mostrarán en el panel lateral

### 3. **Agregar Nuevos Nodos**
- Completa el formulario en el panel de control
- Especifica ID, coordenadas, tipo y estado del nodo
- Haz clic en **"Agregar Nodo"** para incluirlo en la red

### 4. **Registrar Puntos Críticos**
- Usa el formulario de puntos críticos para marcar obstáculos
- Especifica tipo, prioridad y población afectada
- Los puntos críticos se mostrarán en el mapa como advertencias

### 5. **Visualizar Resultados**
- Los flujos máximos se muestran ordenados por capacidad
- El resumen incluye rutas activas y flujo total
- Las rutas se visualizan en el mapa con diferentes colores

## 🔧 Tecnologías Utilizadas

### Backend
- **Flask**: Framework web para Python
- **SQLAlchemy**: ORM para gestión de base de datos
- **NetworkX**: Biblioteca para análisis de grafos
- **Pandas**: Manipulación y análisis de datos

### Frontend
- **Leaflet.js**: Biblioteca de mapas interactivos
- **Bootstrap 5**: Framework CSS para diseño responsivo
- **Font Awesome**: Iconografía
- **JavaScript ES6+**: Lógica del lado del cliente

### Base de Datos
- **SQLite**: Base de datos ligera y portable

## 📊 Características Técnicas

- **Arquitectura**: Modelo-Vista-Controlador (MVC)
- **API RESTful**: Endpoints para procesamiento y gestión de datos
- **Visualización en tiempo real**: Actualización dinámica del mapa
- **Responsive Design**: Interfaz adaptable a diferentes dispositivos
- **Optimización de rendimiento**: Cálculos eficientes de rutas y flujos


## 👥 Autores

- **Equipo Sumakyaku** - *Desarrollo inicial* - 
