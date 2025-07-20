from app import create_app
from app.gemini_agent import GeminiAgent
import threading

app = create_app()

def main():
    # Iniciar servidores
    tcp_server = TCPServer(port=6000)
    udp_server = UDPServer(port=7000)
    # gemini_agent = GeminiAgent()

    tcp_server.start()
    udp_server.start()
    # gemini_agent.start()

    try:
        # Mantener el programa principal en ejecución
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Deteniendo servicios...")
        tcp_server.stop()
        udp_server.stop()
        # gemini_agent.stop()
        print("Servicios detenidos.")


if __name__ == '__main__':
    print("asasd")
    main()
    app.run(host='0.0.0.0', port=8081, use_reloader=False, debug=True)
    print("yeehaw")
