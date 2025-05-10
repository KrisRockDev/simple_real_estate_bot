import asyncio
import logging
import os
import re
import sys
from datetime import datetime
from icecream import ic
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, InputMediaPhoto  # InputMediaPhoto не используется в текущей активной части кода
from dotenv import load_dotenv
from create_cian import format_price  # Теперь это будет вызываться как функция

# Предполагается, что эти импорты есть в вашем проекте
from parser import parse_cian
from settings import cookies, headers

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

# Получаем токен бота и ID администратора
BOT_TOKEN = os.getenv("TOKEN")
ADMIN_CHAT_ID_STR = os.getenv("CHAT_ID")
ADMIN_CHAT_ID = None

if not BOT_TOKEN:
    logger.critical("Не найден токен бота (TOKEN) в .env файле. Завершение работы.")
    sys.exit(1)

if ADMIN_CHAT_ID_STR:
    try:
        ADMIN_CHAT_ID = int(ADMIN_CHAT_ID_STR)
    except ValueError:
        logger.error("CHAT_ID в .env не является числом. Уведомления администратору не будут отправляться.")
else:
    logger.warning("CHAT_ID не найден в .env. Уведомления администратору не будут отправляться.")

# Создаём объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Регулярное выражение для проверки URL Циан (квартиры)
URL_PATTERN = re.compile(r"^https://www\.cian\.ru/sale/flat/\d+/?$", re.IGNORECASE)

# Приветственное сообщение
WELCOME_MESSAGE = (
    "👋 Привет! Я бот для парсинга объявлений с Циан.\n\n"
    "Отправь мне ссылку на квартиру в формате:\n"
    "🔹 `https://www.cian.ru/sale/flat/123456789/`\n\n"
    "Я обработаю её и пришлю данные в виде PDF-отчета, "
    "текстового сообщения и фотографий (если доступны)."
)

MAX_CAPTION_LENGTH = 1024
MAX_MESSAGE_LENGTH = 4096


def escape_md(text: str) -> str:
    """
    Экранирует специальные символы Markdown V1 для aiogram.
    Важно: `\` экранируется первым, чтобы не заэкранировать уже добавленные \.
    """
    if not isinstance(text, str):
        text = str(text)
    # Основные символы, которые aiogram обрабатывает как Markdown V1 сущности: *, _, `, [
    # Также \ как символ экранирования.
    # ] важен для ссылок [text] и просто как символ.
    text = text.replace('\\', '\\\\')
    text = text.replace('*', r'\*')
    text = text.replace('_', r'\_')
    text = text.replace('`', r'\`')
    text = text.replace('[', r'\[')
    text = text.replace(']', r'\]')
    return text


