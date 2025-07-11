let map;
let markersLayer;
let routesLayer;
let connectionLayer;
let loadingModal;

document.addEventListener('DOMContentLoaded', function() {
    initializeMap();
    initializeComponents();
    verificarEstado();
    inicializarFormularioNodo();
    inicializarFormularioPuntoCritico();
});
function formatNumber(num) {
    return num.toLocaleString('es-PE');
}

function initializeMap() {
    map = L.map('map').setView([-16.4090, -71.5375], 12);

    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    markersLayer = L.layerGroup().addTo(map);
    connectionLayer = L.layerGroup().addTo(map);
    routesLayer = L.layerGroup().addTo(map);

    map.whenReady(function() {
        document.getElementById('map-loading').style.display = 'none';
    });
    
    console.log('Map initialized successfully');
}

function initializeComponents() {
    loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'), {
        keyboard: false,
        backdrop: 'static'
    });
}

function verificarEstado() {
    const estadoElement = document.getElementById('estado-sistema');
    
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                estadoElement.innerHTML = `
                    <span class="badge bg-success">Sistema Operativo</span>
                    <div class="mt-2 small">
                        <div>🏛️ Embalses: ${data.data_summary.embalses}</div>
                        <div>⚠️ Puntos Críticos: ${data.data_summary.puntos_criticos}</div>
                        <div>🔵 Nodos: ${data.data_summary.nodos}</div>
                        <div>🔗 Conexiones: ${data.data_summary.aristas}</div>
                    </div>
                `;
            } else {
                estadoElement.innerHTML = `
                    <span class="badge bg-danger">Error del Sistema</span>
                    <div class="mt-2 small text-danger">${data.message}</div>
                `;
            }
        })
        .catch(error => {
            console.error('Error checking system status:', error);
            estadoElement.innerHTML = `
                <span class="badge bg-warning">Estado Desconocido</span>
                <div class="mt-2 small text-warning">No se pudo verificar el estado</div>
            `;
        });
}

function procesar() {
    const btnProcesar = document.getElementById('btn-procesar');
    const resultadosDiv = document.getElementById('resultados');

    btnProcesar.classList.add('btn-loading');
    btnProcesar.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Procesando...';
    loadingModal.show();

    markersLayer.clearLayers();
    routesLayer.clearLayers();
    resultadosDiv.innerHTML = '<p class="text-muted small">Procesando datos...</p>';
    
    fetch('/procesar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Processing successful:', data);
        
        if (data.error) {
            throw new Error(data.error);
        }

        // Limpiar el panel de resultados antes de mostrar los nuevos
        const resultadosDiv = document.getElementById('resultados');
        resultadosDiv.innerHTML = '';

        visualizarNodos(data.nodos);

        visualizarAristas(data.nodos, data.aristas);

        // Filtrar flujos para que el panel muestre todos los nodos relevantes de las rutas rojas activas (no solo el destino final)
        let flujosRutasRojas = {};
        let nodosIncluidos = new Set();
        if (data.rutas_destacadas && typeof data.rutas_destacadas === 'object' && !Array.isArray(data.rutas_destacadas)) {
            // Si rutas_destacadas es un objeto (diccionario de rutas)
            for (const destino in data.rutas_destacadas) {
                const ruta = data.rutas_destacadas[destino];
                if (Array.isArray(ruta)) {
                    ruta.forEach(nodo => {
                        if (data.flujos_maximos[nodo] > 0 && !nodosIncluidos.has(nodo)) {
                            flujosRutasRojas[nodo] = data.flujos_maximos[nodo];
                            nodosIncluidos.add(nodo);
                        }
                    });
                }
            }
        } else if (Array.isArray(data.rutas_destacadas)) {
            // Si rutas_destacadas es un array de objetos {inicio, fin, ruta, flujo_maximo}
            data.rutas_destacadas.forEach(rutaObj => {
                if (rutaObj && Array.isArray(rutaObj.ruta)) {
                    rutaObj.ruta.forEach(nodo => {
                        if (data.flujos_maximos[nodo] > 0 && !nodosIncluidos.has(nodo)) {
                            flujosRutasRojas[nodo] = data.flujos_maximos[nodo];
                            nodosIncluidos.add(nodo);
                        }
                    });
                }
            });
        }
        // Si no hay rutas activas, mostrar mensaje claro en el panel
        if (Object.keys(flujosRutasRojas).length === 0) {
            const resultadosDiv = document.getElementById('resultados');
            resultadosDiv.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    No hay rutas activas para mostrar.
                </div>
            `;
        } else {
            mostrarResultados(data.rutas_destacadas, flujosRutasRojas, data.fuente);
        }

        // Pintar todas las rutas destacadas si existen
        if (data.rutas_destacadas && Array.isArray(data.rutas_destacadas)) {
            const nodos = obtenerCoordenadasNodos();
            data.rutas_destacadas.forEach(rutaObj => {
                if (rutaObj && Array.isArray(rutaObj.ruta) && rutaObj.ruta.length > 1) {
                    const coords = rutaObj.ruta.map(nodo => nodos[nodo] ? [nodos[nodo].lat, nodos[nodo].lng] : null).filter(Boolean);
                    if (coords.length > 1) {
                        L.polyline(coords, {
                            color: '#FF0000',
                            weight: 8,
                            opacity: 1,
                            dashArray: null
                        }).addTo(routesLayer).bindPopup(
                            `<b>Ruta óptima ${rutaObj.inicio} → ${rutaObj.fin}</b><br>` +
                            (rutaObj.flujo_maximo !== undefined ? `<b>Flujo máximo:</b> ${formatNumber(rutaObj.flujo_maximo)} unidades/h` : '')
                        );
                    }
                }
            });
        }

        loadingModal.hide();
    })
    .catch(error => {
        console.error('Error processing data:', error);
        
        resultadosDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Error:</strong> ${error.message}
            </div>
        `;
        
        loadingModal.hide();
    })
    .finally(() => {
        btnProcesar.classList.remove('btn-loading');
        btnProcesar.innerHTML = '<i class="fas fa-play me-1"></i>Procesar Datos';
    });
}

