import logging
import sys
import os
import httpx
import threading
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from functools import wraps


def thread_safe_singleton(func):
    """Decorator to make singleton initialization thread-safe."""
    lock = threading.Lock()

    @wraps(func)
    def wrapper(cls):
        if not cls.CONTEXT:
            with lock:
                if not cls.CONTEXT:  # double-check pattern
                    cls.CONTEXT = func(cls)
        return cls.CONTEXT
    return wrapper


@dataclass
class IntegrationContext:
    httpx_client: httpx.AsyncClient = field(default_factory=httpx.AsyncClient)
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger('centra_sdk'))
    component_id: str = None
    configuration: Dict = None
    schema: List = None


class IntegrationContextApi:
    CONTEXT: Optional[IntegrationContext] = None

    @classmethod
    async def clean(cls):
        if cls.CONTEXT:
            await cls.CONTEXT.httpx_client.aclose()
            cls.CONTEXT = None

    @classmethod
    @thread_safe_singleton
    def context(cls):
        if cls.CONTEXT is None:
            cls.CONTEXT = cls._build_context(cls._get_log_level())
        return cls.CONTEXT

    @classmethod
    def _build_context(cls, log_level):
        ctx = IntegrationContext()
        ctx.logger.setLevel(log_level)

        if not ctx.logger.handlers:
            formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(formatter)
            ctx.logger.addHandler(handler)

        return ctx

    @classmethod
    def client(cls):
        return cls.context().httpx_client

    @classmethod
    def log(cls):
        return cls.context().logger

    @classmethod
    def schema(cls):
        return cls.context().schema

    @classmethod
    def configuration(cls):
        return cls.context().configuration

    @classmethod
    def component_id(cls):
        return cls.context().component_id

    @classmethod
    def set_schema(cls, schema):
        """ Register schema of integration configuration.
        For example
        set_schema([
        ConfigOpts(
            name="api_url",
            opt_type=OptType.OPT_STRING,
            default_value="default",
            description="Inventory API URL"
        ), ..
        ])
        """
        cls.context().schema = schema

    @classmethod
    def set_component_id(cls, component_id):
        """ Set component_id that is used to identify integration on Centra side
        """
        cls.context().component_id = component_id

    @classmethod
    def set_configuration(cls, configuration: Dict):
        """ Set configuration as dict of Key: Value.
        For example: {api_url: http://www.integration.com, api_key: <123>}
        """
        cls.context().configuration = configuration

    @classmethod
    def set_log_level(cls, level: int):
        """Set the log level for the SDK logger."""
        cls.context().logger.setLevel(level)

    @classmethod
    def _get_log_level(cls) -> int:
        """Get log level from environment variable or default to INFO."""
        level_name = os.getenv('CENTRA_SDK_LOG_LEVEL', 'INFO').upper()
        return getattr(logging, level_name, logging.INFO)
