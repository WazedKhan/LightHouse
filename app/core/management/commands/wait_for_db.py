"""
Command for wait until DB connection stabilized
"""
import time

from psycopg2 import OperationalError as Psycopg2OpError  # type: ignore

from django.db.utils import OperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Commands: wait for DB"""

    def handle(self, *args, **options):
        self.stdout.write('Waiting for DB connection..')
        db_up = False

        while db_up is False:
            try:
                self.check(databases=['default'])
                db_up = True
            except (Psycopg2OpError, OperationalError):
                self.stdout.write(self.style.WARNING('Database Connection failed, reconnecting in 1 sec..'))  # noqa
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS('DB connection stabilized.'))
