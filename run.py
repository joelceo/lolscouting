import os
import subprocess
import threading

def run_command(command):
    """Ejecuta un comando de terminal."""
    try:
        print(f"Ejecutando: {command}...")
        subprocess.run(command, shell=True, check=True)
        print(f"{command} ejecutado correctamente.\n")
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar {command}: {e}\n")

if __name__ == "__main__":
    # Paso 1: Ejecutar `get_game_links.py`
    run_command('python .\\get_game_links.py')

    # Paso 2: Ejecutar `get_player_data.py` y `get_game_timeline.py` en simultáneo
    threads = []
    for script in ['get_player_data.py', 'get_game_timeline.py']:
        thread = threading.Thread(target=run_command, args=(f'python .\\{script}',))
        threads.append(thread)
        thread.start()

    # Esperar a que ambos threads terminen
    for thread in threads:
        thread.join()

    print("Todos los scripts se ejecutaron correctamente.")
