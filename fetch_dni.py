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

def perform_navigation(dni):
    """
    Performs the Selenium automation by navigating through the website
    and entering the provided DNI.
    """
    # Initialize Chrome Options
    chrome_options = Options()
    chrome_options.add_argument("--user-data-dir=C:\\Users\\Mateo Rovere\\AppData\\Local\\Google\\Chrome\\User Data")  # Replace with the path to your profile directory
    chrome_options.add_argument("--profile-directory=Default")  # Use the default profile or specify another profile
    
    # Initialize the WebDriver with options
    svc = Service(executable_path=binary_path)
    driver = webdriver.Chrome(service=svc, options=chrome_options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)

    try:
        # Step 1: Navigate to the first page
        logging.info(f"Navigating to {FIRST_PAGE_URL}")
        driver.get(FIRST_PAGE_URL)
        
        # Wait for the page to load
        time.sleep(3)  # Consider using WebDriverWait for better reliability
        
        # Find the input field and enter "terragene"
        input_field = driver.find_element("id", FIRST_INPUT_ID)
        input_field.send_keys("terragene")
        logging.info("Entered 'terragene' into the first input field.")
        
        # Simulate pressing ENTER to submit and wait for navigation
        input_field.send_keys(Keys.RETURN)
        logging.info("Submitted the first form.")
        time.sleep(5)  # Adjust based on your network speed

        # Step 2: Navigate to the second page
        logging.info(f"Navigating to {SECOND_PAGE_URL}")
        driver.get(SECOND_PAGE_URL)
        
        # Wait for the page to load
        time.sleep(3)
        
        # Find the input field and enter the fetched DNI
        input_field = driver.find_element("id", SECOND_INPUT_ID)
        input_field.send_keys(dni)
        logging.info(f"Entered DNI '{dni}' into the second input field.")
        
        # Simulate pressing ENTER to submit
        input_field.send_keys(Keys.RETURN)
        logging.info("Submitted the second form.")
        
        # Optional: Wait to observe the result
        time.sleep(5)

    except Exception as e:
        logging.error(f"An error occurred during navigation: {e}")
    finally:
        # Close the browser
        driver.quit()
        logging.info("Browser closed.")
def main():
    """
    Main function to continuously fetch DNI and perform automation.
    """
    while True:
        dni = fetch_dni()
        if dni:
            perform_navigation(dni)
            # After successful automation, you might want to wait or exit
            # Here, we'll wait for the next polling interval
        else:
            logging.info("No DNI fetched. Will retry after the polling interval.")
        
        logging.info(f"Waiting for {POLLING_INTERVAL} seconds before the next attempt.")
        time.sleep(POLLING_INTERVAL)

if __name__ == "__main__":
    main()
