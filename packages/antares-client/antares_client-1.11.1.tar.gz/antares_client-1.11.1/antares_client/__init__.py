from importlib.metadata import version

from . import search
from .exceptions import AntaresException

__version__ = version("antares_client")

try:
    from .stream import StreamingClient
except ImportError:

    class _MissingStreamingClient:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "To use KafkaStreamingClient you must install confluent_kafka or antares-client[subscriptions]"
            )

    StreamingClient = _MissingStreamingClient
