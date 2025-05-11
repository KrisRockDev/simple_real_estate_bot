import os
import time
import requests
from icecream import ic
from settings import downloads_dir_absolute
from servise import printer
import re
from datetime import datetime, timedelta


def get_title(soup):
    """
    Извлекает полный заголовок объявления (включая название ЖК, если есть)
    из контейнера с data-name='OfferTitleNew'.
    Использует get_text() для получения всего текста и последующую очистку.
    """
    try:
        # 1. Находим основной контейнер заголовка
        title_container = soup.find('div', {'data-name': 'OfferTitleNew'})
        # ic(title_container) # Оставляем для отладки

        if not title_container:
            printer("Контейнер заголовка (data-name='OfferTitleNew') не найден.", kind='warning')
            return None

        # 2. Извлекаем весь текст из найденного контейнера.
        #    separator=' ' добавляет пробел между текстовыми блоками (например, между h1 и div с ЖК).
        #    strip=True удаляет лишние пробелы/переносы строк по краям каждого отдельного текстового узла.
        full_text = title_container.get_text(separator=' ', strip=True)
        # Пример результата на этом этапе: "Продается 3-комн. квартира, 86,2 м² в ЖК «Новые Смыслы»"
        # (могут быть лишние пробелы или \xa0 в зависимости от HTML)

        # 3. Очищаем извлеченный текст:
        #    - Заменяем неразрывные пробелы (\xa0 или  ) на обычные пробелы.
        #    - Убираем лишние пробелы (если их несколько подряд) и пробелы по краям строки.
        cleaned_text = full_text.replace('\xa0', ' ').replace('&nbsp;', ' ').replace(' ', ' ')
        # Используем ' '.join(cleaned_text.split()) - это Pythonic способ
        # заменить любые последовательности пробельных символов одним пробелом
        # и убрать пробелы по краям. Эквивалентно re.sub(r'\s+', ' ', cleaned_text).strip()
        cleaned_text = ' '.join(cleaned_text.split())

        # printer(f"[Заголовок] {cleaned_text}", kind='info') # Раскомментируйте, если нужно логировать успешный результат
        return cleaned_text

    except Exception as _ex:
        printer(f'error_get_title: Произошла ошибка при извлечении заголовка: {_ex}', kind='error')
        return None


# def get_adress(soup):
#     try:
#         # Находим блок с атрибутом data-name="AddressContainer"
#         address_container = soup.find('div', {'data-name': 'AddressContainer'})
#         # Извлекаем текст из найденного блока
#         result = ''.join(address_container.get_text(separator='\t').replace('\t,', '').split('\t')[-3:-1])
#         if ' ул. ' in result:
#             result = f'ул. {result.replace(' ул. ', ' д.')}'
#         printer(f"[Адрес] {result}", kind='info')
#         return result
#     except Exception as _ex:
#         printer(f'error_get_adress: {_ex}', kind='error')
#         return None


def get_adress(soup):
    try:
        # Находим блок с атрибутом data-name="AddressContainer"
        address_container = soup.find('div', {'data-name': 'AddressContainer'})
        if not address_container:
            printer('error_get_adress: AddressContainer not found', kind='error')
            return None

        # Находим все элементы <a> с атрибутом data-name="AddressItem" внутри контейнера
        address_items = address_container.find_all('a', {'data-name': 'AddressItem'})

        if not address_items:
            printer('error_get_adress: No AddressItem elements found in AddressContainer', kind='error')
            # Как запасной вариант, можно попробовать взять весь текст, если нет AddressItem,
            # но это менее надежно и может потребовать дополнительной очистки.
            # Для данного случая, найдем AddressItem.
            return None

        # Извлекаем текст из каждого найденного элемента и удаляем лишние пробелы
        parts = [item.get_text(strip=True) for item in address_items]

        # Объединяем части адреса через запятую и пробел
        result = ", ".join(parts)

        # Ваша оригинальная логика для обработки " ул. "
        # Примечание: для текущего HTML эта часть не будет выполнена, т.к. " ул. " нет в `result`.
        # Она оставлена для совместимости, если другие адреса могут содержать " ул. ".
        if ' ул. ' in result:
            # Эта логика преобразует, например, "Что-то ул. Название, ХХ" в "ул. Что-то д. Название, ХХ"
            # Возможно, это не всегда желаемое поведение, но сохранено как в оригинале.
            result = f'ул. {result.replace(" ул. ", " д.")}'

        printer(f"[Адрес] {result}", kind='info')
        return result
    except AttributeError as ae: # Если soup.find вернул None и мы пытаемся вызвать на нем метод
        printer(f'error_get_adress: Attribute error, possibly missing HTML element - {ae}', kind='error')
        return None
    except Exception as _ex:
        printer(f'error_get_adress: {_ex}', kind='error')
        return None

