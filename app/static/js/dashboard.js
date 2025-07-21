// Variable para el umbral de alerta (valor inicial 9.8)
let alertThreshold = 9.8;

// Configuración inicial del gráfico
const ctx = document.getElementById('accelerationChart').getContext('2d');
const chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            {
                label: 'Aceleración X',
                data: [],
                borderColor: '#3498db',
                borderWidth: 2,
                tension: 0.3
            },
            {
                label: 'Aceleración Y',
                data: [],
                borderColor: '#2ecc71',
                borderWidth: 2,
                tension: 0.3
            },
            {
                label: 'Aceleración Z',
                data: [],
                borderColor: '#9b59b6',
                borderWidth: 2,
                tension: 0.3
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                title: {
                    display: true,
                    text: 'Aceleración (m/s²)'
                }
            },
            x: {
                title: {
                    display: true,
                    text: 'Tiempo'
                }
            }
        }
    }
});

// Configurar el control deslizante del umbral
const thresholdSlider = document.getElementById('thresholdSlider');
const thresholdValue = document.getElementById('thresholdValue');

// Actualizar la visualización del valor del umbral
thresholdSlider.addEventListener('input', function() {
    alertThreshold = parseFloat(this.value);
    thresholdValue.textContent = alertThreshold.toFixed(1);
});

// Conectar a WebSocket
const socket = io();

// Función para actualizar el estado de alerta
function updateAlertStatus(magnitude) {
    const statusElement = document.getElementById('accelerationStatus');
    const accelerationCard = document.getElementById('accelerationCard');
    
    if (magnitude > alertThreshold) {
        statusElement.textContent = 'ALERTA!';
        statusElement.className = 'status alert';
        accelerationCard.classList.add('alert-card');
    } else {
        statusElement.textContent = 'Normal';
        statusElement.className = 'status normal';
        accelerationCard.classList.remove('alert-card');
    }
}

// Manejar datos en tiempo real
socket.on('new_acceleration_data', (data) => {
    // Calcular la magnitud de la aceleración
    const magnitude = Math.sqrt(data.x**2 + data.y**2 + data.z**2);
    const formattedMagnitude = magnitude.toFixed(2);
    
    // Actualizar valor numérico
    document.getElementById('accelerationValue').textContent = formattedMagnitude;
    
    // Actualizar valores de componentes
    document.getElementById('xValue').textContent = data.x.toFixed(2);
    document.getElementById('yValue').textContent = data.y.toFixed(2);
    document.getElementById('zValue').textContent = data.z.toFixed(2);
    
    // Actualizar estado de alerta
    updateAlertStatus(magnitude);
    
    // Actualizar gráfico
    const time = new Date(data.Timestamp).toLocaleTimeString();
    
    // Agregar nuevos puntos manteniendo solo los últimos 20
    chart.data.labels.push(time);
    if (chart.data.labels.length > 20) {
        chart.data.labels.shift();
    }
    
    // Actualizar datasets
    chart.data.datasets[0].data.push(data.x);
    chart.data.datasets[1].data.push(data.y);
    chart.data.datasets[2].data.push(data.z);
    
    // Mantener solo los últimos 20 puntos en cada dataset
    chart.data.datasets.forEach(dataset => {
        if (dataset.data.length > 20) {
            dataset.data.shift();
        }
    });
    
    chart.update();
});

// Manejar solicitud de insights
document.getElementById('insightsBtn').addEventListener('click', async () => {
    const insightsResult = document.getElementById('insightsResult');
    insightsResult.textContent = 'Analizando datos...';
    
    try {
        const response = await fetch('/api/insights');
        const data = await response.json();
        insightsResult.textContent = data.insight || 'No se obtuvieron insights';
    } catch (error) {
        console.error('Error fetching insights:', error);
        insightsResult.textContent = 'Error al obtener insights';
    }
});

// Inicializar el valor del umbral
thresholdValue.textContent = alertThreshold.toFixed(1);