function visualizarNodos(nodos) {
    nodos.forEach(nodo => {
        const pos = nodo.pos || [nodo.latitud, nodo.longitud];

        let color, icon, className;
        
        switch(nodo.tipo) {
            case 'embalse':
                color = '#198754';
                icon = '🏛️';
                className = 'marker-embalse';
                break;
            case 'punto_critico':
                color = '#fd7e14'; 
                icon = '⚠️';
                className = 'marker-critico';
                break;
            default:
                if (nodo.estado === 'obstaculo' || nodo.estado === 'bloqueado') {
                    color = '#dc3545';
                    icon = '🚫';
                    className = 'marker-obstaculo';
                } else {
                    color = '#0dcaf0'; 
                    icon = '🔵';
                    className = 'marker-normal';
                }
        }

        const marker = L.circleMarker([pos[0], pos[1]], {
            radius: nodo.tipo === 'embalse' ? 10 : 6,
            color: color,
            fillColor: color,
            fillOpacity: 0.8,
            weight: 2,
            className: className,
            title: nodo.id,
            nodeId: nodo.id
        });

        let popupContent = `
            <div class="p-2">
                <h6 class="mb-2">${icon} ${nodo.id}</h6>
                <div class="small">
                    <div><strong>Tipo:</strong> ${nodo.tipo}</div>
                    <div><strong>Estado:</strong> ${nodo.estado || 'transitable'}</div>
        `;
        
        if (nodo.capacidad) {
            popupContent += `<div><strong>Capacidad:</strong> ${nodo.capacidad.toLocaleString()} m³</div>`;
        }
        
        if (nodo.subtipo) {
            popupContent += `<div><strong>Subtipo:</strong> ${nodo.subtipo}</div>`;
        }
        
        popupContent += `
                    <div><strong>Coordenadas:</strong> ${pos[0].toFixed(4)}, ${pos[1].toFixed(4)}</div>
                </div>
            </div>
        `;
        
        marker.bindPopup(popupContent);
        markersLayer.addLayer(marker);
    });
    
    console.log(`Visualized ${nodos.length} nodes on the map`);
}

