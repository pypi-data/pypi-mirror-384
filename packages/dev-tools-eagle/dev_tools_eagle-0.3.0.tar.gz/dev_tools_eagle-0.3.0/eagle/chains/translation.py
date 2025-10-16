from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence, RunnablePassthrough
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.output_parsers.string import StrOutputParser

def create_translation_chain(
    prompt_language: str,
    llm: BaseLanguageModel
) -> RunnableSequence:
    """
    Create a translation chain based on the provided configuration.

    Args:
        prompt_language (str): Language for the prompt (e.g., "pt-br", "en").
        llm (BaseLanguageModel): Language model to be used for translation.

    Returns:
        RunnableSequence: A chain that translates text based on the provided configuration.
    """
    # Define prompts for different languages
    PROMPTS = {
        "pt-br": "Traduza o seguinte texto para português: {text}",
        "en": "Translate the following text to English: {text}",
    }
    
    # Select the appropriate prompt template
    if prompt_language not in PROMPTS:
        raise ValueError(f"Unsupported prompt language: {prompt_language}")
    prompt = PromptTemplate.from_template(PROMPTS[prompt_language])

    # Create chain using LCEL
    chain = (
        {"text": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain

