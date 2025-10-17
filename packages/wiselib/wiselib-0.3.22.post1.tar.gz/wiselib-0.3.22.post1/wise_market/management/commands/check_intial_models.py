from django.core.management import BaseCommand


from django.db.migrations.loader import MigrationLoader
from django.db import connection


class Command(BaseCommand):
    _model_names = [
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

    def compare_model_fields(self, state1, state2):
        # Extract field names from both ModelStates
        fields1 = {name: field for name, field in state1.fields.items()}
        fields2 = {name: field for name, field in state2.fields.items()}

        # Find added, removed, and modified fields
        added = fields2.keys() - fields1.keys()
        removed = fields1.keys() - fields2.keys()
        modified = {
            name: diff
            for name in fields1.keys() & fields2.keys()
            if (
                diff := self.diff_dicts(
                    fields1[name].__dict__,
                    fields2[name].__dict__,
                    {"creation_counter", "remote_field"},
                )
            )
        }

        return {"added": added, "removed": removed, "modified": modified}

    def compare_model_metadata(self, state1, state2):
        options1 = state1.options
        options2 = state2.options

        # Compare options
        differences = self.diff_dicts(options1, options2)

        return differences

    def compare_model_states(self, state1, state2):
        # Compare fields
        fields_diff = self.compare_model_fields(state1, state2)

        # Compare metadata
        meta_diff = self.compare_model_metadata(state1, state2)

        return {"fields": fields_diff, "metadata": meta_diff}

    def diff_dicts(self, dict1, dict2, exclude=None):
        if exclude is None:
            exclude = {}
        return {
            key: (dict1.get(key), dict2.get(key))
            for key in set(dict1.keys()).union(dict2.keys()).difference(exclude)
            if dict1.get(key) != dict2.get(key)
        }

    def handle(self, *args, **options):
        print("Checking initial models...")
        loader = MigrationLoader(connection, ignore_no_migrations=True)
        state = loader.project_state()

        app_label = options["app_label"]

        model_names = options["models"]

        if not model_names:
            model_names = self._model_names.copy()

        for model_name in model_names:
            model_name = model_name.lower()
            wise_model = state.models[("wise_market", model_name.lower())]
            model = state.models[(app_label, model_name)]
            comparison = self.compare_model_states(wise_model, model)
            diffs = []
            for verb in ["added", "removed"]:
                if comparison["fields"][verb]:
                    for f in comparison["fields"][verb]:
                        diffs.append(f"{f} has been {verb}.")
            if comparison["metadata"]:
                diffs.append(f"metadata {comparison['metadata']}")
            for field_name, diff in comparison["fields"]["modified"].items():
                diffs.append(f"field {field_name} is modified {diff}")

            if diffs:
                print("\n    ".join([f"{model_name} has changed:"] + diffs))
