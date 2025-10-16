from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_core.language_models.chat_models import BaseChatModel
from eagle.memory.shared.shared_objects_memory import SharedObjectsMemory
from eagle.chains.image_interpretation import create_image_interpretation_chain, create_image_crop_suggestion_chain
from eagle.utils.pdf_utils import convert_pdf_page_to_image_with_max_bytes
from eagle.utils.image_utils import normalized_crop
import tempfile

class PdfPageToImageInput(BaseModel):
    pdf_id: str = Field(description="The ID of the PDF file stored in SharedObjectsMemory.")
    page_number: int = Field(description="The page number to convert (1-based index).")
    context_about_the_image: Optional[str] = Field(default="", description="Optional context about the image for interpretation.")
    crop_context: Optional[str] = Field(default="", description="Optional context for cropping the image.")

class PdfPageToImageTool(BaseTool):
    name: str = "pdf_page_to_image"
    description: str = (
        "Converts a page from a PDF (stored in SharedObjectsMemory) to an image (PIL), "
        "crops it if a crop context is passed, "
        "stores it in SharedObjectsMemory, and generates a name and description for the image using an LLM."
    )
    memory: SharedObjectsMemory
    chat_id: str
    llm: BaseChatModel
    max_image_bytes: int = 1000000
    prompt_language: str = "en"  # Add prompt_language for chain

    args_schema: Type[BaseModel] = PdfPageToImageInput

    def _run(self, **_inputs: PdfPageToImageInput) -> Dict[str, Any]:
        inputs = PdfPageToImageInput(**_inputs)
        pdf_obj = self.memory.get_memory(chat_id=self.chat_id, object_id=inputs.pdf_id)
        if not pdf_obj or not hasattr(pdf_obj, "object"):
            raise ValueError(f"No PDF found with ID: {inputs.pdf_id}")
        pdf_path = pdf_obj.object.metadata.disk_path
        # Convert the specified page to image
        with tempfile.TemporaryDirectory() as tmpdir:

            image = convert_pdf_page_to_image_with_max_bytes(
                pdf_path, 
                page_number=inputs.page_number, 
                max_bytes=self.max_image_bytes,
                dpi_max=160
            )

        base_context = f"PDF page {inputs.page_number} from shared object memory id {inputs.pdf_id}"

        combined_context = f"{base_context}\n{inputs.context_about_the_image}\n{inputs.crop_context}"
        
        # Se habilitado, sugere crop
        if inputs.crop_context:
            crop_chain = create_image_crop_suggestion_chain(prompt_language=self.prompt_language, llm=self.llm)
            crop_result = crop_chain.invoke({"image": image, "context": combined_context})
            try:
                x1, y1, x2, y2 = (
                    crop_result.x1,
                    crop_result.y1,
                    crop_result.x2,
                    crop_result.y2,
                )
                image = normalized_crop(image, x1, y1, x2, y2)
            except Exception:
                pass  # Se falhar, mantém imagem original
        # Use the image interpretation chain
        chain = create_image_interpretation_chain(prompt_language=self.prompt_language, llm=self.llm)
        result = chain.invoke({"image": image, "context": combined_context})
        # Ajuste para suportar pt-br e en
        if self.prompt_language == "pt-br":
            name = getattr(result, "nome", None) or f"Página do PDF {inputs.page_number}"
            description = getattr(result, "descricao", None) or f"Imagem da página {inputs.page_number} do PDF {inputs.pdf_id}"
            answer = getattr(result, "resposta", None) or ""
        else:
            name = getattr(result, "name", None) or f"PDF page {inputs.page_number}"
            description = getattr(result, "description", None) or f"Image of page {inputs.page_number} from PDF {inputs.pdf_id}"
            answer = getattr(result, "answer", None) or ""
        # Store the image in SharedObjectsMemory
        image_id = self.memory.put_memory(
            chat_id=self.chat_id,
            object_name=name,
            obj=image,
            description=description,
            object_type=type(image).__name__
        )
        # Monta o texto de resposta conforme idioma
        if self.prompt_language == "pt-br":
            response = (
                f"Fizemos um foco na imagem do PDF de acordo com a demanda. "
                f"Esse recorte está no shared memory com o id '{image_id}', com o nome '{name}' e descrição '{description}'.\n"
                f"{answer}"
            )
        else:
            response = (
                f"We focused on the PDF image according to the request. "
                f"This crop is stored in shared memory with id '{image_id}', name '{name}' and description '{description}'.\n"
                f"{answer}"
            )
        return response

    async def _arun(self, **_inputs: PdfPageToImageInput) -> Dict[str, Any]:
        # For simplicity, just call the sync version (could be improved for true async)
        return self._run(**_inputs)
