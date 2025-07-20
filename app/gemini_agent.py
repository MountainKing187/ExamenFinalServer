from datetime import datetime, timedelta
import time
from app.utils import config_loader
from app import mongo
import os
import google.generativeai as genai
import threading

class GeminiAgent:

    def __init__(self):
        # Cargar configuración centralizada
        self.config = config_loader.load_config()

        if not self.config.GEMINI_API_KEY:
            raise ValueError("La API Key de Gemini no está configurada")

        self.sensor_readings = mongo.get_collection('sensor_readings')
        self.ia_analisis = mongo.get_collection('ia_analisis')
        
        self.running = False
        self.thread = None

    def start(self):
        """Inicia el agente en un hilo separado"""
        if self.running:
            print("El agente ya está en ejecución")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_analysis_loop, daemon=True)
        self.thread.start()
        print("GeminiAgent iniciado")

    def stop(self):
        """Detiene el agente"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)  # Esperar a que termine el hilo
        print("GeminiAgent detenido")

    def _run_analysis_loop(self):
        """Bucle principal de análisis periódico"""
        # Configurar Gemini una sola vez
        genai.configure(api_key=self.config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        while self.running:
            try:
                self._perform_analysis(model)
            except Exception as e:
                print(f"Error en el análisis: {e}")
                self._safe_sleep(10)
            
            # Espera principal entre análisis
            self._safe_sleep(120)

    def _perform_analysis(self, model):
        """Realiza el análisis de datos con Gemini"""
        hora_actual = datetime.utcnow()
        hace_un_minuto = hora_actual - timedelta(minutes=1)
        
        # Consultar registros recientes
        query = {"timestamp": {"$gte": hace_un_minuto}}
        registros = list(self.sensor_readings.find(query))

        # Si no hay datos nuevos, saltar el análisis
        if not registros:
            print("No hay nuevos datos para analizar")
            return

        prompt = f"""
        Analiza estos datos de un sensor acelerómetro y detecta posibles anomalías.

        Datos en formato JSON (Tiempo: Unix Timestamp en milisegundos, x=float, y=float, z=float):
        {registros}
        """
      
        response = model.generate_content(prompt)
        analisis = response.text.strip()
        
        # Crear documento para insertar
        documento_analisis = {
            "fecha_analisis": datetime.utcnow(),
            "prompt_utilizado": prompt,
            "analisis_gemini": analisis,
            "datos_analizados": len(registros)
        }
            
        self.ia_analisis.insert_one(documento_analisis)
        print(f"Análisis insertado en la base de datos (registros: {len(registros)})")

    def _safe_sleep(self, seconds):
        """Espera con verificación periódica para permitir detención"""
        for _ in range(seconds):
            if not self.running:
                break
            time.sleep(1)