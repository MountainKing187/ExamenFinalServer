from app import create_app
from app.gemini_agent import GeminiAgent
import threading

app = create_app()

def main():
    # Iniciar el servidor TCP
    tcp_server = TCPServer(port=6000)
    tcp_server.start()

    # Iniciar el agente Gemini
    gemini_agent = GeminiAgent()
    gemini_agent.start()

    try:
        # Mantener el programa principal en ejecución
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Deteniendo servicios...")
        tcp_server.stop()
        gemini_agent.stop()
        print("Servicios detenidos.")

if __name__ == '__main__':
    print("asasd")
    main()
    app.run(host='0.0.0.0', port=8081, use_reloader=False, debug=True)
    print("yeehaw")
