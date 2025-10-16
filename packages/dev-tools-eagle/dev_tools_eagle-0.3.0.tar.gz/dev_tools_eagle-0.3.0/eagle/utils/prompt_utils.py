from typing import ClassVar
from pydantic import BaseModel
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import AIMessage
from langchain_core.language_models.chat_models import BaseChatModel
from eagle.utils.output import convert_schema



class PromptGenerator:
    """
    A utility class for generating prompts based on a provided dictionary of prompts.
    """

    def __init__(self, prompts_dict: dict):
        """
        Initialize the PromptGenerator with a dictionary of prompts.

        Args:
            prompts_dict (dict): A dictionary where the keys are prompt names and the values
                                 are dictionaries with language-specific prompts and a shared output parser.
        """
        self.prompts_dict = prompts_dict

    def generate_prompt(self, prompt_name: str, language: str, llm: BaseChatModel, use_structured_output: bool = False) -> dict:
        """
        Generate a prompt based on the prompt name and language.

        Args:
            prompt_name (str): The name of the prompt to generate.
            language (str): The language of the prompt to generate.
            use_structured_output (bool): Whether to use structured output for the prompt.
        Returns:
            dict: A dictionary containing the prompt and its associated output parser.

        Raises:
            ValueError: If the prompt name or language is not supported.
        """
        if prompt_name not in self.prompts_dict:
            raise ValueError(f"Prompt '{prompt_name}' is not supported in this prompt generator.")

        prompt_data = self.prompts_dict[prompt_name]

        if language not in prompt_data["languages"]:
            raise ValueError(f"Language '{language}' is not supported for prompt '{prompt_name}'.")

        output_parser = prompt_data["output_parser"](source_lang=language, llm=llm, use_structured_output=use_structured_output)

        return {
            "prompt": prompt_data["languages"][language],
            "output_parser": output_parser
        }
    
class EagleJsonOutputParser(JsonOutputParser):

    source_lang: str = "en"
    use_structured_output: bool = False
    llm: BaseChatModel = None
    CONVERTION_SCHEMA: ClassVar[dict] = {}
    TARGET_SCHEMA: BaseModel = None

    def __init__(self, source_lang: str, llm: BaseChatModel, use_structured_output: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.use_structured_output = use_structured_output
        self.source_lang = source_lang
        self.llm = llm

    def parse(self, message: AIMessage):
        """Parse the output of the LLM call to a JSON object."""
        try:
            # Use the utility function to handle schema conversion
            return convert_schema(
                message=message,
                conversion_schema=self.CONVERTION_SCHEMA,
                source_lang=self.source_lang,
                target_schema=self.TARGET_SCHEMA,
                use_structured_output=self.use_structured_output,
                llm=self.llm
            )
        except Exception as e:
            raise Exception(f"Failed to parse output: {e}") from e