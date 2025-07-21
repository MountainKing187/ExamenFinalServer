import socket
import threading
import json
from bson import ObjectId, json_util
from datetime import datetime
from app import mongo

class TCPServer:
    def __init__(self, host='0.0.0.0', port=5001, collection_name='sensor_readings_tcp'):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        
        self.sensor_collection = mongo.get_collection(collection_name)
    
    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Habilitar keep-alive
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self.server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
            self.server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 30)
            self.server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
            
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            print(f"TCP Server escuchando en {self.host}:{self.port}")
            server_thread = threading.Thread(target=self._run_server, daemon=True)
            server_thread.start()
        except Exception as e:
            print(f"ERROR al iniciar servidor: {e}")
            self.running = False
    
    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                # Cierra conexiones activas
                self.server_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass  # Ignora errores si el socket ya estaba cerrado
            finally:
                self.server_socket.close()
                print("Socket TCP cerrado correctamente")
    
    def _run_server(self):
        print("Iniciando bucle principal del servidor...")
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                print(f"Nueva conexión aceptada de {addr}")
                client_thread = threading.Thread(
                    target=self._handle_client, 
                    args=(conn, addr),
                    daemon=True
                )
                client_thread.start()
                print(f"Conexiones activas: {threading.active_count() - 1}")
            except OSError as e:
                if self.running:
                    print(f"Error en accept(): {str(e)}")
                break

    def _handle_client(self, conn, addr):
        with conn:
            print(f"Conexión TCP establecida desde {addr}")
            buffer = b''
            timeout_count = 0  # Contador de timeouts consecutivos
            max_timeouts = 3   # Máximo de timeouts antes de cerrar
            
            # Timeout más corto para detección rápida
            conn.settimeout(2.0)
            
            while self.running:
                try:
                    data = conn.recv(1024)
                    if not data:
                        print(f"Conexión cerrada por cliente: {addr}")
                        break
                        
                    # Reiniciar contador al recibir datos
                    timeout_count = 0
                    buffer += data
                    
                    # Procesar cuando recibamos un fin de línea
                    if buffer.endswith(b'\n'):
                        message = buffer.decode('utf-8').strip()
                        buffer = b''
                        
                        try:
                            parsed = self._parse_message(message)
                            print(f"Datos recibidos de {addr}: {parsed}")
                            
                            # Guardar en MongoDB
                            if self._save_to_database(parsed):
                                conn.sendall(b"ACK: Datos recibidos y guardados\n")
                            else:
                                conn.sendall(b"ACK: Datos recibidos pero error en DB\n")
                        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as e:
                            error_msg = f"ERROR: {str(e)}\n"
                            conn.sendall(error_msg.encode('utf-8'))

                
                except socket.timeout:
                    timeout_count += 1
                    if timeout_count >= max_timeouts:
                        print(f"Demasiados timeouts ({timeout_count}), cerrando conexión con {addr}")
                        break
                    
                    print(f"Timeout {timeout_count}/{max_timeouts} con {addr}")
                    # Enviar ping para verificar conexión
                    try:
                        conn.sendall(b"PING\n")
                    except OSError:
                        print(f"Conexión perdida con {addr}")
                        break
                    continue
                    
                except (ConnectionResetError, BrokenPipeError, OSError) as e:
                    print(f"Error de conexión con {addr}: {str(e)}")
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
            raise ValueError(f"Error en conversión de datos TCP de tipos: {str(e)}")
    
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
            print(f"Datos TCP guardados en MongoDB con ID: {result.inserted_id}")
            return True
        except Exception as e:
            print(f"Error al guardar datos TCP en MongoDB: {e}")
            return False