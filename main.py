import os
import django
import logging
import asyncio

from rag_app.news_crawlers.irna_crawler import IRNACrawler

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'persian_news_rag.settings')
django.setup()

logger = logging.getLogger(__name__)
crawler = IRNACrawler(logger=logger)
asyncio.run(crawler.run())
