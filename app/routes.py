from flask import Blueprint, render_template, jsonify, request, current_app
from app import mongo
import json
from bson import json_util
from flask_socketio import emit
from app import socketio
from datetime import datetime, timedelta
from pymongo import DESCENDING


main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def dashboard():
    return render_template('dashboard.html')


@main_bp.route('/api/blocks/recent')
def recent_blocks():
    collection = mongo.get_collection('blocks')
    data = collection.find().sort('blockNumber', -1).limit(10)
    return json.loads(json_util.dumps(data))

@main_bp.route('/api/transactions/<block_number>')
def block_transactions(block_number):
    collection = mongo.get_collection('transactions')
    data = collection.find({'blockNumber': int(block_number)})
    return json.loads(json_util.dumps(data))

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@main_bp.route('/api/price/<symbol>')
def price_data(symbol):
    try:
        collection = mongo.get_collection('price_history')

        # Calcular timestamp de hace n horas
        hours = request.args.get('hours', default=24, type=int)
        time_range = datetime.utcnow() - timedelta(hours=hours)

        # Consultar solo datos de las últimas 24 horas
        data = collection.find({
            'symbol': symbol,
            'timestamp': {'$gte': time_range}
        }).sort('timestamp', 1)  # Orden ascendente para el gráfico

        return json.loads(json_util.dumps(data))
    except Exception as e:
        current_app.logger.error(f"Error en /api/price: {str(e)}")
        return jsonify({"error": "Database error"}), 500

@main_bp.route('/api/aiprompt')
def latest_ai_prompt():
    collection = mongo.get_collection('aiprompt')
    data = collection.find_one(sort=[('fecha_analisis', DESCENDING)])
    return json.loads(json_util.dumps(data))

@main_bp.route('/api/devices/register', methods=['POST'])
def register_device():
    """
    Registra un dispositivo para recibir notificaciones
    ---
    tags:
      - Dispositivos
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - token
            - device_id
          properties:
            token:
              type: string
              description: Token FCM del dispositivo
            device_id:
              type: string
              description: ID único del dispositivo físico
            user_id:
              type: string
              description: ID del usuario (opcional)
            platform:
              type: string
              description: Plataforma (android/ios)
    responses:
      201:
        description: Dispositivo registrado
      400:
        description: Datos inválidos
    """
    data = request.get_json()
    collection = mongo.get_collection('devices_collection')
    
    # Validación básica
    if not data or 'token' not in data or 'device_id' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Se requieren token y device_id'
        }), 400
    
    token = data['token']
    device_id = data['device_id']
    user_id = data.get('user_id')
    platform = data.get('platform', 'android')
    
    # Buscar si ya existe el dispositivo
    existing_device = collection.find_one({
        'device_id': device_id
    })
    
    try:
        if existing_device:
            # Actualizar token existente
            result = collection.update_one(
                {'_id': existing_device['_id']},
                {'$set': {
                    'token': token,
                    'updated_at': datetime.utcnow(),
                    'user_id': user_id,
                    'platform': platform
                }}
            )
            operation = 'updated'
        else:
            # Crear nuevo registro
            new_device = {
                'token': token,
                'device_id': device_id,
                'user_id': user_id,
                'platform': platform,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'active': True
            }
            result = collection.insert_one(new_device)
            operation = 'created'
        
        return jsonify({
            'status': 'success',
            'message': f'Dispositivo {operation}',
            'device_id': device_id
        }), 201
    
    except Exception as e:
        current_app.logger.error(f"Error registrando dispositivo: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error interno del servidor'
        }), 500