function visualizarAristas(nodos, aristas) {
    // Limpiar conexiones anteriores
    connectionLayer.clearLayers();
    
    aristas.forEach(arista => {
        const nodoOrigen = nodos.find(n => n.id === arista.origen);
        const nodoDestino = nodos.find(n => n.id === arista.destino);
        
        if (nodoOrigen && nodoDestino) {
            const posOrigen = nodoOrigen.pos || [nodoOrigen.latitud, nodoOrigen.longitud];
            const posDestino = nodoDestino.pos || [nodoDestino.latitud, nodoDestino.longitud];
            
            const color = arista.estado === 'bloqueado' ? '#dc3545' : '#6c757d';
            const weight = arista.estado === 'bloqueado' ? 3 : 2;
            const opacity = arista.estado === 'bloqueado' ? 0.8 : 0.5;
            
            const polyline = L.polyline([posOrigen, posDestino], {
                color: color,
                weight: weight,
                opacity: opacity,
                dashArray: arista.estado === 'bloqueado' ? '10, 5' : null
            });

            const popupContent = `
                <div class="p-2">
                    <h6 class="mb-2">🔗 Conexión</h6>
                    <div class="small">
                        <div><strong>Origen:</strong> ${arista.origen}</div>
                        <div><strong>Destino:</strong> ${arista.destino}</div>
                        <div><strong>Distancia:</strong> ${arista.distancia?.toFixed(2) || 'N/A'} km</div>
                        <div><strong>Estado:</strong> ${arista.estado}</div>
                        <div><strong>Capacidad:</strong> ${arista.capacidad || 'N/A'}</div>
                    </div>
                </div>
            `;
            
            polyline.bindPopup(popupContent);
            connectionLayer.addLayer(polyline);
        }
    });
    
    console.log(`Visualized ${aristas.length} connections on the map`);
}
function mostrarResultados(rutas, flujos, fuente) {
    const resultadosDiv = document.getElementById('resultados');
    let html = `
        <div class="alert alert-success">
            <i class="fas fa-check-circle me-2"></i>
            Procesamiento completado desde <strong>${fuente}</strong>
        </div>
        <h5 class="mt-4 mb-3"><i class="fas fa-tint me-2"></i>Flujos Máximos</h5>
        <div class="row">
    `;

    // Solo mostrar los flujos de los destinos de rutas rojas
    Object.entries(flujos).forEach(([destino, flujo], index) => {
        if (index % 2 === 0) html += '<div class="col-md-6">';
        html += `
            <div class="mb-3 p-2 border rounded">
                <span class="badge bg-primary">${destino}</span>
                <span class="float-end">${formatNumber(flujo)} L/h</span>
            </div>
        `;
        if (index % 2 !== 0 || index === Object.entries(flujos).length - 1) html += '</div>';
    });

    html += `</div>`;

    // Calcula rutas activas y flujo total SOLO con los flujos actuales
    const rutasActivas = Object.values(flujos).filter(f => f > 0).length;
    const totalDestinos = Object.keys(flujos).length;
    const flujoTotal = Object.values(flujos).reduce((a, b) => a + b, 0);

    html += `
        <div class="card mt-4">
            <div class="card-header bg-primary text-white">
                <i class="fas fa-chart-bar me-2"></i>Resumen
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-6">
                        <div class="text-center">
                            <div class="h4">${rutasActivas}/${totalDestinos}</div>
                            <small class="text-muted">Rutas activas</small>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="text-center">
                            <div class="h4">${formatNumber(flujoTotal)}</div>
                            <small class="text-muted">Flujo total (L/h)</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    resultadosDiv.innerHTML = html;
}

function visualizarRutasEnMapa(rutas, flujos) {

    routesLayer.clearLayers();

    const nodos = obtenerCoordenadasNodos();
    
    for (const [destino, ruta] of Object.entries(rutas)) {
        if (ruta && ruta.length > 1) {
            const flujo = flujos[destino] || 0;
            // Rojo para rutas activas, gris para inactivas
            const color = flujo > 0 ? '#FF0000' : '#6c757d';

            const coordenadas = [];
            for (const nodo of ruta) {
                if (nodos[nodo]) {
                    coordenadas.push([nodos[nodo].lat, nodos[nodo].lng]);
                }
            }
            
            if (coordenadas.length > 1) {
                const polyline = L.polyline(coordenadas, {
                    color: color,
                    weight: Math.max(3, Math.min(8, flujo / 200)), 
                    opacity: 0.8,
                    dashArray: flujo === 0 ? '5, 5' : null 
                }).addTo(routesLayer);
                
                polyline.bindPopup(`
                    <div class="route-popup">
                        <h6 class="mb-2">${destino}</h6>
                        <p class="small mb-1"><strong>Ruta:</strong> ${ruta.join(' → ')}</p>
                        <p class="small mb-0"><strong>Flujo máximo:</strong> ${formatNumber(flujo)} unidades/h</p>
                    </div>
                `);
            }
        }
    }
}

function obtenerCoordenadasNodos() {
    const nodos = {};

    markersLayer.eachLayer(function(layer) {
        if (layer.options && layer.options.nodeId) {
            const nombre = layer.options.nodeId;
            nodos[nombre] = {
                lat: layer.getLatLng().lat,
                lng: layer.getLatLng().lng
            };
        } else if (layer.options && layer.options.title) {
            const nombre = layer.options.title;
            nodos[nombre] = {
                lat: layer.getLatLng().lat,
                lng: layer.getLatLng().lng
            };
        } else if (layer._popup && layer._popup._content) {
            const content = layer._popup._content;
            const match = content.match(/<h6[^>]*>([^<]+)<\/h6>/);
            if (match) {
                const nombre = match[1].replace(/[🏛️⚠️🔵🚫]/g, '').trim();
                nodos[nombre] = {
                    lat: layer.getLatLng().lat,
                    lng: layer.getLatLng().lng
                };
            }
        }
    });
    
    return nodos;
}

function inicializarFormularioNodo() {
    const form = document.getElementById('form-agregar-nodo');
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const nuevoNodo = {
            id_nodo: document.getElementById('nuevo-id-nodo').value,
            latitud: parseFloat(document.getElementById('nueva-latitud').value),
            longitud: parseFloat(document.getElementById('nueva-longitud').value),
            tipo: document.getElementById('nuevo-tipo').value,
            estado: document.getElementById('nuevo-estado').value
        };
        
        agregarNodo(nuevoNodo);
    });

    map.on('click', function(e) {
        document.getElementById('nueva-latitud').value = e.latlng.lat.toFixed(4);
        document.getElementById('nueva-longitud').value = e.latlng.lng.toFixed(4);

        const marker = L.marker([e.latlng.lat, e.latlng.lng])
            .addTo(map)
            .bindPopup('📍 Coordenadas copiadas al formulario')
            .openPopup();

        setTimeout(() => {
            map.removeLayer(marker);
        }, 2000);
    });
}

function agregarNodo(nuevoNodo) {
    fetch('/api/agregar-nodo', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(nuevoNodo)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        console.log('Nodo agregado exitosamente:', data);
        mostrarMensaje('✅ Nodo agregado exitosamente', 'success');
        document.getElementById('form-agregar-nodo').reset();
        generarNuevoIdSugerido();
        verificarEstado();
        
    })
    .catch(error => {
        console.error('Error agregando nodo:', error);
        mostrarMensaje('❌ Error: ' + error.message, 'danger');
    });
}

function generarNuevoIdSugerido() {
    const ultimoId = document.getElementById('nuevo-id-nodo').placeholder;
    const numero = parseInt(ultimoId.substr(1)) + 1;
    const nuevoId = 'N' + numero.toString().padStart(3, '0');
    document.getElementById('nuevo-id-nodo').placeholder = nuevoId;
}

function mostrarMensaje(mensaje, tipo) {
    const alert = document.createElement('div');
    alert.className = `alert alert-${tipo} alert-dismissible fade show position-fixed`;
    alert.style.top = '20px';
    alert.style.right = '20px';
    alert.style.zIndex = '9999';
    alert.style.minWidth = '300px';
    alert.innerHTML = `
        ${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alert);

    setTimeout(() => {
        if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
        }
    }, 5000);
}

