import os

from jupyter_server.extension.application import ExtensionApp
from tornado.web import StaticFileHandler

from amazon_sagemaker_jupyter_ai_q_developer.request_logger import (
    init_api_operation_logger,
)

from .handlers import TelemetryHandler
from .provider import AmazonQPersona

AMAZON_Q_AVATAR_PATH = str(os.path.join(os.path.dirname(__file__), "static", "q.svg"))


class SagemakerQChatExtension(ExtensionApp):
    name = "amazon_sagemaker_jupyter_ai_q_developer"
    handlers = [
        # serve the default persona avatar at this path.
        # the `()` at the end of the URL denotes an empty regex capture group,
        # required by Tornado.
        (
            rf"{AmazonQPersona.avatar_route}()",
            StaticFileHandler,
            {"path": AMAZON_Q_AVATAR_PATH},
        ),
        (r"amazon_sagemaker_jupyter_ai_q_developer/telemetry/?", TelemetryHandler),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        init_api_operation_logger(self.log)
