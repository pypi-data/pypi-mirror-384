import datetime
import html
import logging
import traceback
import uuid
from typing import Any, Coroutine, Iterator, List, Mapping, Optional

import requests
from botocore.exceptions import ClientError, EndpointConnectionError
from jupyter_ai_magics import Persona
from jupyter_ai_magics.providers import AwsAuthStrategy, BaseProvider
from langchain.prompts import PromptTemplate
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM
from langchain_core.outputs import GenerationChunk
from sagemaker_jupyterlab_extension_common.util.environment import (
    Environment,
    EnvironmentDetector,
)

from amazon_sagemaker_jupyter_ai_q_developer.clients.q_dev_client import (
    QDevChatClientFactory,
    QDevClient,
)
from amazon_sagemaker_jupyter_ai_q_developer.clients.telemetry_client import (
    TelemetryClientFactory,
)
from amazon_sagemaker_jupyter_ai_q_developer.constants import (
    MD_IDE,
    Q_DEVELOPER_SETTINGS_ENDPOINT,
)
from amazon_sagemaker_jupyter_ai_q_developer.exceptions import ServerExtensionException
from amazon_sagemaker_jupyter_ai_q_developer.file_cache_manager import FileCacheManager
from amazon_sagemaker_jupyter_ai_q_developer.request_logger import (
    flush_metrics,
    get_new_metrics_context,
)
from amazon_sagemaker_jupyter_ai_q_developer.utils import (
    get_ide_category,
    get_q_customization_arn,
    get_q_dev_profile_arn,
    get_settings_property_value,
    get_smus_q_enabled,
    get_telemetry_event,
    is_smus_environment,
)

logging.basicConfig(format="%(levelname)s: %(message)s")

REQUEST_OPTOUT_HEADER_NAME = "x-amzn-codewhisperer-optout"


