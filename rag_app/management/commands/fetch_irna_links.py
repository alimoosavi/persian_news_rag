import logging
import jdatetime

from django.core.management.base import BaseCommand

from rag_app.crawlers import IRNALinksCrawler


class Command(BaseCommand):
    help = 'Fetch Fresh Links of IRNA Press'

    def add_arguments(self, parser):
        parser.add_argument('--start_jalali_date', type=str, help='The start jalali date in the format YYYY-MM-DD')
        parser.add_argument('--end_jalali_date', type=str, help='The end jalali date in the format YYYY-MM-DD')

    def handle(self, *args, **options):
        start_jalali_date = jdatetime.datetime.strptime(options.get('start_jalali_date'),
                                                        "%Y-%m-%d")
        end_jalali_date = jdatetime.datetime.strptime(options.get('end_jalali_date'),
                                                      "%Y-%m-%d")
        logger = logging.getLogger(__name__)

        IRNALinksCrawler(
            start_jalali_date=start_jalali_date,
            end_jalali_date=end_jalali_date,
            logger=logger).run()
