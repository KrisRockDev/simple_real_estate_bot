# Бот для конвертации страницы с ЦИАН в PDF

1. Клонирование репозитория с помощью команды:
    ```sh
    git clone https://github.com/KrisRockDev/simple_real_estate_bot.git
    ```
2. Перейдите в директорию:
   ```sh
   cd simple_real_estate_bot
   ```
3. Сборка образа:
   Выполните следующую команду в терминале для создания Docker-образа:
   ```bash
   sudo docker build -t krisrockdev/kriss_real_estate_bot:latest .
   ```
4. Запуск контейнера:
   Запустите контейнер, передав переменные окружения:
   ```bash
   sudo docker run -d \
   --restart on-failure \
   -e TOKEN='TELEGRAM-TOKEN' \
   -e CHAT_ID='1234567890' \
   -e NAME='YOUR-NAME' \
   -e PHONE='YOUR-PHONE' \
   -e TELEGRAM_BOT_LINK='LINK' \
   -e TELEGRAM_BOT_USERNAME='USERNAME' \
   -e EMAIL='EMAIL@EXAMPLE.COM' \
   -v $(pwd)/downloads:/downloads \
   --name real_estate_bot_container \
   krisrockdev/kriss_real_estate_bot:latest
   ```
