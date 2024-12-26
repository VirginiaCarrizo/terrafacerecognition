import time
import logging
import requests
import keyboard
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bbdd_conection import initialize_firebase  # Configuración de Firebase
from bbdd import actualizar_bd_dni, actualizar_bd_cuil

# Configure logging
logging.basicConfig(level=logging.INFO)

# Global timeouts
TIMEOUT = 30  # Default timeout for Selenium waits
RETRY_INTERVAL = 2  # Interval to sleep between retries for DNI fetching
EC2_REQUEST_TIMEOUT = 10  # Timeout for EC2 requests
FETCH_DNI_MAX_RETRIES = 20

EC2_SERVER_URL = "http://54.81.210.167/get_dni"
# Configurar Firebase
db, bucket = initialize_firebase()

decision_espacio = None


def on_space_press(event):
    global decision_espacio
    if event.name == "space":
        
        decision_espacio = "Volver"  # SI EL USUARIO APRIETA LA BARRA ESPACIADORA POR SI SE ARREPIENTO DE PEDIR
        keyboard.unhook_all()


def fetch_dni(max_retries=FETCH_DNI_MAX_RETRIES, retry_interval=RETRY_INTERVAL):
    """
    Fetches the DNI from the EC2 server within specified timeouts and retry logic.
    """
    retries = 0
    while retries < max_retries:
        try:
    

            response = requests.get(EC2_SERVER_URL, timeout=EC2_REQUEST_TIMEOUT)

            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                logging.info(f"Server response status: {status}")

                if status == 'success':
                    dni = data.get('dni')
                    print(dni)
                    if dni != 0:
                
                        return dni
                    else:
                        logging.warning("DNI not found in response.")
                        return None
                else:
                    logging.info("Status not successful, retrying...")
            # else:
            #     logging.warning(f"Server returned status code {response.status_code}, retrying...")
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")

        retries += 1

        time.sleep(retry_interval)

    logging.error("Max retries reached. Could not fetch DNI.")
    return None


def setup_driver():
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.media_stream_camera": 1,
        "profile.default_content_setting_values.media_stream_mic": 1,
        "profile.default_content_setting_values.geolocation": 1,
        "profile.default_content_setting_values.notifications": 1
    })

    chrome_options.add_argument("--use-fake-ui-for-media-stream")
    chrome_options.add_argument("--ignore-certificate-errors")  
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument('--kiosk-printing')
    chrome_options.add_experimental_option('prefs', {
    'printing.print_preview_sticky_settings.appState': '{"recentDestinations":[{"id":"Save as PDF","origin":"local","account":""}],"selectedDestinationId":"Save as PDF","version":2}',
    'savefile.default_directory': r'C:\Users\virginia.carrizo\Desktop\tickets/'  # Ruta para guardar PDFs automáticamente
    })

    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.maximize_window()

        return driver
    except Exception as e:
        logging.error(f"Failed to initialize WebDriver: {e}")
        raise


def login_to_terragene(driver):
    driver.get("https://terragene.life/terrarrhh/camara")

    # Wait for username and password fields (Timeout applied)
    WebDriverWait(driver, TIMEOUT).until(EC.visibility_of_element_located((By.ID, "username")))

    username_input = driver.find_element(By.ID, "username")
    password_input = driver.find_element(By.ID, "password")

    username_input.send_keys("generalfood")
    password_input.send_keys("generalfood")

    login_button = driver.find_element(By.CSS_SELECTOR, "button.btn")
    login_button.click()


