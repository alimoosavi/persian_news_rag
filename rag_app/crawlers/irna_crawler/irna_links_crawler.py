from urllib.parse import urlencode, urljoin

import jdatetime
import threading
from bs4 import BeautifulSoup

from rag_app.crawlers import utils
from rag_app.models import NewsSource, NewsLink


class IRNALinksCrawler:
    SOURCE_NAME = 'IRNA'
    IRNA_NEWS_TYPE = 1
    WORKERS_COUNT = 10

    def __init__(self, logger, start_jalali_date, end_jalali_date):
        self.logger = logger
        self.start_jalali_date = start_jalali_date
        self.end_jalali_date = end_jalali_date
        self.source = None
        self.fetched_links = set({})

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
                                        date__range=(self.start_jalali_date.togregorian(),
                                                     self.end_jalali_date.togregorian()))
                                 .values_list('news_link', flat=True))

    def run(self):
        self.setup()
        datetime_range = list(self.datetime_generator())
        time_batches = utils.split_list(datetime_range, self.WORKERS_COUNT)

        threads = [
            threading.Thread(target=self.get_datetime_batch,
                             args=(time_batch,))
            for time_batch in time_batches
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    def get_datetime_batch(self, time_batch):
        for jalali_date in time_batch:
            # self.logger.log(f'Crawling jalali date: {jalali_date}')
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
                         date=utils.convert_jdatetime_to_gregorian(item['time']))
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
        html_content = utils.fetch(full_url)
        if html_content is None:
            return news_links

        soup = BeautifulSoup(html_content, 'html.parser')
        news_items = soup.find_all('li', class_='news')

        for news_item in news_items:
            href = news_item.find('a').get('href')
            time_text = news_item.find('time').a.text.strip()

            news_links[href] = {'news_link': href, 'time': time_text}

        return news_links
