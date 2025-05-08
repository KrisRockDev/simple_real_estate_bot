import os
import re  # Для очистки описания от лишних пробелов и замены переносов строк
from settings import templates_dir_absolute, downloads_dir_absolute
from dotenv import load_dotenv
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
            symbol_to_append = ' '+ currency_symbol
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
            print(f"Не удалось отформатировать цену '{price_string}': {e}")
            return price_string
    else:
        return 'Цена не указана'


def create_report_cian(res, cian_number):
    """
    Создает HTML-отчет на основе шаблона cian.html и данных из словаря res.
    Заменяет плейсхолдеры в шаблоне и сохраняет результат в новый файл.

    Args:
        res (dict): Словарь с данными для заполнения шаблона.
    """
    tempfile_path = os.path.join(templates_dir_absolute, 'cian7.html')
    output_filename = 'index.html'  # Имя выходного файла
    output_path = os.path.join(os.path.join(downloads_dir_absolute, cian_number), output_filename)

    try:
        with open(file=tempfile_path, mode='r', encoding='utf8') as f:
            template = f.read()

        # --- Подготовка данных ---

        # Безопасное извлечение данных с дефолтными значениями
        offer = res.get('offer', {})
        metro_list = res.get('metro', [])
        params = res.get('params', {})
        developer = res.get('developer', {})
        rosreestr = res.get('rosreestr', {})
        agent = res.get('agent', {})
        images = res.get('images', [])
        description = res.get('description', 'Описание отсутствует.')

        # Форматирование списка метро
        metro_html = ""
        if metro_list:
            metro_items = []
            for station_info in metro_list:
                station = station_info.get('station', '?')
                method = station_info.get('method', '')
                time = station_info.get('time', '')
                # Добавляем иконку метро из Bootstrap Icons
                metro_items.append(f'<i class="bi bi-geo-alt-fill text-success"></i> {station} ({method} {time})')
            metro_html = " ".join(metro_items)  # Соединяем через <br>
        else:
            metro_html = "Нет данных о метро"

        # Форматирование изображений (простой грид Bootstrap)
        images_html = '<div class="row">'

        if images:
            if len(images) >= 3:
                images_3 = images[:3]
                for i, img_path in enumerate(images_3):
                    # Используем file:/// URI для локальных файлов, если отчет будет открываться локально
                    # ВАЖНО: Это может не работать при переносе HTML на веб-сервер без копирования картинок
                    # или потребует относительных/абсолютных URL веб-сервера.
                    img_src = f"file:///{img_path.replace(os.sep, '/')}"  # Преобразуем путь для URL
                    images_html += f'''
                            <td style="padding: 0.5rem; text-align: center;">
                              <img src="{img_src}" style="width:280px;" alt="Фото {i + 1}">
                            </td>'''
        else:
            images_html = '<p>Фотографии отсутствуют.</p>'

        # Обработка описания: замена переносов строк на <br> и удаление лишних пробелов
        # Заменяем табы и множественные пробелы/переносы на один пробел, затем переносы на <br>
        cleaned_description = re.sub(r'\s+', ' ', description).strip()
        cleaned_description = cleaned_description.replace('\n', '<br>').replace('\r', '')  # Основные переносы
        # Если в данных есть "\t", они уже заменены re.sub, но на всякий случай:
        cleaned_description = cleaned_description.replace('\t', ' ')

        # Извлечение этажа и этажности
        floor_info = params.get('Этаж', ' / ')
        try:
            floor, total_floors = floor_info.split(' из ')
            floor = floor.strip()
            total_floors = total_floors.strip()
        except ValueError:
            floor = floor_info  # Если формат не "X из Y", берем как есть
            total_floors = '?'  # Неизвестно

        # --- Список замен ---
        # Список значений, которые, если получены из params, означают отсутствие данных для отображения
        # (кроме случаев, когда само значение информативно, как "Нет данных")
        EMPTY_VALUES_FOR_HIDE = ['?', None, '', 'Не указано', 'Не указана', 'Нет данных']
        # --- Функции для генерации HTML строк для таблицы деталей ---

        def generate_total_area_row(params_dict):
            value = params_dict.get('Общая площадь')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Общая площадь</span></td>
                                <td class="value-cell"><span class="value">{value} м²</span></td>
                            </tr>"""
            return ''

        def generate_living_area_row(params_dict):
            value = params_dict.get('Жилая площадь')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Жилая площадь</span></td>
                                <td class="value-cell"><span class="value">{value} м²</span></td>
                            </tr>"""
            return ''

        def generate_kitchen_area_row(params_dict):
            value = params_dict.get('Площадь кухни')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Площадь кухни</span></td>
                                <td class="value-cell"><span class="value">{value} м²</span></td>
                            </tr>"""
            return ''

        def generate_ceiling_height_row(params_dict):
            value = params_dict.get('Высота потолков')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Высота потолков</span></td>
                                <td class="value-cell"><span class="value">{value} м</span></td>
                            </tr>"""
            return ''

        def generate_floor_info_row(floor_val, total_floors_val):
            floor_str = str(floor_val) if floor_val not in EMPTY_VALUES_FOR_HIDE else None
            total_floors_str = str(total_floors_val) if total_floors_val not in EMPTY_VALUES_FOR_HIDE else None

            if floor_str and total_floors_str:
                value_display = f"{floor_str} из {total_floors_str}"
            elif floor_str:
                value_display = floor_str
            elif total_floors_str:  # Менее вероятно, но возможно
                value_display = f"? из {total_floors_str}"
            else:
                return ''  # Нет данных для отображения

            return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Этаж</span></td>
                                <td class="value-cell"><span class="value">{value_display}</span></td>
                            </tr>"""

        def generate_renovation_row(params_dict):
            value = params_dict.get('Отделка')
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

        # Функции для правой колонки "О доме"

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

        def generate_elevator_count_row(params_dict):
            value = params_dict.get('Количество лифтов')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Лифт</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
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
                                <td class="value-cell"><span class="value">{value}</span></td>
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

        def generate_saler_status_row(params_dict):
            value = params_dict.get('Обременения')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Обременения</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        def generate_peoples_status_row(params_dict):
            value = params_dict.get('Собственников')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Собственников</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        def generate_kadaster_status_row(params_dict):
            value = params_dict.get('Кадастровый номер')
            if value not in EMPTY_VALUES_FOR_HIDE:
                return f"""<tr class="detail-item">
                                <td class="label-cell"><span class="label">Кадастровый номер</span></td>
                                <td class="value-cell"><span class="value">{value}</span></td>
                            </tr>"""
            return ''

        # Обновленный replace_list
        # Переменные floor и total_floors должны быть определены до этого списка
        # (например, извлечены из params или другого источника)

        replace_list = [
            ('ИМЯ_РЕЕЛТОРА', os.getenv("NAME", "Имя не указано")),
            ('ТЕЛЕФОН_РИЕЛТОРА', os.getenv("PHONE", "Телефон не указан")),
            ('НАЗВАНИЕ', res.get('title', 'Без названия')),
            ('АДРЕС', res.get('adress', 'Адрес не указан')),
            ('ТИП_ЖИЛЬЯ', params.get('Тип жилья', 'Тип не указан')), # Закомментировано, т.к. ниже есть 'Квартира'
            ('СТОИМОСТЬ', format_price(res.get('price', 0))),
            ('МЕТРО', metro_html),
            ('ЦЕНА_ЗА_МЕТР', offer.get('Цена за метр', 'Не указано')),
            ('УСЛОВИЯ_СДЕЛКИ', offer.get('Условия сделки', params.get('Дом', 'Не указано')).capitalize()),
            ('ИПОТЕКА', offer.get('Ипотека', 'Не указано')),
            ('ФОТОГРАФИИ', images_html),
            ('ГОД_ПОСТРОЙКИ', params.get('Год постройки', params.get('Год сдачи', 'Не указан'))),
            ('ОПИСАНИЕ', cleaned_description),
            ('ФОТООТЧЁТ', images_html),  # Используем те же фото, что и для основного блока

            # Плейсхолдеры для строк таблицы деталей, заменяемые вызовами функций
            ('ОБЩАЯ_ПЛОЩАДЬ_ROW', generate_total_area_row(params)),
            ('ЖИЛАЯ_ПЛОЩАДЬ_ROW', generate_living_area_row(params)),
            ('ПЛОЩАДЬ_КУХНИ_ROW', generate_kitchen_area_row(params)),
            ('ВЫСОТА_ПОТОЛКОВ_ROW', generate_ceiling_height_row(params)),
            ('ЭТАЖ_ROW', generate_floor_info_row(floor, total_floors)),  # floor и total_floors передаются как аргументы
            ('РЕМОНТ_ROW', generate_renovation_row(params)),
            ('САНУЗЕЛ_ROW', generate_bathroom_row(params)),
            ('ВИД_ИЗ_ОКОН_ROW', generate_window_view_row(params)),
            ('СОБСТВЕННИКОВ_ROW', generate_saler_status_row(rosreestr)),
            ('ОБРЕМЕНЕНИЯ_ROW', generate_peoples_status_row(rosreestr)),
            ('КАДАСТРОВЫЙ_НОМЕР_ROW', generate_kadaster_status_row(rosreestr)),

            ('ТИП_ДОМА_ROW', generate_house_type_row(params)),
            ('ТИП_ПЕРЕКРЫТИЙ_ROW', generate_flooring_type_row(params)),
            ('СТРОИТЕЛЬНАЯ_СЕРИЯ_ROW', generate_building_series_row(params)),
            ('КОЛИЧЕСТВО_ЛИФТОВ_ROW', generate_elevator_count_row(params)),
            ('ПОДЪЕЗДЫ_ROW', generate_entrances_row(params)),
            ('ПАРКОВКА_ROW', generate_parking_row(params)),
            ('ОТОПЛЕНИЕ_ROW', generate_heating_row(params)),
            ('АВАРИЙНОСТЬ_ROW', generate_emergency_status_row(params)),
            ('ГАЗОСНАБЖЕНИЕ_ROW', generate_gas_status_row(params)),
        ]

        # --- Выполнение замен ---
        for placeholder, value in replace_list:
            # Преобразуем значение в строку на всякий случай
            template = template.replace(placeholder, str(value))

        # --- Сохранение результата ---
        with open(file=output_path, mode='w', encoding='utf8') as f:
            f.write(template)
        print(f"Отчет успешно создан и сохранен в: {output_path}")  # Добавим сообщение об успехе

        return output_path

    except FileNotFoundError:
        print(f"Ошибка: Шаблон не найден по пути {tempfile_path}")
    except KeyError as e:
        print(f"Ошибка: Отсутствует необходимый ключ в словаре 'res': {e}")
    except Exception as e:
        print(f"Произошла непредвиденная ошибка при создании отчета: {e}")


if __name__ == '__main__':
    res = {
        'title': 'Продается 3-комн. квартира, 86,2 м² в ЖК «Новые Смыслы»',
        'adress': '№ 174 квартал Новые Смыслы жилой комплекс', 'price': '21347430₽',
        'offer': {'Цена за метр': '247 650 ₽/м²', 'Условия сделки': 'долевое участие (214-ФЗ)',
                  'Ипотека': 'возможна'},
        'metro': [{'station': 'Бунинская аллея', 'method': 'пешком', 'time': '5 мин.'},
                  {'station': 'Потапово', 'method': 'пешком', 'time': '17 мин.'},
                  {'station': 'Улица Горчакова', 'method': 'пешком', 'time': '6 мин.'}],
        'params': {'Общая площадь': '86,2', 'Площадь кухни': '22,9', 'Этаж': '2 из 27', 'Год сдачи': '2027',
                   'Дом': 'Не сдан', 'Отделка': 'Без отделки'},
        'description': 'В жилом комплексе, расположенном по соседству с ландшафтным парком "Южное Бутово", продается  3-комнатная квартира  площадью 86.20 кв. м. без отделки. Квартира расположена на 2 этаже 1 корпуса в жилом квартале комфорт-класса "Новые Смыслы" (ГК Unikey/Юникей).Доступная и удобная локация:-   10 минут ходьбы до станции метро "Потапово".-\t25 минут ходьбы до станции метро "Бунинская аллея".-\t15 минут на авто до Калужского шоссе.-\t20 минут на авто до МКАД.-\t30 минут на машине до аэропортов "Внуково" и "Остафьево".Продуманный архитектурный проект:-\tРазноуровневые секции с эстетичные башнями и контрастными цветовыми сочетаниями, напоминающими башни в Сити.-\tСказочные виды из окон на современный район столицы.-\tАвторские планировки с потолками в 3 метра, просторными кухнями-гостиными и мастер-спальнями.-\tКомфортные бесплатные общественные пространства.-\tПодземный паркинг с прямым доступом на лифте.-\tНастоящий лес с живописными пейзажами и прудом прямо во дворе.РасположениеКомплекс "Новые Смыслы" расположится в благоприятном районе Новой Москвы - Коммунарка. Зеленое окружение, богатая инфраструктура развивающегося района - все это сформирует особое пространство для комфортной жизни, наполненной смыслом.10 минут на велосипеде - и вы в ландшафтном парке "Южное Бутово" или сквере у Потаповских прудов. Чуть дальше расположен Бутовский лесопарк.В окружении "Новых Смыслов" вы найдете все необходимые социальные объекты. В двух шагах от дома находится 5 школ, более десятка детских садов, секции для занятий малышей и подростков, частные клиники, супермаркеты, рестораны, студии красоты и фитнес-центры. За 12 минут на авто вы доберетесь до ледовой арены, комплекса "Спорт Станция" и спа-центра "Termoland".Внутренняя инфраструктураДля жителей "Новых Смыслов" будут созданы бесплатные общественные пространства:-\tДеловая гостиная с эстетичным коворкингом и переговорными.-\tГостиная для души и тела, включающая фитнес-зону с тренажерами и пространства для стретчинга, йоги и медитаций.-\tГостиная детства, где дети будут играть и развиваться под присмотром тьютора.-\tКино-гостиная - кинотеатр на крыше одного из домов, предлагающий разнообразную программу.-\tПрачечная, работающая только для жильцов.Вместе с корпусами комплекса на территории запланировано строительство детского сада. На первых этажах корпусов откроются кофейни, пекарни, сервисы быта и пункты доставки.БлагоустройствоЧтобы отдохнуть от суеты города, достаточно выйти во двор: здесь раскинулся настоящий лес с живописными пейзажами. В тени деревьев жителей ждут пруд с мостиком и беседкой на берегу, тихие прогулочные аллеи, спортивная площадка и зоны для занятий йогой и бадминтоном на свежем воздухе.Юных жителей порадуют современные детские площадки, жукарий и специальное пространство для подвижных игр.Безопасность на территории гарантирована: двор огорожен от машин и оснащен камерами видеонаблюдения.',
        'images': [
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2451958729-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2371999717-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2371999866-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2371999924-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2371999976-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2372000051-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2372000217-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2372000330-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2372000421-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2372000520-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2372000619-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2372000691-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2372000786-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2372000870-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2372000913-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2372000943-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2372000984-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2372001026-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2372001071-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2372001120-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2372001190-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2372001272-1.jpg',
            'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\2372001342-1.jpg'
        ]
    }
    create_report_cian(res)
