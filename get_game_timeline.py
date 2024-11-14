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

# Ruta del archivo que contiene los enlaces de las partidas
PARTIDAS_LINKS_FILE = "partidas_links.txt"
# Archivo CSV de salida
OUTPUT_CSV_FILE = "eventos_importantes.csv"
# Ruta al controlador de Edge WebDriver
EDGE_DRIVER_PATH = r"C:\edgedriver_win64\msedgedriver.exe"

# Arreglo de invocadores del equipo
invocadores_equipo = ["kingpower", "arielpalma2", "ceress", "IIIPatrocloI", "saidgalan"]

# Verificar si el controlador existe
if not os.path.isfile(EDGE_DRIVER_PATH):
    raise FileNotFoundError(f"El archivo del controlador no se encuentra en la ruta especificada: {EDGE_DRIVER_PATH}")

# Configurar las opciones de Edge
edge_options = Options()
edge_options.add_argument("--start-maximized")
edge_options.add_argument("--log-level=3")  # Silenciar la salida de log del navegador

# Inicializar el navegador con Selenium
service = Service(EDGE_DRIVER_PATH)
driver = webdriver.Edge(service=service, options=edge_options)

# Función para convertir el tiempo al formato h:mm:ss
def convertir_a_formato_tiempo(tiempo_str):
    tiempo = int(tiempo_str)
    minutos, segundos = divmod(tiempo, 60)
    horas, minutos = divmod(minutos, 60)
    return f"{horas}:{minutos:02}:{segundos:02}"

# Leer los enlaces de las partidas
def leer_enlaces(file_path):
    with open(file_path, 'r') as file:
        return [line.split(":", 1)[1].strip() for line in file.readlines() if "http" in line]

# Analizar el HTML para extraer eventos importantes
def extraer_eventos_importantes(html, partida_numero):
    soup = BeautifulSoup(html, 'html.parser')
    eventos = []
    timeline_div = soup.find('div', class_='timeline')

    if not timeline_div:
        return eventos  # Si no se encuentra el div de timeline, no hay eventos que extraer

    botones_eventos = timeline_div.find_all('button', class_='timeline--WIN') + timeline_div.find_all('button', class_='timeline--LOSE')

    # Extraer información de los equipos
    equipo_azul_div = soup.find('div', class_='team--blue')
    equipo_rojo_div = soup.find('div', class_='team--red')
    
    equipo_azul_invocadores = [span.get_text(strip=True).lower() for span in equipo_azul_div.find_all('span', class_='name')] if equipo_azul_div else []
    equipo_rojo_invocadores = [span.get_text(strip=True).lower() for span in equipo_rojo_div.find_all('span', class_='name')] if equipo_rojo_div else []

    for boton in botones_eventos:
        mensaje_div = boton.find('div', class_='message')
        if not mensaje_div:
            continue

        # Asegurarse de que el elemento de mensaje exista antes de llamar a get_text
        evento_texto_elemento = mensaje_div.find('div', class_='message')
        if evento_texto_elemento:
            evento_texto = evento_texto_elemento.get_text(strip=True)
        else:
            evento_texto = "N/A"

        tiempo_div = mensaje_div.find('div', class_='time')
        tiempo = tiempo_div.get_text(strip=True) if tiempo_div else "N/A"

        invocador_elements = mensaje_div.find_all('span', class_='name')
        campeon_elements = mensaje_div.find_all('img', alt=True)

        if len(campeon_elements) >= 1 and len(invocador_elements) >= 1:
            campeon = campeon_elements[0]['alt']
            invocador = invocador_elements[0].get_text(strip=True).lower()
        else:
            campeon, invocador = "N/A", "N/A"

        # Determinar el equipo del invocador
        if invocador in equipo_azul_invocadores:
            lado = "Equipo Azul"
        elif invocador in equipo_rojo_invocadores:
            lado = "Equipo Rojo"
        else:
            lado = "N/A"

        # Determinar si el invocador pertenece al equipo especificado
        pertenece_al_equipo = "yes" if invocador in [i.lower() for i in invocadores_equipo] else "no"

        if "Primera Sangre" in evento_texto:
            eventos.append([partida_numero, tiempo, "Primera Sangre", invocador, campeon, "N/A", "N/A", lado, pertenece_al_equipo])
        elif "Primera Torre" in evento_texto:
            eventos.append([partida_numero, tiempo, "Primera Torre", invocador, campeon, "Torre", "N/A", lado, pertenece_al_equipo])
        elif "Dragón Asesinado" in evento_texto:
            eventos.append([partida_numero, tiempo, "Dragón Asesinado", invocador, campeon, "Dragón", "N/A", lado, pertenece_al_equipo])
        elif "Horda Asesinado" in evento_texto:
            eventos.append([partida_numero, tiempo, "Larva Asesinada", invocador, campeon, "Horda", "N/A", lado, pertenece_al_equipo])
        elif "Barón Asesinado" in evento_texto:
            eventos.append([partida_numero, tiempo, "Barón Asesinado", invocador, campeon, "Barón", "N/A", lado, pertenece_al_equipo])
        elif "Primera Torreta Destruida" in evento_texto:
            eventos.append([partida_numero, tiempo, "Primera Torreta Destruida", invocador, campeon, "Torreta", "N/A", lado, pertenece_al_equipo])

    return eventos

# Escribir los eventos en un archivo CSV
def escribir_eventos_csv(eventos, file_path):
    # Si el archivo ya existe, eliminarlo para comenzar desde cero
    if os.path.exists(file_path):
        os.remove(file_path)

    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        # Escribir encabezados
        csvwriter.writerow(["Partida", "Tiempo", "Evento", "Invocador", "Campeón", "Objetivo", "Invocador Objetivo", "Lado", "Team"])
        # Escribir datos
        for evento in eventos:
            csvwriter.writerow(evento)

# Proceso principal para extraer los eventos importantes de cada partida
def procesar_partidas():
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

            escribir_eventos_csv(eventos, OUTPUT_CSV_FILE)
        except Exception as e:
            print(f"Error abriendo el enlace de partida {partida_numero}: {e}")
        
        partida_numero += 1

# Ejecutar el script
try:
    procesar_partidas()
finally:
    driver.quit()
