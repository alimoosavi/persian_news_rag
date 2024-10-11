import threading

from bs4 import BeautifulSoup
from django.core.paginator import Paginator

from rag_app.crawlers import utils
from rag_app.models import NewsSource, NewsLink, News


class IRNAContentCrawler:
    SOURCE_NAME = 'IRNA'
    BATCH_SIZE = 20

    def __init__(self, logger):
        self.logger = logger
        self.source = None
        self.not_processed_links = None

    def setup(self):
        self.source = NewsSource.objects.get(name=self.SOURCE_NAME)
        self.not_processed_links = NewsLink.objects.filter(source=self.source,
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
        results = {}
        threads = []

        def thread_fetch(news_link):
            html_content = self.fetch(news_link.get_full_url())
            results[news_link] = html_content

        # Create and start threads
        for nl in batch:
            thread = threading.Thread(target=thread_fetch, args=(nl,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        result_dict = {}
        for nl, html_content in results.items():
            try:
                result_dict[nl] = self.process_news_content_page(html_content) if html_content else None
            except:
                result_dict[nl] = None
        return result_dict

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
                            news_source=news_link.source.name,
                            date=news_link.date,
                            news_link=news_link.get_full_url(),
                            title=news_data.get('title'),
                            body=news_data.get('body'),
                        )
                    )

            News.objects.bulk_create(news)
            NewsLink.objects.bulk_update(list(batch_results.keys()), ['has_processed'])
