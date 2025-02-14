from flask import Flask, request, jsonify
import pytesseract
from PIL import Image
import easyocr
import io
import os
from google.cloud import vision

app = Flask(__name__)

# 1) Configurar credenciales de Google Vision
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_credentials.json"

# 2) Inicializar EasyOCR con múltiples idiomas
#    (soporte para catalán, español, inglés, francés, alemán, gallego, euskera)
#    Ojo que esto puede requerir descargar distintos modelos => la primera vez será más lento.
easy_reader = easyocr.Reader(['ca','es','en','fr','de','gl','eu'], gpu=False)

# Umbral de confianza para marcar [ILEGIBLE]
confidence_threshold = 0.7

def tesseract_ocr(image_path):
    """
    Tesseract deshabilitando diccionarios (load_system_dawg=false, load_freq_dawg=false)
    y usando varios idiomas: catalán (cat), español (spa), inglés (eng), francés (fra),
    alemán (deu), gallego (glg), euskera (eus).
    NOTA: Debes haber instalado los 'traineddata' para cada idioma en Tesseract.
    """
    try:
        img = Image.open(image_path)

        # Config para reducir correcciones automáticas
        tesseract_config = (
            "--psm 6 --oem 3 "
            "-c load_system_dawg=false "
            "-c load_freq_dawg=false"
        )

        # Llamada con múltiples idiomas (si no los tienes instalados, Tesseract fallará)
        text = pytesseract.image_to_string(
            img,
            lang="cat+spa+eng+fra+deu+glg+eus",
            config=tesseract_config
        )

        text_limpio = text.strip()
        return text_limpio if text_limpio else "[ILEGIBLE]"
    except Exception as e:
        print("Error Tesseract:", e)
        return "[ILEGIBLE]"

def easyocr_ocr(image_path):
    """
    EasyOCR palabra por palabra (detail=1) y si la confianza es baja, marcamos [ILEGIBLE].
    """
    try:
        result = easy_reader.readtext(image_path, detail=1)  # detail=1 da bounding box y confidence
        palabras = []
        for (bbox, text, confidence) in result:
            if confidence < confidence_threshold or not text.strip():
                palabras.append("[ILEGIBLE]")
            else:
                palabras.append(text)
        texto_final = " ".join(palabras).strip()
        return texto_final if texto_final else "[ILEGIBLE]"
    except Exception as e:
        print("Error EasyOCR:", e)
        return "[ILEGIBLE]"

def google_vision_ocr(image_path):
    """
    Google Vision no expone "un modo literal", pero podemos analizar palabra a palabra
    revisando la 'confidence' en cada símbolo.
    """
    try:
        client = vision.ImageAnnotatorClient()
        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        response = client.text_detection(image=image)

        if response.error.message:
            print("Google Vision error:", response.error.message)
            return "[ILEGIBLE]"

        annotations = response.full_text_annotation
        if not annotations.text:
            return "[ILEGIBLE]"

        # Extraemos cada bloque, párrafo o palabra. Aquí iremos palabra a palabra
        # y si su confidence es baja, la marcamos [ILEGIBLE].
        palabras = []
        for page in annotations.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        # confidence está en word.confidence (0.0 a 1.0)
                        word_text = "".join([symbol.text for symbol in word.symbols])
                        if (word.confidence < confidence_threshold) or (not word_text.strip()):
                            palabras.append("[ILEGIBLE]")
                        else:
                            palabras.append(word_text)
        texto_final = " ".join(palabras).strip()
        return texto_final if texto_final else "[ILEGIBLE]"
    except Exception as e:
        print("Error Google Vision:", e)
        return "[ILEGIBLE]"

@app.route('/ocr', methods=['POST'])
def ocr_endpoint():
    if 'file' not in request.files:
        return jsonify({"error": "No se adjuntó ningún archivo"}), 400

    file = request.files['file']
    image_path = "temp_image.png"
    file.save(image_path)

    # Procesar imagen con los tres OCR
    tesseract_text = tesseract_ocr(image_path)
    easyocr_text = easyocr_ocr(image_path)
    google_text = google_vision_ocr(image_path)

    # Retornar resultado en JSON
    return jsonify({
        "tesseract": tesseract_text,
        "easyocr": easyocr_text,
        "google_vision": google_text
    })

if __name__ == '__main__':
    # Nota: Si ya tienes port=5000, añade host='0.0.0.0'
    app.run(host='0.0.0.0', port=5000, debug=True)