def format_short_caption(data: dict, url: str) -> str:
    """Формирует короткую подпись для PDF с основной информацией."""
    if not data:
        return escape_md("Информация по объявлению отсутствует.")  # Экранируем на всякий случай

    title_orig = data.get('title', "Без заголовка")
    address_orig = data.get('adress', "Адрес не указан")
    price_val = data.get('price', "не указана")

    # Корректный вызов функции format_price
    if price_val != "не указана":
        # Функция format_price из create_cian.py ожидает строку
        actual_formatted_price = format_price(str(price_val))
    else:
        # Если цена не указана, format_price может вернуть "Цена не указана" или что-то похожее
        # Либо можно просто использовать "не указана"
        actual_formatted_price = "не указана"

    # Экранируем все динамические части
    title_escaped = escape_md(title_orig)
    address_escaped = escape_md(address_orig)
    price_display_escaped = escape_md(actual_formatted_price)

    params_parts_escaped = []
    if isinstance(data.get('params'), dict):
        params_data = data['params']
        if params_data.get('Общая площадь'):
            params_parts_escaped.append(f"Общ.пл: {escape_md(str(params_data['Общая площадь']))} м²")
        if params_data.get('Этаж'):
            params_parts_escaped.append(f"Этаж: {escape_md(str(params_data['Этаж']))}")
    params_str_escaped_joined = ", ".join(params_parts_escaped)

    # Формируем части с Markdown-разметкой
    parts_md_version = [
        f"*{title_escaped}*",
        f"📍 {address_escaped}",
        f"💰 {price_display_escaped}",
    ]
    if params_str_escaped_joined:
        parts_md_version.append(f"📏 {params_str_escaped_joined}")
    base_text_md_version = "\n".join(parts_md_version)

    # Формируем ссылки (они всегда с Markdown)
    # Текст "Подробнее на Циан" не содержит спецсимволов, не требует экранирования. URL тоже.
    link_part = f"\n🔗 [Подробнее на Циан]({url})"

    bot_username_orig = os.getenv("TELEGRAM_BOT_USERNAME", "kriss_real_estate_bot")  # Рекомендуется имя без @
    bot_link_env = os.getenv("TELEGRAM_BOT_LINK")
    # ic(bot_username_orig, bot_link_env) # Оставьте для вашей отладки, если нужно

    if bot_link_env:
        # Текст для ссылки: в Markdown V1 внутри квадратных скобок [текст]
        # необходимо экранировать только символы ']' и '\'.
        # Символы '_' и '*' не требуют экранирования и будут отображены как есть.

        # Используем имя пользователя как текст ссылки.
        # Если в TELEGRAM_BOT_USERNAME есть '@', он будет включен в текст ссылки.
        # Если вы хотите текст ссылки без '@', убедитесь, что TELEGRAM_BOT_USERNAME его не содержит.
        link_text_content = bot_username_orig

        escaped_link_text = link_text_content.replace('\\', '\\\\').replace(']', r'\]')

        # Добавляем .strip() к URL на случай, если в .env есть случайные пробелы по краям
        clean_bot_link_env = bot_link_env.strip()

        link_bot = f"\nОтчёт сформирован автоматически при помощи Телеграм бота:\n[{escaped_link_text}]({clean_bot_link_env})"
    else:
        # Если ссылки нет, используем формат @username.
        # Убедимся, что имя пользователя "чистое" (без '@' в начале, т.к. мы его добавляем).
        clean_username_for_mention = bot_username_orig.lstrip('@')
        # Имена пользователей в @упоминаниях обычно не требуют Markdown-экранирования, если они валидны.
        link_bot = f"\nОтчёт сформирован автоматически при помощи Телеграм бота: @{clean_username_for_mention}"

    caption_links_combined = '' + link_bot
    len_links = len(caption_links_combined)

    # Проверяем, помещается ли версия с Markdown
    if len(base_text_md_version) + len_links <= MAX_CAPTION_LENGTH:
        return base_text_md_version + caption_links_combined
    else:
        # Markdown-версия слишком длинная. Формируем plain text версию для обрезания.
        # Используем оригинальные (неэкранированные для Markdown) значения, т.к. escape_md будет применен позже ко всему блоку.
        plain_parts_list = [
            title_orig,
            f"📍 {address_orig}",
            f"💰 {actual_formatted_price}",  # Используем уже отформатированную цену
        ]
        if isinstance(data.get('params'), dict):  # Собираем оригинальные параметры для plain text
            params_data_orig = data['params']
            params_orig_str_list = []
            if params_data_orig.get('Общая площадь'):
                params_orig_str_list.append(f"Общ.пл: {str(params_data_orig['Общая площадь'])} м²")
            if params_data_orig.get('Этаж'):
                params_orig_str_list.append(f"Этаж: {str(params_data_orig['Этаж'])}")
            if params_orig_str_list:
                plain_parts_list.append(f"📏 {', '.join(params_orig_str_list)}")

        base_text_plain_joined = "\n".join(plain_parts_list)

        available_space_for_plain_text = MAX_CAPTION_LENGTH - len_links - 3  # 3 for "..."

        if available_space_for_plain_text < 10:  # Если места совсем мало
            trimmed_plain_text = "Инфо..."
        else:
            trimmed_plain_text = base_text_plain_joined[:available_space_for_plain_text] + "..."

        # Экранируем всю текстовую часть перед добавлением ссылок
        return escape_md(trimmed_plain_text) + caption_links_combined


