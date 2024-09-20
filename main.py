import os
import django
import logging
import asyncio

from rag_app.crawlers.irna_crawler import IRNALinksCrawler

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'persian_news_rag.settings')
django.setup()

logger = logging.getLogger(__name__)
crawler = IRNALinksCrawler(logger=logger)
asyncio.run(crawler.run())
