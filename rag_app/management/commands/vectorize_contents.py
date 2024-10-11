import logging
import jdatetime

from django.core.management.base import BaseCommand

# from rag_app.crawlers import IRNALinksCrawler
from rag_app.vectorizer import NewsVectorizer


class Command(BaseCommand):
    help = 'Vectorize Contents from IRNA Press'

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        NewsVectorizer(logger=logger).run()
