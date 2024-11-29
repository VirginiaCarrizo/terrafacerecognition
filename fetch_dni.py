import requests
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("fetch_dni.log")
    ]
)

EC2_SERVER_URL = "http://54.81.210.167/get_dni"

def fetch_dni():
    try:
        response = requests.get(EC2_SERVER_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                dni = data['dni']
                logging.info(f"Received DNI: {dni}")
                # Process the DNI as needed
            elif data['status'] == 'no_dni':
                logging.info("No DNI available at the moment.")
            else:
                logging.error(f"Error from server: {data['message']}")
        else:
            logging.error(f"Failed to fetch DNI. Status Code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

def main():
    polling_interval = 10  # seconds
    while True:
        fetch_dni()
        time.sleep(polling_interval)

if __name__ == "__main__":
    main()
