from flask import Flask
from flask_socketio import SocketIO
from .utils.mongo_handler import MongoHandler
from .utils.config_loader import load_config

socketio = SocketIO()
mongo = MongoHandler()

def create_app():
    app = Flask(__name__)
    
    # Cargar configuración
    app.config.from_object(load_config())
    
    # Inicializar extensiones
    mongo.init_app(app)
    socketio.init_app(app)
    
    # Registrar blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
