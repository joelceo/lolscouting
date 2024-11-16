import csv
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
import os

# Importar variables desde config.py
from config import EDGE_DRIVER_PATH, INVOCADORES, TEAM_NAME

# Ruta del archivo que contiene los enlaces de las partidas
PARTIDAS_LINKS_FILE = "partidas_links.txt"
# Archivo CSV de salida
OUTPUT_CSV_FILE = "timeline.csv"

# Arreglo de invocadores del equipo
invocadores_equipo = INVOCADORES

# Verificar si el controlador existe
if not os.path.isfile(EDGE_DRIVER_PATH):
    raise FileNotFoundError(f"El archivo del controlador no se encuentra en la ruta especificada: {EDGE_DRIVER_PATH}")

# Configurar las opciones de Edge
edge_options = Options()
edge_options.add_argument("--headless")  # Ejecutar en modo headless
edge_options.add_argument("--disable-blink-features=AutomationControlled")  # Evitar la detección de headless
edge_options.add_argument("--start-maximized")
edge_options.add_argument("--log-level=3")
edge_options.add_argument("--disable-gpu")
edge_options.add_argument("--no-sandbox")
edge_options.add_argument("--disable-dev-shm-usage")
edge_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
edge_options.add_argument("--enable-unsafe-swiftshader")  # Habilitar SwiftShader para evitar advertencias de WebGL

# Inicializar el navegador con Selenium
service = Service(EDGE_DRIVER_PATH)
driver = webdriver.Edge(service=service, options=edge_options)

# Función para convertir el tiempo al formato h:mm:ss
def convertir_a_formato_tiempo(tiempo_str):
    return f"0:{tiempo_str.replace(' ', ':')}"

# Leer los enlaces de las partidas
def leer_enlaces(file_path):
    with open(file_path, 'r') as file:
        return [line.split(":", 1)[1].strip() for line in file.readlines() if "http" in line]

# Analizar el HTML para extraer eventos importantes
def extraer_eventos_importantes(html, partida_numero):
    soup = BeautifulSoup(html, 'html.parser')
    eventos = []
    timeline_container = soup.find('div', class_='timeline-container')

    if not timeline_container:
        print(f"[Partida {partida_numero}] No se encontró el div de 'timeline-container'.")
        return eventos  # Si no se encuentra el div de timeline-container, no hay eventos que extraer

    mensajes = timeline_container.find_all('div', class_='message')

    for mensaje_div in mensajes:
        # Extraer texto del evento
        evento_texto_elemento = mensaje_div.find('div', class_='message')
        evento_texto = evento_texto_elemento.get_text(strip=True) if evento_texto_elemento else "N/A"
        # Reemplazar 'Horda Asesinado' por 'Larva Asesinada'
        if evento_texto == "Horda Asesinado":
            evento_texto = "Larva Asesinada"

        # Extraer tiempo del evento
        tiempo_div = mensaje_div.find('div', class_='time')
        tiempo = convertir_a_formato_tiempo(tiempo_div.get_text(strip=True)) if tiempo_div else "N/A"

        # Extraer ejecutor
        ejecutor_element = mensaje_div.find('span', class_='css-ao94tw')
        campeon_ejecutor_element = mensaje_div.find('img', alt=True)

        ejecutor = ejecutor_element.get_text(strip=True).lower() if ejecutor_element else "N/A"
        campeon_ejecutor = campeon_ejecutor_element['alt'] if campeon_ejecutor_element else "N/A"

        # Log detallado de elementos encontrados
        print(f"[Partida {partida_numero}] Datos extraídos - Evento: {evento_texto}, Tiempo: {tiempo}, Ejecutor: {ejecutor}, Campeón Ejecutor: {campeon_ejecutor}")

        # Si el evento tiene información incompleta, tratar de identificar qué falta
        if evento_texto == "N/A" or tiempo == "N/A" or ejecutor == "N/A" or campeon_ejecutor == "N/A":
            print(f"[Partida {partida_numero}] Información incompleta para el evento. Evento: {evento_texto}, Tiempo: {tiempo}, Ejecutor: {ejecutor}, Campeón Ejecutor: {campeon_ejecutor}")
            continue

        # Determinar el equipo del ejecutor
        equipo_azul_invocadores = [i.lower() for i in invocadores_equipo]
        lado = "blue" if ejecutor in equipo_azul_invocadores else "red"

        # Determinar si el ejecutor pertenece al equipo especificado
        pertenece_al_equipo = TEAM_NAME if ejecutor in equipo_azul_invocadores else "None"

        print(f"[Partida {partida_numero}] Evento completo: {evento_texto}, Tiempo: {tiempo}, Ejecutor: {ejecutor}, Campeón Ejecutor: {campeon_ejecutor}, Lado: {lado}, Equipo: {pertenece_al_equipo}")

        # Añadir evento a la lista de eventos si tiene nombre
        if evento_texto != "N/A":
            eventos.append([partida_numero, tiempo, evento_texto, ejecutor, campeon_ejecutor, lado, pertenece_al_equipo])

        # Crear nuevo evento "Primera Muerte" a partir de "Primera Sangre"
        if evento_texto == "Primera Sangre":
            objetivo_element = mensaje_div.find_all('img', alt=True)
            if len(objetivo_element) > 1:
                objetivo = objetivo_element[1]['alt']
                objetivo_ejecutor_element = mensaje_div.find_all('span', class_='css-ao94tw')
                if len(objetivo_ejecutor_element) > 1:
                    invocador_objetivo = objetivo_ejecutor_element[1].get_text(strip=True).lower()
                    lado_inverso = "red" if lado == "blue" else "blue"
                    pertenece_al_equipo_inverso = TEAM_NAME if invocador_objetivo in [i.lower() for i in invocadores_equipo] else "None"
                    eventos.append([partida_numero, tiempo, "Primera Muerte", invocador_objetivo, objetivo, lado_inverso, pertenece_al_equipo_inverso])

    return eventos

