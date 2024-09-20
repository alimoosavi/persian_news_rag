import asyncio
import datetime
import jdatetime
import logging
import aiohttp
from asgiref.sync import sync_to_async  # Import sync_to_async

from urllib.parse import urlencode, urljoin
from bs4 import BeautifulSoup
from khayyam import JalaliDatetime

from rag_app.models import NewsSource, NewsCategory, NewsLink


class IRNACrawler:
    SOURCE_NAME = 'IRNA'
    PERSIAN_TO_WESTERN = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
    }
    WORKERS_COUNT = 4

    def __init__(self, logger):
        self.logger = logger

    async def setup(self):
        self.source = await sync_to_async(NewsSource.objects.get(name=self.SOURCE_NAME))
        self.categories = await sync_to_async(NewsCategory.objects.filter(source=self.source))

    @staticmethod
    def remove_empty_strings(strings):
        return [item for item in strings if len(item) != 0]

    @classmethod
    def convert_persian_to_western(cls, string):
        for persian_digit, western_digit in cls.PERSIAN_TO_WESTERN.items():
            string = string.replace(persian_digit, western_digit)
        return string

    def category_batch_generator(self):
        idx = 0
        while True:
            batch = self.categories[idx * self.WORKERS_COUNT:(idx + 1) * self.WORKERS_COUNT]
            if len(batch) == 0:
                return
            yield batch
            idx += 1

    async def run(self):
        await self.setup()
        category_batch_gen = self.category_batch_generator()

        for batch in category_batch_gen:
            args = [(category, datetime.datetime.now()) for category in batch]
            await asyncio.gather(*(self.get_list_of_news(category, date) for category, date in args))

    async def get_list_of_news(self, category, date):
        page_number = 1
        news_links = {}
        jalali_date = jdatetime.date.fromgregorian(date=date)

        params = {
            'pi': str(page_number),
            'tp': category.category_id,
            'ms': '0',
            'dy': str(jalali_date.day),
            'mn': str(jalali_date.month),
            'yr': str(jalali_date.year)
        }

        while True:
            fetched_news_links = await self.get_page_news_list(params)
            if not fetched_news_links:
                break

            news_links.update(fetched_news_links)
            page_number += 1
            params['pi'] = str(page_number)

            batch = [
                NewsLink(
                    category=category,
                    news_link=item['news_link'],
                    date=JalaliDatetime.strptime(self.convert_persian_to_western(item['time']),
                                                 '%Y-%m-%d %H:%M').todatetime()
                )
                for _, item in fetched_news_links.items()
            ]

            await sync_to_async(NewsLink.objects.bulk_create)(batch)  # Use sync_to_async for bulk_create
            self.logger.info(f'Batch size: {len(batch)}, Total size: {await sync_to_async(NewsLink.objects.count)()}')

    async def get_page_news_list(self, params):
        query_string = urlencode(params)
        full_url = urljoin(self.source.base_url, "?" + query_string)

        async with aiohttp.ClientSession() as session:
            async with session.get(full_url) as response:
                html_content = await response.text()

        soup = BeautifulSoup(html_content, 'html.parser')
        news_items = soup.find_all('li', class_='news')
        news_links = {}

        for news_item in news_items:
            href = news_item.find('a').get('href')
            time_text = news_item.find('time').a.text.strip()

            news_links[href] = {'news_link': href, 'time': time_text}

        return news_links


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    crawler = IRNACrawler(logger=logger)
    asyncio.run(crawler.run())
