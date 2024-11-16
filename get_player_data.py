import csv
import os
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

# Importar variables desde config.py
from config import EDGE_DRIVER_PATH, INVOCADORES, TEAM_NAME

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
csv_file = "game_details.csv"

# Escribir la cabecera del archivo CSV
with open(csv_file, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow([
        "Partida", "Resultado", "Duración", "Nombre Invocador", "SoloQ", "OP Score" , "Game Rank" , 
        "Campeón Utilizado", "Nivel Campeón", "Hechizo 1", "Hechizo 2", "Runa 1", "Runa 2", "Kills", "Deaths", "Assists", 
        "KP", "KDA Ratio", "Daño Realizado", "Daño Recibido", "Control Wards", "Centinelas Colocados", "Centinelas Destruidos", 
        "CS Total", "CS por Min", "Item 1", "Item 2", "Item 3", "Item 4", "Item 5", "Item 6", "Trinket", "Team", "Side", "Rol"
    ])

# Arreglo de invocadores del equipo
invocadores_equipo = INVOCADORES

def extraer_resultado_y_duracion():
    try:
        resultado = driver.find_element(By.CSS_SELECTOR, 'div.result').text
    except NoSuchElementException:
        resultado = "N/A"

    try:
        duracion = driver.find_element(By.CSS_SELECTOR, 'div.length').text
        # Añadir '0:' al principio para representar horas si es necesario
        duracion = f"0:{duracion.replace(' ', ':')}"
    except NoSuchElementException:
        duracion = "N/A"
    return resultado, duracion

def extraer_nombre_invocador(jugador_element):
    try:
        return jugador_element.find_element(By.CSS_SELECTOR, 'td.name span').text.lower()
    except NoSuchElementException:
        return "N/A"

def extraer_campeon_y_nivel(jugador_element):
    try:
        campeon_icon = jugador_element.find_element(By.CSS_SELECTOR, 'div img')
        campeon_utilizado = campeon_icon.get_attribute("alt")
        nivel_campeon = jugador_element.find_element(By.CLASS_NAME, 'level').text
    except NoSuchElementException:
        campeon_utilizado, nivel_campeon = "N/A", "N/A"
    return campeon_utilizado, nivel_campeon

def extraer_hechizos(jugador_element):
    try:
        hechizos_elements = jugador_element.find_elements(By.CSS_SELECTOR, 'td.spells img')
        hechizo_1 = hechizos_elements[0].get_attribute("alt") if len(hechizos_elements) > 0 else "N/A"
        hechizo_2 = hechizos_elements[1].get_attribute("alt") if len(hechizos_elements) > 1 else "N/A"
    except NoSuchElementException:
        hechizo_1, hechizo_2 = "N/A", "N/A"
    return hechizo_1, hechizo_2

def extraer_runas(jugador_element):
    try:
        runas_elements = jugador_element.find_elements(By.CSS_SELECTOR, 'td.runes img')
        runa_1 = runas_elements[0].get_attribute("alt") if len(runas_elements) > 0 else "N/A"
        runa_2 = runas_elements[1].get_attribute("alt") if len(runas_elements) > 1 else "N/A"
    except NoSuchElementException:
        runa_1, runa_2 = "N/A", "N/A"
    return runa_1, runa_2

def extraer_rango_soloq(jugador_element):
    try:
        # Extraer el elemento div que contiene el rango de SoloQueue
        rango_element = jugador_element.find_element(By.CSS_SELECTOR, 'td.name div.tier div')
        rango_soloqueue = rango_element.text if rango_element else "N/A"
    except NoSuchElementException:
        rango_soloqueue = "Unranked"
    return rango_soloqueue

def extraer_op_score(jugador_element):
    try:
        # Extraer el elemento div que contiene el OP Score
        score_element = jugador_element.find_element(By.CSS_SELECTOR, 'td.op-score-wrapper div.op-score div.score')
        op_score = score_element.text if score_element else "N/A"
    except NoSuchElementException:
        op_score = "N/A"
    return op_score

def extraer_game_rank(jugador_element):
    try:
        # Extraer el elemento div que contiene el Game Rank
        rank_element = jugador_element.find_element(By.CSS_SELECTOR, 'td.op-score-wrapper div.op-score div.rank div')
        game_rank = rank_element.text if rank_element else "N/A"
    except NoSuchElementException:
        game_rank = "N/A"
    return game_rank

def extraer_kda(jugador_element):
    try:
        kda_element = jugador_element.find_element(By.CSS_SELECTOR, 'td.kda div.k-d-a').text
        try:
            kills, deaths, assists_with_kp = kda_element.split("/")
            assists, kp = assists_with_kp.split(" (")
            kp = kp.replace("%)", "").strip()
        except ValueError:
            kills, deaths, assists, kp = "N/A", "N/A", "N/A", "N/A"
        try:
            deaths_value = int(deaths)
            kills_value = int(kills)
            assists_value = int(assists)
            if deaths_value == 0:
                kda_ratio_element = "PERFECT"
            else:
                kda_ratio_element = f"{((kills_value + assists_value) / deaths_value):.2f}:1"
        except ValueError:
            kda_ratio_element = "N/A"
    except NoSuchElementException:
        kills, deaths, assists, kp, kda_ratio_element = "N/A", "N/A", "N/A", "N/A", "N/A"
    return kills, deaths, assists, kp, kda_ratio_element

def extraer_daño(jugador_element):
    try:
        daño_realizado = jugador_element.find_element(By.CLASS_NAME, 'dealt').text.replace(",", "")
        daño_recibido = jugador_element.find_element(By.CLASS_NAME, 'taken').text.replace(",", "")
    except NoSuchElementException:
        daño_realizado, daño_recibido = "N/A", "N/A"
    return daño_realizado, daño_recibido

def extraer_wards(jugador_element):
    try:
        ward_element = jugador_element.find_element(By.CLASS_NAME, 'ward')
        ward_divs = ward_element.find_elements(By.TAG_NAME, 'div')
        if len(ward_divs) >= 2:
            all_values = ward_element.text.replace("\n", "/")
            values = all_values.split("/")
            if len(values) == 3:
                control_wards = values[0].strip()
                centinelas_colocados = values[1].strip()
                centinelas_destruidos = values[2].strip()
            else:
                control_wards, centinelas_colocados, centinelas_destruidos = "N/A", "N/A", "N/A"
            control_wards = int(control_wards) if control_wards.isdigit() else "N/A"
            centinelas_colocados = int(centinelas_colocados) if centinelas_colocados.isdigit() else "N/A"
            centinelas_destruidos = int(centinelas_destruidos) if centinelas_destruidos.isdigit() else "N/A"
        else:
            control_wards, centinelas_colocados, centinelas_destruidos = "N/A", "N/A", "N/A"
    except NoSuchElementException:
        control_wards, centinelas_colocados, centinelas_destruidos = "N/A", "N/A", "N/A"
    return control_wards, centinelas_colocados, centinelas_destruidos

def extraer_cs(jugador_element):
    try:
        cs_element = jugador_element.find_element(By.CLASS_NAME, 'cs')
        cs_divs = cs_element.find_elements(By.TAG_NAME, 'div')
        if len(cs_divs) >= 2:
            cs_total = cs_divs[0].text.strip()
            cs_por_min = cs_divs[1].text.split()[0].strip()
        else:
            cs_total, cs_por_min = "N/A", "N/A"
    except NoSuchElementException:
        cs_total, cs_por_min = "N/A", "N/A"
    return cs_total, cs_por_min

def extraer_items(jugador_element):
    try:
        # Extraer todos los elementos de ítems
        items_elements = jugador_element.find_elements(By.CSS_SELECTOR, 'td.items div.item')
        
        # Inicializar lista de ítems y el trinket
        items = []
        trinket = "N/A"
        
        # Recorrer los elementos y separar ítems y trinket
        for item_element in items_elements:
            try:
                img_element = item_element.find_element(By.TAG_NAME, 'img')
                alt_text = img_element.get_attribute("alt") if img_element else "N/A"
                if "item--trinket" in item_element.get_attribute("class"):
                    trinket = alt_text  # Identificar el trinket
                else:
                    items.append(alt_text)  # Añadir a la lista de ítems normales
            except NoSuchElementException:
                continue
        
        # Rellenar con "N/A" si hay menos de 6 ítems
        items += ["N/A"] * (6 - len(items))
        
        # Añadir el trinket como el séptimo ítem
        items.append(trinket)
    except Exception as e:
        items = ["N/A"] * 7
        print(f"Error general al extraer ítems: {e}")  # Debugging output
    return items


# RUN
try:
    # Recorrer cada enlace de partida
    for partida_idx, enlace in enumerate(enlaces_partidas, start=1):
        try:
            print(f"Abriendo enlace de partida {partida_idx}: {enlace}")
            driver.get(enlace)
            wait = WebDriverWait(driver, 15)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            resultado, duracion = extraer_resultado_y_duracion()
            equipos_elements = driver.find_elements(By.CSS_SELECTOR, 'div.css-10e7s6g.ehma9yf0 table.e13yshnv0')
            sides = ["blue", "red"]

            with open(csv_file, "a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                for side_idx, equipo_element in enumerate(equipos_elements):
                    jugadores_elements = equipo_element.find_elements(By.TAG_NAME, "tr")[1:]
                    for jugador_idx, jugador_element in enumerate(jugadores_elements):
                        try:
                            nombre_invocador = extraer_nombre_invocador(jugador_element)
                            rango_soloqueue = extraer_rango_soloq(jugador_element)
                            game_rank = extraer_game_rank(jugador_element)
                            op_score = extraer_op_score(jugador_element)
                            campeon_utilizado, nivel_campeon = extraer_campeon_y_nivel(jugador_element)
                            hechizo_1, hechizo_2 = extraer_hechizos(jugador_element)
                            runa_1, runa_2 = extraer_runas(jugador_element)
                            kills, deaths, assists, kp, kda_ratio_element = extraer_kda(jugador_element)
                            daño_realizado, daño_recibido = extraer_daño(jugador_element)
                            control_wards, centinelas_colocados, centinelas_destruidos = extraer_wards(jugador_element)
                            cs_total, cs_por_min = extraer_cs(jugador_element)
                            items = extraer_items(jugador_element)

                            team = TEAM_NAME if nombre_invocador in invocadores_equipo else "none"
                            side = sides[side_idx]
                            roles = ["TOP", "JG", "MID", "ADC", "SUPP"]
                            rol = roles[jugador_idx] if jugador_idx < len(roles) else "N/A"

                            writer.writerow([
                                partida_idx, resultado, duracion, nombre_invocador, rango_soloqueue, op_score, game_rank, 
                                campeon_utilizado, nivel_campeon, hechizo_1, hechizo_2, runa_1, runa_2, kills, deaths, assists, 
                                kp, kda_ratio_element, daño_realizado, daño_recibido, control_wards, centinelas_colocados, centinelas_destruidos,
                                cs_total, cs_por_min, *items, team, side, rol
                            ])

                        except Exception as e:
                            print(f"Error procesando el jugador en la partida {partida_idx}: {e}")

        except Exception as e:
            print(f"Error abriendo el enlace de partida {partida_idx}: {e}")

finally:
    driver.quit()