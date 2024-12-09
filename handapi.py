import time
import logging
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    NoSuchElementException,
    TimeoutException
)


logging.basicConfig(level=logging.INFO)

EC2_SERVER_URL = "http://54.81.210.167/get_dni"

def fetch_dni(max_retries=5, retry_interval=5):
    """
    Fetches the DNI from the EC2 server.
    """
    retries = 0
    while retries < max_retries:
        try:
            logging.info("Attempting to fetch DNI from server...")
            response = requests.get(EC2_SERVER_URL, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                logging.info(f"Server response status: {status}")
                
                if status == 'success':
                    dni = data.get('dni')
                    if dni:
                        logging.info(f"Received DNI: {dni}")
                        return dni
                    else:
                        logging.warning("DNI not found in response.")
                        return None
                else:
                    logging.info("Status not successful, retrying...")
            else:
                logging.warning(f"Server returned status code {response.status_code}, retrying...")
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
        
        retries += 1
        logging.info(f"Retrying... ({retries}/{max_retries})")
        time.sleep(retry_interval)
    
    logging.error("Max retries reached. Could not fetch DNI.")
    return None

def setup_driver():
    logging.info("Setting up the WebDriver with camera and mic permissions.")
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

    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    logging.info("WebDriver setup completed successfully.")
    return driver

def login_terragene(driver):
    """
    Logs into terragene page.
    """
    logging.info("Logging into terragene...")
    driver.get("https://terragene.life/terrarrhh/camara")
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "username")))
    
    username_input = driver.find_element(By.ID, "username")
    password_input = driver.find_element(By.ID, "password")

    username_input.send_keys("generalfood")
    password_input.send_keys("generalfood")

    login_button = driver.find_element(By.CSS_SELECTOR, "button.btn")
    login_button.click()
    logging.info("Login button clicked.")

def wait_for_alert_and_fetch_dni(driver):
    """
    Waits for the JavaScript alert in terragene, fetches DNI, and waits for alert to go away.
    """
    logging.info("Waiting for JS alert to appear...")
    WebDriverWait(driver, 600).until(EC.alert_is_present())  # Wait for up to 10 minutes
    alert = driver.switch_to.alert
    alert_text = alert.text
    logging.info(f"Alert appeared with text: {alert_text}")
    
    # Wait for the alert to go away - this implies user action on terragene's side
    logging.info("Waiting for alert to be dismissed by the user...")
    WebDriverWait(driver, 300).until_not(EC.alert_is_present())  # Wait for up to 5 minutes
    logging.info("Alert dismissed by the user.")
    
    dni = fetch_dni()
    if not dni:
        logging.error("No DNI fetched. Handling error or retry...")
    return dni

def get_ion_input_native_element(driver, ion_input_locator):
    """
    Given a locator for an ion-input element, wait for it,
    then use JavaScript to access its shadow root and find the native <input>.
    """
    ion_input = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(ion_input_locator)
    )
    # Execute JS to get the native input inside the shadow root
    native_input = driver.execute_script("return arguments[0].shadowRoot.querySelector('input.native-input')", ion_input)
    return native_input

def first_iteration_generalfood_flow(driver, dni):
    """
    On the first iteration:
    1. Access https://generalfoodargentina.movizen.com/pwa
    2. Type "terragene" into the ion-input, press Enter
    3. After navigating to /pwa/inicio, input the DNI, press Enter
    4. Wait for the sequence of pages to proceed (pedido-pc, then pedido-web-print)
    """
    driver.get("https://generalfoodargentina.movizen.com/pwa")
    logging.info("Navigating to generalfood pwa and inputting 'terragene'...")

    # Locate the first ion-input on the page for "terragene"
    terragene_input = get_ion_input_native_element(driver, (By.TAG_NAME, "ion-input"))
    terragene_input.send_keys("terragene")
    terragene_input.send_keys(Keys.ENTER)
    logging.info("Entered 'terragene' and pressed Enter.")

    # Wait until the URL changes to /pwa/inicio
    WebDriverWait(driver, 30).until(EC.url_contains("/pwa/inicio"))
    logging.info("At pwa/inicio page, inputting DNI...")

    # Now locate the ion-input for the DNI field
    # Assuming it has placeholder="Ingresar DNI"
    dni_input = get_ion_input_native_element(driver, (By.CSS_SELECTOR, "ion-input[placeholder='Ingresar DNI']"))
    dni_input.send_keys(dni)
    dni_input.send_keys(Keys.ENTER)
    logging.info(f"Entered DNI: {dni} and pressed Enter.")

    # After pressing enter, it automatically goes to pedido-pc
    WebDriverWait(driver, 30).until(EC.url_contains("pedido-pc"))
    logging.info("At pedido-pc page. Waiting for user input...")

    # The user enters a number and the page automatically redirects to pedido-web-print
    WebDriverWait(driver, 180).until(EC.url_contains("pedido-web-print"))
    logging.info("Redirected to pedido-web-print page.")


def subsequent_iteration_generalfood_flow(driver, dni):
    """
    On subsequent iterations:
    1. Access https://generalfoodargentina.movizen.com/pwa/inicio directly
    2. Input the DNI and press Enter (no need to type 'terragene' again)
    3. The same sequence of waiting for pedido-pc and then pedido-web-print applies
    """
    driver.get("https://generalfoodargentina.movizen.com/pwa/inicio")
    logging.info("At pwa/inicio page, inputting DNI...")

    # Locate the DNI ion-input again using placeholder
    dni_input = get_ion_input_native_element(driver, (By.CSS_SELECTOR, "ion-input[placeholder='Ingresar DNI']"))
    dni_input.send_keys(dni)
    dni_input.send_keys(Keys.ENTER)
    logging.info(f"Entered DNI: {dni} and pressed Enter (subsequent iteration).")

    WebDriverWait(driver, 30).until(EC.url_contains("pedido-pc"))
    logging.info("At pedido-pc page again. Waiting for user input...")

    # Wait for the user input to cause redirect to pedido-web-print
    WebDriverWait(driver, 180).until(EC.url_contains("pedido-web-print"))
    logging.info("Redirected to pedido-web-print page (subsequent iteration).")


def main_loop():
    driver = setup_driver()
    first_iteration = True

    while True:
        # Go to terragene page
        driver.get("https://terragene.life/terrarrhh/camara")

        if first_iteration:
            # Perform login only on the first iteration
            login_terragene(driver)

        # Wait for alert, fetch DNI, wait for alert to go away
        dni = wait_for_alert_and_fetch_dni(driver)
        if not dni:
            logging.error("No DNI fetched, skipping this iteration.")
            continue

        # Proceed with the generalfood flow
        if first_iteration:
            first_iteration_generalfood_flow(driver, dni)
            first_iteration = False
        else:
            subsequent_iteration_generalfood_flow(driver, dni)

        # After finishing the iteration, we loop again.
        # The next iteration will not login into terragene and not type 'terragene' at generalfood.
        logging.info("Iteration completed. Starting next iteration...")
        # Add a small delay if needed to avoid too fast loops
        time.sleep(5)

if __name__ == "__main__":
    main_loop()