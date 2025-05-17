import os
import re  # Для очистки описания от лишних пробелов и замены переносов строк
import traceback  # Для более детальной информации об ошибке
import datetime
from servise import printer
from settings import templates_dir_absolute, downloads_dir_absolute
from dotenv import load_dotenv
from icecream import ic

load_dotenv()


def format_price(price_string):
    """
    Форматирует строку с ценой, добавляя разделители тысяч (пробелы).

    Принимает строку вида "ЦИФРЫ₽" (например, "21347430₽").
    Возвращает строку вида "ЦИФРЫ С ПРОБЕЛАМИ₽" (например, "21 347 430₽").
    Если входная строка не соответствует ожидаемому формату или пуста,
    возвращает исходную строку.

    Args:
        price_string (str): Строка с ценой и символом рубля в конце.

    Returns:
        str: Отформатированная строка цены или исходная строка при ошибке.
    """
    if price_string != 'Цена не указана':
        if not price_string or not isinstance(price_string, str):
            return price_string  # Возвращаем как есть, если не строка или пустая

        currency_symbol = '₽'
        numeric_part = price_string

        # 1. Отделяем символ валюты, если он есть
        if price_string.endswith(currency_symbol):
            numeric_part = price_string[:-len(currency_symbol)]
            symbol_to_append = ' ' + currency_symbol
        else:
            # Если символа нет, форматируем как есть, символ не добавляем
            symbol_to_append = ''

        # 2. Удаляем возможные существующие пробелы/разделители для чистого числа
        numeric_part_cleaned = numeric_part.replace(' ', '').replace('\xa0', '')

        # 3. Пытаемся преобразовать в число и отформатировать
        try:
            number = int(numeric_part_cleaned)

            # Используем f-строку с форматированием через запятую, затем заменяем запятую на пробел
            # Это стандартный способ добавить разделители тысяч
            formatted_number = f"{number:,}".replace(',', ' ')

            # 4. Собираем результат обратно
            return formatted_number + symbol_to_append

        except ValueError:
            # Если не удалось преобразовать в число, возвращаем исходную строку
            return price_string
        except Exception as e:
            # Обработка других возможных ошибок
            printer(f"[format_price] error: Не удалось отформатировать цену '{price_string}': {e}", kind='error')
            return price_string
    else:
        return 'Цена не указана'


def create_header_and_footer(cian_number):
    """
    Создаёт заголовок и подвал для HTML-отчета.
    """
    header_template_path = os.path.join(templates_dir_absolute, 'header.html')
    footer_template_path = os.path.join(templates_dir_absolute, 'footer.html')

    header_index = os.path.join(downloads_dir_absolute, os.path.join(cian_number, 'header_index.html'))
    footer_index = os.path.join(downloads_dir_absolute, os.path.join(cian_number, 'footer_index.html'))

    replace_list = [
        ('ИМЯ_РИЕЛТОРА', os.getenv("NAME", "")),
        ('ТЕЛЕФОН_РИЕЛТОРА', os.getenv("PHONE", "")),
        ('EMAIL_PLACEHOLDER', os.getenv("EMAIL", "")),
        ('TELEGRAM_BOT_USERNAME', os.getenv("TELEGRAM_BOT_USERNAME", "")),
        ('TELEGRAM_BOT_LINK', os.getenv("TELEGRAM_BOT_LINK", ""))
    ]

    with open(file=header_template_path, mode='r', encoding='utf8') as f:
        header_html = f.read()

    for i in replace_list:
        header_html = header_html.replace(i[0], i[1])

    with open(file=header_index, mode='w', encoding='utf8') as f:
        f.write(header_html)

    with open(file=footer_template_path, mode='r', encoding='utf8') as f:
        footer_html = f.read()

    for i in replace_list:
        footer_html = footer_html.replace(i[0], i[1])

    with open(file=footer_index, mode='w', encoding='utf8') as f:
        f.write(footer_html)

    return header_index, footer_index