def wait_for_user_capture(driver):
    """
    Waits for a user to accept a JavaScript alert and fetches the DNI.

    We apply a long wait timeout here as this likely involves user interaction.
    """
    try:
        # Webdriver espera a que aparezca el alert
        WebDriverWait(driver, timeout=30).until(lambda d: d.find_element(By.ID, "custom-confirm").is_displayed() or d.find_element(By.ID, "custom-prompt").is_displayed())
        
        # Bloquear ratón
        button = driver.find_element(By.ID, "capture")
        driver.execute_script("arguments[0].disabled = true;", button)

        # Webdriver espera a que desaparezca el alert
        WebDriverWait(driver, timeout=9999999).until(lambda d: EC.invisibility_of_element((By.ID, "custom-confirm"))(d) and EC.invisibility_of_element((By.ID, "custom-prompt"))(d))
        keyboard.block_key('*')  # Bloquea todas las teclas
        logging.info("Teclado y ratón bloqueados.")

        dni = fetch_dni()
        
        print(dni)
        if not dni:
            logging.warning("DNI could not be fetched or was empty.")
        else:
            logging.info(f"Fetched DNI: {dni}")

        # Wait for alert to disappear

        WebDriverWait(driver, 10).until_not(EC.alert_is_present())


        return dni
    except Exception as e:
        logging.error(f"An error occurred during wait_for_user_capture: {e}")
        return None


def fill_terragene_in_movizen(driver):
    driver.get("https://generalfoodargentina.movizen.com/pwa/")

    WebDriverWait(driver, TIMEOUT).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "input[id^='ion-input-']"))
    )

    ion_input = driver.find_element(By.CSS_SELECTOR, "input[id^='ion-input-']")
    time.sleep(1)
    ion_input.send_keys("terragene")
    ion_input.send_keys(Keys.ENTER)
    current_url = driver.current_url
    WebDriverWait(driver, TIMEOUT).until(EC.url_changes(current_url))


    time.sleep(1)


def navigate_and_fill_dni(driver, dni):
    driver.get("https://generalfoodargentina.movizen.com/pwa/inicio")
    
    WebDriverWait(driver, TIMEOUT).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[id^='ion-input-']")))
    
    ion_input = driver.find_element(By.CSS_SELECTOR, "input[id^='ion-input-']")
    ion_input.clear()
    ion_input.send_keys(int(dni))
    ion_input.send_keys(Keys.ENTER)

    inicio = time.time()

    while True:
        current_url = str(driver.current_url)

        if current_url == 'https://generalfoodargentina.movizen.com/pwa/inicio':
            if time.time() - inicio > 2:
                break 

        elif current_url == 'https://generalfoodargentina.movizen.com/pwa/pedido-pc':
           
            script = """
            window.onbeforeprint = function() {
                // Bloqueo silencioso
            };

            window.print = function() {
                // Bloqueo silencioso
            };
            """
            driver.execute_script(script)

            WebDriverWait(driver, 99999).until(EC.url_changes('https://generalfoodargentina.movizen.com/pwa/pedido-pc'))
            driver.execute_script("window.open('about:blank', '_blank');")
            time.sleep(1)
            driver.close()

            driver.switch_to.window(driver.window_handles[-1])

            new_url = "https://generalfoodargentina.movizen.com/pwa/pedido-web-print"
            driver.get(new_url)

            logging.info(dni)
            logging.info(len(dni))

            actualizar_bd_dni(db, int(dni))

            time.sleep(4)
       
            break

def main_loop():
    global raton_listener
    driver = setup_driver()
    login_to_terragene(driver)
    while True:
        dni = wait_for_user_capture(driver)
        if dni == None:
            continue
        else:
            break

    fill_terragene_in_movizen(driver)
    navigate_and_fill_dni(driver, dni)
    while True:
        driver.get("https://terragene.life/terrarrhh/camara")

        new_dni = wait_for_user_capture(driver)
        if not new_dni:
            logging.error("No DNI retrieved in loop. Will wait and retry.")
            time.sleep(RETRY_INTERVAL)
            continue

        navigate_and_fill_dni(driver, new_dni)
        # Desbloquear teclado y ratón al salir
        keyboard.unblock_key('*')  # Desbloquea todas las teclas
        # Desbloquear ratón
        button = driver.find_element(By.ID, "capture")
        driver.execute_script("arguments[0].disabled = false;", button)
        logging.info("Teclado y ratón desbloqueados.")


if __name__ == "__main__":
    try:
        main_loop()
    except Exception as e:

        logging.error(f"An unhandled exception occurred: {e}", exc_info=True)