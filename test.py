import time
import logging
import requests
import threading
import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
    """
    try:
        logging.info("Waiting for JS alert to appear...")
        WebDriverWait(driver, 600).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        alert_text = alert.text
        logging.info(f"JS alert detected: {alert_text}")

        if "No se ha reconocido a la persona" in alert_text:
            logging.info("Prompt scenario detected. Waiting for user to input DNI and manually accept the prompt.")
        else:
            logging.info("Confirm scenario detected. Waiting for user confirmation (manual accept).")

        dni = fetch_dni()

        if not dni:
            logging.warning("DNI could not be fetched or was empty.")
        else:
            logging.info(f"Fetched DNI: {dni}")

        logging.info("Waiting for alert to be dismissed...")
        WebDriverWait(driver, 300).until_not(EC.alert_is_present())
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
        EC.visibility_of_element_located((By.CSS_SELECTOR, "input[id^='ion-input-']"))
    )

    ion_input = driver.find_element(By.CSS_SELECTOR, "input[id^='ion-input-']")
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

    ion_inputs = driver.find_element(By.CSS_SELECTOR, "input[id^='ion-input-']")

    logging.info(f"Filling DNI '{dni}' into ion-input-0.")
    ion_inputs.clear()
    ion_inputs.send_keys(dni)
    ion_inputs.send_keys(Keys.ENTER)
    logging.info("DNI submitted successfully.")
    logging.info(f"Current URL: {driver.current_url}")
    current_url = driver.current_url
    WebDriverWait(driver, 300).until(EC.url_changes(current_url))
    logging.info(f"Current URL: {driver.current_url}")
    current_url = driver.current_url
    WebDriverWait(driver, 300).until(EC.url_changes(current_url))
    logging.info(f"Current URL: {driver.current_url}")
    logging.info("todo correcto hasta aca")


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
        driver.quit()
        return
    logging.info("User capture step completed.")

    logging.info("Filling terragene input on Movizen site...")
    fill_terragene_in_movizen(driver)
    logging.info("Terragene input filled successfully.")

    logging.info("Navigating to /pwa/inicio and filling DNI...")
    navigate_and_fill_dni(driver, dni)
    logging.info("DNI filled successfully.")

    # Close the driver session at the end
    driver.quit()
    logging.info("Process completed successfully.")


# GUI code using tkinter
def run_process(button):
    # Disable the button to prevent multiple runs
    button.config(state=tk.DISABLED)
    # Use a thread to run the process so GUI remains responsive
    thread = threading.Thread(target=run_main_loop_thread, args=(button,))
    thread.start()


def run_main_loop_thread(button):
    try:
        main_loop()
        # Once done, show a message to the user.
        messagebox.showinfo("Process Complete", "The process has completed successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
    finally:
        # Re-enable the button for another run
        button.config(state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("GeneralFood")

    instruction_label = tk.Label(root, text="Pulsa el boton para iniciar el proceso para sacar la orden")
    instruction_label.pack(pady=10)

    run_button = tk.Button(root, text="Iniciar orden", command=lambda: run_process(run_button))
    run_button.pack(pady=20)

    root.mainloop()
