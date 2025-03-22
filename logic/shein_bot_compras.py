import os
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.common.action_chains import ActionChains
from data.shein_processor import SheinBotProcessor
from data.dat_bug_logs import BugLogogger
from bs4 import BeautifulSoup
import json
import re
from datetime import date

class SheinBotCompras():

    def __init__(self, language='en_US', gui_callback=None):
        self.language = language
        self.headless=True
        self.gui_callback = gui_callback
        self.driver = None
        self.url_base = "https://www.shein.com/"
        self.url_base_usa="https://us.shein.com/"
        self.soup = None
        self.logger = BugLogogger()
        self.on_device_process = 'vps1'
        self.batch_size = 12
        self.sku_detail = []
        self.sku_data = []
        self.lenght_sku_list = None
        self.affected_rows = 0
        # self.images_path = os.getenv('IMAGES_PATH')
        # self.domain_path = os.getenv('DOMAIN_LOCAL')
        #self.account_shein=os.getenv('ACCOUNT_SHEIN')
        #self.password_shein=os.getenv('PASSWORD_SHEIN')
        self.url_complete=None
        self.is_found=None
        self.not_processed=[]
        self.proces = SheinBotProcessor()
        self.close_popup_cockies=False
        self.is_login=False
        self.is_close_modalv2=False
        self.is_close_modal=False
        self.is_close_banner=False
        self.is_set_size=False
        self.html_bs4=None
        self.is_login=False
        



    def init_driver(self):

        if self.driver is not None:
            try:
                if self.driver.window_handles:  # Comprueba si hay ventanas abiertas
                    self.gui_callback("El WebDriver ya está en ejecución. Reutilizando...")
                    return self.driver
            except Exception as e:
                self.gui_callback("El WebDriver se cerró inesperadamente. Reiniciando...")
                self.driver = None 

        """ Inicializa el WebDriver con las opciones deseadas """
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            'Accept': "*/*",
            'Accept-Language': self.language,
            'Accept-Encoding': "gzip,deflate,br",
            'Connection': "keep-alive"
        }
        selenium_url = 'http://selenium:4444/wd/hub'
        opts = Options()
        #opts.add_argument("--headless")
        if not self.headless:
            opts.add_argument("--headless")  
        opts.add_argument("--start-maximized")
        opts.add_argument("--disable-notifications")
        #opts.add_argument("--lang=" + self.language)
        #INIT Por Pedro 
        opts.add_experimental_option('detach',True)
        opts.add_experimental_option('excludeSwitches',['enable-automation'])
        opts.add_experimental_option('useAutomationExtension',False)
        opts.add_argument('--disable-blink-features=AutomationControlled')
        opts.add_argument('--disable-infobars')
        opts.add_argument('--disable-browser-side-navigation')
        #END
        opts.add_argument("--disable-backgrounding-occluded-windows")  
        opts.add_argument("--disable-renderer-backgrounding")  
        opts.add_argument("--disable-background-timer-throttling") 
        #
        opts.add_argument("--lang=es-ES")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-extensions")
        opts.add_argument("--disable-software-rasterizer")  # Nueva opción para reducir tiempos de carga
        opts.add_argument("--no-sandbox")  # Mejora el rendimiento en algunos entornos
        opts.add_argument("--disable-dev-shm-usage")  # Mejora en sistemas con poca memoria compartida
        #opts.add_argument("--disk-cache-dir=/tmp/cache")  # Redireccionar caché para mejorar tiempos
        
        opts.add_argument("--ignore-certificate-errors")
        opts.add_argument(f'User-agent={headers["User-Agent"]}')
        opts.add_experimental_option("prefs", {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False
        })  

        # Intenta conectarte al servidor de Selenium
        # driver= webdriver.Remote(
        #     command_executor=selenium_url,
        #     options=opts
        # )
        self.driver= webdriver.Chrome(options=opts)
        #self.driver = driver
        return self.driver
    
    



    # def guardar_cookies(self, archivo="cookies.pkl"):
    #     """ Guarda las cookies en un archivo """
    #     cookies = self.driver.get_cookies()
    #     with open(archivo, 'wb') as archivo_cookies:
    #         pickle.dump(cookies, archivo_cookies)

    # def guardar_session_storage(self, archivo="session_storage.pkl"):
    #     """ Guarda el sessionStorage en un archivo """
    #     session_storage = self.driver.execute_script('return window.sessionStorage;')
    #     with open(archivo, 'wb') as archivo_storage:
    #         pickle.dump(session_storage, archivo_storage)


    # def cargar_cookies(self, archivo="cookies.pkl"):
    #     """ Carga las cookies desde un archivo y las agrega al navegador """
    #     try:
    #         with open(archivo, 'rb') as archivo_cookies:
    #             cookies = pickle.load(archivo_cookies)
    #             for cookie in cookies:
    #                 self.driver.add_cookie(cookie)
    #     except FileNotFoundError:
    #         print("No se encontraron cookies guardadas.")

    # def cargar_session_storage(self, archivo="session_storage.pkl"):
    #     """ Carga el sessionStorage desde un archivo """
    #     try:
    #         with open(archivo, 'rb') as archivo_storage:
    #             session_storage = pickle.load(archivo_storage)
    #             for key, value in session_storage.items():
    #                 self.driver.execute_script(f"window.sessionStorage.setItem('{key}', '{value}');")
    #     except FileNotFoundError:
    #         print("No se encontraron datos de sessionStorage guardados.")

    def affected_data(self):
        return self.affected_rows
    
    def updated_rows(self, affected : int):
        
        if self.affected_rows is None:
            self.affected_rows = 0 
        self.affected_rows += affected

    def get_data_process(self,platform:str='Shein',from_app:str='vps1',data=None):

        
        if not data:
            self.gui_callback("No se encontraron datos para procesar", error=True)
            return

        # Crear lista de SKUs para enviar a la BD
        sku_list = [{"SKU": item["SKU"]} for item in data]
        #print("sku_list", sku_list)

        # Obtener los datos de la BD
        response_db = self.proces.get_data_shein_by_skus(sku_list)
        if response_db is None or len(response_db) == 0:
            self.gui_callback("Error al obtener los datos de la BD", error=True)
            return
        #print("response_db", response_db)

        # Crear un diccionario con SKU como clave y un diccionario con 'product_id' y 'size' como valor
        sku_dict = {item["SKU"]: {"product_id": item["product_id"], "size": item["size"],"sku_code":item["sku_code"]} for item in response_db}
        #print("sku_dict", sku_dict)

        # Agregar 'product_id' y 'size' a cada elemento de data
        for item in data:
            item.update(sku_dict.get(item["SKU"], {"product_id": None, "size": None,"sku_code":None}))

        response = data

        if response:
            self.set_sku_data_list(response)
        else:
           #print("No se encontraron datos para procesar")
            self.gui_callback("No se encontraron datos para procesar", error=True)
            return
        
        if self.is_login == False:
            self.is_login=self.ingresar_datos_cuenta()
            
        if self.is_login:
            return self.process_skus_data()
        else:
            #print("Error al ingresar datos de la cuenta")
            self.gui_callback("Error al ingresar datos de la cuenta", error=True)
            return



    def set_sku_data_list(self, data):
        self.sku_data=None
        self.sku_data = [{**item, "Resultado": None} for item in data]


    def process_skus_data(self):
        sku_list= self.get_sku_data_list()

        if not sku_list:
            return
        self.lenght_sku_list = len(sku_list)

        self.gui_callback(f"Procesando {self.lenght_sku_list} SKUs", error=False)

        for data_sdk in sku_list:
            self.gui_callback(f"Procesando SKU {data_sdk['SKU']} {data_sdk['product_id']}", error=False)

        try:
            for index,data in enumerate(sku_list):

                if data.get("product_id", None).strip(): #and bool(int(data.get("is_parent", False))):
                    url=self.url_base+f"product-p-{data['product_id']}.html?languaje=es"
                    self.url_complete=self.url_base_usa+f"product-p-{data['product_id']}.html"
                    self.driver.get(self.url_complete)
                    self.gui_callback(f"-------- Procesando SKU {data['SKU']} ---------- ", error=False)
                    #self.driver.execute_script("document.body.style.zoom='80%'")
                    self.automatizacion(index)
                    self.url_complete=None
                    self.html_bs4=None
                    if index == self.lenght_sku_list - 1:
                        self.gui_callback("Accediendo a CHECKOUT PARA PRECIOS ", error=False)
                        self.process_price_in_checkout()
                else:
                    #print("no se encontro el product id")
                    self.sku_data[index]["Resultado"] = "no se encontro el product id en la BD"
                    self.not_processed.append(data)
            return self.sku_data
            #self.sku_data=None
        except Exception as e:
            self.gui_callback("Error al actualizar los datos", error=True)
            self.logger.createLog("Error al actualizar los datos", "ERROR", "SheinBuyBot", str(e))
            
            return None

    def get_sku_data_list(self):
        return  self.sku_data


    def esperar_captcha(self):
        """
        Espera hasta que el captcha sea resuelto. Si no se resuelve en 5 minutos, se registra un log y se continúa.
        """
        tiempo_maximo = 300  # 5 minutos
        intervalo_chequeo = 5  # Cada 5 segundos
        tiempo_transcurrido = 0

        #print("Esperando resolución del captcha...")
        self.gui_callback("Captcha detectado. Esperando resolución...", error=True)

        while "captcha" in self.driver.current_url:
            if tiempo_transcurrido >= tiempo_maximo:
                #print("Tiempo límite alcanzado. Continuando con la siguiente iteración...")
                self.gui_callback("Tiempo límite alcanzado. Saltando iteración...", error=True)
                return False
            time.sleep(intervalo_chequeo)
            tiempo_transcurrido += intervalo_chequeo

        #print("Captcha resuelto, continuando ejecución...")
        self.gui_callback("Captcha resuelto, continuando ejecución...", error=False)
        return True


    def cambiar_tipo_talla(self):

        if self.is_set_size:
            return True
        try:

            
            # Localiza el contenedor del selector de tipo de talla
            tipo_talla = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@class="common-local-size__country"]'))
            )

            # Obtiene el texto dentro del contenedor
            tipo_talla_texto = tipo_talla.text.strip().lower()

            # Si ya contiene "tipo" o "por defecto", no hace nada
            if "tipo" in tipo_talla_texto or "por defecto" in tipo_talla_texto or "type" in tipo_talla_texto or "default" in tipo_talla_texto:
                self.gui_callback("Tipo de talla ya está configurado correctamente.")
                self.is_set_size=True
                return True

            container = self.driver.find_element(By.XPATH, '//div[@class="product-intro__size-choose"]')
            self.driver.execute_script("""
                var element = arguments[0];
                var rect = element.getBoundingClientRect();
                var absoluteElementTop = rect.top + window.pageYOffset;
                var middle = absoluteElementTop - (window.innerHeight / 2) + (rect.height / 2);
                window.scrollTo({ top: middle, behavior: 'smooth' });
            """, container)
            # Si no tiene el texto deseado, hace clic para abrir el dropdown
            self.gui_callback("Abriendo selector de tipo de talla...")
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(tipo_talla)
            ).click()

            # Espera a que aparezca el dropdown con el ul
            dropdown_opciones = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//ul[@class="common-local-size__country-box"]'))
            )

            # Localiza el primer li dentro del dropdown
            primer_li = dropdown_opciones.find_element(By.XPATH, './li[1]')

            # Obtiene el texto del primer li
            primer_li_texto = primer_li.text.strip().lower()

            # Si el primer li contiene "por defecto" o "tallas por defecto", hace clic en él
            if "por defecto" in primer_li_texto or "tallas por defecto" in primer_li_texto:
                self.gui_callback(f"Seleccionando opción: {primer_li_texto}")
                WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(primer_li)
                ).click()
            else:
                self.gui_callback(f"Opción no encontrada: {primer_li_texto}", error=True)
                return False

            self.is_set_size=True
            return True

        except Exception as e:
            self.gui_callback(f"Error en cambiar_tipo_talla: {e}", error=True)
            return False
        

    def automatizacion(self,index):

        current_sku=self.sku_data[index]
        current_sku["Precio Compra"]="0.0"

        #self.process_price_in_checkout()


        if current_sku["SKU"] == "" or current_sku["SKU"] == None:
            #print("SKU vacío")
            self.gui_callback("SKU vacío", error=True)
            self.not_processed.append(current_sku)
            return
        
        try:
            WebDriverWait(self.driver, 10).until(
                lambda d: "captcha" not in d.current_url
            )
            #print("Acceso al producto exitoso:", self.driver.current_url)
            self.gui_callback("Acceso al producto exitoso", error=False)
        except:
            if self.gui_callback:
                self.gui_callback("Captcha detectado. Resuelve manualmente.", error=True)
            if not self.esperar_captcha():
                return

        # ⏳ **Verifica si el CAPTCHA está presente**
        try:
            captcha_element = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.CLASS_NAME, "captcha_click_wrapper"))
            )
            if captcha_element:
                #print("⚠️ CAPTCHA detectado. Esperando resolución manual...")
                self.gui_callback("CAPTCHA detectado. Esperando resolución manual...", error=True)

                # ⏳ **Espera hasta 5 minutos**
                start_time = time.time()
                while time.time() - start_time < 300:  # 300 segundos = 5 minutos
                    try:
                        # Si el CAPTCHA desaparece, continuamos
                        WebDriverWait(self.driver, 2).until_not(
                            EC.presence_of_element_located((By.CLASS_NAME, "captcha_click_wrapper"))
                        )
                        #print("✅ CAPTCHA resuelto. Continuando...")
                        self.gui_callback("CAPTCHA resuelto. Continuando...", error=False)
                        break
                    except:
                        pass  # Sigue esperando
                else:
                    #print("❌ CAPTCHA no resuelto en 5 minutos. Pasando al siguiente SKU.")
                    self.gui_callback("CAPTCHA no resuelto en 5 minutos", error=True)
                    current_sku["Resultado"] = "CAPTCHA no resuelto"
                    self.not_processed.append(current_sku)
                    return
        except:
            #print("✅ No se detectó CAPTCHA.")
            pass

        if self.validate_not_exists_page():
            #print("Producto no encontrado")
            current_sku["Resultado"] = "producto no encontrado"
            self.gui_callback(f"producto no encontrado", error=True)
            self.not_processed.append(current_sku)
            return

        self.cerrar_modalV2()
        self.close_modal()
        self.close_banner()
        self.close_popup()

        

        self.cambiar_tipo_talla()

        if self.validate_agotado():
            #print("Producto agotado")
            current_sku["Resultado"] = "agotado"
            self.gui_callback("producto agotado", error=True)
            self.not_processed.append(current_sku)
            return
        
        #print("Producto disponible")
        self.gui_callback("producto disponible", error=False)

        #current_sku["precio"] = self.get_price()

        if not self.validate_size(current_sku['size']):
            #print("Talla no disponible")
            current_sku["Resultado"] = "talla no disponible"
            self.gui_callback("talla no disponible", error=True)
            self.not_processed.append(current_sku)
            return
        
        #print("Talla disponible")
        self.gui_callback("talla disponible", error=False)
        cantidad=current_sku['Cantidad']
        if not self.añadir_carrito(cantidad):
            #print("Error al añadir al carrito self.añadir_carrito()")
            current_sku["Resultado"] = "error al añadir al carrito"
            self.gui_callback("error al añadir al carrito", error=True)
            self.not_processed.append(current_sku)
            current_sku['Resultado']="Error al añadir producto"
            return
        
        #print("salio de añadir al carrito")
        self.gui_callback("salio de añadir al carrito", error=False)
        try:
            self.driver.execute_script("window.scrollTo(0, 0)")
            time.sleep(1)
        except Exception as e:
            #print(f"Error en scroll")
            self.gui_callback("Error en scroll", error=True)
            self.not_processed.append(current_sku)
            return
        # if not self.validar_producto_añadido():
        #     print("Producto no añadido al carrito validacion")
        #     current_sku["Resultado"] = "producto no añadido al carrito"
        #     self.gui_callback("producto no añadido al carrito", error=True)
        #     self.not_processed.append(current_sku)
        #     return
        # if not self.page_compra():
        #     print("Error al procesar la página de compra")
        #     self.not_processed.append(current_sku)
        #     return
        self.gui_callback("Producto listo para validar", error=False)

        current_sku["Resultado"] = "añadido al carrito"
        self.updated_rows(1)
        self.driver.implicitly_wait(5)
        

    def get_price(self):

        try:
            #container=self.driver.find_element(By.XPATH,'//div[@class="ProductIntroHeadPrice__head-mainprice"]')
            #precio_total=container.find_element(By.XPATH,'.//div[@class="from original"]/span')
            container=self.driver.find_element(By.XPATH,'//div[@class="price-estimated-percent"]')
            precio_total=container.find_element(By.XPATH,'.//div[@class="price-estimated-percent__retail"]/span')
            self.gui_callback("Precio obtenido correctamente", error=False)
            return precio_total.text
        except Exception as e:
            #print(f"Error al obtener el precio: {str(e)}")
            self.gui_callback("Error al obtener el precio", error=True)
            return "0.0"


    def validate_not_exists_page(self):

        try:
            container=self.driver.find_element(By.XPATH,'//div[@class="c-error-404 j-error-vue"]')

            if container.is_displayed():
                return True
            
            return False
        except Exception as e:
            return False

    def click_para_checkout_validar_data(self):
        try:
            container=self.driver.find_element(By.XPATH,'//div[@class="c-order-summary"]')

            #precio_total=container.find_element(By.XPATH,'.//div[@class="summary-item total-item"]/div')

            button=WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@class="check-btn"]//button[@class="sui-button-common sui-button-common__primary sui-button-common__H54PX j-cart-check incentive-button"]'))
            )

            button.click()
            #print("Botón de checkout clickeado correctamente.")
            return True
        except Exception as e:

            #print(f"Error al validar el checkout: {str(e)}")
            return False

    
    def ingresar_datos_cuenta(self):

        try:
            url_login="https://us.shein.com/user/auth/login"
            self.driver.get(url_login)

            self.gui_callback("Ingresa datos de la cuenta", error=False)
            current_url=self.driver.current_url
            contador=1
            while "login" in current_url:
                print("en login")
                time.sleep(1)
                self.gui_callback(f"Esperando carga de la cuenta ({contador})", error=False)
                contador+=1
                current_url=self.driver.current_url

            if "login" not in current_url:
                self.is_login = True
                return True


        except Exception as e:
            print(f"Error al ingresar datos de la cuenta: {str(e)}")
            self.gui_callback("Error al ingresar datos de la cuenta", error=True)
            return False
        


    def procesar_pago_and_checkout_price(self):

        try:


            container=WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@id="checkPayment"]'))
            )

            payment_list=container.find_element(By.XPATH, './/div[@class="payment-list"]')

            opciones_pagos=payment_list.find_elements(By.XPATH, './/div[@class="payment-item payment-ideal"]')


            for opcion in opciones_pagos:
                print(opcion.text)

    
            btn_pago=WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@class="c-order-summary"]//button[@class="sui-button-common sui-button-common__primary sui-button-common__H54PX"]'))
            )

            btn_pago.click()
            print("Botón de pago clickeado correctamente.")




        except Exception as e:
            print(f"Error al procesar el pago y el precio del checkout: {str(e)}")
            return False
            

    def set_quantity(self, quantity):
        try:
            # Espera explícita para localizar el input
            input_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@class="bsc-cart-item-goods-qty__input-wrap"]//input[@class="bsc-cart-item-goods-qty__input"]'))
            )

            # Limpia el campo antes de escribir
            input_element.clear()

            # Escribe el nuevo valor
            input_element.send_keys(str(quantity))

            print(f"Cantidad {quantity} escrita correctamente en el input.")
            return True

        except Exception as e:
            print(f"Error al escribir en el input: {e}")
            return False


    def close_popup(self):

        if self.close_popup_cockies:
            return


        try:
            element=self.driver.find_element(By.XPATH, '//div[@class="cmp_c_1100"]//div[contains(text(), "Aceptar Todo")]')
        except Exception as e:
            self.close_popup_cockies=True
            return

        try:
            # Esperar a que el popup sea visible
            popup = WebDriverWait(self.driver, 2).until(
                EC.visibility_of_element_located((By.XPATH, "//div[@class='cmp_c_1100']//div[contains(text(), 'Aceptar Todo')]"))
            )

            if not popup.is_displayed():
                return 
            popup.click()
            print("Popup cerrado o aceptado.")
            self.close_popup_cockies=True
        
        except Exception as e:
            self.close_popup_cockies=True
            print("No se pudo cerrar el popup o no estaba presente:", e)


    def page_compra(self):

        url=self.driver.current_url
        try:

            ir_pagina_compra = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@class="header-icon not-fsp-element"]//div[@class="bsc-mini-cart__trigger j-bsc-mini-cart__trigger"]'))
            )
            ir_pagina_compra.click()
            self.driver.implicitly_wait(5)
            if self.driver.current_url == url:
                return False
            
            return True
        
        except Exception as e:
            print(f"Error al procesar la página de compra: {str(e)}")
            return False



    def añadir_carrito(self, cantidad):
        print("Dentro de añadir carrito")
        self.gui_callback(f"Añadiendo al carrito {cantidad} productos", error=False)


        #hacer hover a una imagen sino el modal del carrito se queda pegado 
        try:
            cantidad = int(cantidad)

            # Esperar hasta que el botón de añadir al carrito sea clickeable
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@class="product-intro__add-btn btn-main"]'))
            )
            add_cart_button = self.driver.find_element(By.XPATH, '//div[@class="product-intro__add-btn btn-main"]')
            self.gui_callback("Botón de añadir al carrito encontrado", error=False)

            for _ in range(cantidad):
                add_cart_button.click()
                print("Producto clickeado")
                self.driver.execute_script("window.scrollTo(0, 0)")
                time.sleep(2)
                if add_cart_button.text.upper().strip() == 'AGOTADO' or add_cart_button.text.upper().strip() == 'SOLD OUT':
                    print("Producto agotado")
                    self.gui_callback("Producto agotado", error=True)
                    return False
                container_sizes = self.driver.find_element(By.XPATH, '//div[@class="product-intro__size-choose"]') 

                if container_sizes.is_displayed() or container_sizes:

                    self.driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", container_sizes)
                    try:
                        image_element = self.driver.find_element(By.CSS_SELECTOR, ".product-intro__thumbs-item img")
                    # Crea una acción para hacer hover
                    except Exception as e:
                        image_element = None
                    if image_element:
                        actions = ActionChains(self.driver)
                        actions.move_to_element(image_element).perform()
                        # Esperar a que aparezca el banner (que no tenga display: none)
                        try:
                            WebDriverWait(self.driver, 3).until(
                                lambda d: d.find_element(By.XPATH, '//div[@class="bsc-mini-cart__overlay"]').is_displayed()
                            )
                            print("Banner detectado, esperando a que desaparezca...")

                            WebDriverWait(self.driver, 5).until(
                                lambda d: not d.find_element(By.XPATH, '//div[@class="bsc-mini-cart__overlay"]').is_displayed()
                            )
                            print("Banner desapareció, continuando...")
                        except Exception as e:
                            print("No se detectó el banner o desapareció antes de lo esperado")
                else:
                    print("No se detectó el contenedor de tallas")
                    self.gui_callback("No se detectó el contenedor de tallas", error=True)
                    self.gui_callback("verificando si el producto se puede adquirir sin talla", error=False)
                    time.sleep(1)
                    add_cart_button.click()

            return True
        except Exception as e:
            print(f"Error al añadir al carrito: {str(e)}")
            return False

        

    def validar_producto_añadido(self):

        productos_añadidos=0

        print("dentro de validar producto añadido")
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@class="bsc-mini-cart__trigger j-bsc-mini-cart__trigger"]//span[@class="bsc-cart-num"]'))
            )

            data= self.driver.find_element(By.XPATH,'//div[@class="bsc-mini-cart__trigger j-bsc-mini-cart__trigger"]//span[@class="bsc-cart-num"]').text.strip()

            if not data:
                print("Producto no añadido al carrito")
                return False

            if not data.isdigit():
                print("Producto no añadido al carrito")
                return False

            if int(data) > 0:
                if int(data)<productos_añadidos:
                    print("Producto no añadido al carrito")
                    return False
                productos_añadidos+=1
                print("Producto añadido al carrito")
                return True
            else:
                print("Producto no añadido al carrito")
                return False
        except Exception as e:
            print(f"Producto no añadido al carrito. Error: {str(e)}")
            return False

    def validate_agotado(self):
        try:
            content=WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.XPATH, 
                    '//div[@class="goodsDetail-btn-xl__container"]//div[@class="add-cart__btn-contentwithprice type-b"]//div[@class="text add-carttext-style"]'
                    
                ))
            )
            if content.text.upper().strip() == 'AGOTADO' or content.text.upper().strip() == 'SOLD OUT':
                return True

            return False
        except Exception as e:
            print(f" producto puede añadirse al carrito")
            return False


    def cerrar_modalV2(self):
        if self.is_close_modalv2:
            return
        
        try:

            try:
                container=self.driver.find_element(By.XPATH, '//div[@class="dialog-header-v2__close-btn svg"]')
            except Exception as e:
                print(f"Error al intentar cerrar el modal: {e}")
                self.is_close_modalv2=True
                return


            
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".dialog-header-v2__close-btn svg"))
            )

            boton_cerrar = self.driver.find_element(By.CSS_SELECTOR, ".dialog-header-v2__close-btn svg")
            
            # Hacer clic en el botón de cerrar
            boton_cerrar.click()
            print("Modal cerrado con éxito.")
            self.is_close_modalv2=True
        except Exception as e:
            print(f"Error al intentar cerrar el modal: {e}")
            self.is_close_modalv2=True


    def close_modal(self):
        #time.sleep(1)
        if self.is_close_modal:
            return True
        

        try:
            element=self.driver.find_element(By.XPATH, '//div[@class="sui-dialog__body"]//span[@class="sui-icon-common__wrap icon-close homepage-she-close"] | //div[@class="sui-dialog__body"]//div[@class="dialog-header-v2__close-btn"]/*')
        except Exception as e:
            print(f"Error al intentar cerrar el modal: {e}")
            self.is_close_modal=True
            return False

        try:
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.XPATH, '//div[@class="sui-dialog__body"]'))
            )

            # if not element.is_displayed():
            #     return True

            close_button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@class="sui-dialog__body"]//span[@class="sui-icon-common__wrap icon-close homepage-she-close"] | //div[@class="sui-dialog__body"]//div[@class="dialog-header-v2__close-btn"]/*'))
            )
            close_button.click()
            self.is_close_modal=True
            return True
        except (TimeoutException,NoSuchElementException) as e:
            print(f"No se encontró el modal o el botón de cierre. Error:")
            self.is_close_modal=True
            return False



    def validate_size(self,size):

        try:
            try:
                container = self.driver.find_element(By.XPATH, '//div[@class="product-intro__size-choose"]')
                if not container:
                    self.gui_callback("No se encontró el contenedor de tallas", error=True)
                    self.gui_callback("Verificando otro tipo de producto(sin talla)", error=False)
                    return True
                sizes = container.find_elements(By.XPATH, './/span') 
                if sizes is None or len(sizes) == 0:
                    self.gui_callback("No se encontraron tallas", error=True)
                    return True
                
                data_size=sizes[0].text.strip()
                if not data_size or data_size == "":
                    self.gui_callback("No se encontraron tallas", error=True)
                    return True
            except NoSuchElementException as e:
                print(f"Error al intentar validar la talla: {e}")
                return True
            
            self.driver.execute_script("""
                var element = arguments[0];
                var rect = element.getBoundingClientRect();
                var absoluteElementTop = rect.top + window.pageYOffset;
                var middle = absoluteElementTop - (window.innerHeight / 2) + (rect.height / 2);
                window.scrollTo({ top: middle, behavior: 'smooth' });
            """, container)
            time.sleep(1)
            for s in sizes:
                if s.text == size:
                    WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(s))
                    s.click()
                    return True
            return False
        except Exception as e:
            print(f"Error al validar la talla: {str(e)}")
            return False
        

    def close_banner(self):


        if self.is_close_banner:
            return 

        try:
            # Verificar si el div con la clase específica está presente
            banners = self.driver.find_elements(By.XPATH, '//div[@class="c-quick-register j-quick-register c-quick-register-hide c-quick-register__pe"] | //div[@class="c-quick-register j-quick-register c-quick-register-hide c-quick-register__uses"]')

            

            #//div[@class="c-quick-register j-quick-register c-quick-register-hide c-quick-register__uses"]
            if not banners or len(banners) == 0:
                print("El div del banner no está presente. No hay nada que cerrar.")
                self.is_close_banner=True  # No hay banner que cerrar
                return True
            
            # Si el div está presente, intentar cerrar el banner
            close_button = WebDriverWait(self.driver,2).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@class="quickg-outside"]'))
            )
            close_button.click()
            print("Banner cerrado exitosamente.")
            self.is_close_banner=True
            return True
        
        except Exception as e:
            print("No se pudo cerrar el banner:", e)
            self.is_close_banner=True
            return False



    def process_price_in_checkout(self):

        self.driver.get("https://us.shein.com/checkout")
        self.gui_callback("Procesando precios en el checkout", error=False)
        self.driver.implicitly_wait(5)
        fecha_actual = date.today()
        self.html_bs4 = BeautifulSoup(self.driver.page_source, 'html.parser')

        try:
            container = self.html_bs4.find("div", class_="c-outermost-ctn j-outermost-ctn")
            if container:
                script_tag = container.find("script")
                if script_tag and script_tag.string:
                    script_text = script_tag.string
                    data_script = script_text.split("var gbRawData")[0]
                    data_script = data_script.split("gbCheckoutSsrData =")[1]
                    sanitize_data_script = data_script.replace("\n", "")
                    clean_data_script = sanitize_data_script.strip().strip("'")
                    dict_data = json.loads(clean_data_script)
                    id_to_skus = {}
                    groups = dict_data.get("cartsInfo", {}).get("good_business_group", [])
                    #print(f"Total de grupos en cartsInfo: {len(groups)}")

                    for i, group in enumerate(groups):
                        goods_list = group.get("goods", [])
                        #print(f"Grupo {i}: contiene {len(goods_list)} productos")

                        for item in goods_list:
                            sku_code = item.get("skuCode")
                            sku_fallback = item.get("product", {}).get("goods_sn")  # por si acaso
                            item_id = item.get("id")

                            if item_id:
                                skus = []
                                if sku_code:
                                    skus.append(sku_code)
                                if sku_fallback:
                                    skus.append(sku_fallback)
                                id_to_skus[item_id] = skus
                            else:
                                print(f"[ADVERTENCIA] Producto sin ID válido: SKU_CODE={sku_code}, SKU={sku_fallback}, ID={item_id}")

                    #print(f"\nTotal IDs mapeados en id_to_skus: {len(id_to_skus)}")
                    #print(f"IDs: {list(id_to_skus.keys())}\n")

                    # Paso 2: Buscar ID en cartList según sku_code o sku
                    cart_list = dict_data.get("checkout", {}).get("cartList", [])
                    #print(f"Total de items en checkout.cartList: {len(cart_list)}")

                    for index in range(len(self.sku_data)):
                        sku_dict = self.sku_data[index]
                        sku_code = sku_dict.get("sku_code", "")
                        sku_fallback = sku_dict.get("SKU", "")
                        #print(f"Procesando SKU del cliente: sku_code={sku_code}, sku={sku_fallback}")

                        # Buscar coincidencia en id_to_skus
                        matching_id = None
                        for item_id, skus in id_to_skus.items():
                            if sku_code in skus or sku_fallback in skus:
                                matching_id = item_id
                                break

                        if not matching_id:
                            #print(f"[NO MATCH] SKU '{sku_code}' ni '{sku_fallback}' encontrado en ninguna lista de SKUs")
                            continue

                        #print(f"Match encontrado: ID '{matching_id}' para SKU '{sku_code or sku_fallback}'")

                        # Buscar el precio
                        encontrado = False
                        for cart_item in cart_list:
                            if cart_item.get("cartId") == matching_id:
                                price = cart_item.get("priceData", {}).get("unitPrice", {}).get("price", {}).get("amount")
                                if price:
                                    #print(f"[OK] Precio encontrado para ID {matching_id}: {price}")
                                    self.gui_callback(f"SKU {sku_code or sku_fallback} - Precio: {price}", error=False)
                                    self.sku_data[index]["Precio Compra"] = price
                                    self.sku_data[index]["Fecha Compra"] = fecha_actual
                                    self.sku_data[index]["Resultado"] = "añadido al carrito"
                                encontrado = True
                                break
                        if not encontrado:
                            print(f"[NO MATCH] ID '{matching_id}' no encontrado en cartList")

                    # Paso 3: Eliminar campos innecesarios
                    for sku in self.sku_data:
                        for field in ["sku_code", "product_id"]:
                            if field in sku:
                                del sku[field]
        except Exception as e:
            self.gui_callback(f"Error al procesar precios en el checkout: {e}", error=True)
            #print(f"Error: {e}")



    def insert_log(self, sku, message):
        self.logger.createLog(sku, message)

            #cuenta_regresiva = 5
            # for _ in range(5):
            #     self.gui_callback(f"Ingresando datos de la cuenta en {cuenta_regresiva} segundos", error=False)
            #     time.sleep(1)
            #     cuenta_regresiva -= 1
            # if "login" not in current_url:
            #     self.is_login = True
            #     return True
        # current_url=self.driver.current_url
        
        # try:
        #     WebDriverWait(self.driver, 10).until(
        #         EC.presence_of_element_located((By.XPATH, '//div[@class="input_filed-wrapper"]'))
        #     )


        #     container_input=self.driver.find_element(By.XPATH,'//div[@class="email-recommend-input"]')
        #     input_email=container_input.find_element(By.XPATH,'.//input[@class="sui-input__inner sui-input__inner-suffix"]')
        #     input_email.send_keys(self.account_shein)

        #     click_button_continue=self.driver.find_element(By.XPATH,'//div[@class="actions"]//div[@class="login-point_button"]/button')

        #     click_button_continue.click()
        #     time.sleep(1)
        #     container_password=WebDriverWait(self.driver, 10).until(
        #         EC.presence_of_element_located((By.XPATH, '//div[@class="input_filed-text"]'))
        #     )
        #     try:

        #         click_button_continue.click()
        #     except Exception as e:
        #         #print(f"Error al clickear el por 2 vez el botón de continuar: {str(e)}")
        #         return False

        #     try:
        #         input_password_1 = container_password.find_element(By.XPATH, './/div[@class="sui-input"]//input[@class="sui-input__inner sui-input__inner-suffix"]')
        #         input_password_1.send_keys(self.password_shein)
        #     except (ElementNotInteractableException, WebDriverException) as e:
        #         try:
        #             # Si no se puede interactuar con el primero, intentamos con el segundo
        #             input_password_2 = container_password.find_elements(By.XPATH, './/div[@class="sui-input"]//input[@class="sui-input__inner sui-input__inner-suffix"]')[1]
        #             input_password_2.send_keys(self.password_shein)
        #         except (ElementNotInteractableException, WebDriverException) as e:
        #             # Si ambos fallan, lanzamos un error
        #             raise Exception("No se pudo enviar la contraseña a ninguno de los campos.")

        #     click_button_continue_2=self.driver.find_element(By.XPATH,'//div[@class="actions"]//div[@class="login-point_button"]/button')[1]
            

        #     click_button_continue_2.click()
        #     time.sleep(1)
            
        #     if current_url == self.driver.current_url:
        #         print("Error al ingresar datos de la cuenta , no cambió de pagina")
        #         return False

        #self.guardar_cookies()
        #self.guardar_session_storage()

















        # if not self.set_quantity(current_sku['quantity']):
        #     print("Error al establecer la cantidad")
        #     self.not_processed.append(current_sku)
        #     return
        
        
        # print("Cantidad establecida correctamente")
        
        # if self.click_para_checkout_validar_data():
        #     print("Checkout validado")
        # else:
        #     print("Error al validar el checkout")
        #     self.not_processed.append(current_sku)
        #     return
        

        # self.ingresar_datos_cuenta()

        # if self.procesar_pago_and_checkout_price():
        #     print("Pago procesado y precio de checkout validado")
        # else:
        #     print("Error al procesar el pago y el precio del checkout")
        #     self.not_processed.append(current_sku)
        #     return