def get_price(soup):
    try:
        # Находим элемент с атрибутом data-testid="price-amount"
        price_element = soup.find('div', {'data-testid': 'price-amount'})
        # Извлекаем текст из найденного элемента и приводим его в нужный вид
        result = price_element.text.strip().replace('\xa0', '').replace('&nbsp;', ' ').split('₽')[0]
        printer(f"[Цена] {result} ₽", kind='info')
        return result
    except Exception as _ex:
        printer(f'error_get_price: {_ex}', kind='error')
        return None


def get_offer(soup):
    try:
        # Находим блок с атрибутами data-name="OfferFactsInSidebar" и data-testid="offer-facts"
        offer_facts_block = soup.find('div', {'data-name': 'OfferFactsInSidebar', 'data-testid': 'offer-facts'})
        # Проверяем, найден ли блок
        if not offer_facts_block:
            raise ValueError("Блок offer-facts не найден")
        res_dict = {}
        # Проходимся по всем элементам с data-name="OfferFactItem"
        for item in offer_facts_block.find_all('div', {'data-name': 'OfferFactItem'}) or []:
            spans = item.find_all('span')
            # Проверяем, что есть хотя бы два <span>
            if len(spans) >= 2:
                key = spans[0].text.strip()
                value = spans[1].text.strip()
                res_dict[key] = value
        printer(f"[Предложение] {res_dict}", kind='info')
        if 'Цена за метр' in res_dict:
            res_dict['Цена за метр'] = res_dict['Цена за метр'].replace(' ₽/м²', '').replace(' ', '')
        return res_dict
    except Exception as _ex:
        printer(f'error_get_offer: {_ex}', kind='error')
        return None


def get_metro(soup):
    try:
        # Находим блок с атрибутами data-name="UndergroundList"
        underground_list = soup.find('ul', {'data-name': 'UndergroundList'})

        # Извлекаем данные из каждого элемента li внутри блока
        result = []
        for item in underground_list.find_all('li', {'data-name': 'UndergroundItem'}):
            station = item.find('a', {'class': 'a10a3f92e9--underground_link--VnUVj'}).text.strip()
            time_element = item.find('span', {'class': 'a10a3f92e9--underground_time--YvrcI'})
            time_icon = time_element.find('svg')

            # Проверяем наличие иконки времени
            if time_icon:
                # Время указано пешком
                time = time_element.contents[-1].strip()
                result.append({'station': station, 'method': 'пешком', 'time': time})
            else:
                # Время указано на автомобиле
                time = time_element.contents[-1].strip()
                result.append({'station': station, 'method': 'автомобилем', 'time': time})
        printer(f"[Метро] {result}", kind='info')
        return result
    except Exception as _ex:
        printer(f'error_get_metro: {_ex}', kind='error')
        return None


def get_params_old(soup):
    try:
        factoids_block = soup.find('div', {'data-name': 'ObjectFactoids'})
        if not factoids_block:
            return None

        result = {}
        for item in factoids_block.find_all('div', {'data-name': 'ObjectFactoidsItem'}):
            # Ищем категорию по частичному совпадению класса
            category_span = item.find('span', class_=lambda x: x and 'color_gray60_100' in x)
            # Ищем значение по частичному совпадению класса
            value_span = item.find('span', class_=lambda x: x and 'color_text-primary-default' in x)

            if not category_span or not value_span:
                continue

            category = category_span.text.strip()
            value = value_span.text.strip().replace('\xa0', ' ')

            # Убираем единицы измерения для площадей
            if 'площад' in category.lower():
                value = value.replace('м²', '').strip()

            result[category] = value

        printer(f"[Параметры_old] {result=}", kind='info')
        return result
    except Exception as _ex:
        printer(f'error_get_params: {_ex}', kind='error')
        return None


