import os
import logging
from dotenv import load_dotenv
import asyncio
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,    
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from das.ai.plugins.entries.entries_plugin import GetEntryByCodePlugin
from das.common.config import load_openai_api_key

logger = logging.getLogger(__name__)
load_dotenv()

class DasAI:

    def __init__(self):
        self.kernel = Kernel()
        api_key = os.getenv("OPENAI_API_KEY") or load_openai_api_key()
        if not api_key:
            raise ValueError("OpenAI API key is not configured.")
        self.openai_chat_completion = OpenAIChatCompletion(ai_model_id="gpt-4o-mini", api_key=api_key)
        self.kernel.add_service(self.openai_chat_completion)
        self.kernel.add_plugin(GetEntryByCodePlugin(), plugin_name="get_entry_by_code")                                

    async def main(self):
        history = ChatHistory()
        history.add_system_message("You are a laboratory assistent that helps researchers; phD students and any employee of NIOZ to find their answers in DAS (Data Archive System). Only answer questions about DAS.")
        user_input = None
        while user_input != "exit":
            user_input = input("User > ")
            history.add_user_message(user_input)
            result = await self.openai_chat_completion.get_chat_message_content(
                chat_history=history,
                settings=PromptExecutionSettings(
                    api_key=os.getenv("OPENAI_API_KEY") or load_openai_api_key(),
                    function_choice_behavior=FunctionChoiceBehavior.Auto()
                ),
                kernel=self.kernel
            )           
            print("Assistant >",str(result))
            history.add_message(result)


if __name__ == "__main__":
    ai = DasAI()    
    asyncio.run(ai.main())