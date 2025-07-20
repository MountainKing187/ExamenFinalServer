from app import create_app
from app.gemini_agent import GeminiAgent
import threading

app = create_app()

def threads():
    gem_age = GeminiAgent()

    ai_thread = threading.Thread(
        target=gem_age.analizar_datos_gemini()
    )

    ai_thread.daemon = True

    ai_thread.start()

if __name__ == '__main__':
    print("asasd")
    threads()
    app.run(host='0.0.0.0', port=8081, use_reloader=False, debug=True)
    print("yeehaw")
