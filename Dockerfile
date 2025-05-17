# Используем официальный образ Python
FROM python:3.13-slim

# Устанавливаем переменные окружения для корректной работы Python и wkhtmltopdf
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV QT_QPA_PLATFORM=offscreen

# Устанавливаем необходимые пакеты
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    wkhtmltopdf \
    fonts-liberation \
    fonts-freefont-ttf \
#    tk \  # <--- Добавлено для tkinter
#    tcl \  # <--- Добавлено для tkinter
    && rm -rf /var/lib/apt/lists/*

# Обновляем pip
RUN pip install --no-cache-dir --upgrade pip

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файл requirements.txt
COPY requirements.txt /app/

# Устанавливаем зависимости Python
# Используем --no-cache-dir для уменьшения размера образа
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код бота в контейнер
COPY . /app/

# Создаем директорию для скачиваемых/генерируемых файлов, если она нужна
# Замени 'downloads' на актуальное имя твоей директории, если оно другое
RUN mkdir -p /app/downloads
RUN mkdir -p /app/logs

# Указываем команду для запуска приложения
CMD ["python", "bot.py"]