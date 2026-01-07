import pandas as pd
import time
import os
import glob
import math
import sys
from dotenv import load_dotenv
import shutil

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException

import concurrent.futures


def descargar_session_individual(session_uid, url_web, ruta_descarga, canal, fechas, opciones, estado):
    
    def esperar_invisibilidad(driver, ruta, timeout=120):
        try:
            WebDriverWait(driver, timeout).until(EC.invisibility_of_element_located((By.XPATH, ruta)))
            return True
        except TimeoutException:
            print(f"[{session_uid}] Demasiada espera por invisibilidad.")
            return True 

    def tipo_elemento(driver, ruta, elemento, timeout=60):
        diccionario = {
            'clickable': WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, ruta))),
            'existente': WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, ruta)))
        }
        return diccionario[elemento]

    def tipo_elemento_css(driver, ruta, elemento, timeout=120):
        diccionario = {
            'css': WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, ruta)))
        }
        return diccionario[elemento]

    def inicio_sesion(driver, user, pwd):
        div_usuario = '/html/body/div/div/div[3]/div/form/div/div[2]/div[1]/div/input'
        div_password = '/html/body/div/div/div[3]/div/form/div/div[2]/div[2]/div/input'
        div_login = '/html/body/div/div/div[3]/div/form/div/div[3]/div[1]/button'
        
        time.sleep(2)
        input_usuario = tipo_elemento(driver, div_usuario, 'existente')
        input_password = tipo_elemento(driver, div_password, 'existente')
        button_login = tipo_elemento(driver, div_login, 'existente')
        #time.sleep(2)
        input_usuario.send_keys(user)
        #time.sleep(2)
        input_password.send_keys(pwd)
        time.sleep(0.5)
        button_login.click()
        time.sleep(2)

    def opciones_div(valor, opcion):
        
        diccionario = {1: 'Client', 2:'Organization', 4: 'From Date', 5: 'To Date', 8: 'Sub Trade Channel'}

        return {'filtro':f"//div[contains(@class, 'filter-modal') or contains(@class, 'ant-modal')]//label[text()='{diccionario[valor]}']/..//input",
                'div_export_filtro':f'/html/body/div[1]/div/div[2]/div[1]/div/div[2]/div[2]/div/div[2]/div[1]/div[1]/div/div/div[2]/div/button[{valor}]'}[opcion]


    def filtro_survey(driver):
        div_filtro_survey = opciones_div(1, 'div_export_filtro')
        boton_filtro_survey = tipo_elemento(driver, div_filtro_survey, 'clickable')
        boton_filtro_survey.click()

    def click_survey(driver):
        xpath_mng = "//div[contains(@data-menu-id, '/SurveyManagement')]"
        xpath_rvw = "//li[contains(@data-menu-id, '/SurveyManagement/SurveyReview')]"

        boton_survey_mng = tipo_elemento(driver, xpath_mng, 'clickable', timeout=30)
        boton_survey_mng.click()
        time.sleep(1)
        boton_survey_rvw = tipo_elemento(driver, xpath_rvw, 'clickable', timeout=30)
        boton_survey_rvw.click()
        filtro_survey(driver)
        

    pag_carga = "//div[contains(@class, 'ant-modal-content')]"
    div_excel = '/html/body/div[3]/div/ul/li[1]'
    div_export = '/html/body/div[1]/div/div[1]/div[2]/button[3]'
    div_filtro = "/html/body/div[1]/div/div[2]/div[1]/div/div[2]/div[2]/div/div[2]/div[1]/div[2]/div[1]/div[3]/div[1]/div[2]/div[1]/div[2]/div/div/div[2]/div[2]/div/span/span"
    div_input_filtro = '/html/body/div[1]/div/div[2]/div[1]/div/div[2]/div[2]/div/div[2]/div[1]/div[2]/div[1]/div[3]/div[3]/div/div[3]/div/div/div/div/div[1]/div/input[1]'
    div_fila_css = "div.ag-row[row-index='0']"

    #NUEVOS PATHS
    #div_apply_filtro_survey = '/html/body/div[4]/div/div/div/div[1]/div/div[3]/button[2]'
    div_apply_filtro_survey = "//button[contains(@class, 'ant-btn') and .//span[text()='Apply Filters']]"

    
    load_dotenv(dotenv_path='credenciales.env')
    usuario_arca = os.getenv('usuario_arca')
    password = os.getenv('contraseña_arca')
    
    driver = None
    ruta_completa_descarga = ruta_descarga + canal

    try:
        print(f"[{session_uid}] Iniciando proceso de descarga...")
        
        options_driver = webdriver.ChromeOptions()
        options_driver.add_argument('--disable-extensions')
        #options_driver.add_argument("--headless=new")

        options_driver.add_experimental_option("prefs", {
            "download.default_directory": ruta_completa_descarga,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })

        driver = webdriver.Chrome(options=options_driver)
        driver.get(url_web)

        inicio_sesion(driver, usuario_arca, password)
        esperar_invisibilidad(driver, pag_carga, timeout=120)
        click_survey(driver)
        time.sleep(1)

        for i in range(2,9):
            if i == 2 or i == 8:
                div_org_c_store = opciones_div(i,'filtro')
                input_org_c_tore = tipo_elemento(driver,div_org_c_store,'clickable')
                input_org_c_tore.send_keys(opciones[math.floor(math.sqrt(i))-1])
                time.sleep(2)
                input_org_c_tore.send_keys(Keys.ENTER)
                time.sleep(1)
            elif i == 4 or i == 5:
                div_fechas = opciones_div(i, 'filtro')
                input_fecha = tipo_elemento(driver, div_fechas,'clickable')
                input_fecha.send_keys(Keys.CONTROL + 'a')
                time.sleep(1)
                input_fecha.send_keys(Keys.CLEAR)
                time.sleep(1)
                input_fecha.send_keys(fechas[i - 4])
                input_fecha.send_keys(Keys.ENTER)
                time.sleep(2)
        
        print("CORRIDA 1")
        button_search = tipo_elemento(driver, div_apply_filtro_survey,'clickable')
        button_search.click()
        time.sleep(5)
        print("CORRIDA 2")
        
        if estado ==  "0":
            #click al botón exportar
            div_export_survey = opciones_div(2, 'div_export_filtro')
            button_export_survey = tipo_elemento(driver, div_export_survey,'clickable')
            button_export_survey.click()
            time.sleep(1)

            #click opcion excel
            button_excel = tipo_elemento(driver,div_excel,'existente')
            button_excel.click()
            
            #AQUI SE ABRE OTRA VENTANA.
            #DEBEMOS CONTAR LAS VENTANAS ACTUALES Y CUANDO HAYA SOLO 1 VENTANA ACTIVA QUIERE DECIR QUE YA SE DESCARGÓ EL EXCEL
            #RECIEN AHI PODREMOS CERRAR EL DRIVER
            #POR MIENTRAS USAREMOS EL TIME SLEEP(8)
            time.sleep(8)

        else:

            filtro = driver.find_element(By.XPATH,div_filtro)
            driver.execute_script("arguments[0].click();", filtro)
            time.sleep(1)

            input_id_session = tipo_elemento(driver,div_input_filtro,'clickable')
            time.sleep(1)
            input_id_session.send_keys(Keys.CONTROL + 'a')
            time.sleep(1)
            input_id_session.send_keys(Keys.DELETE)
            time.sleep(1)
            
            input_id_session.send_keys(session_uid) 
            time.sleep(2)
            input_id_session.send_keys(Keys.ENTER)
            time.sleep(3)

            fila_aparece = tipo_elemento_css(driver, div_fila_css, 'css', timeout=30)
            filas = driver.find_elements(By.CSS_SELECTOR, div_fila_css)
            cod_ventana_principal = driver.current_window_handle
            
            ActionChains(driver).double_click(filas[0]).perform()
            time.sleep(2)
            
            cod_ventanas = driver.window_handles
            if len(cod_ventanas) > 1:
                nueva_ventana = [h for h in cod_ventanas if h != cod_ventana_principal][0]
                driver.switch_to.window(nueva_ventana)

                esperar_invisibilidad(driver, pag_carga, timeout=60)
                time.sleep(3)
                
                button_export = tipo_elemento(driver, div_export,'clickable')
                button_export.click()
                time.sleep(3)
                
                esperar_invisibilidad(driver, pag_carga, timeout=60)
                time.sleep(3)

                driver.close()
                driver.switch_to.window(cod_ventana_principal)
                time.sleep(2)
                
                print(f"[{session_uid}] Descarga finalizada exitosamente.")
                return f"Éxito: {session_uid}"
            else:
                print(f"[{session_uid}] ERROR: No se abrió la ventana secundaria.")
                return f"Fallo: {session_uid} - No se abrió la ventana secundaria."

    except (WebDriverException, TimeoutException) as e:
        print(f"[{session_uid}] FALLO: Error de Selenium o Timeout: {e}")
        return f"Fallo: {session_uid} - Error de Selenium/Timeout."
        
    except Exception as e:
        print(f"[{session_uid}] FALLO: Ocurrió un error inesperado: {e}")
        return f"Fallo: {session_uid} - Error inesperado."
        
    finally:
        if driver:
            driver.quit()


