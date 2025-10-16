from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence, RunnableLambda
from langchain_core.language_models.base import BaseLanguageModel
from pydantic import BaseModel, Field
from typing import ClassVar
from operator import itemgetter
from eagle.utils.prompt_utils import EagleJsonOutputParser
from eagle.utils.image_utils import object_to_image_url 
import base64
from io import BytesIO
from langchain_core.messages import HumanMessage


class ImageInterpretationOutputEN(BaseModel):
    name: str = Field(description="A short, descriptive name for the image.")
    description: str = Field(description="A concise description of the image content.")
    answer: str = Field(description="An answer to the question or demand about the image.")

class ImageInterpretationOutputPTBR(BaseModel):
    nome: str = Field(description="Um nome curto e descritivo para a imagem.")
    descricao: str = Field(description="Uma descrição concisa do conteúdo da imagem.")
    resposta: str = Field(description="Uma resposta para a pergunta ou demanda sobre essa imagem.")

class ImageInterpretationOutputParser(EagleJsonOutputParser):
    CONVERTION_SCHEMA: ClassVar[dict] = {
        "pt-br": {
            "class_for_parsing": ImageInterpretationOutputPTBR,
            "convertion_schema": {
                "nome": {"target_key": "name", "value_mapping": {}},
                "descricao": {"target_key": "description", "value_mapping": {}},
                "resposta": {"target_key": "answer", "value_mapping": {}}
            }
        },
        "en": {
            "class_for_parsing": ImageInterpretationOutputEN,
            "convertion_schema": {
                "name": {"target_key": "name", "value_mapping": {}},
                "description": {"target_key": "description", "value_mapping": {}},
                "answer": {"target_key": "answer", "value_mapping": {}}
            }
        },
    }
    TARGET_SCHEMA: BaseModel = ImageInterpretationOutputEN

PROMPT_EN = "You are an expert at interpreting images. Given the following image and some optional context, generate a short, descriptive name, a concise description for the image and an answer to the question or demand about this image. Context (optional): {{context}}. Return your answer as JSON: {'name': ..., 'description': ..., 'answer': ...}"
PROMPT_PTBR = "Você é um especialista em interpretar imagens. Dada a seguinte imagem e um contexto opcional, gere um nome curto e descritivo, uma descrição concisa para a imagem e uma resposta para a pergunta ou demanda sobre essa imagem. Contexto (opcional): {{context}}. Retorne sua resposta em JSON: {'nome': ..., 'descricao': ..., 'resposta': ...}"

PROMPTS = {
    "en": PromptTemplate.from_template(PROMPT_EN, template_format="jinja2"),
    "pt-br": PromptTemplate.from_template(PROMPT_PTBR, template_format="jinja2"),
}

def create_image_interpretation_chain(prompt_language: str, llm: BaseLanguageModel, use_structured_output: bool = False) -> RunnableSequence:
    if prompt_language not in PROMPTS:
        raise ValueError(f"Unsupported prompt language: {prompt_language}")
    prompt = PROMPTS[prompt_language]
    output_parser = ImageInterpretationOutputParser(
        source_lang=prompt_language,
        llm=llm,
        use_structured_output=use_structured_output
    )
    _parse = RunnableLambda(lambda x: output_parser.parse(x))

    def prepare_message(inputs):
        image = inputs["image"]
        context = inputs.get("context", "")
        image_b64_url = object_to_image_url(image, format="JPEG")
        prompt_text = prompt.format(context=context)
        msg = HumanMessage(
            content=[
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": {"url": image_b64_url}}
            ]
        )
        return [msg]

    chain = (
        RunnableLambda(prepare_message)
        | llm
        | _parse
    )
    return chain

