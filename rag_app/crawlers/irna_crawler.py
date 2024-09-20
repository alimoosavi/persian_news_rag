import datetime
from multiprocessing import Pool, cpu_count
from urllib.parse import urlencode, urljoin

import jdatetime
from bs4 import BeautifulSoup
from khayyam import JalaliDatetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from rag_app.models import NewsSource, NewsCategory, NewsLink


class IRNALinksCrawler:
    SOURCE_NAME = 'IRNA'
    PERSIAN_TO_WESTERN = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
    }
    WORKERS_COUNT = cpu_count()

    def __init__(self, logger, jalali_date):
        self.logger = logger
        self.jalali_date = jalali_date
        self.source = None
        self.categories = None
        self.fetched_links = set({})

    def setup(self):
        self.source = NewsSource.objects.get(name=self.SOURCE_NAME)
        self.categories = NewsCategory.objects.filter(source=self.source)

    @staticmethod
    def remove_empty_strings(strings):
        return [item for item in strings if len(item) != 0]

    @classmethod
    def convert_persian_to_western(cls, string):
        for persian_digit, western_digit in cls.PERSIAN_TO_WESTERN.items():
            string = string.replace(persian_digit, western_digit)
        return string

    @staticmethod
    def get_web_driver():
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Enables headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")  # For better performance in headless mode

        return webdriver.Chrome(options=chrome_options)

    def category_batch_generator(self):
        idx = 0
        while True:
            batch = self.categories[idx * self.WORKERS_COUNT:(idx + 1) * self.WORKERS_COUNT]
            if len(batch) == 0:
                return
            yield batch
            idx += 1

    def run(self):
        self.setup()

        for batch in self.category_batch_generator():
            for cat in batch:
                self.get_list_of_news(category=cat)
            # with Pool(processes=self.WORKERS_COUNT) as pool:
            # pool.map(self.get_list_of_news, [(category, datetime.datetime.now())
            #                                  for category in batch])

    def get_list_of_news(self, category):
        page_number = 1
        news_links = {}
        # jalali_date = jdatetime.date.fromgregorian(date=date)

        params = {
            'pi': str(page_number),
            'tp': category.category_id,
            'ms': '0',
            'dy': str(self.jalali_date.day),
            'mn': str(self.jalali_date.month),
            'yr': str(self.jalali_date.year)
        }

        while True:
            fetched_news_links = self.get_page_news_list(params)
            fetched_news_links = {
                link: data
                for link, data in fetched_news_links.items()
                if link not in self.fetched_links
            }
            if len(fetched_news_links) == 0:
                break

            batch = [
                NewsLink(
                    category=category,
                    news_link=item['news_link'],
                    date=JalaliDatetime.strptime(self.convert_persian_to_western(item['time']),
                                                 '%Y-%m-%d %H:%M').todatetime()
                )
                for _, item in fetched_news_links.items()
            ]

            NewsLink.objects.bulk_create(batch)
            self.logger.info(f'Batch size: {len(batch)}, Total size: {NewsLink.objects.count()}')

            news_links.update(fetched_news_links)
            page_number += 1
            params['pi'] = str(page_number)

    def get_page_news_list(self, params):
        query_string = urlencode(params)
        full_url = urljoin(self.source.base_url, "?" + query_string)

        driver = self.get_web_driver()
        driver.get(full_url)
        html_content = driver.page_source

        soup = BeautifulSoup(html_content, 'html.parser')
        news_items = soup.find_all('li', class_='news')
        news_links = {}

        for news_item in news_items:
            href = news_item.find('a').get('href')
            time_text = news_item.find('time').a.text.strip()

            news_links[href] = {'news_link': href, 'time': time_text}

        return news_links
#
#
# if __name__ == '__main__':
#     logger = logging.getLogger(__name__)
#     crawler = IRNACrawler(logger=logger)
#     crawler.run()
