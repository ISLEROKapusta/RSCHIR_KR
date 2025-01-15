# Используем образ Python 3.12
FROM python:3.12

# Устанавливаем рабочую директорию
WORKDIR /var/www/html

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости без использования кэша
RUN python3.12 -m pip install --no-cache-dir -r requirements.txt

# Копируем приложение в рабочую директорию
COPY ./src /var/www/html

# Указываем порт, который будет использовать приложение
EXPOSE 8000

# Команда для запуска FastAPI приложения через uvicorn
CMD ["python3.12", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


