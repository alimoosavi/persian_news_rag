import requests
import utils
from bs4 import BeautifulSoup
from django.core.paginator import Paginator

from rag_app.models import NewsSource, NewsCategory, NewsLink, News


class IRNAContentCrawler:
    SOURCE_NAME = 'IRNA'
    WORKERS_COUNT = 5
    BATCH_SIZE = 15

    def __init__(self, logger):
        self.logger = logger
        self.source = None
        self.categories = None
        self.not_processed_links = None

    def setup(self):
        self.source = NewsSource.objects.get(name=self.SOURCE_NAME)
        self.categories = NewsCategory.objects.filter(source=self.source)
        self.not_processed_links = NewsLink.objects.filter(category__source=self.source,
                                                           has_processed=False).order_by('-date')

    @staticmethod
    def fetch(news_link):
        return utils.run_curl_command(news_link)

    def links_generator(self):
        paginator = Paginator(self.not_processed_links, self.BATCH_SIZE)
        for page_num in range(1, paginator.num_pages + 1):
            batch = [news_link for news_link in paginator.page(page_num).object_list]
            yield batch

    def fetch_batch_concurrently(self, batch):

        results = {
            nl: self.fetch(nl.get_full_url())
            for nl in batch
        }
        return {nl: self.process_news_content_page(html_content) if html_content else None
                for nl, html_content in results.items()}

    @staticmethod
    def process_news_content_page(html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        title_text = soup.find('h1', class_='title').a.get_text(strip=True)
        body_text = '\n'.join([p.get_text(strip=True) for p in soup.find('div', class_='item-body').find_all('p') if
                               p.get_text(strip=True)])

        return {
            'title': title_text,
            'body': body_text
        }

    def run(self):
        self.setup()

        for batch in self.links_generator():
            self.logger.info(f"Processing batch of {len(batch)} links")
            batch_results = self.fetch_batch_concurrently(batch)

            news = []
            for news_link, news_data in batch_results.items():
                news_link.has_processed = True

                if news_data is not None:
                    news.append(
                        News(
                            news_source=news_link.category.source.name,
                            news_category=news_link.category.category_name,
                            date=news_link.date,
                            news_link=news_link.get_full_url(),
                            title=news_data.get('title'),
                            body=news_data.get('body'),
                        )
                    )

            News.objects.bulk_create(news)
            NewsLink.objects.bulk_update(list(batch_results.keys()), ['has_processed'])
