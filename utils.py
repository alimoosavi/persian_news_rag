import time
import functools
import os
import requests
from selenium import webdriver
from appdirs import user_cache_dir
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

APP_NAME = 'NewsCrawler'


def retry_on_exception(retries=3, delay=1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < retries:
                try:
                    return func(*args, **kwargs)
                except:
                    attempt += 1
                    time.sleep(delay)
            return None

        return wrapper

    return decorator


def get_web_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Enables headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")  # For better performance in headless mode

    driver_path = ChromeDriverManager().install()

    return webdriver.Chrome(service=Service(driver_path), options=chrome_options)


def run_curl_command(url):
    command = f"curl -s {url}"

    with os.popen(command) as stream:
        output = stream.read()

    return output

# def get_web_driver():
#     # Get a cross-platform cache directory
#     cache_dir = user_cache_dir("webdriver_manager", APP_NAME)
#     os.makedirs(cache_dir, exist_ok=True)
#
#     # Path to store the WebDriver
#     driver_cache_file = os.path.join(cache_dir, "webdriver_path.txt")
#
#     # Check if WebDriver path is already cached
#     if os.path.exists(driver_cache_file):
#         with open(driver_cache_file, 'r') as file:
#             driver_path = file.read().strip()
#     else:
#         # If not cached, install and save path
#         driver_path = ChromeDriverManager().install()
#         with open(driver_cache_file, 'w') as file:
#             file.write(driver_path)
#
#     chrome_options = Options()
#     chrome_options.add_argument("--headless")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#
#     # Use the cached or newly installed driver path
#     return webdriver.Chrome(service=Service(driver_path), options=chrome_options)