def get_params(soup):
    params_old = get_params_old(soup)
    try:
        # 1. Находим основной блок с информацией о квартире
        summary_group = soup.find('div', {'data-name': 'OfferSummaryInfoGroup'})
        if not summary_group:
            printer("Блок 'OfferSummaryInfoGroup' не найден.", kind='warning')
            return None

        result = {}
        if 'Этаж' in params_old:
            result['Этаж'] = params_old['Этаж']
        if 'Дом' in params_old:
            result['Дом'] = params_old['Дом']
        if 'Год постройки' in params_old:
            result['Год постройки'] = params_old['Год постройки']
        if 'Год сдачи' in params_old:
            result['Год сдачи'] = params_old['Год сдачи']

        # 2. Итерируемся по каждому элементу параметра
        for item in summary_group.find_all('div', {'data-name': 'OfferSummaryInfoItem'}):
            # Ищем категорию (ключ) по частичному совпадению класса в теге <p>
            category_p = item.find('p', class_=lambda x: x and 'color_gray60_100' in x)
            # Ищем значение по частичному совпадению класса в теге <p>
            value_p = item.find('p', class_=lambda x: x and 'color_text-primary-default' in x)

            if not category_p or not value_p:
                printer(f"Не удалось найти категорию или значение в элементе: {item.prettify()}", kind='info')
                continue

            category = category_p.text.strip()
            value = value_p.text.strip().replace('\xa0', ' ')  # Заменяем неразрывный пробел
            # ic(category) # Раскомментируйте для отладки
            # ic(value)   # Раскомментируйте для отладки

            # Убираем единицы измерения
            if 'площад' in category.lower():
                value = value.replace('м²', '').strip()
            elif 'высота потолков' in category.lower():  # Добавлено для высоты потолков
                value = value.replace('м', '').strip()
            # Можно добавить другие специфичные очистки, если потребуется

            result[category] = value

        if not result:
            printer("Не найдено ни одного параметра в 'OfferSummaryInfoGroup'.", kind='warning')
            return None

        # printer(f"[Параметры] {result=}", kind='info')
        # ic(result)

        if 'Продаётся с\xa0мебелью' in result:
            result['Продаётся с мебелью'] = result['Продаётся с\xa0мебелью']
            del result['Продаётся с\xa0мебелью']

        return result
    except Exception as _ex:
        printer(f'error_get_params_new: {_ex}', kind='error')
        return None


def get_all_offer_params(soup):
    params_data = {}

    # Этап 1: Извлечение данных из блока 'ObjectFactoids' (старый формат)
    try:
        factoids_block = soup.find('div', {'data-name': 'ObjectFactoids'})
        if factoids_block:
            for item in factoids_block.find_all('div', {'data-name': 'ObjectFactoidsItem'}):
                category_span = item.find('span', class_=lambda x: x and 'color_gray60_100' in x)
                value_span = item.find('span', class_=lambda x: x and 'color_text-primary-default' in x)

                if category_span and value_span:
                    category = category_span.text.strip()
                    value = value_span.text.strip().replace('\xa0', ' ')

                    if 'площад' in category.lower() and 'м²' in value:
                        value = value.replace('м²', '').strip()
                    elif 'высота потолков' in category.lower() and ' м' in value:
                        value = value.replace('м', '').strip()

                    params_data[category] = value
            printer(f"[Параметры из ObjectFactoids] {params_data}", kind='info')
    except Exception as e:
        printer(f'Ошибка при парсинге ObjectFactoids: {e}', kind='error')

    # Этап 2: Извлечение данных из блока 'OfferSummaryInfoLayout' (новый формат)
    # Данные из этого блока перезапишут существующие с теми же ключами из ObjectFactoids
    try:
        summary_layout_block = soup.find('div', {'data-name': 'OfferSummaryInfoLayout'})
        if summary_layout_block:
            current_params_from_summary = {}
            for group in summary_layout_block.find_all('div', {'data-name': 'OfferSummaryInfoGroup'}):
                for item in group.find_all('div', {'data-name': 'OfferSummaryInfoItem'}):
                    category_p = item.find('p', class_=lambda x: x and 'color_gray60_100' in x)
                    value_p = item.find('p', class_=lambda x: x and 'color_text-primary-default' in x)

                    if category_p and value_p:
                        category = category_p.text.strip()
                        value = value_p.text.strip().replace('\xa0', ' ')

                        if 'площад' in category.lower() and 'м²' in value:
                            value = value.replace('м²', '').strip()
                        elif 'высота потолков' in category.lower() and ' м' in value:  # Проверяем наличие пробела перед "м"
                            value = value.replace('м', '').strip()

                        current_params_from_summary[category] = value

            if current_params_from_summary:
                printer(f"[Параметры из OfferSummaryInfoLayout] {current_params_from_summary}", kind='info')
                params_data.update(current_params_from_summary)

    except Exception as e:
        printer(f'Ошибка при парсинге OfferSummaryInfoLayout: {e}', kind='error')

    if not params_data:
        printer("Не найдено никаких параметров на странице.", kind='info')
        return None

    printer(f"[Итоговые параметры] {params_data}", kind='info')
    # ic(params_data)
    return params_data


