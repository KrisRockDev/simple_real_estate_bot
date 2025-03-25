import re
import os
import logging
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from settings import cookies, headers
from parser_cian.parser import parse_cian


# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

load_dotenv()

# Замените на ваш токен бота и chat_id
bot = Bot(token=os.getenv("TOKEN"))

# Создаём объекты бота и диспетчера
dp = Dispatcher()

# Регулярное выражение для проверки URL
URL_PATTERN = re.compile(r"^https://www\.cian\.ru/sale/flat/\d+/?$")

# Приветственное сообщение
WELCOME_MESSAGE = (
    "Привет! Я бот для парсинга объявлений с Циан.\n"
    "Отправь мне ссылку на квартиру в формате:\n"
    "🔹 `https://www.cian.ru/sale/flat/123456789/`\n\n"
    "Я обработаю её и пришлю данные!"
)


@dp.message(CommandStart())
async def start_command(message: types.Message):
    """Обрабатывает команду /start и приветствует пользователя."""
    await message.answer(WELCOME_MESSAGE, parse_mode="Markdown")


@dp.message()
async def process_cian_url(message: types.Message):
    """Обрабатывает входящие ссылки и парсит их."""
    url = message.text.strip()

    # Проверяем, что сообщение содержит валидный URL
    if not URL_PATTERN.match(url):
        await message.answer("🚫 Ошибка: Ссылка должна вести на квартиру с www.cian.ru\n"
                             "Пример: https://www.cian.ru/sale/flat/123456789/")
        return

    await message.answer(f"🔄 Обрабатываю страницу: {url}")

    # Парсим страницу
    try:
        # result = await asyncio.to_thread(parse_cian, url, cookies, headers)
        result = {'description': 'Тестовое описание'}

        if result:
            text = f"✅ Данные получены!\n\n{result['description']}"
        else:
            text = "⚠️ Не удалось получить данные. Возможно, объявление удалено."
    except Exception as e:
        text = f"❌ Ошибка парсинга: {e}"

    await message.answer(text)


# Запуск бота
if __name__ == "__main__":
    dp.run_polling(bot)
