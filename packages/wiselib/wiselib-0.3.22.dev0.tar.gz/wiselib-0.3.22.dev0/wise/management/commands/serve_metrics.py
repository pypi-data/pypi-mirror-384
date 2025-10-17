import logging
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer, make_server
from django.core.management.base import BaseCommand
from prometheus_client import make_wsgi_app

from wise.utils.monitoring import REGISTRY

logger = logging.getLogger(__name__)


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    """Thread per request HTTP server."""

    # Make worker threads "fire and forget". Beginning with Python 3.7 this
    # prevents a memory leak because ``ThreadingMixIn`` starts to gather all
    # non-daemon threads in a list in order to join on them at server close.
    daemon_threads = True


class Command(BaseCommand):
    help = "Serve prometheus metrics endpoint"

    def add_arguments(self, parser):
        parser.add_argument("addr", type=str)
        parser.add_argument("port", type=int)

    def handle(self, *args, **options):
        app = make_wsgi_app(REGISTRY)
        httpd = make_server(options["addr"], options["port"], app, ThreadingWSGIServer)
        logger.info(f"Metrics are exposed on port {options['port']}...\n")
        httpd.serve_forever()
