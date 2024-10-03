import jdatetime

from multiprocessing import cpu_count
from urllib.parse import urlencode, urljoin

from bs4 import BeautifulSoup
from khayyam import JalaliDatetime

from rag_app.models import NewsSource, NewsCategory, NewsLink
from utils import retry_on_exception, get_web_driver


class IRNALinksCrawler:
    SOURCE_NAME = 'IRNA'
    IRNA_NEWS_TYPE = 1
    PERSIAN_TO_WESTERN = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
    }
    WORKERS_COUNT = cpu_count()

    def __init__(self, logger, start_jalali_date, end_jalali_date):
        self.logger = logger
        self.start_jalali_date = start_jalali_date
        self.end_jalali_date = end_jalali_date
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

    def category_batch_generator(self):
        for category in self.categories:
            yield category
        # idx = 0
        # while True:
        #     batch = self.categories[idx * self.WORKERS_COUNT:(idx + 1) * self.WORKERS_COUNT]
        #     if len(batch) == 0:
        #         return
        #     yield batch
        #     idx += 1

    def datetime_generator(self):
        current_jalali_date = self.start_jalali_date

        while current_jalali_date <= self.end_jalali_date:
            yield current_jalali_date
            current_jalali_date += jdatetime.timedelta(days=1)

    def run(self):
        self.setup()

        for category in self.category_batch_generator():
            for jalali_date in self.datetime_generator():
                self.get_list_of_news(category=category, jalali_date=jalali_date)

    def get_list_of_news(self, category, jalali_date):
        page_number = 1
        news_links = {}

        params = {
            'ty': str(self.IRNA_NEWS_TYPE),
            'pi': str(page_number),
            'tp': category.category_id,
            'ms': '0',
            'dy': str(jalali_date.day),
            'mn': str(jalali_date.month),
            'yr': str(jalali_date.year)
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

        news_links = {}
        html_content = self.fetch(full_url)
        if html_content is None:
            return news_links

        soup = BeautifulSoup(html_content, 'html.parser')
        news_items = soup.find_all('li', class_='news')

        for news_item in news_items:
            href = news_item.find('a').get('href')
            time_text = news_item.find('time').a.text.strip()

            news_links[href] = {'news_link': href, 'time': time_text}

        return news_links
