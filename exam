from fastapi import FastAPI, UploadFile, File
import pytesseract
from PIL import Image
import io

app = FastAPI()

@app.post("/ocr/")
async def process_image(file: UploadFile = File(...)):
    image = Image.open(io.BytesIO(await file.read()))
    
    # Configuración para evitar correcciones del OCR
    custom_config = r'--psm 6 -c preserve_interword_spaces=1'
    raw_text = pytesseract.image_to_string(image, config=custom_config)

    # Postprocesado para marcar palabras ilegibles
    processed_text = raw_text.replace("?", "[ILEGIBLE]")  # Simple ajuste, mejorable con IA

    return {"text": processed_text}
