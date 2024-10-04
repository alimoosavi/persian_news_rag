from rag_app.models import NewsSource, NewsLink, News

from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class TradingViewsContentCrawler:
    SOURCE_NAME = 'TradingView'

    def __init__(self, logger):
        self.logger = logger
        self.source = None
        self.routes = None

    def setup(self):
        self.source = NewsSource.objects.get(name=self.SOURCE_NAME)
        self.routes = NewsLink.objects.filter(source=self.source).values_list('news_link', flat=True)

    @staticmethod
    def get_web_driver():
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        return webdriver.Chrome(options=chrome_options)

    def fetch(self, route):
        driver = self.get_web_driver()
        try:
            url = urljoin(self.source.base_url, route)
            driver.get(url)
            return driver.page_source
        finally:
            driver.quit()

    def get_news(self, route):
        html_content = self.fetch(route)
        soup = BeautifulSoup(html_content, 'html.parser')

        print(html_content)

        title = soup.find('h2',
                          class_='title-KX2tCBZq').text
        # body = soup.find('div',
        #                  class_='body-KX2tCBZq body-pIO_GYwT content-pIO_GYwT').text
        #
        print(title)
        # return News(news_source=self.source.name,
        #             news_link=route,
        #             title=title,
        #             body=body)

    def run(self):
        self.setup()

        for route in self.routes:
            self.get_news(route)
        # News.objects.bulk_create([self.get_news(route)
        #                           for route in self.routes])
