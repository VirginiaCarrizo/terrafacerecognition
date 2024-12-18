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
from selenium.webdriver.common.action_chains import ActionChains

# Configure logging
logging.basicConfig(level=logging.INFO)

# Global timeouts
TIMEOUT = 30  # Default timeout for Selenium waits
RETRY_INTERVAL = 2  # Interval to sleep between retries for DNI fetching
EC2_REQUEST_TIMEOUT = 10  # Timeout for EC2 requests
FETCH_DNI_MAX_RETRIES = 20

EC2_SERVER_URL = "http://54.81.210.167/get_dni"

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
            # logging.info("Attempting to fetch DNI from server...")
            response = requests.get(EC2_SERVER_URL, timeout=EC2_REQUEST_TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                logging.info(f"Server response status: {status}")

                if status == 'success':
                    dni = data.get('dni')
                    print(dni)
                    if dni != 0:
                        # logging.info(f"Received DNI: {dni}")
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
        # logging.info(f"Retrying... ({retries}/{max_retries})")
        time.sleep(retry_interval)

    logging.error("Max retries reached. Could not fetch DNI.")
    return None


def setup_driver():
    # logging.info("Setting up the WebDriver with camera and mic permissions.")
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
    'savefile.default_directory': r'C:\Users\juan.sanchez\Desktop\pedidos/'  # Ruta para guardar PDFs automáticamente
    })

    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.maximize_window()
        # logging.info("WebDriver setup completed successfully.")
        return driver
    except Exception as e:
        logging.error(f"Failed to initialize WebDriver: {e}")
        raise


def login_to_terragene(driver):
    # logging.info("Navigating to terragene login page.")
    driver.get("https://terragene.life/terrarrhh/camara")

    # Wait for username and password fields (Timeout applied)
    # logging.info("Waiting for username and password fields to appear.")
    WebDriverWait(driver, TIMEOUT).until(EC.visibility_of_element_located((By.ID, "username")))

    username_input = driver.find_element(By.ID, "username")
    password_input = driver.find_element(By.ID, "password")

    # logging.info("Filling username and password.")
    username_input.send_keys("generalfood")
    password_input.send_keys("generalfood")

    # logging.info("Clicking login button.")
    login_button = driver.find_element(By.CSS_SELECTOR, "button.btn")
    login_button.click()


def wait_for_user_capture(driver):
    """
    Waits for a user to accept a JavaScript alert and fetches the DNI.

    We apply a long wait timeout here as this likely involves user interaction.
    """
    try:
        # logging.info("Waiting for JS alert to appear (up to 10 minutes)...")
        # Long timeout for user interaction, e.g., 600 seconds
        WebDriverWait(driver, timeout=9999999).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        alert_text = alert.text
        # logging.info(f"JS alert detected: {alert_text}")

        if "No se ha reconocido a la persona" in alert_text:
            logging.info("Prompt scenario detected. Waiting for user to input DNI and manually accept the prompt.")
        else:
            logging.info("Confirm scenario detected. Waiting for user confirmation (manual accept).")

        # Fetch DNI after user interaction with the alert
        # time.sleep(5)
        dni = fetch_dni()
        
        print(dni)
        if not dni:
            logging.warning("DNI could not be fetched or was empty.")
        else:
            logging.info(f"Fetched DNI: {dni}")

        # Wait for alert to disappear
        # logging.info("Waiting for alert to be dismissed (up to 5 minutes)...")
        WebDriverWait(driver, 300).until_not(EC.alert_is_present())
        # logging.info("Alert dismissed by the user.")

        return dni
    except Exception as e:
        logging.error(f"An error occurred during wait_for_user_capture: {e}")
        return None


def fill_terragene_in_movizen(driver):
    # logging.info("Navigating to Movizen PWA to fill 'terragene'.")
    driver.get("https://generalfoodargentina.movizen.com/pwa/")

    # logging.info("Waiting for ion-input-0 element on Movizen page.")
    WebDriverWait(driver, TIMEOUT).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "input[id^='ion-input-']"))
    )

    ion_input = driver.find_element(By.CSS_SELECTOR, "input[id^='ion-input-']")
    time.sleep(1)
    ion_input.send_keys("terragene")
    ion_input.send_keys(Keys.ENTER)
    current_url = driver.current_url
    WebDriverWait(driver, TIMEOUT).until(EC.url_changes(current_url))
    # logging.info("'terragene' submitted successfully.")


    time.sleep(1)


def navigate_and_fill_dni(driver, dni):
    # logging.info("Navigating to /pwa/inicio page.")
    driver.get("https://generalfoodargentina.movizen.com/pwa/inicio")

    # driver.refresh()
    # logging.info("Waiting for ion-input-0 on /pwa/inicio page.")
    WebDriverWait(driver, TIMEOUT).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "input[id^='ion-input-']"))
    )

    ion_input = driver.find_element(By.CSS_SELECTOR, "input[id^='ion-input-']")


 
    ion_input.clear()
    ion_input.send_keys(int(dni))
    ion_input.send_keys(Keys.ENTER)



    inicio = time.time()
    segunda_fase = True
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
            # Abrir una nueva pestaña
            # driver.close() 
            WebDriverWait(driver, 99999).until(EC.url_changes('https://generalfoodargentina.movizen.com/pwa/pedido-pc'))
            driver.execute_script("window.open('about:blank', '_blank');")
            time.sleep(1)
            driver.close()
                        # Script para habilitar la impresión
            # Cambiar al contexto de la nueva pestaña
            driver.switch_to.window(driver.window_handles[-1])

            # Navegar a la URL deseada en la nueva pestaña
            new_url = "https://generalfoodargentina.movizen.com/pwa/pedido-web-print"
            driver.get(new_url)
         
            #ACA SE TIENEN QUE GUARDAR LOS DATOS DEL PEDIDO


            
            time.sleep(4)
       
            break



        


def main_loop():

    # logging.info("Starting main_loop...")

    driver = setup_driver()
    # logging.info("WebDriver initialized successfully.")

    # logging.info("Performing initial login to terragene...")
    login_to_terragene(driver)
    # logging.info("Login completed successfully.")

    # logging.info("Waiting for user capture step...")
    while True:
        dni = wait_for_user_capture(driver)
        if dni == None:
            continue
        else:
            break
    # logging.info("User capture step completed.")

    # logging.info("Filling terragene input on Movizen site...")
    fill_terragene_in_movizen(driver)
    # logging.info("Terragene input filled successfully.")

    # logging.info("Navigating to /pwa/inicio and filling DNI...")
    navigate_and_fill_dni(driver, dni)
    # logging.info("DNI filled successfully.")

    # Loop for subsequent captures
    while True:
        # logging.info("Navigating back to terragene camera page...")
        driver.get("https://terragene.life/terrarrhh/camara")
        # logging.info("Navigation to camera page completed.")

        # logging.info("Waiting for user capture step again...")
        new_dni = wait_for_user_capture(driver)
        if not new_dni:
            logging.error("No DNI retrieved in loop. Will wait and retry.")
            time.sleep(RETRY_INTERVAL)
            continue
        # logging.info("User capture step completed again.")
 
        # logging.info("Navigating to /pwa/inicio and filling new DNI...")
        navigate_and_fill_dni(driver, new_dni)
        # logging.info("DNI filled successfully again.")

if __name__ == "__main__":
    try:
        main_loop()
    except Exception as e:

        logging.error(f"An unhandled exception occurred: {e}", exc_info=True)