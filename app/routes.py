from flask import Blueprint, render_template, jsonify, request, current_app
from datetime import datetime, timedelta
import google.generativeai as genai
from app.utils import config_loader
from pymongo import DESCENDING
from bson import json_util
from app import mongo
import json
import time

main_bp = Blueprint('main', __name__)


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

        print(f"Received JSON data: {data}")

        data['source'] = 'HTTP'
        
        # Insertar el documento en MongoDB
        result = collection.insert_one(data)
        print(str(result.inserted_id))
        
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
        print(f"Campo faltante en documento: {str(e)}")
        return jsonify({"error": f"Campo requerido faltante: {str(e)}"}), 500
    except ValueError:
        return jsonify({"error": "El parámetro 'n' debe ser un número entero válido"}), 400
    except Exception as e:
        print(f"Error al obtener lecturas: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

@main_bp.route('/api/veria', methods=['GET'])
def get_ia_analisis():
    collection = mongo.get_collection('sensor_readings')

    # Obtener el tiempo actual y el de hace 1 minuto
    ahora = datetime.utcnow()
    hace_un_minuto = ahora - timedelta(minutes=1)
    
    # Convertir a timestamp en milisegundos
    ahora_millis = int(ahora.timestamp() * 1000)
    hace_un_minuto_millis = int(hace_un_minuto.timestamp() * 1000)
    
    registros = list(collection.find({
        "timestamp": {
            "$gte": hace_un_minuto_millis,
            "$lte": ahora_millis
        }
    }))
    
    resultado = [reg for reg in registros]

    analisis = perform_analysis(resultado)

    return analisis

def perform_analysis(registros):
    config = config_loader.load_config()

    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

    try:
        """Realiza el análisis de datos con Gemini"""

        # Si no hay datos nuevos, saltar el análisis
        if not registros:
            print("No hay nuevos datos para analizar")
            return "No hay nuevos datos para analizar"

        prompt = f"""
        Analiza estos datos de un sensor acelerómetro y detecta posibles anomalías.

        Datos en formato JSON (Tiempo: Unix Timestamp en milisegundos, x=float, y=float, z=float):
        {registros}
        """
      
        response = model.generate_content(prompt)
        analisis = response.text.strip()
        
        return analisis

    except Exception as e:
        print(f"Error en el análisis: {e}")
        time.sleep(10)
        return f"Error en el análisis: {e}"

def utc_time_to_millis(utc_time):
    # Calculate total seconds since epoch
    epoch = datetime(1970, 1, 1)
    total_seconds_since_epoch = (utc_time - epoch).total_seconds()

    # Convert to milliseconds
    milliseconds_since_epoch = int(total_seconds_since_epoch * 1000)
    return milliseconds_since_epoch