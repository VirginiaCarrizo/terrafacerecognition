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

# Configure logging
logging.basicConfig(level=logging.INFO)

EC2_SERVER_URL = "http://54.81.210.167/get_dni"

def fetch_dni(max_retries=5, retry_interval=5):
    """
    Fetches the DNI from the EC2 server.
    
    Args:
        max_retries (int): Maximum number of retries for fetching DNI.
        retry_interval (int): Time (in seconds) to wait between retries.
        
    Returns:
        str: The DNI as a string if successful, else None.
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
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.maximize_window()
        logging.info("WebDriver setup completed successfully.")
        return driver
    except Exception as e:
        logging.error(f"Failed to initialize WebDriver: {e}")
        raise

def login_to_terragene(driver):
    logging.info("Navigating to terragene login page.")
    driver.get("https://terragene.life/terrarrhh/camara")
    logging.info("Waiting for username and password fields to appear.")
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, "username")))

    username_input = driver.find_element(By.ID, "username")
    password_input = driver.find_element(By.ID, "password")

    logging.info("Filling username and password.")
    username_input.send_keys("generalfood")
    password_input.send_keys("generalfood")

    logging.info("Clicking login button.")
    login_button = driver.find_element(By.CSS_SELECTOR, "button.btn")
    login_button.click()

def wait_for_user_capture(driver):
    """
    Waits for a user to accept a JavaScript alert and fetches the DNI.
    
    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        
    Returns:
        str: The fetched DNI if successful, or None if no DNI was found.
    """
    try:
        logging.info("Waiting for JS alert to appear...")
        WebDriverWait(driver, 600).until(EC.alert_is_present())  # Wait for up to 10 minutes
        alert = driver.switch_to.alert
        alert_text = alert.text
        logging.info(f"JS alert detected: {alert_text}")

        if "No se ha reconocido a la persona" in alert_text:
            logging.info("Prompt scenario detected. Waiting for user to input DNI and manually accept the prompt.")
        else:
            logging.info("Confirm scenario detected. Waiting for user confirmation (manual accept).")

        # Fetch DNI after user interaction with the alert
        dni = fetch_dni()
        
        if not dni:
            logging.warning("DNI could not be fetched or was empty.")
        else:
            logging.info(f"Fetched DNI: {dni}")
        
        # Wait for alert to disappear
        logging.info("Waiting for alert to be dismissed...")
        WebDriverWait(driver, 300).until_not(EC.alert_is_present())  # Wait for up to 5 minutes
        logging.info("Alert dismissed by the user.")
        
        return dni
    except Exception as e:
        logging.error(f"An error occurred during wait_for_user_capture: {e}")
        return None

def fill_terragene_in_movizen(driver):
    logging.info("Navigating to Movizen PWA to fill 'terragene'.")
    driver.get("https://generalfoodargentina.movizen.com/pwa")

    logging.info("Waiting for ion-input-0 element on Movizen page.")
    WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.ID, "ion-input-0"))
    )

    ion_input = driver.find_element(By.ID, "ion-input-0")
    logging.info("Clearing and filling 'terragene' into ion-input-0.")
    ion_input.clear()
    ion_input.send_keys("terragene")
    ion_input.send_keys(Keys.ENTER)
    logging.info("'terragene' submitted successfully.")

def navigate_and_fill_dni(driver, dni):
    logging.info("Navigating to /pwa/inicio page.")
    time.sleep(1)
    driver.get("https://generalfoodargentina.movizen.com/pwa/inicio")

    logging.info("Waiting for ion-input-0 on /pwa/inicio page.")
    WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "input[id^='ion-input-']"))
    )

    # Find all inputs whose ID starts with "ion-input-"
    ion_inputs = driver.find_element(By.CSS_SELECTOR, "input[id^='ion-input-']")

    logging.info("Fetching DNI from server.")

    logging.info(f"Filling DNI '{dni}' into ion-input-0.")
    ion_inputs.clear()
    ion_inputs.send_keys(dni)
    ion_inputs.send_keys(Keys.ENTER)
    logging.info("DNI submitted successfully.")
    
    current_url = driver.current_url
    WebDriverWait(driver, 300).until(EC.url_changes(current_url))
    
    current_url = driver.current_url
    WebDriverWait(driver, 300).until(EC.url_changes(current_url))
    


def main_loop():
    logging.info("Starting main_loop...")

    driver = setup_driver()
    logging.info("WebDriver initialized successfully.")

    logging.info("Performing initial login to terragene...")
    login_to_terragene(driver)
    logging.info("Login completed successfully.")

    logging.info("Waiting for user capture step...")
    dni = wait_for_user_capture(driver)
    if not dni:
        logging.error("No DNI retrieved. Cannot proceed.")
        return  # Exit if we don't have a DNI
    logging.info("User capture step completed.")

    logging.info("Filling terragene input on Movizen site...")
    fill_terragene_in_movizen(driver)
    logging.info("Terragene input filled successfully.")

    logging.info("Navigating to /pwa/inicio and filling DNI...")
    navigate_and_fill_dni(driver, dni)
    logging.info("DNI filled successfully.")

    # Start the loop only after we have confirmed a DNI is available
    while True:
        logging.info("Navigating back to terragene camera page...")
        driver.get("https://terragene.life/terrarrhh/camara")
        logging.info("Navigation to camera page completed.")

        logging.info("Waiting for user capture step again...")
        new_dni = wait_for_user_capture(driver)
        if not new_dni:
            logging.error("No DNI retrieved in loop. Will wait and retry.")
            # Decide how you want to handle the lack of DNI here.
            # For example, you could break, continue, or return.
            continue
        logging.info("User capture step completed again.")

        logging.info("Filling terragene input on Movizen site again...")
        fill_terragene_in_movizen(driver)
        logging.info("Terragene input filled successfully again.")

        logging.info("Navigating to /pwa/inicio and filling DNI again...")
        navigate_and_fill_dni(driver, new_dni)  # Pass the DNI here
        logging.info("DNI filled successfully again.")
        
        driver.get("https://terragene.life/terrarrhh/camara")

if __name__ == "__main__":
    try:
        main_loop()
    except Exception as e:
        logging.error(f"An unhandled exception occurred: {e}", exc_info=True)
        