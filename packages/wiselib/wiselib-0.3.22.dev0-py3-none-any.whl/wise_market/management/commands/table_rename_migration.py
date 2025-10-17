from django.core.management import BaseCommand, call_command
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
    def get_dependencies(app_label, models):
        loader = MigrationLoader(connection, ignore_no_migrations=True)
        state = loader.project_state()
        model_names = [model.lower() for model in models]
        dependent_apps = set()
        for model, related_models in state.relations.items():
            if model[0] == app_label and model[1] in model_names:
                for related_model in related_models.keys():
                    dependent_apps.add(related_model[0])

        dependent_apps.remove(app_label)

        return (leaf for leaf in loader.graph.leaf_nodes() if leaf[0] in dependent_apps)

    def handle(self, *args, **options):
        app_label = options["app_label"]

        models = options["models"]
        if not models:
            models = self._models.copy()

        migration, migration_file = get_empty_migration(app_label, "wise_rename_tables")

        migration.operations.append(
            migrations.SeparateDatabaseAndState(
                database_operations=[
                    *(
                        migrations.AlterModelTable(
                            model, f"wise_market_{model.lower()}"
                        )
                        for model in models
                    )
                ]
            )
        )

        migration.dependencies = set(migration.dependencies).union(
            self.get_dependencies(app_label, models)
        )

        writer = MigrationWriter(migration)
        migration_content = writer.as_string()
        migration_content = migration_content.replace(
            "dependencies",
            "run_before = [\n"
            "        ('wise_market', '0001_initial')\n"
            "    ]\n\n"
            "    dependencies",
        )

        with open(migration_file, "w") as f:
            f.write(migration_content)
