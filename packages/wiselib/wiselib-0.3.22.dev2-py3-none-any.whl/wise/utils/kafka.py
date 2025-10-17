import json
import logging
from functools import cached_property
from time import perf_counter as time_now

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from kafka.producer import KafkaProducer as KafkaProducerClient

from wise.utils.monitoring import KAFKA_PRODUCE_DURATION
from wise.utils.tracing import with_trace

logger = logging.getLogger(__name__)


class KafkaProducer:
    def __init__(self, topic_name: str):
        self.topic_name = topic_name

    @cached_property
    def instance(
        self,
    ) -> KafkaProducerClient:
        kafka = settings.ENV.kafka
        assert kafka.enabled

        return KafkaProducerClient(
            bootstrap_servers=kafka.bootstrap_servers,
            security_protocol=kafka.security_protocol,
            sasl_mechanism=kafka.sasl_mechanism,
            sasl_plain_username=kafka.username,
            sasl_plain_password=kafka.password,
            api_version=(0, 10, 2),
            value_serializer=lambda m: json.dumps(m, cls=DjangoJSONEncoder).encode(
                "utf-8"
            ),
            key_serializer=lambda k: k.encode("utf-8"),
        )

    @with_trace("produce")
    def produce(self, key: str, value: dict, should_close: bool = False):
        logger.info(
            f"Attempting to send message to kafka: topic={self.topic_name}, {key=}, {value=}"
        )

        start = time_now()
        success = "false"

        retries = 0
        while retries < 5:
            try:
                self.instance.send(self.topic_name, value, key)
                success = "true"
            except Exception as e:
                logger.exception(e)
                retries += 1
            else:
                break

        KAFKA_PRODUCE_DURATION.labels(self.topic_name, success).observe(
            time_now() - start
        )

        if should_close:
            self.instance.close()

    def close(self):
        self.instance.close()