# Вспомогательная функция для парсинга блока с информацией об агентстве или риелторе
def _parse_branding_card_details(card_soup, prefix, result_dict):
    """
    Извлекает детали (тип, имя, ссылку, лейблы) из карточки агентства/риелтора.
    """
    if not card_soup:
        return

    # Тип (Агентство недвижимости / Риелтор)
    # <span style="letter-spacing:1px" class="a10a3f92e9--color_gray60_100--r_axa ...">Агентство недвижимости</span>
    type_span = card_soup.find('span', class_=lambda
        c: c and 'a10a3f92e9--color_gray60_100--r_axa' in c and 'a10a3f92e9--text_textTransform__uppercase--C4ydW' in c)
    if type_span:
        entity_type_text = type_span.text.strip().replace('\xa0', ' ')
        result_dict[f'{prefix}_type'] = entity_type_text
        # printer(f"[{prefix.capitalize()}] Тип: {entity_type_text}", kind='info') # Для детальной отладки

    # Имя и ссылка
    # <div class="a10a3f92e9--name-container--enElO"><a href="/company/7302" ...><span ...>Замоскворечье</span></a></div>
    name_container = card_soup.find('div', class_='a10a3f92e9--name-container--enElO')
    if name_container:
        link_tag = name_container.find('a', class_='a10a3f92e9--link--wbne1')
        if link_tag:
            name_span = link_tag.find('span')  # Имя обычно в первом span внутри ссылки
            if name_span:
                name = name_span.text.strip().replace('\xa0', ' ')
                result_dict[f'{prefix}_name'] = name
                # printer(f"[{prefix.capitalize()}] Имя: {name}", kind='info')

            href = link_tag.get('href')
            if href:
                full_link = f"https://www.cian.ru{href}" if href.startswith('/') else href
                result_dict[f'{prefix}_link'] = full_link
                # printer(f"[{prefix.capitalize()}] Ссылка: {full_link}", kind='info')

    # Лейблы (Документы проверены, Рейтинг и т.д.)
    # <div class="a10a3f92e9--labels--LepFl">...<span class="a10a3f92e9--title--LeqmQ">Документы проверены</span>...</div>
    labels_container = card_soup.find('div', class_='a10a3f92e9--labels--LepFl')
    if labels_container:
        labels = []
        for title_span in labels_container.find_all('span', class_='a10a3f92e9--title--LeqmQ'):
            label_text = title_span.text.strip().replace('\xa0', ' ')
            if label_text:  # Добавляем только непустые лейблы
                labels.append(label_text)

        if labels:
            result_dict[f'{prefix}_labels'] = labels
            # printer(f"[{prefix.capitalize()}] Лейблы: {labels}", kind='info')


def get_author_branding_info(soup):
    """
    Парсит блок AuthorBrandingAside для извлечения информации об агентстве и риелторе.
    """
    try:
        author_branding_aside = soup.find('div', {'data-name': 'AuthorBrandingAside'})
        if not author_branding_aside:
            printer("[Брендинг автора] Блок 'AuthorBrandingAside' не найден.", kind='info')
            return None

        card_component = author_branding_aside.find('div', {'data-testid': 'AgencyBrandingAsideCard'})
        if not card_component:
            printer("[Брендинг автора] Компонент 'AgencyBrandingAsideCard' не найден.", kind='info')
            return None

        branding_data = {}

        # Информация об агентстве
        # Ищем основной блок агентства по его уникальному внутреннему контейнеру
        agency_section_container = card_component.find('div', class_='a10a3f92e9--main--_w7i2')
        if agency_section_container:
            _parse_branding_card_details(agency_section_container, 'agency', branding_data)
        else:
            printer("[Брендинг автора] Секция агентства (main--_w7i2) не найдена.", kind='info')

        # Информация о риелторе
        # Ищем блок риелтора по его уникальному внутреннему контейнеру
        realtor_section_container = card_component.find('div', class_='a10a3f92e9--subcontact--SJ_VG')
        if realtor_section_container:
            _parse_branding_card_details(realtor_section_container, 'realtor', branding_data)
        else:
            printer("[Брендинг автора] Секция риелтора (subcontact--SJ_VG) не найдена.", kind='info')

        if not branding_data:
            printer("[Брендинг автора] Не удалось извлечь информацию об агентстве или риелторе.", kind='info')
            return None

        printer(f"[Брендинг автора] {branding_data}", kind='info')
        return branding_data

    except Exception as _ex:
        printer(f'error_get_author_branding_info: Произошла ошибка: {_ex}', kind='error')
        return None


