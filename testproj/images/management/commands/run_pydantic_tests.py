from django.core.management.base import BaseCommand
from pydantic_tests import run_test


class Command(BaseCommand):
    def handle(self, *args, **options):
        run_test()