# --- LÓGICA PRINCIPAL DE PRE-PROCESAMIENTO Y EJECUCIÓN PARALELA ---

if __name__ == '__main__':

    def mover_descargas(opcion):
        
        rt2 = f'\{opcion}'
        rt1 = r"C:\Users\bbartolome\Downloads"
        ruta_origen = rt1 + rt2

        if opcion == 'C-STORE':
            ruta_destino = r'C:\Users\bbartolome\Desktop\CODBARRA\CARPETA1'
            #ruta_destino = r'C:\Users\bbartolome\OneDrive - Lock & Asociados\Gestión TI - PROYECTO LINDLEY\PBI-ACL-Archivos\Validador CSTORES_NOV'
        else:
            ruta_destino = r'C:\Users\bbartolome\Desktop\CODBARRA\CARPETA2'
            #ruta_destino = r'C:\Users\bbartolome\OneDrive - Lock & Asociados\Gestión TI - PROYECTO LINDLEY\PBI-ACL-Archivos\ValidarAASS_NOV'


        patron_excel = 'Session_export*.xlsx'
        ruta_patron = os.path.join(ruta_origen, patron_excel)
        archivos_a_mover = glob.glob(ruta_patron)


        if not archivos_a_mover:
            print("No se encontraron archivos")
        else:
            print(f"{len(archivos_a_mover)} archivos encontrados.")
            
            if not os.path.exists(ruta_destino):
                os.makedirs(ruta_destino)
                print("carpeta creada")

            for ruta_origen_archivo in archivos_a_mover:
                
                nombre_archivo = os.path.basename(ruta_origen_archivo)
                ruta_destino_archivo = os.path.join(ruta_destino, nombre_archivo)
                
                try:
                    shutil.move(ruta_origen_archivo, ruta_destino_archivo)

                except Exception as e:
                    print(f"Error al mover {nombre_archivo}: {e}")


    def Canal_Lindley():
        
        while True:
            print("\n--- MENÚ DE CANALES ---")
            print("1. Autoservicio")
            print("2. C-stores")
            print("0. Salir")
            print("------------------------")

            entrada_usuario = input("Ingrese su opción (0 para salir): ").strip()
            
            try:
                opcion = int(entrada_usuario)
                
                if opcion == 0:
                    print("Saliendo del menú de canales.")
                    return None
                elif opcion == 1:
                    return "AUTOSERVICIO"
                elif opcion == 2:
                    return "C-STORE"
                else:
                    print(f"Opción inválida")
            
            except ValueError:
                print(f"Entrada inválida: No es un número. Por favor, ingrese un número.")
                
    
    opcion = Canal_Lindley()
    ruta_descarga = r'C:\Users\bbartolome\Downloads'
    canal = f"\{opcion}"
    
    fechas = ['01/01/2025', '01/06/2025'] #"mm/dd/yyyy"
    opciones = ['',f'{opcion}']
    
    load_dotenv(dotenv_path='credenciales.env')
    url_web = os.getenv('ruta_web')

    # --- 1. PROCESO SECUENCIAL PREVIO (Obtener lista de UIDs) ---
    
    def subir_excel(archivos_encontrados, patron):
        if not archivos_encontrados:
            print(f"No se encontró ningún archivo que coincida con el patrón: {patron}")
            return None
        else:
            archivo_a_cargar = archivos_encontrados[0]
            try:
                df = pd.read_excel(archivo_a_cargar)
                print("Archivo de UIDs maestro cargado exitosamente.")
                return df
            except Exception as e:
                print(f"Error al intentar cargar el archivo: {e}")
                return None
    
    descargar_session_individual("NaN", url_web, ruta_descarga, canal, fechas, opciones, "0")

    try:
        ruta_descargas_carpetas = ruta_descarga + canal
        patron = os.path.join(ruta_descargas_carpetas, 'Survey*.XLSX')
        archivos_encontrados = glob.glob(patron)
        
        Dataframe = subir_excel(archivos_encontrados, patron)
        
        if Dataframe is None:
            sys.exit(1)
            
        Dataframe_validos = Dataframe[(Dataframe['Session Review Status'] != 'Rejected') & (Dataframe['Survey Status'] != 'InComplete')].reset_index(drop=True)
        lista_uids = Dataframe_validos['Session Uid'].tolist()
        
        print(f"--- 1. Éxito: {len(lista_uids)} Session Uids válidos encontrados para descargar ---")

    except Exception as e:
        print(f"ERROR FATAL: Fallo en el pre-procesamiento para obtener la lista de UIDs. {e}")
        sys.exit(1)
    
    
    MAX_PROCESOS = 7 # Número de navegadores/procesos concurrentes

    print(f"\n--- 2. INICIO DE DESCARGAS PARALELAS con {MAX_PROCESOS} procesos ---")


    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_PROCESOS) as executor:
        
        resultados = executor.map(
            descargar_session_individual,
            lista_uids,
            [url_web] * len(lista_uids),
            [ruta_descarga] * len(lista_uids),
            [canal] * len(lista_uids),
            [fechas] * len(lista_uids),
            [opciones] * len(lista_uids),
            ["1"] * len(lista_uids)
        )
        
        for resultado in resultados:
            print(f"Resultado final: {resultado}")
            
    print("\n--- 3. PROCESO PARALELO FINALIZADO ---\n")

    mover_descargas(opcion)



#NOTA FINAL 
#Pensar en abrir multiples pestañas por cada 10 datos de un dataframe que se reflejen en la tabla del survey
