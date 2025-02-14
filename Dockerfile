# Usa una imagen base con Python 3.11
FROM python:3.11-slim

# Instala Tesseract y los idiomas necesarios
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    tesseract-ocr-cat \
    tesseract-ocr-glg \
    tesseract-ocr-eus \
    tesseract-ocr-eng \
    tesseract-ocr-fra \
    tesseract-ocr-deu \
    curl && \
    apt-get clean

# Instala dependencias de Python
WORKDIR /app
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código
COPY . /app

# Expón el puerto 5000
EXPOSE 5000

# Lanza la aplicación Flask
CMD ["python", "main.py"]
