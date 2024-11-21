import os
import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# Importar variables desde config.py
from config import EDGE_DRIVER_PATH, SUMMONER_NAME, SERVER, INVOCADORES, BUSCAR_CANT, GAMEMODE

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

# Inicialización del navegador
service = Service(EDGE_DRIVER_PATH)
driver = webdriver.Edge(service=service, options=edge_options)

# Ejecutar JavaScript para sobrescribir navigator.webdriver
driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    'source': '''
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
    '''
})

# URL del sitio web
url = f"https://www.op.gg/summoners/{SERVER}/{SUMMONER_NAME}?queue_type={GAMEMODE}"
print(f"Navegando a URL: {url}")

try:
    # Navegar a la página principal para establecer cookies
    driver.get("https://www.op.gg/")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Luego navegar a la página del invocador
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print("Página cargada exitosamente.")

    # Hacer clic en el botón "Mostrar más" varias veces para cargar todas las partidas
    for i in range(10):
        try:
            mostrar_mas_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Mostrar más")]'))
            )
            mostrar_mas_button.click()
            time.sleep(2)  # Esperar a que se carguen las partidas adicionales
        except TimeoutException:
            print("No se encontró el botón 'Mostrar más' o no hay más partidas para cargar.")
            break

    # Buscar todos los elementos de las partidas
    partidas_elements = driver.find_elements(By.CSS_SELECTOR, "div.css-j7qwjs.e1c5dkji0")
    print(f"Se encontraron {len(partidas_elements)} partidas para procesar.")

    # Procesar cada partida encontrada
    with open("partidas_links.txt", "w") as file:
        for idx, partida_element in enumerate(partidas_elements):
            try:
                # Verificar si es victoria o derrota
                resultado_element = partida_element.find_element(By.CSS_SELECTOR, 'div.result')
                resultado_texto = resultado_element.text.strip().lower()
                if "victory" in resultado_texto or "victoria" in resultado_texto:
                    resultado = "WIN"
                elif "defeat" in resultado_texto or "derrota" in resultado_texto:
                    resultado = "LOSE"
                else:
                    continue

                # Comprobar si al menos N invocadores están en la partida
                invocadores_equipo = partida_element.text.lower().replace(" ", "").replace("-", "")
                count = sum(1 for inv in INVOCADORES if inv.lower().replace(" ", "").replace("-", "") in invocadores_equipo)

                if count >= BUSCAR_CANT:
                    # Abrir los detalles de la partida para obtener el enlace
                    detalles_button = partida_element.find_element(By.CSS_SELECTOR, 'button.btn-detail')
                    detalles_button.click()
                    time.sleep(2)  # Esperar a que se carguen los detalles

                    # Obtener el enlace del input con clase "copy-link"
                    link_element = partida_element.find_element(By.CSS_SELECTOR, 'input.copy-link')
                    link = link_element.get_attribute("value") if link_element else "N/A"

                    # Guardar el índice de la partida y el enlace en el archivo de texto
                    file.write(f"Partida {idx + 1}: {link}\n")
                    print(f"Partida {idx + 1} procesada y agregada al archivo.")

            except NoSuchElementException as e:
                print(f"Error procesando la partida {idx + 1}: {e}")

finally:
    # Cerrar el navegador
    driver.quit()
    print("Navegador cerrado.")
