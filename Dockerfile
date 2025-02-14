# Usa una imagen base con Python 3.11
FROM python:3.11-slim

# Instala Tesseract (y otros paquetes si necesitas)
RUN apt-get update && apt-get install -y tesseract-ocr

# Crea y usa una carpeta /app
WORKDIR /app

# Copia tu archivo de requisitos
COPY requirements.txt /app

# Instala dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de tu código
COPY . /app

# Expón el puerto 5000 (o el que uses en Flask)
EXPOSE 5000

# Lanza tu app (asegúrate de que tu app.py inicie Flask en 0.0.0.0:5000)
CMD ["python", "app.py"]