def parse_custom_date_to_datetime(date_str_rus):
    """
    Преобразует строку с датой и временем на русском языке
    (например, "сегодня, 05:58", "вчера, 00:10", "6 май, 09:54")
    в объект datetime.
    Возвращает datetime объект или None в случае ошибки.
    """
    if not date_str_rus or not isinstance(date_str_rus, str):
        printer("[Парсинг даты] Получена пустая или не строковая дата.", kind='warning')
        return None

    now = datetime.now()
    date_str_rus = date_str_rus.strip().lower()
    dt_object = None

    # Словарь для месяцев (родительный падеж, как обычно используется в датах)
    # Ключи в нижнем регистре для унификации
    month_map_genitive = {
        "янв": 1, "фев": 2, "мар": 3, "апр": 4, "май": 5, "июн": 6,
        "июл": 7, "авг": 8, "сен": 9, "окт": 10, "ноя": 11, "дек": 12,
        # Полные названия на всякий случай, если формат изменится
        "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
        "июня": 6, "июля": 7, "августа": 8, "сентября": 9,
        "октября": 10, "ноября": 11, "декабря": 12
    }
    # Для "мая" особый случай, так как "май" (им.п.) и "мая" (род.п.)
    # Порядок важен, чтобы "мая" не перекрыло "май" если используется startswith

    try:
        # Пытаемся извлечь время
        time_match = re.search(r'(\d{1,2}:\d{2})$', date_str_rus)
        if not time_match:
            printer(f"[Парсинг даты] Не удалось извлечь время из строки: '{date_str_rus}'", kind='warning')
            return None

        time_str = time_match.group(1)
        hours, minutes = map(int, time_str.split(':'))

        if "сегодня" in date_str_rus:
            dt_object = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        elif "вчера" in date_str_rus:
            target_date = now - timedelta(days=1)
            dt_object = target_date.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        else:
            # Попытка разобрать дату типа "6 май, 09:54" или "6 мая, 09:54"
            # Убираем время из строки, чтобы не мешало парсить дату
            date_part_str = date_str_rus.replace(time_str, '').strip().rstrip(',')

            # Ищем день и месяц
            # (\d{1,2})\s+([а-я]+) - день, пробел, название месяца буквами
            date_match = re.match(r'(\d{1,2})\s+([а-я]+)', date_part_str)
            if date_match:
                day = int(date_match.group(1))
                month_name_rus = date_match.group(2)
                month = None

                # Ищем совпадение в словаре месяцев
                for k_month, v_month in month_map_genitive.items():
                    if month_name_rus.startswith(k_month):  # Позволяет "май" для "мая"
                        month = v_month
                        break

                if month:
                    year = now.year  # Предполагаем текущий год
                    # Проверка: если полученная дата (месяц, день) позже текущей даты в текущем году,
                    # и это не текущий месяц (т.е. не просто более позднее время в том же месяце),
                    # то, возможно, это дата прошлого года.
                    # Это более актуально для дат публикации, чем для "обновлено", но добавим на всякий случай.
                    # Однако для "обновлено" это редкость. Чаще всего год текущий.
                    # Для простоты пока оставляем текущий год.
                    # Если бы это была дата публикации, логика определения года могла бы быть сложнее.

                    dt_object = datetime(year, month, day, hour=hours, minute=minutes, second=0, microsecond=0)
                else:
                    printer(
                        f"[Парсинг даты] Не удалось определить месяц из: '{month_name_rus}' в строке '{date_str_rus}'",
                        kind='warning')
            else:
                printer(f"[Парсинг даты] Не удалось разобрать дату (день и месяц) из строки: '{date_str_rus}'",
                        kind='warning')

    except ValueError as ve:
        printer(f"[Парсинг даты] Ошибка значения при преобразовании даты '{date_str_rus}': {ve}", kind='error')
        return None
    except Exception as e:
        printer(f"[Парсинг даты] Общая ошибка при преобразовании даты '{date_str_rus}': {e}", kind='error')
        return None

    return dt_object


def parse_views_stats_to_dict(stats_str):
    """
    Разбирает строку статистики просмотров на отдельные числовые значения.
    Возвращает словарь с ключами на русском или пустой словарь, если ничего не найдено.
    """
    parsed_stats = {}
    if not stats_str or not isinstance(stats_str, str):
        printer("[Парсинг статистики] Получена пустая или не строковая статистика.", kind='warning')
        return parsed_stats

    # Общее количество просмотров
    total_views_match = re.search(r'(\d+)\s+просмотр(?:а|ов)?', stats_str)
    if total_views_match:
        try:
            parsed_stats['всего_просмотров'] = int(total_views_match.group(1))
        except ValueError:
            printer(
                f"[Парсинг статистики] Не удалось преобразовать общее кол-во просмотров в число: '{total_views_match.group(1)}'",
                kind='warning')

    # Просмотров за сегодня
    today_views_match = re.search(r'(\d+)\s+за\s+сегодня', stats_str)
    if today_views_match:
        try:
            parsed_stats['просмотров_сегодня'] = int(today_views_match.group(1))
        except ValueError:
            printer(
                f"[Парсинг статистики] Не удалось преобразовать просмотры за сегодня в число: '{today_views_match.group(1)}'",
                kind='warning')

    # Уникальных просмотров
    # Учитываем "уникальный" и "уникальных"
    unique_views_match = re.search(r'(\d+)\s+уникальн(?:ый|ых)', stats_str)
    if unique_views_match:
        try:
            parsed_stats['уникальных_просмотров'] = int(unique_views_match.group(1))
        except ValueError:
            printer(
                f"[Парсинг статистики] Не удалось преобразовать уникальные просмотры в число: '{unique_views_match.group(1)}'",
                kind='warning')

    return parsed_stats


