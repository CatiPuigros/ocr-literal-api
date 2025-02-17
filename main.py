import os
import io
import base64
import pytesseract
from flask import Flask, request, jsonify
from PIL import Image
from google.cloud import vision

app = Flask(__name__)

# Configurar credenciales de Google Vision
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_credentials.json"
vision_client = vision.ImageAnnotatorClient()

# Idiomas disponibles para Tesseract
TESSERACT_LANGUAGES = "spa+eng+fra+deu"

def extract_text_tesseract(image):
    """Extrae texto con Tesseract sin corrección automática."""
    try:
        text = pytesseract.image_to_string(
            image,
            lang=TESSERACT_LANGUAGES,
            config="--psm 6 --oem 3"
        )
        return text.strip() if text.strip() else "[ILEGIBLE]"
    except Exception as e:
        print("Error en Tesseract:", e)
        return "[ILEGIBLE]"

def extract_text_google_vision(image):
    """Extrae texto con Google Vision si Tesseract no logra resultados."""
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

@app.route("/", methods=["GET"])
def home():
    """Endpoint para la raíz: Verifica que la API esté activa."""
    return jsonify({"message": "API de OCR activa. Usa POST /ocr para enviar imágenes."}), 200

@app.route("/ocr", methods=["POST"])
def ocr_endpoint():
    """Endpoint para recibir una imagen y extraer texto."""
    
    # Intentar obtener la imagen enviada como archivo (form-data)
    if "file" in request.files:
        file = request.files["file"]
        try:
            image = Image.open(file)
        except Exception:
            return jsonify({"error": "El archivo no es una imagen válida"}), 400

    # Si no viene "file", intentar obtener la imagen en formato base64 desde JSON
    else:
        data = request.get_json(silent=True)
        if not data or "image_base64" not in data:
            return jsonify({"error": "No se envió ninguna imagen (ni archivo ni base64)"}), 400

        try:
            image_data = base64.b64decode(data["image_base64"])
            image = Image.open(io.BytesIO(image_data))
        except Exception as e:
            print("Error decodificando base64:", e)
            return jsonify({"error": "No se pudo decodificar la imagen base64"}), 400

    # Paso 1: Extraer texto con Tesseract
    tesseract_text = extract_text_tesseract(image)

    # Paso 2: Si Tesseract no pudo extraer texto, usar Google Vision
    if tesseract_text == "[ILEGIBLE]":
        google_text = extract_text_google_vision(image)
    else:
        google_text = "[NO NECESARIO]"

    return jsonify({
        "tesseract": tesseract_text,
        "google_vision": google_text
    })

if __name__ == "__main__":
    # Usar el puerto asignado por Render o el 5000 por defecto
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

