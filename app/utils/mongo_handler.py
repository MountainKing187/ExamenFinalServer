from pymongo import MongoClient

class MongoHandler:
    def __init__(self):
        self.client = None
        self.db = None
    
    def create_client(self, mongo_uri):
        """Crea y devuelve una instancia de cliente MongoDB"""
        return MongoClient(mongo_uri)
    
    def init_app(self, app):
        """Método para inicializar con la aplicación Flask"""
        self.client = self.create_client(app.config['MONGODB_URI'])
        self.db = self.client[app.config['MONGO_DB_NAME']]
    
    def get_collection(self, collection_name):
        """Obtiene una colección de MongoDB de manera segura"""
        # Verificación corregida usando is not None
        if self.db is not None:
            return self.db[collection_name]
        raise RuntimeError("MongoDB database not initialized")
