import socket
import threading
import json
import time
from datetime import datetime
from app import mongo

class UDPServer:
    def __init__(self, host='0.0.0.0', port=5003, collection_name='sensor_readings_udp'):
        self.host = host
        self.port = port
        self.sock = None
        self.running = False
        self.thread = None
        self.buffer_size = 65507  # Tamaño máximo de datagrama UDP
        
        self.collection = mongo.get_collection(collection_name)

    def start(self):
        """Inicia el servidor UDP en un hilo separado"""
        if self.running:
            print("UDPServer ya está en ejecución")
            return
            
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.sock.setblocking(False)  # Socket no bloqueante
        self.running = True
        
        print(f"UDP Server escuchando en {self.host}:{self.port}")
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Detiene el servidor UDP"""
        self.running = False
        if self.sock:
            self.sock.close()
        if self.thread:
            self.thread.join(timeout=2.0)
        print("UDP Server detenido")
    
    def _run_server(self):
        """Bucle principal del servidor UDP"""
        while self.running:
            try:
                # Intentar recibir datos sin bloquear
                data, addr = self.sock.recvfrom(self.buffer_size)
                self._handle_datagram(data, addr)
            except BlockingIOError:
                # No hay datos disponibles, esperar brevemente
                time.sleep(0.01)
            except OSError as e:
                if self.running:
                    print(f"Error en socket UDP: {e}")
                break
    
    def _handle_datagram(self, data, addr):
        """Procesa un datagrama recibido"""
        try:
            message = data.decode('utf-8').strip()
            json_data = json.loads(message)
            print(f"Recibido UDP de {addr}: {json_data}")
            
            # Normalizar y guardar los datos
            document = self._normalize_data(json_data)
            self._save_to_database(document)
            
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            print(f"Error procesando datagrama UDP: {e}")
    
    def _normalize_data(self, data):
        """Normaliza los datos al formato esperado"""
        # Convertir timestamp si está presente
        if 'timestamp' in data:
            try:
                # Asumimos que es un entero (milisegundos)
                ts = int(data['timestamp'])
                data['timestamp'] = datetime.utcfromtimestamp(ts / 1000.0)
            except (TypeError, ValueError):
                # Si falla, usar fecha actual
                data['timestamp'] = datetime.utcnow()
        else:
            data['timestamp'] = datetime.utcnow()
        
        # Asegurar que x, y, z son floats
        for coord in ['x', 'y', 'z']:
            if coord in data:
                try:
                    data[coord] = float(data[coord])
                except (TypeError, ValueError):
                    data[coord] = 0.0
            else:
                data[coord] = 0.0
        
        # Añadir la fuente
        data['source'] = 'UDP'
        return data
    
    def _save_to_database(self, document):
        """Guarda los datos en MongoDB"""
        try:
            result = self.collection.insert_one(document)
            print(f"Datos UDP guardados con ID: {result.inserted_id}")
            return True
        except Exception as e:
            print(f"Error al guardar datos UDP: {e}")
            return False