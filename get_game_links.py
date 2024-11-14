import time
import os
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

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

# Nombre del invocador y servidor
summoner_name = "KINGPOWER-ECU"
server = "lan"

# URL del sitio web
url = f"https://www.op.gg/summoners/{server}/{summoner_name}?queue_type=FLEXRANKED"

# Lista de invocadores a buscar
invocadores = ["kingpower", "arielpalma2", "ceress", "IIIPatrocloI", "saidgalan"]

try:
    # Navegar a la URL
    driver.get(url)

    # Esperar hasta que la página se cargue completamente
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Hacer clic en el botón "Mostrar más" varias veces para cargar todas las partidas
    for i in range(10):
        try:
            mostrar_mas_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Mostrar más")]'))
            )
            driver.execute_script("arguments[0].click();", mostrar_mas_button)
            time.sleep(2)
        except (NoSuchElementException, TimeoutException):
            print("El botón 'Mostrar más' no está disponible o ya no hay más partidas para cargar.")
            break

    # Buscar todos los elementos de las partidas
    partidas_elements = driver.find_elements(By.CSS_SELECTOR, "div.css-j7qwjs.e1c5dkji0")

    # Procesar cada partida encontrada
    with open("partidas_links.txt", "w") as file:
        for idx, partida_element in enumerate(partidas_elements):
            try:
                # Verificar si es victoria o derrota usando el valor del elemento div con clase "result"
                try:
                    resultado_element = partida_element.find_element(By.CSS_SELECTOR, 'div.result')
                    resultado_texto = resultado_element.text.strip().lower()
                    print(f"Resultado de la partida {idx}: '{resultado_texto}'")  # Output para verificar el valor exacto
                    if "victory" in resultado_texto or "victoria" in resultado_texto:
                        resultado = "WIN"
                    elif "defeat" in resultado_texto or "derrota" in resultado_texto:
                        resultado = "LOSE"
                    else:
                        print(f"Partida {idx} no es victoria ni derrota. Saltando.")
                        continue
                except NoSuchElementException:
                    print(f"Partida {idx} no contiene información de resultado. Saltando.")
                    continue

                # Comprobar si al menos 3 invocadores están en la partida
                nombres_invocadores = partida_element.text.lower().replace(" ", "").replace("-", "")
                count = sum(1 for inv in invocadores if inv.lower().replace(" ", "").replace("-", "") in nombres_invocadores)
                if count >= 3:
                    # Abrir los detalles de la partida para obtener el enlace
                    try:
                        detalles_button = partida_element.find_element(By.CSS_SELECTOR, 'button.btn-detail')
                        driver.execute_script("arguments[0].click();", detalles_button)
                        time.sleep(2)  # Esperar a que se carguen los detalles

                        # Obtener el enlace del input con clase "copy-link"
                        link_element = partida_element.find_element(By.CSS_SELECTOR, 'input.copy-link')
                        link = link_element.get_attribute("value") if link_element else "N/A"
                    except NoSuchElementException:
                        link = "N/A"

                    # Guardar el índice de la partida y el enlace en el archivo de texto
                    file.write(f"Partida {idx + 1}: {link}\n")
                    print(f"Partida {idx + 1} procesada y agregada.")

            except Exception as e:
                print(f"Error procesando la partida {idx + 1}: {e}")

finally:
    # Cerrar el navegador
    driver.quit()
