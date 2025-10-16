from pdf2image import convert_from_path
from PIL import Image
import io

def convert_pdf_page_to_image_with_max_bytes(pdf_path, page_number, max_bytes, dpi_min=50, dpi_max=400, output_format="PNG"):
    """
    Converte uma página do PDF em imagem, tentando limitar o tamanho em bytes ajustando o DPI.
    Retorna a imagem PIL.Image.
    """
    best_img = None
    best_dpi = dpi_min
    low, high = dpi_min, dpi_max
    while low <= high:
        dpi = (low + high) // 2
        images = convert_from_path(pdf_path, first_page=page_number, last_page=page_number, dpi=dpi)
        if not images:
            break
        img = images[0]
        buf = io.BytesIO()
        img.save(buf, format=output_format)
        size = buf.tell()
        if size <= max_bytes:
            best_img = img
            best_dpi = dpi
            low = dpi + 1  # tentar dpi maior
        else:
            high = dpi - 1  # tentar dpi menor
    if best_img is None:
        # Não conseguiu atingir o limite, retorna menor possível
        images = convert_from_path(pdf_path, first_page=page_number, last_page=page_number, dpi=dpi_min)
        if not images:
            raise ValueError("Não foi possível converter a página do PDF.")
        return images[0]
    return best_img
