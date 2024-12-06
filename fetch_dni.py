import time
import logging
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException

# Configure logging
logging.basicConfig(level=logging.INFO)

EC2_SERVER_URL = "http://54.81.210.167/get_dni"

def fetch_dni():
    """
    Fetches the DNI from the EC2 server.
    Returns the DNI as a string if successful, else returns None.
    """
    try:
        response = requests.get(EC2_SERVER_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                dni = data.get('dni')
                logging.info(f"Received DNI: {dni}")
                return dni
            elif data.get('status') == 'no_dni':
                logging.info("No DNI available at the moment.")
            else:
                logging.error(f"Error from server: {data.get('message')}")
        else:
            logging.error(f"Failed to fetch DNI. Status Code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    return None

def setup_driver():
    # Set Chrome options to allow camera usage
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.media_stream_camera": 1,
        "profile.default_content_setting_values.media_stream_mic": 1,
        "profile.default_content_setting_values.geolocation": 1,
        "profile.default_content_setting_values.notifications": 1
    })
    chrome_options.add_argument("--use-fake-ui-for-media-stream")  # automatically grant camera permission

    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    return driver

def login_to_terragene(driver):
    driver.get("https://terragene.life/terrarrhh/camara")
    # Fill username and password
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, "username")))
    username_input = driver.find_element(By.ID, "username")
    password_input = driver.find_element(By.ID, "password")
    username_input.send_keys("generalfood")
    password_input.send_keys("generalfood")

    # Click the login button
    login_button = driver.find_element(By.CSS_SELECTOR, "button.btn")
    login_button.click()

def wait_for_user_capture(driver):
    # Wait until the "Capturar" button is present
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, "capture")))

    time.sleep(10)  # Adjust as necessary

    try:
        WebDriverWait(driver, 5).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        logging.info("JS alert detected, accepting it...")
        alert.accept()
        return  # If we get here, scenario A handled successfully
    except:
        logging.info("No JS alert found, checking for second popup scenario...")

    # Scenario B: HTML-based popup with an input and accept button
    # Replace selectors with the actual ones for your popup.
    popup_input_selector = (By.ID, "popup-input")  # Example ID, change to your actual input element
    popup_accept_selector = (By.ID, "popup-accept")  # Example ID, change to your actual accept button element

    try:
        # Wait a bit for the popup elements to appear
        popup_input = WebDriverWait(driver, 5).until(EC.visibility_of_element_located(popup_input_selector))
        popup_accept = WebDriverWait(driver, 5).until(EC.visibility_of_element_located(popup_accept_selector))

        logging.info("Second popup scenario detected. Waiting for user input and accept click.")

        # If you need to programmatically fill the input, uncomment the next line:
        # popup_input.send_keys("Some data")

        # Now we assume the user will input data and click accept.
        # If you need to do it automatically, uncomment:
        # popup_accept.click()

        # Wait until the popup disappears or page updates after the user accepts
        # This could be another WebDriverWait for a condition that indicates the popup closed.
        time.sleep(5)  # Adjust as needed
        logging.info("Second popup scenario handled (assuming user input and accept).")

    except:
        logging.info("No second popup scenario detected either. No popup needed to handle.")
        # If neither scenario appears, just continue.


def fill_terragene_in_movizen(driver):
    # After accepting, redirect or navigate manually to https://generalfoodargentina.movizen.com/pwa
    driver.get("https://generalfoodargentina.movizen.com/pwa")

    # Wait for ion-input-0 to be available
    WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.ID, "ion-input-0"))
    )
    ion_input = driver.find_element(By.ID, "ion-input-0")

    # Clear if needed and type "terragene"
    ion_input.clear()
    ion_input.send_keys("terragene")
    ion_input.send_keys(Keys.ENTER)

def navigate_and_fill_dni(driver):
    # Navigate to inicio page (this might happen automatically after entering terragene, 
    # but if not, explicitly go there)
    time.sleep(3)
    driver.get("https://generalfoodargentina.movizen.com/pwa/inicio")

    # Wait for ion-input-0 again
    WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.ID, "ion-input-0"))
    )
    ion_input = driver.find_element(By.ID, "ion-input-0")

    # Fetch DNI
    dni = fetch_dni()
    if dni is None:
        dni = ""  # If no DNI, leave it blank or handle accordingly

    ion_input.clear()
    ion_input.send_keys(dni)
    ion_input.send_keys(Keys.ENTER)
    
    try:
        ion_input_1 = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "ion-input-1"))
        )
    except:
        # ion-input-1 is not present, nothing else to do here
        return

    start_time = time.time()
    timeout = 60 
    value_filled = False

    while time.time() - start_time < timeout:
        try:
            ion_input_1 = driver.find_element(By.ID, "ion-input-1")
            current_value = ion_input_1.get_attribute("value")
            if current_value and current_value.strip():
                value_filled = True
                break
        except StaleElementReferenceException:
            logging.info("ion_input_1 became stale, retrying...")
        time.sleep(1)

    if value_filled:
        # Press enter after the user has entered a value
        ion_input_1.send_keys(Keys.ENTER)
    else:
        # User did not fill in time, handle accordingly (optional)
        pass

def main_loop():
    logging.info("Starting main_loop...")

    driver = setup_driver()
    logging.info("WebDriver initialized successfully.")

    # First iteration: perform login
    logging.info("Performing initial login to terragene...")
    login_to_terragene(driver)
    logging.info("Login completed.")

    logging.info("Waiting for user capture step...")
    wait_for_user_capture(driver)
    logging.info("User capture step completed.")

    logging.info("Filling terragene input on Movizen site...")
    fill_terragene_in_movizen(driver)
    logging.info("Terragene input filled successfully.")

    logging.info("Navigating to /pwa/inicio and filling DNI...")
    navigate_and_fill_dni(driver)
    logging.info("DNI filled successfully.")

    logging.info("Awaiting user input from console...")
    #user_input = input("Please enter a number and press ENTER: ")
    #logging.info(f"User entered: {user_input}")

    # Subsequent loops: no need to login again
    while True:
        logging.info("Navigating back to terragene camera page...")
        driver.get("https://terragene.life/terrarrhh/camara")
        logging.info("Navigation to camera page completed.")

        logging.info("Waiting for user capture step again...")
        wait_for_user_capture(driver)
        logging.info("User capture step completed again.")

        logging.info("Filling terragene input on Movizen site again...")
        fill_terragene_in_movizen(driver)
        logging.info("Terragene input filled successfully again.")

        logging.info("Navigating to /pwa/inicio and filling DNI again...")
        navigate_and_fill_dni(driver)
        logging.info("DNI filled successfully again.")

        logging.info("Awaiting user input from console again...")
        #user_input = input("Please enter a number and press ENTER (or Ctrl+C to stop): ")
        #logging.info(f"User entered: {user_input}")
if __name__ == "__main__":
    main_loop()
