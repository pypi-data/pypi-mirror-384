import datetime
import json
import logging
import traceback

import tornado
from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
from sagemaker_jupyterlab_extension_common.util.environment import (
    EnvironmentDetector,
)

from amazon_sagemaker_jupyter_ai_q_developer.clients.telemetry_client import (
    TelemetryClientFactory,
)
from amazon_sagemaker_jupyter_ai_q_developer.exceptions import ServerExtensionException
from amazon_sagemaker_jupyter_ai_q_developer.request_logger import (
    flush_metrics,
    get_new_metrics_context,
)
from amazon_sagemaker_jupyter_ai_q_developer.utils import (
    get_ide_category,
    get_q_dev_profile_arn,
    get_settings_async,
    get_telemetry_event,
)

logging.basicConfig(format="%(levelname)s: %(message)s")


class RouteHandler(APIHandler):
    # The following decorator should be present on all verb methods (head, get, post,
    # patch, put, delete, options) to ensure only authorized user can request the
    # Jupyter server
    @tornado.web.authenticated
    def get(self):
        self.finish(
            json.dumps(
                {"data": "This is /amazon_sagemaker_jupyter_ai_q_developer/get-example endpoint!"}
            )
        )


def setup_handlers(web_app):
    host_pattern = ".*$"

    base_url = web_app.settings["base_url"]
    route_pattern = url_path_join(
        base_url, "amazon_sagemaker_jupyter_ai_q_developer", "get-example"
    )
    handlers = [(route_pattern, RouteHandler)]
    web_app.add_handlers(host_pattern, handlers)


class TelemetryHandler(APIHandler):
    telemetry_client_factory = TelemetryClientFactory()

    @tornado.web.authenticated
    async def post(self):
        event = self.get_json_body()
        message = event.get("message", {})

        # Ignore events emitted from non-AI messages
        if message["type"] not in ("agent", "agent-stream"):
            self.finish()
            return

        # Get conversation and message ID
        metadata = message.get("metadata", {})
        conversation_id = metadata.get("q_conversation_id", None)
        message_id = metadata.get("q_message_id", None)

        # Do nothing if either conversation and message ID are missing
        if not (message_id and conversation_id):
            self.finish()
            return

        # Send telemetry event
        await self.send_telemetry_event(event, conversation_id, message_id)

        self.finish()

    async def send_telemetry_event(self, event, conversation_id, message_id):
        # Get info required to send telemetry event
        environment = await EnvironmentDetector.get_environment()
        metrics = get_new_metrics_context("AmazonQLLM_Telemetry", environment.name)
        metrics.set_property("ConversationID", conversation_id)
        metrics.set_property("MessageID", message_id)
        settings = await get_settings_async(metrics)
        telemetry_enabled = settings.get("telemetry_enabled", False)
        ide_category = get_ide_category(environment)

        opt_out = not settings.get("share_content_with_aws", False)
        self._telemetry_client = self.telemetry_client_factory.get_client(
            environment=environment, opt_out=opt_out
        )

        try:
            q_dev_profile_arn = get_q_dev_profile_arn(environment)
            logging.info(f"Q Dev Profile ARN: {q_dev_profile_arn}")
        except (FileNotFoundError, ServerExtensionException):
            metrics.set_property("QDevProfileArnFile", traceback.format_exc())
            logging.error(traceback.format_exc())
            # If q_dev_profile.json is not found or the value is an empty string,
            # then we can assume that domain is not Q enabled
            raise ValueError(self._subscription_error_message)

        # Get telemetry event data
        telemetry_event = get_telemetry_event(
            "chatInteractWithMessageEvent",
            conversation_id,
            message_id,
            metrics,
            q_dev_profile_arn,
            event,
        )
        # Send telemetry event to Q
        telemetry_start_time = datetime.datetime.now()
        try:
            self._telemetry_client.send_telemetry_event(
                ide_category=ide_category,
                telemetry_enabled=telemetry_enabled,
                q_dev_profile_arn=q_dev_profile_arn,
                telemetry_event=telemetry_event,
            )
        except Exception:
            # Get the request ID from the exception metadata
            metrics.set_property("SendTelemetryException", traceback.format_exc())
            logging.error(traceback.format_exc())
        finally:
            telemetry_elapsed_time = datetime.datetime.now() - telemetry_start_time
            metrics.put_metric(
                "TelemetryLatency",
                int(telemetry_elapsed_time.total_seconds() * 1000),
                "Milliseconds",
            )

        flush_metrics(metrics)
