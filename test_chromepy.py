from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import time

from chromedriver_py import binary_path  # Import the binary path for ChromeDriver

def perform_navigation():
    # Initialize the WebDriver
    svc = Service(executable_path=binary_path)
    driver = webdriver.Chrome(service=svc)

    try:
        # Step 1: Navigate to the first page
        driver.get("https://generalfoodargentina.movizen.com/pwa")
        
        # Wait for the page to load
        time.sleep(3)
        
        # Find the input field and enter "terragene"
        input_field = driver.find_element("id", "ion-input-0")
        input_field.send_keys("terragene")
        
        # Simulate pressing ENTER to submit and wait for navigation
        input_field.send_keys(Keys.RETURN)
        time.sleep(5)  # Adjust based on your network speed

        # Step 2: Navigate to the second page
        driver.get("https://generalfoodargentina.movizen.com/pwa/inicio")
        
        # Wait for the page to load
        time.sleep(3)
        
        # Find the input field and enter "44291507"
        input_field = driver.find_element("id", "ion-input-0")
        input_field.send_keys("44291507")
        
        # Simulate pressing ENTER to submit
        input_field.send_keys(Keys.RETURN)
        
        # Optional: Wait to observe the result
        time.sleep(5)

    finally:
        # Close the browser
        driver.quit()

# Run the automation script
if __name__ == "__main__":
    perform_navigation()
