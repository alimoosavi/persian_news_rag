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
