FROM python:3.10-slim

WORKDIR /app

# Primero copia requirements e instala dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Luego copia TODO el proyecto
COPY . .

# Asegúrate que Python pueda encontrar tu módulo
ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]