class AmazonQLLM(LLM):
    UNSUBSCRIBED_MESSAGE: str = (
        "You are not subscribed to Amazon Q Developer. Please request your Studio domain admin to subscribe you. "
        "<a href='https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/q-admin-setup-subscribe-general.html'>"
        "Please refer link.</a>"
    )

    SM_UNSUBSCRIBED_MESSAGE: str = (
        "It looks like you aren't authorized to chat. "
        "You or your AWS administrator might need to update your IAM permissions or restore access to your subscription. For more information, see the "
        "<a href='https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/q-admin-setup-subscribe-general.html#q-admin-setup-subscribe-troubleshooting'>"
        "Amazon Q Documentation.</a> After you obtain the necessary permissions, reload this page to access Amazon Q."
    )

    INVALID_CUSTOMIZATION_MESSAGE: str = "The customization you are using is invalid. Please choose a different customization option from the Other Features page located in the Amazon Q footer."

    GENERATE_RESPONSE_ERROR_MESSAGE: str = "Sorry, an error occurred. Details below:\n\n%s"

    MAX_Q_INPUT_SIZE_CHARS: int = 600000

    model_id: str
    """Required in the constructor. Allowed values: ('Q-Developer')"""

    _client: Optional[QDevClient] = None
    """boto3 client object."""

    _conversation_id: Optional[str] = None
    """The conversation ID included with the first response from Amazon Q."""

    _client_id: Optional[str] = uuid.uuid4()
    """The client ID included with the first response from Amazon Q."""

    file_cache_manager: FileCacheManager = FileCacheManager()

    q_dev_chat_client_factory: QDevChatClientFactory = QDevChatClientFactory()
    telemetry_client_factory: TelemetryClientFactory = TelemetryClientFactory()

    _currentEnv: Optional[Environment] = None

    settings: dict = {}
    """Q Developer extension settings"""

    @property
    def _llm_type(self) -> str:
        return "custom"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        response = ""
        for chunk in self._stream(prompt, **kwargs):
            response += chunk.text
        return response

    def _get_settings(self, metrics):
        settings = {
            "share_content_with_aws": False,
            "suggestions_with_code_references": False,
            "telemetry_enabled": False,
            "log_level": "ERROR",
        }
        get_settings_start_time = datetime.datetime.now()
        try:
            # Q_DEVELOPER_SETTINGS_ENDPOINT is in parity with base url from SMD so in local development
            # it won't be able to fetch settings and also locally headers have to be manually appended for this to work
            response = requests.get(Q_DEVELOPER_SETTINGS_ENDPOINT)
            settings_data = response.json()
            settings["share_content_with_aws"] = get_settings_property_value(
                settings_data, "shareCodeWhispererContentWithAWS", False
            )
            settings["suggestions_with_code_references"] = get_settings_property_value(
                settings_data, "suggestionsWithCodeReferences", False
            )
            settings["telemetry_enabled"] = get_settings_property_value(
                settings_data, "codeWhispererTelemetry", False
            )
            settings["log_level"] = get_settings_property_value(
                settings_data, "codeWhispererLogLevel", "ERROR"
            )
        except Exception as e:
            logging.warning(f"Can not read Q Developer settings, using default values. Error: {e}")
        finally:
            elapsed = datetime.datetime.now() - get_settings_start_time
            metrics.put_metric(
                "SettingsLatency", int(elapsed.total_seconds() * 1000), "Milliseconds"
            )
        return settings

    async def _astream(
        self,
        prompt: str,
        stop=None,
        run_manager=None,
        **kwargs: Any,
    ):
        if self._currentEnv is None:
            self._currentEnv = await EnvironmentDetector.get_environment()

        async for chunk in super()._astream(prompt, stop, run_manager, **kwargs):
            yield chunk

    def _stream(
        self,
        prompt: str,
        *args: Any,
        **kwargs: Any,
    ) -> Iterator[GenerationChunk]:
        environment = self._currentEnv
        if environment is None:
            raise RuntimeError("Environment not initialized. Ensure _acall is called first.")

        # TODO: extract to wrapper based metrics collection mechanism, debug issue with wrapper function
        metrics = get_new_metrics_context("AmazonQLLM_call", environment.name)
        start_time = datetime.datetime.now()

        if len(prompt) > self.MAX_Q_INPUT_SIZE_CHARS:
            raise ValueError(
                f" Your input exceeds the {self.MAX_Q_INPUT_SIZE_CHARS} character limit. Please shorten your message and try again."
            )

        self.settings = self._get_settings(metrics)
        telemetry_enabled = self.settings.get("telemetry_enabled", False)
        logging.info(f"Q Developer Settings: {self.settings}")
        # TODO: consolidate the environment specific changes in a single place, it is scattered too much right now
        self._subscription_error_message = self.UNSUBSCRIBED_MESSAGE
        if is_smus_environment(environment):
            self._subscription_error_message = self.SM_UNSUBSCRIBED_MESSAGE
        try:
            if self.model_id != "Q-Developer":
                raise ValueError("Only 'Q-Developer' is supported by this model provider.")

            # if the environment has changed since the last call, reinstantiate the clients.
            if not self._client or environment != self._currentEnv:
                logging.info("Switching environment to " + environment.value)
                self._init_clients(environment)

            self._currentEnv = environment

            try:
                q_dev_profile_arn = get_q_dev_profile_arn(environment)
                logging.info(f"Q Dev Profile ARN: {q_dev_profile_arn}")
            except (FileNotFoundError, ServerExtensionException):
                metrics.set_property("QDevProfileArnFile", traceback.format_exc())
                # If q_dev_profile.json is not found or the value is an empty string,
                # then we can assume that domain is not Q enabled
                raise ValueError(self._subscription_error_message)

            origin = None
            if is_smus_environment(environment):
                origin = MD_IDE
                try:
                    ## if q is not enabled in the domain, return the error message
                    q_enabled = get_smus_q_enabled(environment)
                    if not q_enabled:
                        raise ValueError(self._subscription_error_message)
                except (FileNotFoundError, ServerExtensionException):
                    metrics.set_property("QSettingsFileQEnabled", traceback.format_exc())
                    raise ValueError(self._subscription_error_message)

            try:
                q_customization_arn = get_q_customization_arn(environment)
                logging.info(f"Q Selected Customization ARN: {q_customization_arn}")
            except (FileNotFoundError, ServerExtensionException):
                # If customization_arn.json is not found or the value is an empty string,
                # then we can assume that customization is not enabled
                q_customization_arn = None
            except Exception:
                # all other errors in fetching customization arn
                raise ValueError(self.INVALID_CUSTOMIZATION_MESSAGE)

            generate_start_time = datetime.datetime.now()

            try:
                response = self._client.call_chat_api(
                    prompt=prompt,
                    q_dev_profile_arn=q_dev_profile_arn,
                    conversation_id=self._conversation_id,
                    customization_arn=q_customization_arn,
                    origin=origin,
                )

                conversation_id = response.get("conversationId", None)
                message_id = response["requestId"]
                event_stream = response["eventStream"]

                if self._conversation_id is None and conversation_id:
                    logging.info(f"Assigned conversation ID '{conversation_id}'.")
                    self._conversation_id = conversation_id
                    AmazonQLLM._conversation_id = conversation_id
                metrics.set_property("ConversationID", self._conversation_id)
                metrics.set_property("MessageID", message_id)
                metrics.set_property(
                    "HasQCustomization", 1 if q_customization_arn is not None else 0
                )
                for event in event_stream:
                    if "assistantResponseEvent" in event:
                        content = html.unescape(event["assistantResponseEvent"]["content"])
                        yield GenerationChunk(
                            text=content,
                        )

                # Add metadata at the end with empty text to yield metadata only one time
                yield GenerationChunk(
                    text="",
                    generation_info={
                        "q_conversation_id": conversation_id,
                        "q_message_id": message_id,
                    },
                )

            except EndpointConnectionError as e:
                # TODO: exact error message to be updated after PM sign off.
                raise ConnectionError(
                    "{}. Please check your network settings or contact support for assistance.".format(
                        str(e)
                    )
                )

            except ClientError as e:
                metrics.set_property("GenerateAssistantException", traceback.format_exc())
                if e.response["Error"]["Code"] == "AccessDeniedException":
                    if (
                        "reason" in e.response
                        and e.response["reason"] == "UNAUTHORIZED_CUSTOMIZATION_RESOURCE_ACCESS"
                    ):
                        raise ValueError(self.INVALID_CUSTOMIZATION_MESSAGE)
                    raise ValueError(self._subscription_error_message)
                elif len(prompt) > self.MAX_Q_INPUT_SIZE_CHARS:
                    raise ValueError(
                        f" Your input exceeds the {self.MAX_Q_INPUT_SIZE_CHARS} character limit. Please shorten your message and try again."
                    )
                else:
                    raise
            finally:
                generate_elapsed_time = datetime.datetime.now() - generate_start_time
                metrics.put_metric(
                    "GenerateAssistantLatency",
                    int(generate_elapsed_time.total_seconds() * 1000),
                    "Milliseconds",
                )

            ide_category = get_ide_category(environment)
            telemetry_start_time = datetime.datetime.now()
            telemetry_event = get_telemetry_event(
                "chatAddMessageEvent",
                conversation_id,
                message_id,
                metrics,
                q_dev_profile_arn,
            )
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
        except Exception as e:
            error_details = {
                "error_type": type(e).__name__,
                "error_msg": str(e),
                "conversation_id": self._conversation_id,
                "environment": self._currentEnv,
                "stacktrace": traceback.format_exc(),
            }
            metrics.set_property("StackTrace", traceback.format_exc())
            logging.error(f"Stream error details: {error_details}")
            yield GenerationChunk(
                text=(
                    self.GENERATE_RESPONSE_ERROR_MESSAGE
                    % f"Type: {type(e).__name__}\nDetails: {str(e)}"
                )
            )
        finally:
            elapsed = datetime.datetime.now() - start_time
            metrics.put_metric("Latency", int(elapsed.total_seconds() * 1000), "Milliseconds")
            flush_metrics(metrics)

    def _init_clients(self, environment):
        opt_out = not self.settings.get("share_content_with_aws", False)
        self._client = self.q_dev_chat_client_factory.get_client(
            environment=environment, opt_out=opt_out
        )
        self._telemetry_client = self.telemetry_client_factory.get_client(
            environment=environment, opt_out=opt_out
        )

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {}


AMAZON_Q_AVATAR_ROUTE = "api/ai/static/q.svg"
AmazonQPersona = Persona(name="Amazon Q", avatar_route=AMAZON_Q_AVATAR_ROUTE)


class AmazonQProvider(BaseProvider, AmazonQLLM):
    id = "amazon-q"
    name = "Amazon Q"
    models = [
        "Q-Developer",
    ]
    model_id_key = "model_id"
    pypi_package_deps = ["boto3"]
    auth_strategy = AwsAuthStrategy()

    persona = AmazonQPersona
    unsupported_slash_commands = {"/generate"}
    manages_history = True

    @property
    def allows_concurrency(self):
        return False

    def get_chat_prompt_template(self) -> PromptTemplate:
        """
        Produce a prompt template optimised for chat conversation.
        This overrides the default prompt template, as Amazon Q expects just the
        raw user prompt without any additional templating.
        """
        return PromptTemplate.from_template(template="{input}")

    async def _acall(self, *args, **kwargs) -> Coroutine[Any, Any, str]:
        if self._currentEnv is None:
            self._currentEnv = await EnvironmentDetector.get_environment()
        return await self._call_in_executor(*args, **kwargs)
