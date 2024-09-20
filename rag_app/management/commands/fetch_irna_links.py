import logging
import jdatetime

from django.core.management.base import BaseCommand

from rag_app.crawlers import IRNALinksCrawler


class Command(BaseCommand):
    help = 'Fetch Fresh Links of IRNA Press'

    def add_arguments(self, parser):
        parser.add_argument('--jalali-date', type=str, help='The jalali date in the format YYYY-MM-DD')

    def handle(self, *args, **options):
        date_string = options.get('jalali_date')
        jalali_date = jdatetime.datetime.strptime(date_string, "%Y-%m-%d")
        logger = logging.getLogger(__name__)

        crawler = IRNALinksCrawler(logger=logger, jalali_date=jalali_date)
        crawler.run()
