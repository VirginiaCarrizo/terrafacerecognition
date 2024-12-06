import time
import logging
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
    WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.ID, "capture")))

    # Here we assume the user will click the "Capturar" button themselves on the webpage.
    # If we need to click it via automation, uncomment the next two lines:
    # capture_button = driver.find_element(By.ID, "capture")
    # capture_button.click()

    # Wait for the popup to appear. If it's a JS alert, handle it:
    time.sleep(10)  # give some time for the popup to appear after user clicks capture
    try:
        WebDriverWait(driver, 10).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        alert.accept()
    except:
        logging.info("No alert found. Possibly a different popup mechanism.")

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

def main_loop():
    driver = setup_driver()

    # First iteration: perform login
    login_to_terragene(driver)
    wait_for_user_capture(driver)
    fill_terragene_in_movizen(driver)
    navigate_and_fill_dni(driver)

    # Now wait for user input in console
    user_input = input("Please enter a number and press ENTER: ")
    # Once the user has pressed enter, loop back

    # In subsequent loops: no need to login again, just go directly to terragene camera
    while True:
        # Go back to camera page
        driver.get("https://terragene.life/terrarrhh/camara")

        # Wait for user to press "Capturar" and handle popup again
        wait_for_user_capture(driver)

        # Fill terragene again on movizen
        fill_terragene_in_movizen(driver)

        # Navigate and fill dni again
        navigate_and_fill_dni(driver)

        # Wait again for user input
        user_input = input("Please enter a number and press ENTER (or Ctrl+C to stop): ")

if __name__ == "__main__":
    main_loop()
