# # your_app/management/commands/your_command.py
# import logging
#
# from django.core.management.base import BaseCommand
#
# from rag_app.crawlers import IRNALinksCrawler
#
#
# class Command(BaseCommand):
#     help = 'Fetch IRNA Contents based on fresh links'
#
#     def handle(self, *args, **kwargs):
#         logger = logging.getLogger(__name__)
#         crawler = IRNALinksCrawler(logger=logger)
#         crawler.run()
