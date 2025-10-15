from typing import Dict, Type

from jupyter_ai.chat_handlers.base import SlashCommandRoutingType
from jupyter_ai.models import HumanChatMessage
from jupyter_ai_magics.providers import BaseProvider
from langchain.prompts import PromptTemplate

from .base_streaming import BaseStreamingSlashCommand

OPTIMIZE_STRING_TEMPLATE = """
Please optimize the code below.

```
{code}
```
""".strip()

OPTIMIZE_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=[
        "code",
    ],
    template=OPTIMIZE_STRING_TEMPLATE,
)

OPTIMIZE_NO_SELECTION_EMSG = """
`/optimize` requires a selection of code to optimize. Please first make a
selection by clicking on a notebook cell or selecting a range of text with your
cursor. Then, click the down arrow next to the send button, and click 'Send
message with selection'.
""".strip()

OPTIMIZE_TOO_LONG = "Selection too large to optimize. Must be 4065 characters or fewer."

OPTIMIZE_SELECTION_LIMIT = 4065


class OptimizeSlashCommand(BaseStreamingSlashCommand):
    """
    Optimizes a code selection.
    """

    id = "optimize"
    name = "Optimize code"
    help = "Optimizes code included in a selection."
    routing_type = SlashCommandRoutingType(slash_id="optimize")
    uses_llm = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name: str = "Optimize"

    def create_llm_chain(self, provider: Type[BaseProvider], provider_params: Dict[str, str]):
        self._create_llm_chain(provider, provider_params, OPTIMIZE_PROMPT_TEMPLATE)

    async def process_message(self, message: HumanChatMessage):
        await self._process_message(
            message,
            OPTIMIZE_NO_SELECTION_EMSG,
            OPTIMIZE_SELECTION_LIMIT,
            OPTIMIZE_TOO_LONG,
            self.name,
        )
