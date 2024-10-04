from multiprocessing import cpu_count
from urllib.parse import urlencode, urljoin

import jdatetime
from bs4 import BeautifulSoup
from khayyam import JalaliDatetime

from rag_app.models import NewsSource, NewsLink
from rag_app.crawlers.utils import retry_on_exception, get_web_driver


class IRNALinksCrawler:
    SOURCE_NAME = 'IRNA'
    IRNA_NEWS_TYPE = 1
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
    WORKERS_COUNT = cpu_count()

    def __init__(self, logger, start_jalali_date, end_jalali_date):
        self.logger = logger
        self.start_jalali_date = start_jalali_date
        self.end_jalali_date = end_jalali_date
        self.source = None
        self.fetched_links = set({})

    @staticmethod
    def remove_empty_strings(strings):
        return [item for item in strings if len(item) != 0]

    @classmethod
    def convert_jdatetime_to_datetime(cls, jdatetime_str):
        datetime_str = jdatetime_str.copy()
        for persian_digit, western_digit in cls.PERSIAN_TO_WESTERN.items():
            datetime_str = datetime_str.replace(persian_digit, western_digit)
        return (JalaliDatetime
                .strptime(datetime_str, '%Y-%m-%d %H:%M').todatetime())

    @property
    def start_date(self):
        return self.start_jalali_date.todatetime()

    @property
    def end_date(self):
        return self.end_jalali_date.todatetime()

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

    def datetime_generator(self):
        current_jalali_date = self.start_jalali_date

        while current_jalali_date <= self.end_jalali_date:
            yield current_jalali_date
            current_jalali_date += jdatetime.timedelta(days=1)

    def setup(self):
        self.source = NewsSource.objects.get(name=self.SOURCE_NAME)
        self.fetched_links = set(NewsLink.
                                 objects.
                                 filter(source=self.source,
                                        date__range=(self.start_date, self.end_date))
                                 .values_list('news_link', flat=True))

    def run(self):
        self.setup()

        for jalali_date in self.datetime_generator():
            self.logger.log('Crawling jalali date', jalali_date)
            self.get_list_of_news(jalali_date=jalali_date)

    def get_list_of_news(self, jalali_date):
        page_number = 1
        params = {
            'ty': str(self.IRNA_NEWS_TYPE),
            'pi': str(page_number),
            'ms': '0',
            'dy': str(jalali_date.day),
            'mn': str(jalali_date.month),
            'yr': str(jalali_date.year)
        }

        while True:
            fetched_news_links = {
                link: data
                for link, data in self.get_page_news_list(params).items()
                if link not in self.fetched_links
            }
            if len(fetched_news_links) == 0:
                break

            batch = [
                NewsLink(source=self.source,
                         news_link=item['news_link'],
                         date=self.convert_jdatetime_to_datetime(item['time']))
                for item in fetched_news_links.values()
            ]

            NewsLink.objects.bulk_create(batch)
            self.logger.info(f'Batch size: {len(batch)}, Total size: {NewsLink.objects.count()}')

            self.fetched_links.update(set(fetched_news_links.keys()))
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
