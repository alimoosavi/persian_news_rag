from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from rag_app.models import NewsSource, NewsLink


class TradingViewNewsLinkCrawler:
    TRADING_VIEW_NEWS_SOURCE = 'https://www.tradingview.com/symbols/BTCUSD/news/?exchange=OANDA'

    def __init__(self, logger):
        self.logger = logger
        self.source = None
        self.routes = set({})

    @staticmethod
    def get_web_driver():
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        return webdriver.Chrome(options=chrome_options)

    @classmethod
    def fetch(cls):
        driver = cls.get_web_driver()
        try:
            driver.get(cls.TRADING_VIEW_NEWS_SOURCE)
            return driver.page_source
        finally:
            driver.quit()

    def setup(self):
        self.source = NewsSource.objects.get(name='TradingView')

    def run(self):
        self.setup()

        page_source = self.fetch()

        soup = BeautifulSoup(page_source, 'html.parser')
        links = soup.find_all('a', href=True)
        routes = set([link['href']
                      for link in links
                      if link is not None and link['href'].startswith('/news/')])

        self.routes.update(routes)
        news_links = [
            NewsLink(source=self.source, news_link=route)
            for route in self.routes]
        NewsLink.objects.bulk_create(news_links)