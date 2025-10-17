from urllib.parse import urlparse

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from wise.settings.env import SentrySettings


class SentryHandler:
    @staticmethod
    def traces_sampler(sampling_context):
        # This deactivates sending performance metrics (aka transactions) to the Sentry server
        # This was done because we do not need them and our Sentry instance cannot tolerate such a high-load
        return 0

    @staticmethod
    def setup_sentry(config: SentrySettings):
        if config.enabled:
            sentry_sdk.init(
                dsn=config.dsn,
                integrations=[
                    DjangoIntegration(),
                ],
                environment=config.environment,
                send_default_pii=True,
                traces_sampler=SentryHandler.traces_sampler,
            )
