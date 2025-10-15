from typing import Dict, Type

from jupyter_ai.chat_handlers.base import SlashCommandRoutingType
from jupyter_ai.models import HumanChatMessage
from jupyter_ai_magics.providers import BaseProvider
from langchain.prompts import PromptTemplate

from .base_streaming import BaseStreamingSlashCommand

EXPLAIN_STRING_TEMPLATE = """
Please explain the code below.

```
{code}
```
""".strip()

EXPLAIN_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=[
        "code",
    ],
    template=EXPLAIN_STRING_TEMPLATE,
)

EXPLAIN_NO_SELECTION_EMSG = """
`/explain` requires a selection of code to explain. Please first make a
selection by clicking on a notebook cell or selecting a range of text with your
cursor. Then, click the down arrow next to the send button, and click 'Send
message with selection'.
""".strip()

EXPLAIN_TOO_LONG = "Selection too large to explain. Must be 4066 characters or fewer."

EXPLAIN_SELECTION_LIMIT = 4066


class ExplainSlashCommand(BaseStreamingSlashCommand):
    """
    Explains a code selection.
    """

    id = "explain"
    name = "Explain code"
    help = "Explains code included in a selection."
    routing_type = SlashCommandRoutingType(slash_id="explain")
    uses_llm = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name: str = "Explain"

    def create_llm_chain(self, provider: Type[BaseProvider], provider_params: Dict[str, str]):
        self._create_llm_chain(provider, provider_params, EXPLAIN_PROMPT_TEMPLATE)

    async def process_message(self, message: HumanChatMessage):
        await self._process_message(
            message, EXPLAIN_NO_SELECTION_EMSG, EXPLAIN_SELECTION_LIMIT, EXPLAIN_TOO_LONG, self.name
        )