def get_offer_metadata_info(soup):
    """
    Парсит блок OfferMetaData для извлечения даты обновления, статистики просмотров,
    а также добавляет дату обновления в формате datetime и разбирает статистику
    просмотров на отдельные числовые значения.
    """
    try:
        offer_metadata_block = soup.find('div', {'data-name': 'OfferMetaData'})
        if not offer_metadata_block:
            printer("[Метаданные] Блок 'OfferMetaData' не найден.", kind='info')
            return None

        metadata = {
            'updated_date': None,
            'updated_datetime': None,  # Новый ключ для datetime объекта
            'views_stats': None
            # Новые ключи для статистики будут добавлены ниже
        }

        # Дата обновления (текст)
        updated_div = offer_metadata_block.find('div', {'data-testid': 'metadata-updated-date'})
        if updated_div:
            updated_span = updated_div.find('span')
            if updated_span:
                updated_text_raw = updated_span.text.strip().replace('\xa0', ' ')
                if updated_text_raw.lower().startswith('обновлено:'):
                    metadata['updated_date'] = updated_text_raw[len('обновлено:'):].strip()
                else:
                    metadata['updated_date'] = updated_text_raw

                # Преобразование в datetime
                if metadata['updated_date']:
                    metadata['updated_datetime'] = parse_custom_date_to_datetime(metadata['updated_date'])
            else:
                printer("[Метаданные] Span с датой обновления не найден.", kind='info')
        else:
            printer("[Метаданные] Div с датой обновления (metadata-updated-date) не найден.", kind='info')

        # Статистика просмотров (текст)
        stats_button = offer_metadata_block.find('button', {'data-name': 'OfferStats'})
        if stats_button:
            stats_text = stats_button.text.strip().replace('\xa0', ' ')
            metadata['views_stats'] = ' '.join(stats_text.split())  # Очистка от лишних пробелов

            # Разбор статистики на отдельные значения
            if metadata['views_stats']:
                parsed_stats_values = parse_views_stats_to_dict(metadata['views_stats'])
                metadata.update(parsed_stats_values)  # Добавляем ключи из parsed_stats_values в metadata
        else:
            printer("[Метаданные] Кнопка статистики (OfferStats) не найдена.", kind='info')

        # Если ни одно из основных полей не было заполнено (кроме производных)
        if metadata['updated_date'] is None and metadata['views_stats'] is None:
            printer("[Метаданные] Не удалось извлечь метаданные объявления (дата и статистика отсутствуют).",
                    kind='info')
            return None  # Возвращаем None, если совсем ничего не нашли

        printer(f"[Метаданные] {metadata}", kind='info')
        return metadata

    except Exception as _ex:
        printer(f'error_get_offer_metadata_info: Произошла ошибка: {_ex}', kind='error')
        return None


def get_developer_info(soup):
    developer_data = {}

    # 1. Парсинг блока NewbuildingSpecifications
    newbuilding_specs_block = soup.find('ul', {'data-name': 'NewbuildingSpecifications'})
    if newbuilding_specs_block:
        printer("[Застройщик] Найден блок NewbuildingSpecifications", kind='info')
        temp_newbuilding_data = {}
        for item_li in newbuilding_specs_block.find_all('li', class_='a10a3f92e9--item--E1gcC', recursive=False):
            title_div = item_li.find('div', class_='a10a3f92e9--title--QSQ4B')
            if not title_div:
                continue

            key_span = title_div.find('span')
            if not key_span:
                continue
            key = key_span.text.strip().replace('\xa0', ' ')

            value_tag = title_div.find_next_sibling(['span', 'a'])

            if value_tag and key:
                value = value_tag.text.strip().replace('\xa0', ' ')
                temp_newbuilding_data[key] = value

        if temp_newbuilding_data:
            printer(f"[Застройщик] Данные из NewbuildingSpecifications: {temp_newbuilding_data}", kind='info')
            developer_data.update(temp_newbuilding_data)
    else:
        printer("[Застройщик] Блок NewbuildingSpecifications не найден", kind='info')

    # 2. Парсинг блока DeveloperLayout (данные из него приоритетнее и могут перезаписать/дополнить)
    developer_layout_block = soup.find('div', {'data-name': 'DeveloperLayout'})
    if developer_layout_block:
        printer("[Застройщик] Найден блок DeveloperLayout", kind='info')
        current_developer_layout_data = {}

        # Имя застройщика
        logo_div = developer_layout_block.find('div', {'data-name': 'DeveloperLogo'})
        if logo_div:
            link_tag = logo_div.find('a', {'data-testid': 'developer-logo-link'})
            if link_tag:
                name_span_candidates = link_tag.find_all('span', class_=lambda x: x and 'text--b2YS3' in x)
                if len(name_span_candidates) > 1 and "застройщик" in name_span_candidates[0].text.lower():
                    developer_name = name_span_candidates[1].text.strip().replace('\xa0', ' ')
                    current_developer_layout_data['Застройщик'] = developer_name

        # Статистика: Год основания, Сдано, Строится
        stats_wrapper = developer_layout_block.find('div', class_='a10a3f92e9--wrapper--xyaQb')
        if stats_wrapper:
            # Ищем div или a с классом a10a3f92e9--title--9dsfx
            stat_items = stats_wrapper.find_all(
                lambda tag: (tag.name == 'div' or tag.name == 'a') and tag.get('data-testid') and 'stat' in tag.get(
                    'data-testid'))
            if not stat_items:  # Запасной вариант, если data-testid нет, но класс есть
                stat_items = stats_wrapper.find_all(
                    lambda tag: (tag.name == 'div' or tag.name == 'a') and 'a10a3f92e9--title--9dsfx' in tag.get(
                        'class', []))

            for stat_item in stat_items:
                spans = stat_item.find_all('span', recursive=False)
                if len(spans) == 2:
                    key_stat = spans[0].text.strip().replace('\xa0', ' ')
                    value_stat = spans[1].text.strip().replace('\xa0', ' ')
                    if key_stat and value_stat:
                        current_developer_layout_data[key_stat] = value_stat

        if current_developer_layout_data:
            printer(f"[Застройщик] Данные из DeveloperLayout: {current_developer_layout_data}", kind='info')
            developer_data.update(current_developer_layout_data)
    else:
        printer("[Застройщик] Блок DeveloperLayout не найден", kind='info')

    if not developer_data:
        printer("[Застройщик] Информация о застройщике не найдена.", kind='info')
        return None

    printer(f"[Застройщик] Итоговая информация о застройщике: {developer_data}", kind='info')
    # ic(developer_data)
    return developer_data


