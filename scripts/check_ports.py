import socket
import subprocess
import sys

def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

def find_available_port(start_port=8000, max_attempts=50):
    for port in range(start_port, start_port + max_attempts):
        if not check_port(port):
            return port
    for port in range(3000, 3000 + max_attempts):
        if not check_port(port):
            return port
    for port in range(9000, 9000 + max_attempts):
        if not check_port(port):
            return port
    return None

def get_process_using_port(port):
    try:
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        for line in lines:
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    return pid
    except Exception:
        pass
    return None

def kill_process_on_port(port):
    pid = get_process_using_port(port)
    if pid and pid != '0':
        try:
            subprocess.run(['taskkill', '/F', '/PID', pid], check=True)
            print(f"Proceso {pid} terminado exitosamente en puerto {port}")
            return True
        except subprocess.CalledProcessError:
            print(f"No se pudo terminar el proceso {pid}")
            return False
    return False

def main():
    print("🔍 Verificando puertos disponibles para Django...")

    preferred_ports = [8000, 8080, 3000, 5000, 8888, 9000]
    available_ports = []

    for port in preferred_ports:
        if check_port(port):
            pid = get_process_using_port(port)
            print(f"❌ Puerto {port}: OCUPADO (PID: {pid})")
        else:
            print(f"✅ Puerto {port}: DISPONIBLE")
            available_ports.append(port)

    if not available_ports:
        print("\n🔍 Buscando puerto disponible...")
        available_port = find_available_port(8000)
        if available_port:
            print(f"✅ Puerto disponible encontrado: {available_port}")
            available_ports.append(available_port)

    if available_ports:
        recommended_port = available_ports[0]
        print(f"\n🚀 Puerto recomendado: {recommended_port}")
        print(f"   Comando: python manage.py runserver {recommended_port}")
        return recommended_port
    else:
        print("\n❌ No se encontraron puertos disponibles")
        print("   Puedes intentar liberar un puerto ocupado:")
        for port in preferred_ports:
            if check_port(port):
                pid = get_process_using_port(port)
                print(f"   Puerto {port} (PID {pid}): taskkill /F /PID {pid}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--kill":
        if len(sys.argv) > 2:
            port = int(sys.argv[2])
            if kill_process_on_port(port):
                print(f"Puerto {port} liberado")
            else:
                print(f"No se pudo liberar puerto {port}")
        else:
            print("Uso: python scripts/check_ports.py --kill <puerto>")
    else:
        main()
