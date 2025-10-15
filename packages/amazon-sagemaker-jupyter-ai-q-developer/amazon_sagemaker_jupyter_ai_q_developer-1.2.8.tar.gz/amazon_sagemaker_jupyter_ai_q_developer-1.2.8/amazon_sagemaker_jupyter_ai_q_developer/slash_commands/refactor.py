from typing import Dict, Type

from jupyter_ai.chat_handlers.base import SlashCommandRoutingType
from jupyter_ai.models import HumanChatMessage
from jupyter_ai_magics.providers import BaseProvider
from langchain.prompts import PromptTemplate

from .base_streaming import BaseStreamingSlashCommand

REFACTOR_STRING_TEMPLATE = """
Please refactor the code below.

```
{code}
```
""".strip()

REFACTOR_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=[
        "code",
    ],
    template=REFACTOR_STRING_TEMPLATE,
)

REFACTOR_NO_SELECTION_EMSG = """
`/refactor` requires a selection of code to refactor. Please first make a
selection by clicking on a notebook cell or selecting a range of text with your
cursor. Then, click the down arrow next to the send button, and click 'Send
message with selection'.
""".strip()

REFACTOR_TOO_LONG = "Selection too large to refactor. Must be 4065 characters or fewer."

REFACTOR_SELECTION_LIMIT = 4065


class RefactorSlashCommand(BaseStreamingSlashCommand):
    """
    Refactors a code selection.
    """

    id = "refactor"
    name = "Refactor code"
    help = "Refactors code included in a selection."
    routing_type = SlashCommandRoutingType(slash_id="refactor")
    uses_llm = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name: str = "Refactor"

    def create_llm_chain(self, provider: Type[BaseProvider], provider_params: Dict[str, str]):
        self._create_llm_chain(provider, provider_params, REFACTOR_PROMPT_TEMPLATE)

    async def process_message(self, message: HumanChatMessage):
        await self._process_message(
            message,
            REFACTOR_NO_SELECTION_EMSG,
            REFACTOR_SELECTION_LIMIT,
            REFACTOR_TOO_LONG,
            self.name,
        )
