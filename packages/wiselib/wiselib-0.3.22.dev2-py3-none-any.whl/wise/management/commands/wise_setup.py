import logging

from django.core.management.base import BaseCommand

from wise.station.registry import station_registry
from wise.utils.periodic_tasks import set_periodic_tasks

logger = logging.getLogger("Consumer")


class Command(BaseCommand):
    def handle(self, *args, **options):
        if station_registry.periodic_tasks is not None:
            set_periodic_tasks(
                station_registry.periodic_tasks,
                station_registry.periodic_tasks_disable_rest,
            )
