from rag_app.models import NewsSource, NewsCategory, NewsLink


class IRNAContentCrawler:
    SOURCE_NAME = 'IRNA'

    def __init__(self, logger):
        self.logger = logger
        self.source = None
        self.categories = None
        self.not_processed_links = None

    def setup(self):
        self.source = NewsSource.objects.get(name=self.SOURCE_NAME)
        self.categories = NewsCategory.objects.filter(source=self.source)
        self.not_processed_links = NewsLink.objects.filter(category__source=self.source,
                                                           has_processed=False)