# Proceso principal para extraer los eventos importantes de cada partida
def procesar_partidas():
    # Inicializar el archivo CSV vacío para una nueva ejecución
    with open(OUTPUT_CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        # Escribir encabezados
        csvwriter.writerow(["Partida", "Tiempo", "Evento", "Ejecutor", "Campeón Ejecutor", "Lado", "Team"])

        enlaces = leer_enlaces(PARTIDAS_LINKS_FILE)
        partida_numero = 1

        for enlace in enlaces:
            try:
                print(f"Abriendo enlace de partida {partida_numero}: {enlace}")
                driver.get(enlace)
                wait = WebDriverWait(driver, 15)
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(5)  # Esperar a que la página cargue completamente

                # Hacer clic en "Análisis de equipo" y luego "Línea de tiempo"
                try:
                    boton_analisis_equipo = driver.find_element(By.XPATH, "//button[span[text()='Análisis de equipo']]")
                    boton_analisis_equipo.click()
                    print("Hizo clic en Análisis de equipo")
                    time.sleep(3)
                    boton_linea_tiempo = driver.find_element(By.XPATH, "//button[span[text()='Línea de tiempo']]")
                    boton_linea_tiempo.click()
                    print("Hizo clic en Línea de tiempo")
                    time.sleep(5)
                except NoSuchElementException:
                    print(f"No se encontraron los botones de análisis o línea de tiempo en la partida {partida_numero}")
                    partida_numero += 1
                    continue

                # Obtener el HTML actual de la página
                html = driver.page_source
                print(f"Extrayendo eventos de la partida {partida_numero}")
                eventos = extraer_eventos_importantes(html, partida_numero)

                # Mostrar en consola los eventos encontrados antes de escribir en CSV
                if eventos:
                    for evento in eventos:
                        print(f"Evento encontrado: {evento}")
                else:
                    print(f"No se encontraron eventos importantes en la partida {partida_numero}")

                # Escribir eventos al CSV
                for evento in eventos:
                    csvwriter.writerow(evento)
            except Exception as e:
                print(f"Error abriendo el enlace de partida {partida_numero}: {e}")
            
            partida_numero += 1

# Ejecutar el script
try:
    procesar_partidas()
finally:
    driver.quit()
