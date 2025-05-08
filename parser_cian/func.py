import os
import time
import requests
from icecream import ic
from settings import downloads_dir_absolute
from servise import printer


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


def get_adress(soup):
    try:
        # Находим блок с атрибутом data-name="AddressContainer"
        address_container = soup.find('div', {'data-name': 'AddressContainer'})
        # Извлекаем текст из найденного блока
        result = ''.join(address_container.get_text(separator='\t').replace('\t,', '').split('\t')[-3:-1])
        if ' ул. ' in result:
            result = f'ул. {result.replace(' ул. ', ' д.')}'
        printer(f"[Адрес] {result}", kind='info')
        return result
    except Exception as _ex:
        printer(f'error_get_adress: {_ex}', kind='error')
        return None


def get_price(soup):
    try:
        # Находим элемент с атрибутом data-testid="price-amount"
        price_element = soup.find('div', {'data-testid': 'price-amount'})
        # Извлекаем текст из найденного элемента и приводим его в нужный вид
        result = price_element.text.strip().replace('\xa0', '').replace('&nbsp;', ' ').split('₽/мес.')[0]
        printer(f"[Цена] {result} ₽/мес.", kind='info')
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
        ic(result)
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
    ic(params_data)
    return params_data


def get_developer_info(soup):
    developer_data = {}

    # 1. Парсинг блока NewbuildingSpecifications
    newbuilding_specs_block = soup.find('ul', {'data-name': 'NewbuildingSpecifications'})
    if newbuilding_specs_block:
        printer("[Developer Info] Найден блок NewbuildingSpecifications", kind='info')
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
            printer(f"[Developer Info] Данные из NewbuildingSpecifications: {temp_newbuilding_data}", kind='info')
            developer_data.update(temp_newbuilding_data)
    else:
        printer("[Developer Info] Блок NewbuildingSpecifications не найден", kind='info')

    # 2. Парсинг блока DeveloperLayout (данные из него приоритетнее и могут перезаписать/дополнить)
    developer_layout_block = soup.find('div', {'data-name': 'DeveloperLayout'})
    if developer_layout_block:
        printer("[Developer Info] Найден блок DeveloperLayout", kind='info')
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
            printer(f"[Developer Info] Данные из DeveloperLayout: {current_developer_layout_data}", kind='debug')
            developer_data.update(current_developer_layout_data)
    else:
        printer("[Developer Info] Блок DeveloperLayout не найден", kind='info')

    if not developer_data:
        printer("[Developer Info] Информация о застройщике не найдена.", kind='info')
        return None

    printer(f"[Итоговая информация о застройщике] {developer_data}", kind='info')
    ic(developer_data)
    return developer_data


def get_rosreestr_info(soup):
    rosreestr_data = {}
    rosreestr_section = soup.find('div', {'data-name': 'RosreestrSection'})

    if not rosreestr_section:
        printer("[Rosreestr Info] Блок RosreestrSection не найден.", kind='info')
        return None

    printer("[Rosreestr Info] Найден блок RosreestrSection", kind='info')
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
        printer("[Rosreestr Info] В блоке RosreestrSection не найдено элементов NameValueListItem с данными.",
                kind='info')
        return None

    printer(f"[Информация из Росреестра] {rosreestr_data}", kind='info')
    ic(rosreestr_data)
    return rosreestr_data


def get_agent_info(soup):
    agent_data = {}
    agent_info_block = soup.find('div', {'data-name': 'AgentInfo'})

    if not agent_info_block:
        printer("[Agent Info] Блок AgentInfo не найден.", kind='info')
        return None

    printer("[Agent Info] Найден блок AgentInfo", kind='info')

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
        printer("[Agent Info] В блоке AgentInfo не найдено данных.", kind='info')
        return None

    printer(f"[Информация об авторе объявления] {agent_data}", kind='info')
    ic(agent_data)
    return agent_data


# def get_description(soup):
#     try:
#         # Извлекаем текст из тега span
#         target_div = soup.find('div', {'data-id': 'content'})
#
#         if target_div:
#             text_data = target_div.get_text(separator='\n', strip=True)
#             result = ''.join(line.strip() for line in text_data.split('\n') if line.strip())
#             result = result.replace('-\t', '<br>- ').replace('.-', '.<br>-')
#             printer(f"{result=}", kind='info')
#         else:
#             printer("[get_description] Не удалось найти указанный div с атрибутом data-id='content'.", kind='error')
#
#         return result
#     except Exception as _ex:
#         printer(f'error_get_description: {_ex}', kind='error')
#         return None


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


# def save_image(image_directory, img_url, number):
#     img_url = img_url.replace('-2.jpg', '-1.jpg')
#     t = 0.9
#     if number % 2 == 0:
#         t += 0.4
#     time.sleep(t)
#     try:
#         response = requests.get(img_url)
#         file_name = os.path.split(img_url)[1]
#         path_to_save = os.path.join(image_directory, file_name)
#         with open(path_to_save, 'wb') as img_file:
#             img_file.write(response.content)
#         printer(f"Изображение сохранено как '{file_name}'", kind='info')
#
#     except Exception as _ex:
#         printer(f'error_save_image: {_ex}', kind='error')
#
#     return path_to_save

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
        # Если файл был создан, но не записан, он может остаться пустым или поврежденным.
        # Можно добавить логику удаления такого файла:
        # if os.path.exists(path_to_save):
        # try:
        # os.remove(path_to_save)
        # printer(f"Удален частично загруженный файл: {path_to_save}", kind='warning')
        # except OSError as e_del:
        # printer(f"Не удалось удалить частично загруженный файл {path_to_save}: {e_del}", kind='error')
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

    return img_list
