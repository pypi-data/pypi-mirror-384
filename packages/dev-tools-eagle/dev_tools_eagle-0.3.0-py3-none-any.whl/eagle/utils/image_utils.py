import io
import base64
from PIL import Image
import plotly.graph_objects as go

def object_to_image_url(obj, format: str = None) -> str:
    """
    Converte diferentes tipos de objetos para uma image_url pronta para LLM multimodal.
    
    Suporta:
    - PIL.Image.Image: convertido para base64 usando o formato fornecido ou inferido.
    - plotly.graph_objs._figure.Figure: convertido para base64 usando o formato fornecido ou PNG por padrão.
    
    Retorna a string no formato:
    "data:image/<formato>;base64,<base64_string>"
    
    :param obj: O objeto a ser convertido (PIL image ou Plotly figure).
    :param format: Formato opcional ("PNG", "JPEG", "WEBP") para PIL ou Plotly.
    :return: String pronta para `image_url` em HumanMessage.
    """
    if isinstance(obj, Image.Image):
        buffer = io.BytesIO()
        fmt = format or (obj.format if obj.format else "PNG")

        # Convert RGBA -> RGB se for JPEG
        if fmt.lower() == "jpeg" and obj.mode == "RGBA":
            obj = obj.convert("RGB")

        obj.save(buffer, format=fmt)
        buffer.seek(0)
        b64_str = base64.b64encode(buffer.read()).decode("utf-8")
        mime_type = f"image/{fmt.lower()}"
        return f"data:{mime_type};base64,{b64_str}"

    elif isinstance(obj, go.Figure):
        buffer = io.BytesIO()
        fmt = (format or "png").lower()
        if fmt not in ["png", "jpeg", "webp", "svg", "pdf"]:
            raise ValueError("Formato não suportado para Plotly Figure. Use 'png', 'jpeg', 'webp', 'svg' ou 'pdf'.")
        obj.write_image(buffer, format=fmt)
        buffer.seek(0)
        b64_str = base64.b64encode(buffer.read()).decode("utf-8")
        return f"data:image/{fmt};base64,{b64_str}"

    else:
        return None

def normalized_crop(image: Image.Image, x1: float, y1: float, x2: float, y2: float) -> Image.Image:
    """
    Faz o crop da imagem usando coordenadas normalizadas:
    x de 0 (esquerda) a 1 (direita), y de 0 (baixo) a 1 (cima).
    (x1, y1, x2, y2) seguem a convenção (left, upper, right, lower).
    """
    width, height = image.size
    left = int(round(x1 * width))
    right = int(round(x2 * width))
    # y normalizado: 0 é embaixo, 1 é em cima -> converter para coordenada de pixel
    lower = int(round((1 - y1) * height))
    upper = int(round((1 - y2) * height))
    # Garantir que os limites estejam dentro da imagem
    left = max(0, min(left, width - 1))
    right = max(left + 1, min(right, width))
    upper = max(0, min(upper, height - 1))
    lower = max(upper + 1, min(lower, height))
    return image.crop((left, upper, right, lower))