def get_rosreestr_info(soup):
    rosreestr_data = {}
    rosreestr_section = soup.find('div', {'data-name': 'RosreestrSection'})

    if not rosreestr_section:
        printer("[Росреестр] Блок RosreestrSection не найден.", kind='info')
        return None

    printer("[Росреестр] Найден блок RosreestrSection", kind='info')
    items = rosreestr_section.find_all('div', {'data-name': 'NameValueListItem'})
    for item in items:
        dt_tag = item.find('dt', class_='a10a3f92e9--name--_zate')
        value_div_container = item.find('div', {'data-name': 'RosreestrItemValue'})

        if dt_tag and value_div_container:
            value_text_div = value_div_container.find('div', class_=lambda x: x and 'text--Q7D3p' in x)
            if value_text_div:
                key = dt_tag.text.strip().replace('\xa0', ' ')
                value = value_text_div.text.strip().replace('\xa0', ' ')
                if 'площадь' in key.lower() and 'м²' in value:
                    value = value.replace('м²', '').strip()
                rosreestr_data[key] = value

    if not rosreestr_data:
        printer("[Росреестр] В блоке RosreestrSection не найдено элементов NameValueListItem с данными.",
                kind='info')
        return None

    printer(f"[Росреестр] {rosreestr_data}", kind='info')
    # ic(rosreestr_data)
    return rosreestr_data


def get_agent_info(soup):
    agent_data = {}
    agent_info_block = soup.find('div', {'data-name': 'AgentInfo'})

    if not agent_info_block:
        printer("[Агент] Блок AgentInfo не найден.", kind='info')
        return None

    printer("[Агент] Найден блок AgentInfo", kind='info')

    # ID или имя автора
    agent_name_link = agent_info_block.find('a', class_='a10a3f92e9--agent-name--SVA8M')
    if agent_name_link:
        agent_id_span = agent_name_link.find('span', class_=lambda x: x and 'text--b2YS3' in x)
        if agent_id_span:
            agent_data['Автор ID/Имя'] = agent_id_span.text.strip().replace('\xa0', ' ')

    # На ЦИАН
    lifetime_container = agent_info_block.find('li', {'data-name': 'AgentLifeTimeContainer'})
    if lifetime_container:
        lifetime_span = lifetime_container.find('span', {'data-name': 'AgentLifeTime'})
        if lifetime_span:
            text = lifetime_span.text.strip().replace('\xa0', ' ')
            cleaned_text = text.lower().replace('на циан', '').strip()
            if cleaned_text:
                agent_data['На ЦИАН'] = cleaned_text.capitalize()
            else:
                agent_data['На ЦИАН'] = text

    # Количество объявлений
    more_offers_li = agent_info_block.find('li', {'data-name': 'MoreOffers'})
    if more_offers_li:
        more_offers_link = more_offers_li.find('a')
        if more_offers_link:
            more_offers_span = more_offers_link.find('span')
            if more_offers_span:
                text_content = more_offers_span.text.strip().replace('\xa0', ' ')
                parts = text_content.split(' ')
                if parts and parts[0].isdigit():
                    agent_data['Объявлений автора'] = parts[0]
                else:
                    agent_data['Объявлений автора (текст)'] = text_content

    if not agent_data:
        printer("[Агент] В блоке AgentInfo не найдено данных.", kind='info')
        return None

    printer(f"[Агент] Информация об авторе объявления {agent_data}", kind='info')
    return agent_data


