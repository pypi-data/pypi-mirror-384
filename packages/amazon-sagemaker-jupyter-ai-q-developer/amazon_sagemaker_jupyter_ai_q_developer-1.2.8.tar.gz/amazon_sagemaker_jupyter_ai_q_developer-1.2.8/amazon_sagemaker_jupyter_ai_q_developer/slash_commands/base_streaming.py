import datetime
import time
from typing import Any, Dict, Type
from uuid import uuid4

from amazon_sagemaker_jupyter_ai_q_developer.request_logger import (
    flush_metrics,
    get_new_metrics_context,
)
from jupyter_ai.callback_handlers import MetadataCallbackHandler
from jupyter_ai.chat_handlers.base import BaseChatHandler
from jupyter_ai.models import (
    AgentStreamChunkMessage,
    AgentStreamMessage,
    HumanChatMessage,
    Selection,
)
from jupyter_ai_magics.providers import BaseProvider
from langchain.prompts import PromptTemplate
from langchain_core.messages import AIMessageChunk
from sagemaker_jupyterlab_extension_common.util.environment import (
    EnvironmentDetector,
)


class BaseStreamingSlashCommand(BaseChatHandler):
    def _start_stream(self, human_msg: HumanChatMessage) -> str:
        """
        Sends an `agent-stream` message to indicate the start of a response
        stream. Returns the ID of the message, denoted as the `stream_id`.
        """
        stream_id = uuid4().hex
        stream_msg = AgentStreamMessage(
            id=stream_id,
            time=time.time(),
            body="",
            reply_to=human_msg.id,
            persona=self.persona,
            complete=False,
        )

        for handler in self._root_chat_handlers.values():
            if not handler:
                continue

            handler.broadcast_message(stream_msg)
            break

        return stream_id

    def _send_stream_chunk(
        self,
        stream_id: str,
        content: str,
        complete: bool = False,
        metadata: Dict[str, Any] = {},
    ):
        """
        Sends an `agent-stream-chunk` message containing content that should be
        appended to an existing `agent-stream` message with ID `stream_id`.
        """
        stream_chunk_msg = AgentStreamChunkMessage(
            id=stream_id, content=content, stream_complete=complete, metadata=metadata
        )

        for handler in self._root_chat_handlers.values():
            if not handler:
                continue

            handler.broadcast_message(stream_chunk_msg)
            break

    def _create_llm_chain(
        self,
        provider: Type[BaseProvider],
        provider_params: Dict[str, str],
        prompt_template: PromptTemplate,
    ):
        unified_parameters = {
            **provider_params,
            **(self.get_model_parameters(provider, provider_params)),
        }
        llm = provider(**unified_parameters)

        self.llm = llm
        self.llm_chain
        self.llm_chain = prompt_template | llm

    async def _process_message(
        self,
        message: HumanChatMessage,
        no_selection_msg: str,
        selection_limit: int,
        too_long_msg: str,
        name: str,
    ):
        environment = (await EnvironmentDetector.get_environment()).name
        metrics = get_new_metrics_context(f"{name}SlashCommand", environment)
        try:
            start_time = datetime.datetime.now()
            if not (message.selection):
                self.reply(no_selection_msg, message)
                metrics.put_metric("NoMessageSelectedFault", 1)
                return
            if len(message.selection.source) > selection_limit:
                self.reply(too_long_msg, message)
                metrics.put_metric("MessageTooLongFault", 1)
                return

            # hint type of selection
            selection: Selection = message.selection

            self.get_llm_chain()
            received_first_chunk = False

            # start with a pending message
            with self.pending("Generating response", message) as pending_message:
                # stream response in chunks
                metadata_handler = MetadataCallbackHandler()
                async for chunk in self.llm_chain.astream(
                    {"input": message.body, "code": selection.source},
                    config={
                        "configurable": {"last_human_msg": message},
                        "callbacks": [metadata_handler],
                    },
                ):
                    if not received_first_chunk:
                        # when receiving the first chunk, close the pending message and
                        # start the stream.
                        self.close_pending(pending_message)
                        stream_id = self._start_stream(human_msg=message)
                        received_first_chunk = True

                    if isinstance(chunk, AIMessageChunk):
                        self._send_stream_chunk(stream_id, chunk.content)
                    elif isinstance(chunk, str):
                        self._send_stream_chunk(stream_id, chunk)
                    else:
                        self.log.error(f"Unrecognized type of chunk yielded: {type(chunk)}")
                        metrics.put_metric("InvalidChunkTypeFault", 1)
                        break

                # complete stream after all chunks have been streamed
                self._send_stream_chunk(
                    stream_id, "", complete=True, metadata=metadata_handler.jai_metadata
                )

        finally:
            elapsed = datetime.datetime.now() - start_time
            metrics.put_metric("Latency", int(elapsed.total_seconds() * 1000), "Milliseconds")
            flush_metrics(metrics)
