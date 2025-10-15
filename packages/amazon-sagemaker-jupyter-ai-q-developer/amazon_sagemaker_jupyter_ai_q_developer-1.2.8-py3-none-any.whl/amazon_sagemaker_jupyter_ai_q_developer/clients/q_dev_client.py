import json
import logging
from abc import ABC, abstractmethod
from functools import partial

from amazon_sagemaker_jupyter_ai_q_developer.clients.base_client import (
    BaseClient,
)
from amazon_sagemaker_jupyter_ai_q_developer.constants import (
    MD_IDE,
    USE_DUALSTACK_ENDPOINT,
)
from botocore import UNSIGNED
from sagemaker_jupyterlab_extension_common.util.environment import Environment

CW_PROD_ENDPOINT = "https://codewhisperer.us-east-1.amazonaws.com"
CW_DUALSTACK_PROD_ENDPOINT = "https://codewhisperer.us-east-1.api.aws.com"
logging.basicConfig(format="%(levelname)s: %(message)s")

# we have limit of 5 relevant documents with each having 10k token limit according to Q Developer
MAX_TOKEN_SIZE = 10000


class QDevClient(ABC, BaseClient):
    def __init__(self):
        self._client = None
        self.cw_endpoint = (
            CW_DUALSTACK_PROD_ENDPOINT if USE_DUALSTACK_ENDPOINT else CW_PROD_ENDPOINT
        )

    def _process_prompt(self, prompt):
        """Process the prompt and extract relevant information."""
        question = prompt  # Set a default value
        relevant_documents = []

        try:
            # First, try to parse as JSON
            prompt_dict = json.loads(prompt)
            question = prompt_dict.get("question", prompt)

            if "context" in prompt_dict:
                relevantText = prompt_dict.get("context", "")[:MAX_TOKEN_SIZE]
                relevant_documents.append(
                    {"text": relevantText, "relativeFilePath": "relevant main document"}
                )

            return question, relevant_documents
        except json.JSONDecodeError:
            # JSON parsing failed, continue with other methods
            pass

        return question, relevant_documents

    def _prepare_request_data(
        self, question, relevant_documents, conversation_id=None, customization_arn=None
    ):
        """Prepare the common request data structure."""
        data = {
            "chatTriggerType": "MANUAL",
            "currentMessage": {
                "userInputMessage": {
                    "content": question,
                    "userInputMessageContext": {
                        "editorState": {
                            "relevantDocuments": relevant_documents,
                            "useRelevantDocuments": bool(relevant_documents),
                        }
                    },
                }
            },
        }

        if conversation_id:
            data["conversationId"] = conversation_id

        if customization_arn:
            data["customizationArn"] = customization_arn

        return data

    @abstractmethod
    def call_chat_api(
        self, prompt, q_dev_profile_arn, conversation_id=None, customization_arn=None, origin=None
    ):
        pass


class QDevSSOClient(QDevClient):
    def __init__(self, opt_out):
        super().__init__()
        client = QDevSSOClient.get_client(
            service_name="bearer",
            endpoint_url=self.cw_endpoint,
            api_version="2023-11-27",
            region_name=self.cw_endpoint.split(".")[1],
            signature_version=UNSIGNED,
        )
        partial_add_header = partial(QDevSSOClient.add_header, opt_out=opt_out)
        client.meta.events.register("before-sign.*.*", partial_add_header)
        self._client = client

    def call_chat_api(
        self, prompt, q_dev_profile_arn, conversation_id=None, customization_arn=None, origin=None
    ):
        question, relevant_documents = self._process_prompt(prompt)
        data = self._prepare_request_data(
            question, relevant_documents, conversation_id, customization_arn
        )

        # Set origin in userInputMessage for GenerateAssistantResponse
        if origin:
            data["currentMessage"]["userInputMessage"]["origin"] = origin

        response = self._client.generate_assistant_response(
            conversationState=data, profileArn=q_dev_profile_arn
        )
        event_stream = response["generateAssistantResponseResponse"]

        return {
            "conversationId": response.get("conversationId", None),
            "eventStream": event_stream,
            "requestId": response.get("ResponseMetadata", None).get("RequestId", ""),
        }


class QDevIAMClient(QDevClient):
    def __init__(self, opt_out):
        super().__init__()
        logging.info("Initializing QDevIAMClient...")
        client = QDevIAMClient.get_client(
            service_name="qdeveloperstreaming",
            endpoint_url=self.cw_endpoint,
            region_name=self.cw_endpoint.split(".")[1],
            api_version="2024-06-11",
        )
        self._client = client
        # no headers are needed because this is sigv4 based free tier

    def call_chat_api(
        self, prompt, q_dev_profile_arn, conversation_id=None, customization_arn=None, origin=None
    ):
        question, relevant_documents = self._process_prompt(prompt)
        data = self._prepare_request_data(
            question, relevant_documents, conversation_id, customization_arn
        )

        # we don not use q_dev_profile_arn
        if origin:
            data["currentMessage"]["userInputMessage"]["origin"] = origin
            response = self._client.send_message(conversationState=data, source=origin)
        else:
            response = self._client.send_message(conversationState=data)
        response_stream = response["sendMessageResponse"]
        metadata = {}
        # messageMetadataEvent is not available for Maestro
        if origin != MD_IDE:
            for event in response_stream:
                if "messageMetadataEvent" in event:
                    metadata = event["messageMetadataEvent"]
                    break

        return {
            "conversationId": metadata.get("conversationId", None),
            "eventStream": response_stream,
            "requestId": response.get("ResponseMetadata", None).get("RequestId", ""),
        }


class QDevChatClientFactory:
    _clients = {
        Environment.STUDIO_SSO: QDevSSOClient,
        Environment.MD_IDC: QDevSSOClient,
        Environment.STUDIO_IAM: QDevIAMClient,
        Environment.MD_IAM: QDevIAMClient,
    }

    @classmethod
    def get_client(cls, environment, opt_out):
        logging.info(f"Getting client creator for ${environment}")
        creator = cls._clients.get(environment)
        if not creator:
            raise ValueError(environment)
        return creator(opt_out=opt_out)
