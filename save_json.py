import json
import os
import uuid # Для генерации уникальных имен файлов
import datetime
import asyncio # Для асинхронной работы

# Убедитесь, что у вас установлена библиотека: pip install aiogram
from aiogram import Bot
from aiogram.utils.exceptions import TelegramAPIError # Основной класс ошибок API
from aiogram.enums import ParseMode # Для указания режима разметки (в aiogram 3.x)
# Если у вас aiogram 2.x, то: from aiogram.types import ParseMode

# --- Конфигурация ---
# Замените на ваши реальные значения
TELEGRAM_BOT_TOKEN = "ВАШ_ТЕЛЕГРАМ_БОТ_ТОКЕН"
TELEGRAM_ADMIN_CHAT_ID = "ВАШ_ТЕЛЕГРАМ_ID_АДМИНИСТРАТОРА" # Должен быть числом или строкой с числом

# Директория для временных файлов (можно изменить)
TEMP_DATA_DIR = "temp_data_storage"
if not os.path.exists(TEMP_DATA_DIR):
    os.makedirs(TEMP_DATA_DIR)

# Вспомогательная функция для сериализации datetime объектов в JSON
def datetime_serializer(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def escape_markdown_v2(text: str) -> str:
    """Экранирует специальные символы для MarkdownV2."""
    # Символы, которые нужно экранировать в MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return "".join(['\\' + char if char in escape_chars else char for char in str(text)])


async def send_telegram_message_aiogram(bot_token: str, chat_id: str, message_text: str):
    """Асинхронно отправляет сообщение в Telegram с использованием aiogram."""
    bot = Bot(token=bot_token)
    try:
        await bot.send_message(chat_id=chat_id, text=message_text, parse_mode=ParseMode.MARKDOWN_V2)
        print(f"Сообщение успешно отправлено в Telegram чат {chat_id}.")
        return True
    except TelegramAPIError as e:
        print(f"Ошибка при отправке сообщения в Telegram (aiogram): {e}")
        # Можно добавить более детальный лог, например, e.text для описания ошибки от API
        if hasattr(e, 'response') and e.response: # Для aiogram 3.x
            print(f"Telegram API response: {await e.response.text()}")
        elif hasattr(e, 'text'): # Для некоторых старых версий или других ошибок
            print(f"Telegram API error text: {e.text}")
        return False
    except Exception as e:
        print(f"Непредвиденная ошибка при работе с Telegram API (aiogram): {e}")
        return False
    finally:
        # В aiogram 3.x сессия управляется через bot.session.close() или автоматически
        # при использовании `async with bot:`
        # Для одноразового бота, создаваемого в функции, закрытие сессии важно.
        # В aiogram 3.x это обычно `await bot.session.close()`
        # В aiogram 2.x это было `await bot.close()` или `await (await bot.get_session()).close()`
        # Предполагаем aiogram 3.x+
        await bot.session.close()


async def process_and_notify_data_aiogram(data_item: dict, bot_token: str, admin_chat_id: str):
    """
    Сохраняет данные в JSON файл, отправляет уведомление в Telegram (aiogram) и удаляет файл.
    """
    if not isinstance(data_item, dict):
        print("Ошибка: Входные данные должны быть словарем.")
        return False

    unique_filename = f"data_{uuid.uuid4()}.json"
    filepath = os.path.join(TEMP_DATA_DIR, unique_filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_item, f, ensure_ascii=False, indent=4, default=datetime_serializer)
        print(f"Данные успешно сохранены в файл: {filepath}")
    except IOError as e:
        print(f"Ошибка при записи данных в файл {filepath}: {e}")
        return False
    except TypeError as e:
        print(f"Ошибка сериализации данных в JSON: {e}")
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError as remove_err:
                print(f"Не удалось удалить частично записанный файл {filepath}: {remove_err}")
        return False

    title = data_item.get('title', 'N/A')
    address = data_item.get('adress', 'N/A')
    price = data_item.get('price', 'N/A')

    title_escaped = escape_markdown_v2(title)
    address_escaped = escape_markdown_v2(address)
    price_escaped = escape_markdown_v2(price)
    unique_filename_escaped = escape_markdown_v2(unique_filename)

    message = (
        f"*Новые данные от парсера\\!*\n\n"
        f"*Заголовок:* `{title_escaped}`\n"
        f"*Адрес:* `{address_escaped}`\n"
        f"*Цена:* `{price_escaped}`\n\n"
        f"Данные были временно сохранены в файле: `{unique_filename_escaped}` и будут удалены после этого сообщения\\."
    )

    message_sent = await send_telegram_message_aiogram(bot_token, admin_chat_id, message)

    if message_sent:
        try:
            os.remove(filepath)
            print(f"Файл {filepath} успешно удален.")
            return True
        except OSError as e:
            print(f"Ошибка при удалении файла {filepath} (сообщение было отправлено): {e}")
            return True
    else:
        print(f"Сообщение в Telegram не было отправлено. Файл {filepath} не будет удален для последующего анализа.")
        return False

# --- Пример использования ---
if __name__ == "__main__":
    if "ВАШ_ТЕЛЕГРАМ_БОТ_ТОКЕН" in TELEGRAM_BOT_TOKEN or \
       "ВАШ_ТЕЛЕГРАМ_ID_АДМИНИСТРАТОРА" in TELEGRAM_ADMIN_CHAT_ID:
        print("Пожалуйста, укажите корректные TELEGRAM_BOT_TOKEN и TELEGRAM_ADMIN_CHAT_ID в коде.")
    else:
        # Пример данных (возьмем один из ваших словарей)
        example_data_1 = {
            'title': 'Продается 2-комн. квартира, 51,3 м²',
            'adress': 'Москва, ЗАО, р-н Дорогомилово, Кутузовский просп., 26К1',
            'price': '26300000₽',
            'offer': {'Цена за метр': '512 671 ₽/м²', 'Условия сделки': 'свободная продажа', 'Ипотека': 'возможна'},
            'metro': [{'station': 'Кутузовская', 'method': 'пешком', 'time': '7 мин.'}, {'station': 'Студенческая', 'method': 'пешком', 'time': '10 мин.'}, {'station': 'Москва-Сити', 'method': 'пешком', 'time': '11 мин.'}],
            'params': {'Общая площадь': '51,3', 'Жилая площадь': '33,1', 'Площадь кухни': '6', 'Этаж': '6 из 7', 'Год постройки': '1944', 'Тип жилья': 'Вторичка', 'Высота потолков': '3,5', 'Санузел': '1 раздельный', 'Ремонт': 'Евроремонт', 'Продаётся с мебелью': 'Да', 'Строительная серия': 'Индивидуальный проект', 'Мусоропровод': 'Нет', 'Количество лифтов': '1 пассажирский', 'Тип дома': 'Кирпичный', 'Тип перекрытий': 'Железобетонные', 'Парковка': 'Наземная', 'Подъезды': '15', 'Отопление': 'Центральное', 'Аварийность': 'Нет', 'Газоснабжение': 'Центральное'},
            'author_branding': {'agency_type': 'Агентство недвижимости', 'agency_name': 'МГСН', 'agency_link': 'https://www.cian.ru/company/348', 'agency_labels': ['Документы проверены'], 'realtor_type': 'Риелтор', 'realtor_name': 'МГСН отделение Октябрьское', 'realtor_link': 'https://www.cian.ru/agents/25954'},
            'offer_metadata': {'updated_date': 'вчера, 19:10', 'updated_datetime': datetime.datetime(2025, 5, 9, 19, 10), 'views_stats': '2004 просмотра, 63 за сегодня, 1190 уникальных', 'всего_просмотров': 2004, 'просмотров_сегодня': 63, 'уникальных_просмотров': 1190},
            'developer': None,
            'rosreestr': None,
            'agent': None,
            'description': 'Лот 73438 Квартира в эффектном, монументальном фасадном доме на Кутузовском проспекте. В доме жили видные партийные деятели, представители мира искусства и науки. В закрытом внутреннем современном дворе есть детская площадка, спортивное оборудование, уютная зеленая зона с клумбами, скамейками, фонтаном и деревьями, прогулочными дорожками.С внутренней стороны дома - прямой выход на прогулочную зону набережной Тараса Шевченко. Двор огорожен шлагбаумом, жителям доступны парковочные места и резидентская парковка ЦАО. Просторная и приличная входная группа. Квартира с изолированными комнатами 20,3 кв.м и 12.8 кв.м., раздельный санузел. Квартира с современным ремонтом - проведена полная замена проводки и труб, кухня оборудована кухонным гарнитуром и техникой, установлены кондиционеры. Идеально для проживания и для арендного бизнеса. Собственник владеет квартирой на основании договора купли-продажи более 5 лет. Свободная продажа, никто не прописан. Звоните!',
            'images': ['E:\\py\\main\\simple_real_estate_bot\\downloads\\316237818\\2453663067-1.jpg'],
            'images_links': ['https://images.cdn-cian.ru/images/2453663067-2.jpg']
        }

        example_data_2 = {
            'title': 'Еще одна квартира! (Тест символов)',
            'adress': 'Москва, ЦАО, ул. Примерная-10.',
            'price': '50000000.00₽',
            'offer_metadata': {'updated_date': 'сегодня, 10:00', 'updated_datetime': datetime.datetime.now()},
        }

        async def main_aiogram():
            print("--- Используем aiogram ---")
            success1 = await process_and_notify_data_aiogram(example_data_1, TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_CHAT_ID)
            if success1:
                print("Обработка example_data_1 (aiogram) завершена успешно.")
            else:
                print("Ошибка при обработке example_data_1 (aiogram).")

            print("-" * 30)

            success2 = await process_and_notify_data_aiogram(example_data_2, TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_CHAT_ID)
            if success2:
                print("Обработка example_data_2 (aiogram) завершена успешно.")
            else:
                print("Ошибка при обработке example_data_2 (aiogram).")

        asyncio.run(main_aiogram())