def get_description(soup):
    try:
        # Находим родительский div
        container_div = soup.find('div', {'data-id': 'content'})

        if not container_div:
            printer("[get_description] Не удалось найти div с атрибутом data-id='content'.", kind='info')
            return None

        # Находим нужный span внутри div.
        # Можно использовать один из классов, например, тот, что отвечает за white-space,
        # так как он важен для форматирования.
        # Классы очень длинные и могут меняться, выберите наиболее стабильный или комбинацию.
        target_span = container_div.find('span', class_=lambda
            c: c and 'a10a3f92e9--text_whiteSpace__pre-wrap--dFity' in c.split())
        # Альтернативно, если это единственный span или первый span в div:
        # target_span = container_div.find('span')

        if target_span:
            # Используем .strings для получения всех текстовых узлов как они есть
            # ''.join() соединит их, сохраняя все внутренние пробелы и переносы строк
            raw_text = ''.join(target_span.strings)

            # .strip() уберет лишние пробелы/переносы только в начале и конце всего блока,
            # но сохранит все внутренние.
            result = raw_text.strip().replace('\n', '<br>')

            printer(f"[Описание]: {result}", kind='info')  # для отладки
            return result
        else:
            printer("[get_description] Не удалось найти целевой span внутри div.", kind='info')
            return None

    except Exception as _ex:
        printer(f'error_get_description: {_ex}', kind='error')
        return None


def save_image(image_directory, img_url, number):
    img_url_modified = img_url.replace('-2.jpg', '-1.jpg')  # Модифицируем URL один раз

    try:
        # Формируем имя файла и полный путь для сохранения
        # Используем модифицированный URL для имени файла
        file_name = os.path.split(img_url_modified)[1]
        path_to_save = os.path.join(image_directory, file_name)

        # Проверяем, существует ли файл по этому пути
        if os.path.exists(path_to_save):
            printer(f"Изображение '{file_name}' уже существует. Пропуск загрузки.", kind='info')
            return path_to_save  # Возвращаем путь к уже существующему файлу

        # Если файла нет, продолжаем с загрузкой
        t = 0.9
        if number % 2 == 0:
            t += 0.4

        # printer(f"Пауза перед загрузкой {img_url_modified}: {t:.1f} сек.", kind='info')  # Отладочное сообщение
        time.sleep(t)

        # printer(f"Загрузка изображения: {img_url_modified}", kind='info')  # Отладочное сообщение
        response = requests.get(img_url_modified, timeout=15)  # Добавлен таймаут для запроса
        response.raise_for_status()  # Проверка на HTTP ошибки (4xx, 5xx)

        # Убедимся, что директория существует перед сохранением
        os.makedirs(image_directory, exist_ok=True)

        with open(path_to_save, 'wb') as img_file:
            img_file.write(response.content)
        printer(f"Изображение сохранено как '{file_name}'", kind='info')

    except requests.exceptions.HTTPError as http_err:
        printer(f'HTTP ошибка при загрузке {img_url_modified}: {http_err}', kind='error')
        return None  # или path_to_save, если нужно знать, какой файл не удалось скачать
    except requests.exceptions.ConnectionError as conn_err:
        printer(f'Ошибка соединения при загрузке {img_url_modified}: {conn_err}', kind='error')
        return None
    except requests.exceptions.Timeout as timeout_err:
        printer(f'Таймаут при загрузке {img_url_modified}: {timeout_err}', kind='error')
        return None
    except requests.exceptions.RequestException as req_err:  # Общее исключение для requests
        printer(f'Ошибка requests при загрузке {img_url_modified}: {req_err}', kind='error')
        return None
    except IOError as io_err:  # Ошибки при работе с файлами
        printer(f'Ошибка ввода-вывода при сохранении {path_to_save}: {io_err}', kind='error')
        return None
    except Exception as _ex:
        printer(f'Непредвиденная ошибка при обработке {img_url_modified}: {_ex}', kind='error')
        return None  # Возвращаем None в случае любой другой ошибки, чтобы сигнализировать о неудаче

    return path_to_save


def get_imgages(soup, cian_number):
    # Создадим директорию для сохранения изображений
    image_directory = os.path.join(downloads_dir_absolute, cian_number)
    # ic(image_directory)
    os.makedirs(image_directory, exist_ok=True)
    img_list = []

    try:
        images = []
        image_tags = soup.find_all('img')
        for num, item in enumerate(image_tags):
            if 'data-name="ThumbComponent"' in str(item):
                image = str(item).split('src=')[1][1:-3]
                images.append((image))
                img_list.append(save_image(image_directory, image, num))
        printer(f'{img_list=}', )
    except Exception as _ex:
        printer(f'error_get_imgages: {_ex}', kind='error')

    return [img_list, images]
