import csv
import os
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
# Configurar las opciones de Edge
edge_options = Options()
edge_options.add_argument("--start-maximized")
edge_options.add_argument("--log-level=3")  # Silenciar la salida de log del navegador

# Ruta al controlador de Edge WebDriver
EDGE_DRIVER_PATH = r"C:\edgedriver_win64\msedgedriver.exe"

# Verificar si el controlador existe
if not os.path.isfile(EDGE_DRIVER_PATH):
    raise FileNotFoundError(f"El archivo del controlador no se encuentra en la ruta especificada: {EDGE_DRIVER_PATH}")

# Inicialización del navegador
service = Service(EDGE_DRIVER_PATH)
driver = webdriver.Edge(service=service, options=edge_options)

# Leer enlaces de partidas desde archivo de texto
enlaces_partidas = []
with open("partidas_links.txt", "r") as file:
    for line in file:
        if "http" in line:
            enlace = line.split(":", 1)[1].strip()  # Tomar la parte después de ":"
            enlaces_partidas.append(enlace)

# Archivo CSV donde se almacenan los resultados
csv_file = "timeline.csv"

# Escribir la cabecera del archivo CSV
with open(csv_file, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Partida", "Resultado", "Duración"])

def extraer_resultado_y_duracion():
    try:
        resultado = driver.find_element(By.CSS_SELECTOR, 'div.result').text
    except NoSuchElementException:
        resultado = "N/A"

    try:
        duracion = driver.find_element(By.CSS_SELECTOR, 'div.length').text
        duracion = duracion.replace(" ", ":")  # Reemplazar espacio con dos puntos
    except NoSuchElementException:
        duracion = "N/A"
    return resultado, duracion

try:
    # Recorrer cada enlace de partida
    for partida_idx, enlace in enumerate(enlaces_partidas, start=1):
        try:
            print(f"Abriendo enlace de partida {partida_idx}: {enlace}")
            driver.get(enlace)
            wait = WebDriverWait(driver, 15)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            resultado, duracion = extraer_resultado_y_duracion()

            with open(csv_file, "a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow([partida_idx, resultado, duracion])

        except Exception as e:
            print(f"Error abriendo el enlace de partida {partida_idx}: {e}")

finally:
    driver.quit()
