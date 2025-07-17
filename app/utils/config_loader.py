import os
from dotenv import load_dotenv

def load_config():
    load_dotenv()  # Cargar variables de entorno desde .env
    
    class Config:
        MONGODB_URI = os.getenv('MONGODB_URI')
        MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'crypto_data')
        GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    return Config()
