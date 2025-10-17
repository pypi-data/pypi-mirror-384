from django.core.management import BaseCommand
from django.db import migrations, connection
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.writer import MigrationWriter

from wise_market.management.commands.utils import get_empty_migration


class Command(BaseCommand):
    _models = [
        "Exchange",
        "Market",
        "Network",
        "Symbol",
        "ExchangeMarket",
        "Pair",
        "NetworkSymbolBinding",
        "Asset",
        "ExchangeMarketPairBinding",
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "app_label",
            type=str,
            help="The app for which to create the migration.",
        )

        parser.add_argument("models", help="Models that need to be replaced", nargs="*")

    @staticmethod
    def get_dependencies():
        loader = MigrationLoader(connection, ignore_no_migrations=True)

        return (
            leaf
            for leaf in loader.graph.leaf_nodes()
            if ("wise_market", "0001_initial")
            in loader.get_migration(*leaf).dependencies
        )

    def handle(self, *args, **options):
        app_label = options["app_label"]

        models = options["models"]

        if not models:
            models = self._models.copy()

        migration, migration_file = get_empty_migration(
            app_label, "wise_remove_old_models"
        )

        migration.operations.append(
            migrations.SeparateDatabaseAndState(
                state_operations=[*(migrations.DeleteModel(model) for model in models)]
            )
        )

        migration.dependencies.extend(self.get_dependencies())

        writer = MigrationWriter(migration)
        migration_content = writer.as_string()
        with open(migration_file, "w") as f:
            f.write(migration_content)
