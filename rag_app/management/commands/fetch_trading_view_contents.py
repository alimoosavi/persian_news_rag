import logging

from django.core.management.base import BaseCommand

from rag_app.crawlers import TradingViewsContentCrawler


class Command(BaseCommand):
    help = 'Fetch Fresh Links of Trading View News'

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        TradingViewsContentCrawler(logger=logger).run()