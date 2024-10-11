import time
import functools
import os
import requests
from selenium import webdriver
from appdirs import user_cache_dir
from khayyam import JalaliDatetime
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


@retry_on_exception(retries=3, delay=1)
def fetch(link):
    driver = get_web_driver()
    try:
        driver.get(link)
        return driver.page_source
    except:
        return None
    finally:
        driver.quit()


def run_curl_command(url):
    command = f"curl -s {url}"

    with os.popen(command) as stream:
        output = stream.read()

    return output


def split_list(lst, n):
    if n <= 0:
        return []
    avg = len(lst) // n
    return [lst[i:i + avg + (1 if i < len(lst) % n else 0)] for i in range(0, len(lst), avg + 1)]


PERSIAN_TO_WESTERN = {
    '۰': '0',
    '۱': '1',
    '۲': '2',
    '۳': '3',
    '۴': '4',
    '۵': '5',
    '۶': '6',
    '۷': '7',
    '۸': '8',
    '۹': '9'
}


def convert_jdatetime_to_gregorian(jdatetime_str):
    datetime_str = jdatetime_str
    for persian_digit, western_digit in PERSIAN_TO_WESTERN.items():
        datetime_str = datetime_str.replace(persian_digit, western_digit)
    return (JalaliDatetime
            .strptime(datetime_str,
                      '%Y-%m-%d %H:%M').todatetime())
