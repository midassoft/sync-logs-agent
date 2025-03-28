Comandos para levantar el proyecto:
# Reconstruir la imagen (usando el Dockerfile)
docker build -t logs-management .

# Levantar el contenedor
docker run -d \
  --name logs-management \
  -p 8000:8000 \
  -v $(pwd)/app:/app \
  logs-management