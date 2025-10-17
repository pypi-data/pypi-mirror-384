import requests
import os
import logging
from dotenv import load_dotenv
import json
import time
import random
from .vendors import Vendors
from .vendorintakeform import VendorIntakeForm

try:
    import colorama
    colorama.init()
except ImportError:
    os.system('')  # Enables ANSI escape characters in terminal on Windows

class ColorFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[41m', # Red background
    }
    RESET = '\033[0m'

    def format(self, record):
        # Center the levelname in a field of width 8
        levelname = record.levelname.center(8)
        color = self.COLORS.get(record.levelname.strip(), '')
        record.levelname = f"{color}{levelname}{self.RESET}"
        return super().format(record)

handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter('%(asctime)s - %(levelname)s %(message)s'))
logging.basicConfig(level=logging.INFO, handlers=[handler])


class Whistic:
    def __init__(self, max_workers=5):
        self.page_size = 25
        self.max_workers = max_workers

        if not 'WHISTIC_TOKEN' in os.environ:
            logging.critical("The Whistic module cannot initiate without the WHISTIC_TOKEN being defined")
            exit(1)
        else:
            logging.info("Whistic token found")

        if not 'WHISTIC_ENDPOINT' in os.environ:
            self.endpoint = "https://public.whistic.com/api"
        else:
            self.endpoint = os.environ['WHISTIC_ENDPOINT']
        logging.info(f"Using whistic endpoint {self.endpoint}")

        self.headers = {
            'accept' : 'application/json',
            'Content-Type' : 'application/json',
            'Api-Key' : os.environ['WHISTIC_TOKEN']
        }
        
        self.vendors = Vendors(self)
        self.vendor_intake_form = VendorIntakeForm(self)

    def _make_request_with_retry(self, url, max_retries=3):
        """Make a request with exponential backoff for rate limiting"""
        for attempt in range(max_retries + 1):
            try:
                response = requests.get(url, headers=self.headers, timeout=30)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    if attempt < max_retries:
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        logging.warning(f"Rate limit hit (429). Retrying in {wait_time:.2f} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logging.error(f"Rate limit exceeded after {max_retries} retries: {url}")
                        return response
                else:
                    logging.error(f"{response.status_code} - {url} - {response.content}")
                    return response
                    
            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logging.warning(f"Request failed: {e}. Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                else:
                    logging.error(f"Request failed after {max_retries} retries: {e}")
                    raise
        
        return None

if __name__ == '__main__':
    load_dotenv()

    W = Whistic()

    # Reading all vendors
    my_vendors = W.vendors.list()

    with open('_vendors.json','wt') as q:
        q.write(json.dumps(my_vendors,indent=2))

    # == read just one vendor
    id = my_vendors[10]['identifier']
    my_vendor = W.vendors.get(id)
    
    # == Update a vendor
    W.vendors.update(id,{ "name" : "HOWDY"} )

    # == add a new vendor
    #W.vendors.new(data)

    # == Get vendor intake form
    intake_form = W.vendor_intake_form.get()
    if intake_form:
        with open('_vendor_intake_form.json', 'wt') as f:
            f.write(json.dumps(intake_form, indent=2))
    