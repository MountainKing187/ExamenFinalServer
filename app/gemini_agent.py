from datetime import datetime, timedelta
import time
from app.utils import config_loader, mongo_handler
import os
import google.generativeai as genai

class GeminiAgent:

    def __init__(self):
        # Cargar configuración centralizada
        self.config = config_loader.load_config()

        if not self.config.GEMINI_API_KEY:
            raise ValueError("La API Key de Gemini no está configurada")

        self.mongo = mongo_handler.MongoHandler()
        self.mongo.client = self.mongo.create_client(self.config.MONGODB_URI)
        self.mongo.db = self.mongo.client[self.config.MONGO_DB_NAME]

        self.sensor_readings = self.mongo.db.sensor_readings
        self.ia_analisis = self.mongo.db.ia_analisis

    def analizar_datos_gemini(self):

        # Configurar Gemini
        genai.configure(api_key= self.config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')

        hora_actual = datetime.utcnow()
        hace_un_minuto= hora_actual - timedelta(minutes=1)
        
        try:
                        
            # Consultar registros de hace dos horas
            query = {
                "timestamp": {"$gte": hace_un_minuto}
            }

            registros = list(self.sensor_readings.find(query))

            prompt = f"""
            Analiza estos datos de sensor y detecta posibles anomalias

            Datos de formato json
            (Tiempo : Unix Timestamp in milliseconds , x = float,y = float, z = float)
            {registros}
            """
          
            response = model.generate_content(prompt)
            analisis = response.text.strip()
            
            # Crear documento para insertar
            documento_analisis = {
                "fecha_analisis": datetime.utcnow(),
                "prompt_utilizado": prompt,
                "analisis_gemini": analisis
            }
                
            self.aiprompt.insert_one(documento_analisis)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)

        time.sleep(120)

