// Umbral de alerta (ajustar según necesidades)
const ALERT_THRESHOLD = 9.8;

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

// Conectar a WebSocket
const socket = io();

// Manejar datos en tiempo real
socket.on('new_acceleration_data', (data) => {
    // Calcular la magnitud de la aceleración
    const magnitude = Math.sqrt(data.x**2 + data.y**2 + data.z**2);
    const formattedMagnitude = magnitude.toFixed(2);
    
    // Actualizar valor numérico
    document.getElementById('accelerationValue').textContent = formattedMagnitude;
    
    // Actualizar valores de componentes
    document.getElementById('xValue').textContent = data.x.toFixed(2)
    document.getElementById('yValue').textContent = data.y.toFixed(2);
    document.getElementById('zValue').textContent = data.z.toFixed(2);

    // Actualizar estado de alerta
    const statusElement = document.getElementById('accelerationStatus');
    if (magnitude > ALERT_THRESHOLD) {
        statusElement.textContent = 'ALERTA!';
        statusElement.className = 'status alert';
        document.getElementById('accelerationCard').classList.add('alert-card');
    } else {
        statusElement.textContent = 'Normal';
        statusElement.className = 'status normal';
        document.getElementById('accelerationCard').classList.remove('alert-card');
    }
    
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