import requests
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from chromedriver_py import binary_path
from selenium.webdriver.chrome.options import Options

# --------------------- Configuration ---------------------

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("merged_automation.log")
    ]
)

# EC2 Server URL to fetch DNI
EC2_SERVER_URL = "http://54.81.210.167/get_dni"  # Replace with your EC2's public IP or domain

# Polling Interval for fetching DNI (in seconds)
POLLING_INTERVAL = 30

# URLs for Selenium Navigation
FIRST_PAGE_URL = "https://generalfoodargentina.movizen.com/pwa"
SECOND_PAGE_URL = "https://generalfoodargentina.movizen.com/pwa/inicio"

# Element IDs
FIRST_INPUT_ID = "ion-input-0"
SECOND_INPUT_ID = "ion-input-0"  # Assuming it's the same ID; adjust if different

# Timeout Settings
PAGE_LOAD_TIMEOUT = 10  # seconds
ELEMENT_LOAD_TIMEOUT = 10  # seconds

# --------------------------------------------------------

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

def initialize_session():
    """
    Initialize the Selenium WebDriver session and perform the first login step.
    Returns the driver instance.
    """
    svc = Service(executable_path=binary_path)
    driver = webdriver.Chrome(service=svc)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)

    logging.info(f"Navigating to {FIRST_PAGE_URL}")
    driver.get(FIRST_PAGE_URL)
    time.sleep(3)  # Wait for the page to load

    # Enter "terragene" in the first input field
    input_field = driver.find_element("id", FIRST_INPUT_ID)
    input_field.send_keys("terragene")
    logging.info("Entered 'terragene' into the first input field.")

    # Submit the form
    input_field.send_keys(Keys.RETURN)
    logging.info("Submitted the first form.")
    time.sleep(5)  # Wait for the navigation

    # At this point, we are logged in and the session is active.
    # Return the driver so it can be reused.
    return driver

def perform_dni_submission(driver, dni):
    """
    Uses the given Selenium WebDriver session to navigate to the second page
    and submit the provided DNI, without re-logging in.
    """
    logging.info(f"Navigating to {SECOND_PAGE_URL}")
    driver.get(SECOND_PAGE_URL)
    time.sleep(3)  # Wait for the page to load

    input_field = driver.find_element("id", SECOND_INPUT_ID)
    input_field.send_keys(dni)
    logging.info(f"Entered DNI '{dni}' into the second input field.")

    # Submit the DNI
    input_field.send_keys(Keys.RETURN)
    logging.info("Submitted the second form.")
    time.sleep(5)  # Optional observation time

def main():
    """
    Main function to initialize the session once, then continuously
    fetch and submit DNIs using the same logged-in session.
    """
    # Initialize the session (login once)
    driver = initialize_session()

    try:
        while True:
            # If you have logic to fetch DNI from the server, use it here.
            # For now, we use a hardcoded DNI.
            dni = fetch_dni()
            if dni:
                perform_dni_submission(driver, dni)
            else:
                logging.info("No DNI fetched. Will retry after the polling interval.")

            logging.info(f"Waiting for {POLLING_INTERVAL} seconds before the next attempt.")
            time.sleep(POLLING_INTERVAL)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        # Close the browser when done or on error
        driver.quit()
        logging.info("Browser closed.")

if __name__ == "__main__":
    main()
