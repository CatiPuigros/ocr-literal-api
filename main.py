import os
import io
import pytesseract
import easyocr
from flask import Flask, request, jsonify
from PIL import Image
from google.cloud import vision

# Configurar Flask
app = Flask(__name__)

# Configurar credenciales de Google Vision
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_credentials.json"
vision_client = vision.ImageAnnotatorClient()

# Inicializar EasyOCR con los idiomas clave (sin traducción, solo transcripción)
easy_reader = easyocr.Reader(['es', 'en', 'fr', 'de'], gpu=False)  

# Idiomas disponibles para Tesseract
TESSERACT_LANGUAGES = "spa+eng+fra+deu"

# Umbral de confianza para marcar "[ILEGIBLE]"
CONFIDENCE_THRESHOLD = 0.7

def extract_text_tesseract(image):
    """ Extrae texto con Tesseract, sin corrección automática. """
    try:
        text = pytesseract.image_to_string(image, lang=TESSERACT_LANGUAGES, config="--psm 6 --oem 3")
        return text.strip() if text.strip() else "[ILEGIBLE]"
    except Exception as e:
        print("Error en Tesseract:", e)
        return "[ILEGIBLE]"

def extract_text_google_vision(image):
    """ Extrae texto con Google Vision si Tesseract no logra resultados. """
    try:
        image_bytes = io.BytesIO()
        image.save(image_bytes, format="PNG")
        image_bytes = image_bytes.getvalue()

        image_google = vision.Image(content=image_bytes)
        response = vision_client.text_detection(image=image_google)
        texts = response.text_annotations

        if texts:
            return texts[0].description.strip()
        return "[ILEGIBLE]"
    except Exception as e:
        print("Error en Google Vision:", e)
        return "[ILEGIBLE]"

def extract_text_easyocr(image_path):
    """ Extrae texto con EasyOCR, si Tesseract y Google Vision fallan. """
    try:
        result = easy_reader.readtext(image_path, detail=1)  
        palabras = [text if conf >= CONFIDENCE_THRESHOLD else "[ILEGIBLE]" for (_, text, conf) in result]
        texto_final = " ".join(palabras).strip()
        return texto_final if texto_final else "[ILEGIBLE]"
    except Exception as e:
        print("Error en EasyOCR:", e)
        return "[ILEGIBLE]"

@app.route("/ocr", methods=["POST"])
def ocr_endpoint():
    """ API para recibir una imagen y extraer texto sin corrección automática. """
    if "file" not in request.files:
        return jsonify({"error": "No se envió ninguna imagen"}), 400

    file = request.files["file"]
    image_path = "temp_image.png"
    file.save(image_path)
    image = Image.open(image_path)

    # Paso 1: Intenta con Tesseract
    tesseract_text = extract_text_tesseract(image)

    # Paso 2: Si Tesseract no funciona, prueba con Google Vision
    if tesseract_text == "[ILEGIBLE]":
        google_text = extract_text_google_vision(image)
    else:
        google_text = "[NO NECESARIO]"

    # Paso 3: Si Google Vision también falla, usa EasyOCR
    if tesseract_text == "[ILEGIBLE]" and google_text == "[ILEGIBLE]":
        easyocr_text = extract_text_easyocr(image_path)
    else:
        easyocr_text = "[NO NECESARIO]"

    return jsonify({
        "tesseract": tesseract_text,
        "google_vision": google_text,
        "easyocr": easyocr_text
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


