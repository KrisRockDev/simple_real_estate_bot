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


def get_params(soup):
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

        printer(f"[Параметры] {result=}", kind='info')
        return result
    except Exception as _ex:
        printer(f'error_get_params: {_ex}', kind='error')
        return None


def get_description(soup):
    try:
        # Извлекаем текст из тега span
        target_div = soup.find('div', {'data-id': 'content'})

        if target_div:
            text_data = target_div.get_text(separator='\n', strip=True)
            result = ''.join(line.strip() for line in text_data.split('\n') if line.strip())
            result = result.replace('-\t', '<br>- ')
            printer(f"{result=}", kind='info')
        else:
            printer("[get_description] Не удалось найти указанный div с атрибутом data-id='content'.", kind='error')

        return result
    except Exception as _ex:
        printer(f'error_get_description: {_ex}', kind='error')
        return None


def save_image(image_directory, img_url, number):
    img_url = img_url.replace('-2.jpg', '-1.jpg')
    t = 0.7
    if number % 2 == 0:
        t += 0.3
    time.sleep(t)
    try:
        response = requests.get(img_url)
        file_name = os.path.split(img_url)[1]
        path_to_save = os.path.join(image_directory, file_name)
        with open(path_to_save, 'wb') as img_file:
            img_file.write(response.content)
        printer(f"Изображение сохранено как '{file_name}'", kind='info')

    except Exception as _ex:
        printer(f'error_save_image: {_ex}', kind='error')

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