def create_report_cian(res, cian_number):
    """
    Создает HTML-отчет на основе шаблона cian.html и данных из словаря res.
    Заменяет плейсхолдеры в шаблоне и сохраняет результат в новый файл.

    Args:
        res (dict): Словарь с данными для заполнения шаблона.
        cian_number (str): Номер объявления Cian, используется для создания пути.
    """
    header_index, footer_index = create_header_and_footer(cian_number)
    tempfile_path = os.path.join(templates_dir_absolute, 'cian7.html')

    # Убедимся, что директория для cian_number существует или создаем ее
    output_dir = os.path.join(downloads_dir_absolute, str(cian_number))
    os.makedirs(output_dir, exist_ok=True)

    output_filename = 'index.html'  # Имя выходного файла
    output_path = os.path.join(output_dir, output_filename)

    try:
        with open(file=tempfile_path, mode='r', encoding='utf8') as f:
            template = f.read()

        # --- Подготовка данных ---

        # Безопасное извлечение данных. Используем `res.get(key) or default`,
        # чтобы обработать случаи, когда значение по ключу в res может быть None.
        offer = res.get('offer') or {}
        metro_list = res.get('metro') or []
        params = res.get('params') or {}
        author_branding = res.get('author_branding') or {}
        offer_metadata = res.get('offer_metadata') or {}
        developer = res.get('developer') or {}
        if 'Отделка' in developer:
            Dash_square = '''
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-dash-square" viewBox="0 0 16 16">
              <path d="M14 1a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1zM2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2z"/>
              <path d="M4 8a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7A.5.5 0 0 1 4 8"/>
            </svg>
            '''
            Empty_square = '''
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-square" viewBox="0 0 16 16">
              <path d="M14 1a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1zM2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2z"/>
            </svg>
            '''
            Check_square = '''
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-check-square" viewBox="0 0 16 16">
              <path d="M14 1a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1zM2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2z"/>
              <path d="M10.97 4.97a.75.75 0 0 1 1.071 1.05l-3.992 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
            </svg>
            '''
            otdelka = developer['Отделка'].lower().split(',')
            otdelka_new = []
            for i in otdelka:
                if i == params['Отделка'].lower():
                    otdelka_new.append(f"{Check_square}{i}")
                else:
                    otdelka_new.append(f"{Empty_square}{i}")
            params['Отделка'] = '<br>'.join(otdelka_new)
            # params['Отделка'] = developer['Отделка'].lower().replace(', ', '<br>').replace(params['Отделка'].lower(),f"<b>{params['Отделка'].lower()}</b>").capitalize()
        if 'Парковка' in params and 'Парковка' in developer:
            if len(params['Парковка']) < len(developer['Парковка']):
                params['Парковка'] = developer['Парковка']
        if 'Тип дома' in params and 'Тип дома' in developer:
            if len(params['Тип дома']) < len(developer['Тип дома']):
                params['Тип дома'] = developer['Тип дома']
        rosreestr = res.get('rosreestr') or {}
        agent = res.get('agent') or {}
        images = res.get('images') or []
        description = res.get('description', 'Описание отсутствует.')
        # ic(offer)
        # ic(metro_list)
        # ic(params)
        # ic(author_branding)
        # ic(offer_metadata)
        # ic(developer)
        # ic(rosreestr)
        # ic(agent)
        # ic(description)

        # Форматирование списка метро
        metro_html = ""
        if metro_list:
            metro_items = []
            for station_info in metro_list:
                station = station_info.get('station', '?')
                method = station_info.get('method', '')
                time = station_info.get('time', '')
                metro_items.append(f'<i class="bi bi-geo-alt-fill text-success"></i> {station} ({method} {time})')
            metro_html = " ".join(metro_items)
        else:
            metro_html = "Нет данных о метро"

        # Форматирование изображений
        # HTML-шаблон предполагает, что ФОТОГРАФИИ вставляются внутрь <tr> ... </tr>
        # Поэтому генерируем <td> элементы.
        images_html_parts = []
        if images:
            # Отображаем до 3х картинок
            images_to_display = images[:3]
            for i, img_path in enumerate(images_to_display):
                if img_path:
                    try:
                        img_src = f"file:///{img_path.replace(os.sep, '/')}"
                        images_html_parts.append(f'''
                                <td style="padding: 0.5rem; text-align: center;">
                                  <img src="{img_src}" style="width:280px;" alt="Фото {i + 1}">
                                </td>''')
                    except Exception as e:
                        printer(f"[create_report_cian] Ошибка обработки пути изображения '{img_path}' в отчете: {e}", kind='error')
                else:
                    # Что делать, если изображение не скачалось?
                    # Можно пропустить, можно добавить плейсхолдер в отчет
                    printer("[create_report_cian] Пропуск отсутствующего изображения (None) при создании отчета.", kind='info')
                    # Например, добавить пустую строку или сообщение об ошибке в HTML/PDF
                    # html_content += "<p><i>Изображение не загружено</i></p>"
            # Если картинок меньше 3, и мы хотим занимать все 3 колонки (например, для выравнивания)
            # можно добавить пустые <td>. Но текущий HTML этого не требует явно.
            # while len(images_html_parts) < 3 and len(images_html_parts) > 0:
            #     images_html_parts.append('<td></td>') # Пустая ячейка для выравнивания

        if not images_html_parts:  # Если список пуст (не было картинок или images был пуст)
            images_html = '<td colspan="3"><p>Фотографии отсутствуют.</p></td>'
        else:
            images_html = "".join(images_html_parts)

        # Обработка описания: замена переносов строк на <br> и удаление лишних пробелов
        cleaned_description = re.sub(r'\s+', ' ', description).strip()
        cleaned_description = cleaned_description.replace('\n', '<br>').replace('\r', '')
        cleaned_description = cleaned_description.replace('\t', ' ')

        # Извлечение этажа и этажности
        floor_info = params.get('Этаж', ' / ')
        try:
            floor, total_floors = floor_info.split(' из ')
            floor = floor.strip()
            total_floors = total_floors.strip()
        except ValueError:
            floor = floor_info
            total_floors = '?'

        # --- Список замен ---
        EMPTY_VALUES_FOR_HIDE = ['?', None, '', 'Не указано', 'Не указана', 'Нет данных']

        # --- Функции для генерации HTML строк для таблицы деталей ---
        # (Эти функции теперь получают словари params или rosreestr, которые гарантированно являются dict)

        def generate_developer_info_row(params_dict):
            if params_dict != {}:
                developer_info = params_dict.get('Застройщик', 'н/д')
                developer_year_info = params_dict.get('Год основания', 'н/д')
                bilded_info = params_dict.get('Сдано', 'н/д')
                bilding_info = params_dict.get('Строится', 'н/д')

                return f"""<h4 class="section-title fw-bold">О застройщике</h4>
                            <table style="width: 100%;">
                                <tr>
                                    <td style="width: 25%;" class="detail-item">
                                        <div class="label">Застройщик</div>
                                        <div class="value">{developer_info}</div>
                                    </td>
                                    <td style="width: 25%;" class="detail-item">
                                        <div class="label">Год основания</div>
                                        <div class="value">{developer_year_info}</div>
                                    </td>
                                    <td style="width: 25%;" class="detail-item">
                                        <div class="label">Сдано</div>
                                        <div class="value">{bilded_info}</div>
                                    </td>
                                    <td style="width: 25%;" class="detail-item">
                                        <div class="label">Строится</div>
                                        <div class="value">{bilding_info}</div>
                                    </td>
                                </tr>
                            </table>"""
            return ''

        def generate_developer_year_row(params_dict):
            value = params_dict.get('Год основания')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f""" (c {value})"""
            return ''

        def generate_developer_row(params_dict):
            value = params_dict.get('Застройщик')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Застройщик</span></td>
                                <td class="value-cell"><span class="value">{value}{generate_developer_year_row(params_dict)}</span></td>
                            </tr>"""
            return ''

        def generate_data_complex_row(params_dict):
            value = params_dict.get('Сдача комплекса')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Сдача комплекса</span></td>
                                <td class="value-cell"><span class="value">{value.replace('Сдача в', '')} г.</span></td>
                            </tr>"""
            return ''

        def generate_complex_type_row(params_dict):
            value = params_dict.get('Тип комплекса')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Тип комплекса</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        def generate_class_row(params_dict):
            value = params_dict.get('Класс')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Класс</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        def generate_otdelka_row(params_dict):
            # ic(params_dict)
            value = params_dict.get('Отделка')
            # ic(params_dict.get('Отделка'))
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Отделка</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        def generate_total_area_row(params_dict):
            value = params_dict.get('Общая площадь')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Общая площадь, м²</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        def generate_living_area_row(params_dict):
            value = params_dict.get('Жилая площадь')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Жилая площадь, м²</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        def generate_kitchen_area_row(params_dict):
            value = params_dict.get('Площадь кухни')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Площадь кухни, м²</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        def generate_ceiling_height_row(params_dict):
            value = params_dict.get('Высота потолков')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Высота потолков, м</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        def generate_floor_info_row(floor_val, total_floors_val):
            floor_str = str(floor_val) if floor_val not in EMPTY_VALUES_FOR_HIDE else None
            total_floors_str = str(total_floors_val) if total_floors_val not in EMPTY_VALUES_FOR_HIDE else None

            if floor_str and total_floors_str:
                value_display = f"{floor_str} из {total_floors_str}"
            elif floor_str:
                value_display = floor_str
            elif total_floors_str:
                value_display = f"? из {total_floors_str}"
            else:
                return ''

            return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Этаж</span></td>
                                <td class="value-cell"><span class="value">{value_display}</span></td>
                            </tr>"""

        def generate_balcon_row(params_dict):
            value = params_dict.get('Балкон/лоджия')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Балкон/лоджия</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        def generate_renovation_row(params_dict):
            value = params_dict.get('Ремонт')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Отделка/Ремонт</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        def generate_bathroom_row(params_dict):
            value = params_dict.get('Санузел')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Санузел</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        def generate_window_view_row(params_dict):
            value = params_dict.get('Вид из окон')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Вид из окон</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        def generate_furniture_status_row(params_dict):
            value = params_dict.get('Продаётся с\xa0мебелью')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Продаётся с мебелью</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        def generate_house_type_row(params_dict):
            value = params_dict.get('Тип дома')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Тип дома</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        def generate_flooring_type_row(params_dict):
            value = params_dict.get('Тип перекрытий')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Тип перекрытий</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        def generate_building_series_row(params_dict):
            value = params_dict.get('Строительная серия')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Строительная серия</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        def generate_mosquito_net_row(params_dict):
            value = params_dict.get('Мусоропровод')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Мусоропровод</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        def generate_elevator_count_row(params_dict):
            value = params_dict.get('Количество лифтов')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Лифт</span></td>
                                <td class="value-cell"><span class="value">{value.replace(',', '<br>')}</span></td>
                            </tr>"""
            return ''

        def generate_entrances_row(params_dict):
            value = params_dict.get('Подъезды')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Подъезды</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        def generate_parking_row(params_dict):
            value = params_dict.get('Парковка')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Парковка</span></td>
                                <td class="value-cell"><span class="value">{value.replace(',', '<br>')}</span></td>
                            </tr>"""
            return ''

        def generate_heating_row(params_dict):
            value = params_dict.get('Отопление')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Отопление</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        def generate_emergency_status_row(params_dict):
            value = params_dict.get('Аварийность')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Аварийность</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        def generate_gas_status_row(params_dict):
            value = params_dict.get('Газоснабжение')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Газоснабжение</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        # Функции для Росреестра
        def generate_saler_status_row(rosreestr_dict):  # Получает rosreestr
            value = rosreestr_dict.get('Собственников')  # Исправлен ключ
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Собственников</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        def generate_peoples_status_row(rosreestr_dict):  # Получает rosreestr
            value = rosreestr_dict.get('Обременения')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Обременения</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        def generate_kadaster_status_row(rosreestr_dict):  # Получает rosreestr
            value = rosreestr_dict.get('Кадастровый номер')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Кадастровый номер</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''



        replace_list = [
            ('DATE_TAME_ROW', datetime.datetime.now().strftime("%d.%m.%Y в %H:%M:%S")),
            ('ОБНОВЛЕНО_ROW', offer_metadata.get('updated_date', 'Не указано')),
            ('ПРОСМОТРЫ_ROW', offer_metadata.get('views_stats', 'Не указано')),
            ('ИМЯ_РЕЕЛТОРА', os.getenv("NAME", "Имя не указано")),
            ('ТЕЛЕФОН_РИЕЛТОРА', os.getenv("PHONE", "Телефон не указан")),
            ('НАЗВАНИЕ', res.get('title', 'Без названия').replace('Продается', '')),
            ('АДРЕС', res.get('adress', 'Адрес не указан')),
            ('ТИП_ЖИЛЬЯ', params.get('Тип жилья', 'Тип не указан')),
            ('СТОИМОСТЬ', format_price(res.get('price', 'Цена не указана'))),
            ('МЕТРО', metro_html),
            ('ЦЕНА_ЗА_МЕТР', format_price(offer.get('Цена за метр', 'Не указано'))),
            ('УСЛОВИЯ_СДЕЛКИ', (offer.get('Условия сделки') or params.get('Дом') or 'Не указано').capitalize()),
            ('ИПОТЕКА', offer.get('Ипотека', 'Не указано')),
            ('ФОТОГРАФИИ', images_html),
            ('ГОД_ПОСТРОЙКИ', params.get('Год постройки', params.get('Год сдачи', 'Не указан'))),
            ('ОПИСАНИЕ', cleaned_description),
            # ('ФОТООТЧЁТ', images_html), # Плейсхолдер отсутствует в cian7.html

            ('ОБЩАЯ_ПЛОЩАДЬ_ROW', generate_total_area_row(params)),
            ('ЖИЛАЯ_ПЛОЩАДЬ_ROW', generate_living_area_row(params)),
            ('ПЛОЩАДЬ_КУХНИ_ROW', generate_kitchen_area_row(params)),
            ('ВЫСОТА_ПОТОЛКОВ_ROW', generate_ceiling_height_row(params)),
            ('ЭТАЖ_ROW', generate_floor_info_row(floor, total_floors)),
            ('БАЛКОН_ROW', generate_balcon_row(params)),
            ('РЕМОНТ_ROW', generate_renovation_row(params)),
            ('ОТДЕЛКА_ROW', generate_otdelka_row(params)),
            ('САНУЗЕЛ_ROW', generate_bathroom_row(params)),
            ('ВИД_ИЗ_ОКОН_ROW', generate_window_view_row(params)),
            ('СОБСТВЕННИКОВ_ROW', generate_saler_status_row(rosreestr)),
            ('ОБРЕМЕНЕНИЯ_ROW', generate_peoples_status_row(rosreestr)),
            ('МЕБЕЛЬ_ROW', generate_furniture_status_row(params)),  # Продаётся с мебелью
            ('КАДАСТРОВЫЙ_НОМЕР_ROW', generate_kadaster_status_row(rosreestr)),

            ('ТИП_ДОМА_ROW', generate_house_type_row(params)),
            ('ТИП_ПЕРЕКРЫТИЙ_ROW', generate_flooring_type_row(params)),
            ('СТРОИТЕЛЬНАЯ_СЕРИЯ_ROW', generate_building_series_row(params)),
            ('КОЛИЧЕСТВО_ЛИФТОВ_ROW', generate_elevator_count_row(params)),
            ('ПОДЪЕЗДЫ_ROW', generate_entrances_row(params)),
            ('МУСОРОПРОВОД_ROW', generate_mosquito_net_row(params)),
            ('ПАРКОВКА_ROW', generate_parking_row(params)),
            ('ОТОПЛЕНИЕ_ROW', generate_heating_row(params)),
            ('АВАРИЙНОСТЬ_ROW', generate_emergency_status_row(params)),
            ('ГАЗОСНАБЖЕНИЕ_ROW', generate_gas_status_row(params)),

            ('ЗАСТРОЙЩИК_ROW', generate_developer_row(developer)),
            ('КЛАСС_ДОМА_ROW', generate_class_row(developer)),
            ('ЗДАЧА_КОМПЛЕКСА_ROW', generate_data_complex_row(developer)),
            ('ТИП_КОМПЛЕКСА_ROW', generate_complex_type_row(developer)),
            ('О_ЗАСТРОЙЩИКЕ_INFO', generate_developer_info_row(developer)),
        ]

        for placeholder, value in replace_list:
            template = template.replace(placeholder, str(value))

        with open(file=output_path, mode='w', encoding='utf8') as f:
            f.write(template)
        printer(f"[create_cian] Отчет успешно создан и сохранен в: {output_path}", kind='info')

        return output_path, header_index, footer_index

    except FileNotFoundError:
        printer(f"[create_cian] Ошибка: Шаблон не найден по пути {tempfile_path}", kind='error')
        return None
    except KeyError as e:
        printer(f"[create_cian] Ошибка: Отсутствует необходимый ключ в словаре 'res': {e}", kind='error')
        traceback.print_exc()
        return None
    except Exception as e:
        printer(f"[create_cian] Произошла непредвиденная ошибка при создании отчета: {e}", kind='error')
        traceback.print_exc()
        return None


if __name__ == '__main__':
    res_test_data = {
        'title': 'Продается 3-комн. квартира, 86,2 м² в ЖК «Новые Смыслы»',
        'adress': '№ 174 квартал Новые Смыслы жилой комплекс', 'price': '21347430₽',
        'offer': {'Цена за метр': '247 650 ₽/м²', 'Условия сделки': 'долевое участие (214-ФЗ)',
                  'Ипотека': 'возможна'},
        'metro': [{'station': 'Бунинская аллея', 'method': 'пешком', 'time': '5 мин.'},
                  {'station': 'Потапово', 'method': 'пешком', 'time': '17 мин.'},
                  {'station': 'Улица Горчакова', 'method': 'пешком', 'time': '6 мин.'}],
        'params': {'Общая площадь': '86,2', 'Площадь кухни': '22,9', 'Этаж': '2 из 27', 'Год сдачи': '2027',
                   'Дом': 'Не сдан', 'Отделка': 'Без отделки', 'Тип жилья': 'Новостройка',
                   'Высота потолков': '2,88', 'Санузел': '2 совмещенных', 'Вид из окон': 'На улицу',
                   'Количество лифтов': '1 пассажирский, 1 грузовой', 'Тип дома': 'Монолитный',
                   'Парковка': 'Подземная'},
        'developer': {'Сдача комплекса': 'Сдача в 2027—2029', 'Застройщик': 'ГК Юникей', 'Класс': 'Комфорт',
                      'Тип дома': 'Монолитно-кирпичный', 'Парковка': 'Подземная, гостевая',
                      'Отделка': 'Без отделки, предчистовая, черновая, чистовая',
                      'Тип комплекса': 'Жилой комплекс', 'Год основания': '2018', 'Сдано': '7 домов в 2 ЖК',
                      'Строится': '23 дома в 6 ЖК'},
        'rosreestr': None,  # Симулируем None от парсера, как в логе
        'agent': None,  # Симулируем None от парсера, как в логе
        'description': ('В жилом комплексе, расположенном по соседству с ландшафтным парком "Южное Бутово", '
                        # ... (длинное описание как в примере)
                        'Безопасность на территории гарантирована: двор огорожен от машин и оснащен камерами видеонаблюдения.'),
        'images': [
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2451958729-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2371999717-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2371999866-1.jpg',
        ]
    }
    test_cian_number_main = "test_312256069_main"

    # Исправленный вызов с двумя аргументами для отладки этого файла
    output_path = create_report_cian(res_test_data, test_cian_number_main)
    if output_path:
        print(f"Тестовый HTML из __main__ сохранен в: {output_path}")
        # Если нужно протестировать и PDF создание:
        # from PDF_creater import converter
        # converter(DIRECTORY=output_path)
    else:
        print(f"Не удалось создать тестовый HTML из __main__.")