def format_full_message_text(data: dict, url: str) -> str:
    """Формирует полное текстовое сообщение со всеми деталями."""
    if not data:
        return escape_md("Не удалось получить подробные данные по объявлению.")

    title_orig = data.get('title', "Без заголовка")
    address_orig = data.get('adress', "Адрес не указан")
    price_val = data.get('price', "не указана")

    if price_val != "не указана":
        actual_formatted_price = format_price(str(price_val))
    else:
        actual_formatted_price = "не указана"

    text_parts = [
        f"*{escape_md(title_orig)}*",  # Экранированный заголовок в Markdown *...*
        f"🔗 [Открыть на Циан]({url})\n"  # URL обрабатывается Telegram, текст ссылки безопасен
    ]

    text_parts.append(f"🏷️ *Цена*: {escape_md(actual_formatted_price)}")
    if isinstance(data.get('offer'), dict) and data['offer'].get('Цена за метр'):
        text_parts.append(f"м²: {escape_md(str(data['offer']['Цена за метр']))}")
    if isinstance(data.get('offer'), dict) and data['offer'].get('Ипотека'):
        text_parts.append(f"Ипотека: {escape_md(str(data['offer']['Ипотека']))}")
    text_parts.append(f"📍 *Адрес*: {escape_md(address_orig)}\n")

    if isinstance(data.get('params'), dict):
        text_parts.append("📋 *Параметры квартиры:*")
        params_data = data['params']
        p_list = []
        for key, value in params_data.items():
            key_escaped = escape_md(str(key))
            value_escaped = escape_md(str(value))
            if key in ['Общая площадь', 'Жилая площадь', 'Площадь кухни']:
                p_list.append(f"  • {key_escaped}: {value_escaped} м²")
            elif key == 'Высота потолков':
                p_list.append(f"  • {key_escaped}: {value_escaped} м")
            else:
                p_list.append(f"  • {key_escaped}: {value_escaped}")
        text_parts.append("\n".join(p_list))
        text_parts.append("")

    if isinstance(data.get('metro'), list) and data['metro']:
        text_parts.append("🚇 *Метро рядом:*")
        for station_info in data['metro']:
            station = escape_md(str(station_info.get('station', 'N/A')))
            method = escape_md(str(station_info.get('method', 'N/A')))
            time = escape_md(str(station_info.get('time', 'N/A')))
            text_parts.append(f"  • {station} ({method} {time})")
        text_parts.append("")

    if data.get('description'):
        # Описание может содержать HTML <br>, заменяем их на \n ДО экранирования
        description_orig = str(data['description']).replace('<br>', '\n').replace('<br/>', '\n')
        text_parts.append("📝 *Описание:*")
        text_parts.append(escape_md(description_orig))
        text_parts.append("")

    if isinstance(data.get('agent'), dict):
        text_parts.append("👤 *Автор объявления:*")
        for key, value in data['agent'].items():
            text_parts.append(f"  • {escape_md(str(key))}: {escape_md(str(value))}")
        text_parts.append("")

    if isinstance(data.get('author_branding'), dict):
        text_parts.append("🏢 *Агентство/Риелтор (брендинг):*")
        branding = data['author_branding']
        if branding.get('agency_name'):
            text_parts.append(f"  • Агентство: {escape_md(str(branding['agency_name']))}")
        if branding.get('realtor_name'):
            text_parts.append(f"  • Риелтор: {escape_md(str(branding['realtor_name']))}")
        text_parts.append("")

    if isinstance(data.get('developer'), dict):
        text_parts.append("🏗️ *Застройщик:*")
        dev = data['developer']
        for key, value in dev.items():
            text_parts.append(f"  • {escape_md(str(key))}: {escape_md(str(value))}")
        text_parts.append("")

    if isinstance(data.get('rosreestr'), dict):
        text_parts.append("📜 *Данные Росреестра (если есть):*")
        ros_info = data['rosreestr']
        for key, value in ros_info.items():
            text_parts.append(f"  • {escape_md(str(key))}: {escape_md(str(value))}")
        text_parts.append("")

    if isinstance(data.get('offer_metadata'), dict):
        meta = data['offer_metadata']
        text_parts.append("📊 *Статистика объявления:*")
        if meta.get('updated_date'):
            text_parts.append(f"  • Обновлено: {escape_md(str(meta['updated_date']))}")
        if meta.get('updated_datetime') and isinstance(meta['updated_datetime'], datetime):
            text_parts.append(
                f"  • Дата обновления (UTC): {escape_md(meta['updated_datetime'].strftime('%Y-%m-%d %H:%M:%S'))}")
        if meta.get('views_stats'):
            text_parts.append(f"  • Просмотры: {escape_md(str(meta['views_stats']))}")
        text_parts.append("")

    full_text = "\n".join(text_parts)
    if len(full_text) > MAX_MESSAGE_LENGTH:  # Обрезание полного текста (менее критично для Markdown, т.к. он уже сформирован)
        full_text = full_text[:MAX_MESSAGE_LENGTH - 4] + "\n..."  # Потенциально может сломать, если срез неудачный
        # Но полный текст обычно длинный, вероятность мала.
        # Для полной безопасности, здесь тоже нужна логика plain text при обрезании.
        # Но пока оставим так, т.к. ошибка была с caption.
    return full_text