class ImageCropSuggestionOutputEN(BaseModel):
    x1: float = Field(description="Top-left normalized [0,1] x coordinate for crop.")
    y1: float = Field(description="Top-left normalized [0,1] y coordinate for crop.")
    x2: float = Field(description="Bottom-right normalized [0,1] x coordinate for crop.")
    y2: float = Field(description="Bottom-right normalized [0,1] y coordinate for crop.")

class ImageCropSuggestionOutputPTBR(BaseModel):
    x1: float = Field(description="Coordenada normalizada [0,1] x superior esquerda para o crop.")
    y1: float = Field(description="Coordenada normalizada [0,1] y superior esquerda para o crop.")
    x2: float = Field(description="Coordenada normalizada [0,1] x inferior direita para o crop.")
    y2: float = Field(description="Coordenada normalizada [0,1] y inferior direita para o crop.")

class ImageCropSuggestionOutputParser(EagleJsonOutputParser):
    CONVERTION_SCHEMA: ClassVar[dict] = {
        "pt-br": {
            "class_for_parsing": ImageCropSuggestionOutputPTBR,
            "convertion_schema": {
                "x1": {"target_key": "x1", "value_mapping": {}},
                "y1": {"target_key": "y1", "value_mapping": {}},
                "x2": {"target_key": "x2", "value_mapping": {}},
                "y2": {"target_key": "y2", "value_mapping": {}}
            }
        },
        "en": {
            "class_for_parsing": ImageCropSuggestionOutputEN,
            "convertion_schema": {
                "x1": {"target_key": "x1", "value_mapping": {}},
                "y1": {"target_key": "y1", "value_mapping": {}},
                "x2": {"target_key": "x2", "value_mapping": {}},
                "y2": {"target_key": "y2", "value_mapping": {}}
            }
        },
    }
    TARGET_SCHEMA: BaseModel = ImageCropSuggestionOutputEN

CROP_PROMPT_EN = (
    "Given the following image and context, suggest the best crop rectangle (x1, y1, x2, y2) as a (left, upper, right, lower)-tuple, "
    "where x and y are normalized from 0 to 1: x goes from left (0) to right (1), y goes from bottom (0) to top (1). "
    "Return as JSON: {'x1': ..., 'y1': ..., 'x2': ..., 'y2': ...}. Context: {{context}}."
)
CROP_PROMPT_PTBR = (
    "Dada a seguinte imagem e contexto, sugira o melhor retângulo de crop (x1, y1, x2, y2) como uma tupla (esquerda, superior, direita, inferior), "
    "onde x e y são normalizados de 0 a 1: x vai da esquerda (0) para a direita (1), y vai de baixo (0) para cima (1). "
    "Retorne em JSON: {'x1': ..., 'y1': ..., 'x2': ..., 'y2': ...}. Contexto: {{context}}."
)

CROP_PROMPTS = {
    "en": PromptTemplate.from_template(CROP_PROMPT_EN, template_format="jinja2"),
    "pt-br": PromptTemplate.from_template(CROP_PROMPT_PTBR, template_format="jinja2"),
}

def create_image_crop_suggestion_chain(prompt_language: str, llm: BaseLanguageModel, use_structured_output: bool = False) -> RunnableSequence:
    if prompt_language not in CROP_PROMPTS:
        raise ValueError(f"Unsupported prompt language: {prompt_language}")
    prompt = CROP_PROMPTS[prompt_language]
    output_parser = ImageCropSuggestionOutputParser(
        source_lang=prompt_language,
        llm=llm,
        use_structured_output=use_structured_output
    )
    _parse = RunnableLambda(lambda x: output_parser.parse(x))

    def prepare_message(inputs):
        image = inputs["image"]
        context = inputs.get("context", "")
        image_b64_url = object_to_image_url(image, format="JPEG")
        prompt_text = prompt.format(context=context)
        msg = HumanMessage(
            content=[
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": {"url": image_b64_url}}
            ]
        )
        return [msg]

    chain = (
        RunnableLambda(prepare_message)
        | llm
        | _parse
    )
    return chain


