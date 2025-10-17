from typing import Optional, Union

from ...util import random
from ...util.context_singleton import ContextSingletonProtocol, context_singleton
from .config import Config
from .protocol import Protocol

_DEFAULT_PROTOCOL = {}


@context_singleton
class Pipeline(ContextSingletonProtocol):
    id: str
    protocol: Optional[Protocol]
    config: Config

    def __init__(
        self,
        *,
        id: str = None,
        protocol: Optional[Protocol] = _DEFAULT_PROTOCOL,
        config: Union[dict, Config] = None,
    ):
        self.id = id or random.string()
        if protocol is _DEFAULT_PROTOCOL:
            self.protocol = Protocol.get_instance_or()
        else:
            self.protocol = protocol
        config = config or Config.get_instance_or()
        if isinstance(config, dict):
            config = Config(inputs=config)
        self.config = config
