from flask import Blueprint, render_template, jsonify, request, current_app
from app import mongo
import json
from bson import json_util
from datetime import datetime, timedelta
from pymongo import DESCENDING


main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def dashboard():
    return render_template('dashboard.html')


@app.route('/api/sensor', methods=['POST'])
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

@app.route('/api/sensor/latest', methods=['GET'])
def get_latest_sensor_readings():
    try:
        # Obtener el parámetro 'n' de la query string, con valor por defecto 1 si no se especifica
        n = int(request.args.get('n', default=1))
        
        # Validar que n sea un número positivo
        if n <= 0:
            return jsonify({"error": "El parámetro 'n' debe ser un número positivo"}), 400
        
        # Obtener las últimas N lecturas ordenadas por _id descendente (asumiendo que _id es ObjectId con timestamp)
        # Asumo que los datos del sensor están en una colección llamada 'sensor_readings'
        readings = list(db.sensor_readings.find()
                       .sort([('_id', -1)])
                       .limit(n))
        
        # Convertir ObjectId a string para que sea JSON serializable
        for reading in readings:
            reading['_id'] = str(reading['_id'])
        
        return jsonify({
            "count": len(readings),
            "readings": readings
        }), 200
        
    except ValueError:
        return jsonify({"error": "El parámetro 'n' debe ser un número entero válido"}), 400
    except Exception as e:
        return jsonify({"error": f"Error al obtener las lecturas: {str(e)}"}), 500
