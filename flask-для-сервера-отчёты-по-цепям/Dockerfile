FROM python:3.9-slim

WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY app.py .
COPY templates/ ./templates/

# Создаем директорию для данных
RUN mkdir -p /data

# Копируем данные
COPY data/ /data/

# Открываем порт
EXPOSE 5000

# Запускаем приложение
CMD ["python", "app.py"]