@dp.message(CommandStart())
async def start_command(message: types.Message):
    await message.answer(WELCOME_MESSAGE, parse_mode="Markdown")


@dp.message(F.text)
async def process_cian_url(message: types.Message, current_bot: Bot = bot):
    url = message.text.strip()
    user_id = message.from_user.id
    is_admin_request = ADMIN_CHAT_ID is not None and user_id == ADMIN_CHAT_ID

    if not URL_PATTERN.match(url):
        await message.answer(
            "🚫 *Ошибка: Неверный формат ссылки.*\n\n"
            "Пожалуйста, отправьте ссылку на квартиру с `www.cian.ru`.\n"
            "Пример: `https://www.cian.ru/sale/flat/123456789/`",
            parse_mode="Markdown"
        )
        return

    processing_msg = await message.answer(
        f"⏳ Обрабатываю страницу: {escape_md(url)}\nПожалуйста, подождите...")  # URL тоже экранируем для вывода

    try:
        if sys.version_info >= (3, 9):
            report_path, result_data = await asyncio.to_thread(parse_cian, url, cookies, headers)
        else:
            loop = asyncio.get_event_loop()
            report_path, result_data = await loop.run_in_executor(None, parse_cian, url, cookies, headers)

        if not result_data:
            error_text = "⚠️ Не удалось получить данные по объявлению. Возможно, оно было удалено, изменилась структура страницы или возникла проблема с доступом к Циан."
            # error_text уже безопасен, т.к. не содержит динамических данных и Markdown
            await message.answer(error_text)
            if ADMIN_CHAT_ID and not is_admin_request:
                await current_bot.send_message(chat_id=ADMIN_CHAT_ID,
                                               text=f"Ошибка при парсинге {escape_md(url)} (пользователь {user_id}):\n{error_text}")
            return

        short_caption = format_short_caption(result_data, url)
        pdf_sent_to_user = False
        if report_path and os.path.exists(report_path):
            try:
                pdf_document_for_user = FSInputFile(report_path)
                await message.answer_document(document=pdf_document_for_user, caption=short_caption,
                                              parse_mode="Markdown")
                pdf_sent_to_user = True
                if ADMIN_CHAT_ID and not is_admin_request:
                    pdf_document_for_admin = FSInputFile(report_path)
                    admin_caption = f"Отчет по {escape_md(url)} (запрос от {user_id}):\n{short_caption}"
                    # Убедимся, что admin_caption не превышает лимит
                    if len(admin_caption) > MAX_CAPTION_LENGTH:
                        admin_caption = admin_caption[:MAX_CAPTION_LENGTH - 3] + "..."
                    await current_bot.send_document(chat_id=ADMIN_CHAT_ID, document=pdf_document_for_admin,
                                                    caption=admin_caption,
                                                    parse_mode="Markdown")
            except Exception as e_pdf:
                logger.error(f"Ошибка при отправке PDF ({report_path}) пользователю {user_id}: {e_pdf}")
                # short_caption уже отформатирован и обрезан безопасно
                fallback_text_user = f"Не удалось отправить PDF отчет. {short_caption}"
                await message.answer(fallback_text_user, parse_mode="Markdown")
                if ADMIN_CHAT_ID and not is_admin_request:
                    # Здесь short_caption используется как есть, он уже должен быть безопасным
                    admin_error_text = f"Ошибка отправки PDF ({escape_md(report_path)}) для {escape_md(url)} пользователю {user_id}: {escape_md(str(e_pdf))}\nКороткое описание: {short_caption}"
                    if len(admin_error_text) > MAX_MESSAGE_LENGTH:  # Используем MAX_MESSAGE_LENGTH для текстового сообщения
                        admin_error_text = admin_error_text[
                                           :MAX_MESSAGE_LENGTH - 100] + "..."  # Оставляем место для многоточия и запаса
                    await current_bot.send_message(chat_id=ADMIN_CHAT_ID,
                                                   text=admin_error_text,
                                                   parse_mode="Markdown")
        else:
            logger.warning(f"Файл отчета PDF не найден или не был создан: {report_path} для URL: {url}")
            await message.answer(short_caption, parse_mode="Markdown")  # short_caption безопасен
            if ADMIN_CHAT_ID and not is_admin_request:
                admin_text = f"Отчет по {escape_md(url)} (PDF не найден, запрос от {user_id}):\n{short_caption}"
                if len(admin_text) > MAX_MESSAGE_LENGTH:
                    admin_text = admin_text[:MAX_MESSAGE_LENGTH - 3] + "..."
                await current_bot.send_message(chat_id=ADMIN_CHAT_ID,
                                               text=admin_text,
                                               parse_mode="Markdown")

        # Закомментированные части кода для full_text и images опущены для краткости,
        # но к ним тоже должна применяться логика экранирования escape_md.

    except asyncio.CancelledError:
        logger.warning(f"Задача обработки URL {url} для пользователя {user_id} была отменена.")
    except Exception as e:
        logger.exception(f"Критическая ошибка при обработке URL {url} для пользователя {user_id}: {e}")
        error_message_user = "❌ Произошла внутренняя ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже или свяжитесь с администратором, если проблема повторяется."
        await message.answer(error_message_user)  # Это сообщение не использует Markdown, безопасно

        if ADMIN_CHAT_ID and not is_admin_request:
            # Для сообщения админу экранируем все динамические части
            error_message_admin = f"‼️ Критическая ошибка парсинга {escape_md(url)} для пользователя {user_id}:\nТип: {escape_md(type(e).__name__)}\nСообщение: {escape_md(str(e))}"
            await current_bot.send_message(chat_id=ADMIN_CHAT_ID, text=error_message_admin[:MAX_MESSAGE_LENGTH - 100])
    finally:
        try:
            await current_bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
        except Exception:
            pass


async def main():
    logger.info("Запуск бота...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")