document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    
    // Elementos DOM
    const chartCanvas = document.getElementById('cryptoChart');
    const blocksList = document.getElementById('blocks-list');
    const transactionsContainer = document.getElementById('transactions-container');
    const currencyButtons = document.querySelectorAll('.currency-btn');
    const timeButtons = document.querySelectorAll('.time-btn');
    
    // Variables de estado
    let currentBlock = null;
    let currentCurrency = 'ethereum';
    let timeRange = 24;
    let cryptoChart = null;

    // Función para formatear direcciones
    function formatAddress(address) {
        if (!address) return '';
        return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
    }

    // Inicializar y actualizar el gráfico
    function updateChart(data) {
        // Destruir el gráfico anterior si existe
        if (cryptoChart) {
            cryptoChart.destroy();
        }
        
        // Calcular timestamp de hace X horas
        const hoursAgo = Date.now() - (timeRange * 60 * 60 * 1000);
        
        // Filtrar y procesar datos
        const labels = [];
        const prices = [];
        const colors = {
            ethereum: 'rgb(75, 192, 192)',
            dogecoin: 'rgb(153, 102, 255)',
            bitcoin: 'rgb(255, 159, 64)'
        };
        const color = colors[currentCurrency] || 'rgb(75, 192, 192)';
        
        data
            .filter(item => item.symbol === currentCurrency)
            .sort((a, b) => {
                const dateA = a.timestamp.$date ? new Date(a.timestamp.$date) : new Date(a.timestamp);
                const dateB = b.timestamp.$date ? new Date(b.timestamp.$date) : new Date(b.timestamp);
                return dateA - dateB;
            })
            .forEach(item => {
                const dateObj = item.timestamp.$date ? 
                    new Date(item.timestamp.$date) : 
                    new Date(item.timestamp);
                
                if (dateObj.getTime() >= hoursAgo) {
                    const hours = dateObj.getHours().toString().padStart(2, '0');
                    const minutes = dateObj.getMinutes().toString().padStart(2, '0');
                    labels.push(`${hours}:${minutes}`);
                    prices.push(item.price);
                }
            });
        
        // Crear nuevo gráfico
        const ctx = chartCanvas.getContext('2d');
        cryptoChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: currentCurrency.toUpperCase(),
                    data: prices,
                    borderColor: color,
                    backgroundColor: color.replace('rgb', 'rgba').replace(')', ', 0.1)'),
                    borderWidth: 2,
                    tension: 0.1,
                    fill: true,
                    pointRadius: 3,
                    pointBackgroundColor: '#fff',
                    pointBorderColor: color,
                    pointBorderWidth: 1,
                    pointHoverRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: { color: 'rgba(200, 200, 200, 0.1)' },
                        title: {
                            display: true,
                            text: 'Precio (USD)'
                        }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { maxTicksLimit: 8 },
                        title: {
                            display: true,
                            text: `Últimas ${timeRange} horas`
                        }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return `$${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                },
                interaction: { 
                    intersect: false, 
                    mode: 'nearest',
                    axis: 'x'
                }
            }
        });
    }
    
    // Cargar datos para la moneda actual
    function loadCurrencyData() {
        fetch(`/api/price/${currentCurrency}?hours=${timeRange}`)
            .then(response => response.json())
            .then(data => {
                updateChart(data);
            })
            .catch(error => {
                console.error('Error loading currency data:', error);
            });
    }

    // Cambiar moneda al hacer clic en botón
    currencyButtons.forEach(button => {
        button.addEventListener('click', function() {
            currencyButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            currentCurrency = this.dataset.currency;
            loadCurrencyData();
        });
    });
    
    // Cambiar rango de tiempo
    timeButtons.forEach(button => {
        button.addEventListener('click', function() {
            timeButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            timeRange = parseInt(this.dataset.hours);
            loadCurrencyData();
        });
    });

    // Actualizar lista de bloques
    function updateRecentBlocksList(blocks) {
        if (!blocksList) return;
        blocksList.innerHTML = '';

        blocks.forEach(block => {
            const blockDate = new Date(block.timestamp.$date);
            const listItem = document.createElement('li');
            listItem.className = 'block-item';
            listItem.dataset.blockNumber = block.blockNumber;
            listItem.innerHTML = `
                <div class="block-header">
                    <span class="block-number">#${block.blockNumber}</span>
                    <span class="block-time">${blockDate.toLocaleTimeString()}</span>
                </div>
                <div class="block-hash">${formatAddress(block.hash)}</div>
                <div class="block-transactions">${block.transactions.length} transacciones</div>
            `;
            
            listItem.addEventListener('click', function() {
                loadBlockTransactions(block.blockNumber);
            });
            
            blocksList.appendChild(listItem);
        });
    }
    
    // Cargar transacciones de un bloque
    function loadBlockTransactions(blockNumber) {
        // Resaltar bloque seleccionado
        document.querySelectorAll('.block-item').forEach(item => {
            item.classList.remove('active');
        });
        const selectedBlock = document.querySelector(`.block-item[data-block-number="${blockNumber}"]`);
        if (selectedBlock) {
            selectedBlock.classList.add('active');
        }
        
        fetch(`/api/transactions/${blockNumber}`)
            .then(response => response.json())
            .then(transactions => {
                renderTransactions(transactions);
            })
            .catch(error => {
                console.error('Error loading transactions:', error);
            });
    }
    
    // Renderizar transacciones
    function renderTransactions(transactions) {
        if (!transactionsContainer) return;
        transactionsContainer.innerHTML = '';

        if (transactions.length === 0) {
            transactionsContainer.innerHTML = '<p>No hay transacciones en este bloque</p>';
            return;
        }
        
        const table = document.createElement('table');
        table.className = 'transactions-table';
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Hash</th>
                    <th>De</th>
                    <th>A</th>
                    <th>Valor (ETH)</th>
                </tr>
            </thead>
            <tbody></tbody>
        `;

        const tbody = table.querySelector('tbody');

        transactions.forEach(tx => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td class="tx-hash">${formatAddress(tx.hash)}</td>
                <td class="tx-from">${tx.from ? formatAddress(tx.from) : 'SYSTEM'}</td>
                <td class="tx-to">${tx.to ? formatAddress(tx.to) : 'CONTRACT'}</td>
                <td class="tx-value">${parseFloat(tx.value).toFixed(4)}</td>
            `;
            tbody.appendChild(row);
        });

        transactionsContainer.appendChild(table);
    }

    // Manejar nuevos precios
    function handleNewPrice(data) {
        // Solo procesar si es para la moneda actual
        if (data.symbol === currentCurrency) {
            // Recargar todos los datos
            loadCurrencyData();
        }
    }
    
    // Registrar eventos de precios
    socket.on('new_price_ethereum', handleNewPrice);
    socket.on('new_price_dogecoin', handleNewPrice);
    socket.on('new_price_bitcoin', handleNewPrice);
    
    // Manejar eventos de SocketIO para bloques
    socket.on('new_block', (block) => {
        // Actualizar lista de bloques
        fetch('/api/blocks/recent')
            .then(response => response.json())
            .then(data => updateRecentBlocksList(data))
            .catch(error => {
                console.error('Error updating blocks:', error);
            });
        
        // Si es el bloque seleccionado, actualizar transacciones
        if (currentBlock === block.blockNumber) {
            loadBlockTransactions(block.blockNumber);
        }
    });
    
    // Cargar datos iniciales
    function loadInitialData() {
        // Activar botón de Ethereum por defecto
        document.querySelector('.currency-btn[data-currency="ethereum"]').classList.add('active');
        
        // Activar botón de 24h por defecto
        document.querySelector('.time-btn[data-hours="24"]').classList.add('active');
        
        // Cargar datos iniciales del gráfico
        loadCurrencyData();
        
        // Cargar bloques recientes
        fetch('/api/blocks/recent')
            .then(response => response.json())
            .then(data => {
                updateRecentBlocksList(data);
                if (data.length > 0) {
                    currentBlock = data[0].blockNumber;
                    loadBlockTransactions(currentBlock);
                }
            })
            .catch(error => {
                console.error('Error loading recent blocks:', error);
            });
    }
    
    // Inicializar la aplicación
    loadInitialData();
});
