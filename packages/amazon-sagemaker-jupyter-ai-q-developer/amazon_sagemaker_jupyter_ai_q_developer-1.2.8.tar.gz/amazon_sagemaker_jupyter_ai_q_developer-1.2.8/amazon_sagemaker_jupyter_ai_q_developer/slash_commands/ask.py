import datetime
import json
import logging
from typing import Dict, Type

from amazon_sagemaker_jupyter_ai_q_developer.request_logger import (
    flush_metrics,
    get_new_metrics_context,
)
from jupyter_ai.chat_handlers.ask import AskChatHandler
from jupyter_ai.models import HumanChatMessage
from jupyter_ai_magics.providers import BaseProvider
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from sagemaker_jupyterlab_extension_common.util.environment import (
    EnvironmentDetector,
)

# Configure logging
logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)


class CustomAskChatHandler(AskChatHandler):
    """Custom Ask handler using LCEL without chat history"""

    def create_llm_chain(self, provider: Type[BaseProvider], provider_params: Dict[str, str]):
        unified_parameters = {
            **provider_params,
            **(self.get_model_parameters(provider, provider_params)),
        }
        self.llm = provider(**unified_parameters)

        def format_as_json_string(inputs):
            question = inputs["question"]
            docs = inputs["docs"]

            # Create context chunks with minimal metadata headers
            context_chunks = []
            for doc in docs:
                # Add file path with minimal prefix
                if "path" in doc.metadata:
                    context_chunks.append(f"# {doc.metadata['path']}\n{doc.page_content}")
                else:
                    context_chunks.append(doc.page_content)

            # Join with minimal separators
            context_text = "\n---\n".join(context_chunks)

            # Create JSON object and convert to compact string
            json_data = {
                "question": question,
                "context": context_text,
            }
            json_string = json.dumps(json_data, ensure_ascii=False)

            return json_string

        # Define the chain using LCEL
        retriever_chain = self.retriever.with_config({"run_name": "Retrieve"})
        self.llm_chain = (
            {"question": RunnablePassthrough(), "docs": retriever_chain}
            | RunnableLambda(format_as_json_string)
            | self.llm
            | StrOutputParser()
        )

    async def process_message(self, message: HumanChatMessage):
        try:
            environment = (await EnvironmentDetector.get_environment()).name
            metrics = get_new_metrics_context("AskSlashCommand", environment)
            start_time = datetime.datetime.now()
            args = self.parse_args(message)
            if args is None:
                return
            query = " ".join(args.query)
            if not query:
                self.reply(f"{self.parser.format_usage()}", message)
                return

            self.get_llm_chain()

            with self.pending("Searching learned documents", message):
                assert self.llm_chain
                response = await self.llm_chain.ainvoke(query)
            self.reply(response, message)
            metrics.put_metric("Fault", 0)
        except Exception as e:
            self.log.error(f"Error during /ask processing: {str(e)}")
            response = """Sorry, an error occurred while reading the from the learned documents.
            If you have changed the embedding provider, try deleting the existing index by running
            `/learn -d` command and then re-submitting the `learn <directory>` to learn the documents,
            and then asking the question again.
            """
            self.reply(response, message)
            metrics.put_metric("Fault", 1)
        finally:
            elapsed = datetime.datetime.now() - start_time
            metrics.put_metric("Latency", int(elapsed.total_seconds() * 1000), "Milliseconds")
            flush_metrics(metrics)
