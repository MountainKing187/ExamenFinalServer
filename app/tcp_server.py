import socket
import threading
import json
from bson import ObjectId, json_util
from datetime import datetime
from app import mongo

class TCPServer:
    def __init__(self, host='0.0.0.0', port=5001):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        
        self.sensor_collection = mongo.get_collection('sensor_readings')
    
    def start(self):
        """Inicia el servidor TCP en un hilo separado"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        
        print(f"TCP Server escuchando en {self.host}:{self.port}")
        server_thread = threading.Thread(target=self._run_server, daemon=True)
        server_thread.start()
    
    def stop(self):
        """Detiene el servidor TCP"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
    
    def _run_server(self):
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self._handle_client, 
                    args=(conn, addr),
                    daemon=True
                )
                client_thread.start()
            except OSError:
                break  # Socket cerrado durante accept()
    
    def _handle_client(self, conn, addr):
        with conn:
            print(f"Conexión TCP establecida desde {addr}")
            buffer = b''
            
            while self.running:
                try:
                    data = conn.recv(1024)
                    if not data:
                        break
                    buffer += data
                    
                    # Procesar cuando recibamos un fin de línea
                    if buffer.endswith(b'\n'):
                        message = buffer.decode('utf-8').strip()
                        buffer = b''
                        
                        try:
                            parsed = self._parse_message(message)
                            print("Datos parseados:", parsed)
                            
                            # Guardar en MongoDB
                            self._save_to_database(parsed)
                            
                            # Enviar ACK
                            conn.sendall(b"ACK: Datos recibidos y guardados\n")
                        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as e:
                            error_msg = f"ERROR: {str(e)}\n"
                            conn.sendall(error_msg.encode('utf-8'))
                except (ConnectionResetError, BrokenPipeError):
                    break
    
    def _parse_message(self, message):
        """Parsea el mensaje JSON con manejo de tipos especiales"""
        try:
            # Parseo inicial del JSON usando json_util para manejar tipos BSON
            data = json_util.loads(message)
            
            # Convertir tipos especiales
            if '_id' in data and isinstance(data['_id'], str):
                data['_id'] = ObjectId(data['_id'])
            
            if 'Timestamp' in data:
                # Convertir timestamp de milisegundos a datetime
                if isinstance(data['Timestamp'], str):
                    timestamp_ms = int(data['Timestamp'])
                else:
                    timestamp_ms = data['Timestamp']
                data['timestamp'] = datetime.utcfromtimestamp(timestamp_ms / 1000.0)
                del data['Timestamp']  # Eliminar la clave original
            
            # Asegurar campos numéricos
            for field in ['x', 'y', 'z']:
                if field in data and isinstance(data[field], str):
                    data[field] = float(data[field])
            
            return data
        except (TypeError, ValueError) as e:
            raise ValueError(f"Error en conversión de tipos: {str(e)}")
    
    def _save_to_database(self, data):
        """Guarda los datos en MongoDB"""
        try:
            # Crear documento para insertar
            document = {
                'timestamp': data.get('timestamp', datetime.utcnow()),
                'x': data.get('x', 0.0),
                'y': data.get('y', 0.0),
                'z': data.get('z', 0.0),
                'source': 'TCP'
            }
            
            # Mantener _id si existe
            if '_id' in data:
                document['_id'] = data['_id']
            
            # Insertar en la colección
            result = self.sensor_collection.insert_one(document)
            print(f"Datos guardados en MongoDB con ID: {result.inserted_id}")
            return True
        except Exception as e:
            print(f"Error al guardar en MongoDB: {e}")
            return False