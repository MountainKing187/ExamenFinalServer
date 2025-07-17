from flask import Blueprint, render_template, jsonify, request, current_app
from app import mongo
from app.gemini_agent import GeminiAgent 
import json
from bson import json_util
import time
from datetime import datetime, timedelta
from pymongo import DESCENDING
import logging

main_bp = Blueprint('main', __name__)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@main_bp.route('/')
def dashboard():
    return render_template('dashboard.html')


@main_bp.route('/api/sensor', methods=['POST'])
def handle_json():
    collection = mongo.get_collection('sensor_readings')

    # Verificar que el contenido sea JSON
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400
    
    try:
        # Obtener los datos JSON del request
        data = request.get_json()
        
        # Validar que el JSON no esté vacío
        if not data:
            return jsonify({"error": "El cuerpo de la solicitud no puede estar vacío"}), 400

        logger.debug(f"Received JSON data: {data}")
        
        
        # Insertar el documento en MongoDB (asumo una colección llamada 'coleccion')
        result = collection.insert_one(data)
        
        # Retornar respuesta con el ID del documento insertado
        return jsonify({
            "message": "Datos recibidos y almacenados correctamente",
            "inserted_id": str(result.inserted_id)
        }), 201
        
    except Exception as e:
        # Manejar cualquier error inesperado
        return jsonify({"error": f"Error al procesar la solicitud: {str(e)}"}), 500

@main_bp.route('/api/sensor/latest', methods=['GET'])
def get_latest_sensor_readings():
    collection = mongo.get_collection('sensor_readings')
    try:
        # Obtener el parámetro 'n' con valor por defecto 1
        n = int(request.args.get('n', 1))
        
        # Validar que n sea un número positivo con límite máximo
        if n <= 0 or n > 1000:
            return jsonify({"error": "El parámetro 'n' debe estar entre 1 y 1000"}), 400
        
        # Obtener las últimas N lecturas ordenadas por Timestamp descendente
        readings = list(collection.find()
                       .sort([('Timestamp', DESCENDING)])
                       .limit(n))
        
        # Transformar los documentos para usar Timestamp como id
        formatted_readings = []
        for reading in readings:
            # Crear nuevo documento con el formato requerido
            formatted = {
                "id": reading["Timestamp"],
                "x": reading["x"],
                "y": reading["y"],
                "z": reading["z"]
            }
            formatted_readings.append(formatted)
        
        return jsonify({
            "count": len(formatted_readings),
            "readings": formatted_readings
        }), 200
        
    except KeyError as e:
        logger.error(f"Campo faltante en documento: {str(e)}")
        return jsonify({"error": f"Campo requerido faltante: {str(e)}"}), 500
    except ValueError:
        return jsonify({"error": "El parámetro 'n' debe ser un número entero válido"}), 400
    except Exception as e:
        logger.error(f"Error al obtener lecturas: {str(e)}", exc_info=True)
        return jsonify({"error": "Error interno del servidor"}), 500

@main_bp.route('/api/sensor/veria', methods=['GET'])
def get_ia_analisis():
    sensor_collection = mongo.get_collection('sensor_readings')
    ia_collection = mongo.get_collection('ia_analisis')
    try:
        # Calcular el timestamp de hace 1 minuto (en milisegundos)
        current_time = datetime.utcnow()
        one_minute_ago = current_time - timedelta(minutes=1)
        timestamp_threshold = int(one_minute_ago.timestamp() * 1000)  # Convertir a ms
        
        # Consultar documentos con Timestamp >= timestamp_threshold
        query = {"Timestamp": {"$gte": timestamp_threshold}}
        readings = list(sensor_collection.find(query))
        
        # Formatear la respuesta
        formatted_readings = []

        for reading in readings:
            formatted = {
                "timestamp": reading["Timestamp"],
                "x": reading["x"],
                "y": reading["y"],
                "z": reading["z"]
            }
            formatted_readings.append(formatted)

        analisis = jsonify({
            "analisis": gemini_agent.analizar_datos_gemini(formatted_readings),
            "current_time": current_time
        })
        ia_collection.insert_one(analisis)
        
        return analisis , 201
        
    except Exception as e:
        logger.error(f"Error obteniendo datos: {str(e)}", exc_info=True)
        return jsonify({"error": "Error interno del servidor"}), 500