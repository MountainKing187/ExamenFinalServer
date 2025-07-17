import os
import google.generativeai as genai

class GeminiAgent:

    def __init__(self):
        # Cargar configuración centralizada
        self.config = config_loader.load_config()

        if not self.config.GEMINI_API_KEY:
            raise ValueError("La API Key de Gemini no está configurada")

    def analizar_datos_gemini(self,datos):

        # Configurar Gemini
        genai.configure(api_key= self.config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        try:
            prompt = f"""
            Analiza estos datos de sensor y detecta posibles anomalias

            Datos de formato json
            (Tiempo : Unix Timestamp in milliseconds , x = float,y = float, z = float)
            {datos}
            """
            # Enviar solicitud a Gemini
            response = model.generate_content(prompt)
            analisis = response.text.strip()
            return analisis

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)

