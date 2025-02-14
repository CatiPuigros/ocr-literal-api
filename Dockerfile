# Usa una imagen base con Python 3.11
FROM python:3.11-slim

# Instala Tesseract
RUN apt-get update && apt-get install -y tesseract-ocr

# Crea y usa la carpeta /app
WORKDIR /app

# Copia requirements.txt
COPY requirements.txt /app

# Instala dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de tu código
COPY . /app

# Expón el puerto 5000
EXPOSE 5000

# Lanza la aplicación Flask
CMD ["python", "main.py"]
