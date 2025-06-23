import fitz  # PDF
from PIL import Image
import easyocr # Imagenes lectura OCR
from io import BytesIO
import numpy as np

reader = easyocr.Reader(['es', 'en'], gpu=False)

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        text = ""
        for page in doc:
            text += page.get_text()
        return text.strip()

def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    image = Image.open(BytesIO(image_bytes))
    image_np = np.array(image)  # 👈 Convertimos PIL → numpy.ndarray
    result = reader.readtext(image_np)
    return "\n".join([item[1] for item in result])