function inicializarFormularioPuntoCritico() {
    const form = document.getElementById('form-punto-critico');
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const nuevoPunto = {
            nombre: document.getElementById('nuevo-nombre-critico').value,
            latitud: parseFloat(document.getElementById('nueva-latitud-critico').value),
            longitud: parseFloat(document.getElementById('nueva-longitud-critico').value),
            tipo: document.getElementById('nuevo-tipo-critico').value,
            prioridad: document.getElementById('nueva-prioridad-critico').value,
            poblacion_afectada: parseInt(document.getElementById('nueva-poblacion-critico').value) || 0
        };
        
        agregarPuntoCritico(nuevoPunto);
    });
}

function agregarPuntoCritico(nuevoPunto) {
    fetch('/api/agregar-punto-critico', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(nuevoPunto)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            mostrarMensaje(data.message, 'success');
            console.log('Punto crítico agregado exitosamente:', data);
            
            document.getElementById('form-punto-critico').reset();

            setTimeout(() => {
                verificarEstado();
            }, 1000);
        } else {
            mostrarMensaje(`Error: ${data.error}`, 'danger');
            console.error('Error agregando punto crítico:', data.error);
        }
    })
    .catch(error => {
        mostrarMensaje('Error de conexión al agregar punto crítico', 'danger');
        console.error('Error agregando punto crítico:', error);
    });
}

function generarRedCompleta() {
    const btn = document.getElementById('btn-generar');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Generando...';
    
    fetch('/generar-red-completa', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            mostrarMensaje('✅ Red completa generada: ' + data.summary, 'success');
            console.log('Red generada:', data);

            setTimeout(() => {
                verificarEstado();
            }, 1000);
        } else {
            mostrarMensaje('❌ Error: ' + data.error, 'danger');
            console.error('Error generando red:', data.error);
        }
    })
    .catch(error => {
        mostrarMensaje('❌ Error de conexión al generar red', 'danger');
        console.error('Error:', error);
    })
    .finally(() => {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-network-wired me-1"></i> Generar Red Completa';
    });
}

function formatNumber(num) {
    return num.toLocaleString('es-PE');
}