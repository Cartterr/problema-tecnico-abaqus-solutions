import subprocess
import sys
import os
from check_ports import find_available_port, check_port

def run_django_server():
    print("🚀 Iniciando servidor Django...")

    available_port = find_available_port()

    if not available_port:
        print("❌ No se encontraron puertos disponibles en rangos comunes")
        print("   Intentando puertos aleatorios...")
        for port in range(10000, 11000, 100):
            if not check_port(port):
                available_port = port
                break

    if not available_port:
        print("❌ Error: No se pudo encontrar ningún puerto disponible")
        print("   Sugerencias:")
        print("   1. Reinicia tu computadora")
        print("   2. Cierra otros programas que usen puertos")
        print("   3. Ejecuta como administrador")
        return False

    print(f"✅ Puerto disponible encontrado: {available_port}")
    print(f"🌐 Dashboard: http://127.0.0.1:{available_port}/dashboard/")
    print(f"📊 API: http://127.0.0.1:{available_port}/api/values/")
    print("\n🎯 Presiona Ctrl+C para detener el servidor")
    print("-" * 50)

    try:
        subprocess.run([sys.executable, 'manage.py', 'runserver', str(available_port)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando servidor: {e}")
        return False
    except KeyboardInterrupt:
        print("\n✅ Servidor detenido por el usuario")
        return True

    return True

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    run_django_server()
