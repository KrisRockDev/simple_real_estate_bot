import json
import os
import datetime
from servise import printer

# Функция-обработчик для объектов datetime
def datetime_converter(o):
    if isinstance(o, datetime.datetime):
        return o.isoformat()  # Преобразуем datetime в строку формата ISO
    # Если попадется другой несериализуемый тип, можно добавить обработку здесь
    # или позволить json.dump выбросить стандартную ошибку
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")


def json_converter(data_item: dict, report_path: str):
    """
    Сохраняет данные в JSON файл
    """
    # printer(f"[json_converter] Получены данные для сохранения: {type(data_item)}", kind='info') # Добавим лог для типа data_item
    if not isinstance(data_item, dict):
        printer("[json_converter] Ошибка: Входные данные (data_item) должны быть словарем.", kind='error')
        return False
    if not report_path or not isinstance(report_path, str):
        printer("[json_converter] Ошибка: Некорректный путь к отчету (report_path).", kind='error')
        return False

    # Более надежный способ получить имя файла без расширения и добавить .json
    base_path, _ = os.path.splitext(report_path)
    json_filename = f"{base_path}.json"

    try:
        with open(json_filename, 'w', encoding='utf-8') as f:
            # Используем default=datetime_converter для обработки datetime объектов
            json.dump(data_item, f, ensure_ascii=False, indent=4, default=datetime_converter)
        printer(f"[json_converter] Данные успешно сохранены в файл: {json_filename}", kind='info')
        return json_filename # Возвращаем True в случае успеха
    except IOError as e:
        printer(f"[json_converter] Ошибка при записи данных в файл {json_filename}: {e}", kind='error')
        return False
    except TypeError as e:
        printer(f"[json_converter] Ошибка сериализации данных в JSON: {e}", kind='error')
        # Попытка удалить частично записанный файл, если он существует
        if os.path.exists(json_filename):
            try:
                os.remove(json_filename)
                printer(f"[json_converter] Частично записанный файл {json_filename} удален.", kind='info')
            except OSError as remove_err:
                printer(f"[json_converter] Не удалось удалить частично записанный файл {json_filename}: {remove_err}", kind='error')
        return False


if __name__ == '__main__':
    data_item = {
        'title': 'Продается 2-комн. квартира, 54,6 м²',
        'adress': 'Москва, ЗАО, р-н Дорогомилово, Большая Дорогомиловская ул., 9', 'price': '39000000₽',
        'offer': {'Цена за метр': '714 286 ₽/м²', 'Условия сделки': 'свободная продажа', 'Ипотека': 'возможна'},
        'metro': [{'station': 'Киевская', 'method': 'пешком', 'time': '10 мин.'},
                  {'station': 'Студенческая', 'method': 'пешком', 'time': '14 мин.'},
                  {'station': 'Москва-Сити', 'method': 'пешком', 'time': '14 мин.'}],
        'params': {'Общая площадь': '54,6', 'Площадь кухни': '6,5', 'Этаж': '2 из 8', 'Год постройки': '1954',
                   'Тип жилья': 'Вторичка', 'Высота потолков': '3', 'Санузел': '1 совмещенный',
                   'Вид из окон': 'Во двор',
                   'Ремонт': 'Дизайнерский', 'Строительная серия': 'Индивидуальный проект',
                   'Количество лифтов': '1 пассажирский', 'Тип перекрытий': 'Железобетонные', 'Парковка': 'Наземная',
                   'Подъезды': '5', 'Отопление': 'Центральное', 'Аварийность': 'Нет', 'Газоснабжение': 'Центральное'},
        'author_branding': None,
        # Здесь находится объект datetime, который вызывал ошибку
        'offer_metadata': {'updated_date': 'сегодня, 12:26', 'updated_datetime': datetime.datetime(2025, 5, 11, 12, 26),
                           'views_stats': '2166 просмотров, 169 за сегодня, 1462 уникальных', 'всего_просмотров': 2166,
                           'просмотров_сегодня': 169, 'уникальных_просмотров': 1462}, 'developer': None,
        'rosreestr': {'Обременения': 'Нет', 'Площадь': '54,6', 'Этаж': '2', 'Собственников': '1',
                      'Кадастровый номер': '77:07:0007002:***'},
        'agent': {'Автор ID/Имя': 'ID 20136556', 'На ЦИАН': '6 лет 6 месяцев', 'Объявлений автора': '1'},
        'description': 'Продаётся уникальная дизайнерская квартира в историческом доме сталинской эпохи.<br><br>Локация — идеальная логистика и развитая инфраструктура:<br> 5 минут до метро *Киевская* и *Студенческая*.  <br> Рядом ТЦ Европейский, деловой центр Москва-Сити, кафе, магазины, парки.  <br> Быстрый выезд на основные магистрали города. <br> Шаговая доступность ресторанов  Remi Kitchen, Таке ДО, Кофемании и магазина  Азбука Вкуса<br> По соседству расположены кинотеатр Пионер и Дорогомиловский рынок<br><br>Особенности дома:<br> Монументальная сталинская архитектура с парадным фасадом и высокими дубовыми дверями, вход в подъезд с двух сторон.  <br> Уютный зелёный двор и живописный сквер для прогулок.  <br> Закрытая и спокойная и престижная атмосфера.  <br>  Высокий второй этаж. Квартира расположена над нежилым помещением (бутиком) с высотой потолков 6 метров.<br>Квартира после капитального ремонта:  <br> Дизайнерский ремонт с использованием современных материалов:  <br>- Полы: инженерная доска и керамогранит.  <br>- Стены: высококачественная матовая покраска в нейтральных тонах .  <br>- Подоконники из натурального мрамора.  <br>- Разноплановое освещение: встроенные светильники, бра, дизайнерские люстры и трековые системы.<br> Полная замена электрики и сантехники, в том числе стояка канализации.<br> Встроенная техника (кухня): холодильник, духовой шкаф, варочная панель, вытяжка, посудомоечная машина.  <br> Готова к въезду — осталось добавить личные вещи!  <br>Почему это дом для счастливой жизни?  <br> Просторные светлые комнаты с высотой потолков 3 метра, южная сторона с видом на зеленый двор<br> Эргономичная планировка и продуманное зонирование.  <br> Тишина во дворе и динамика мегаполиса за порогом.  <br> Энергетика места, где сочетаются история и современность.  <br>Квартира, в которой хочется встречать рассветы и создавать воспоминания. Ваш новый дом ждёт вас!',
        'images': ['E:\\py\\main\\simple_real_estate_bot\\downloads\\316598899\\2463448097-1.jpg',
                   'E:\\py\\main\\simple_real_estate_bot\\downloads\\316598899\\kvartira-moskva-bolshaya-dorogomilovskaya-ulica-2463433188-1.jpg'],
        'images_links': ['https://images.cdn-cian.ru/images/2463448097-2.jpg',
                         'https://images.cdn-cian.ru/images/kvartira-moskva-bolshaya-dorogomilovskaya-ulica-2463433188-2.jpg']
    }

    report_path = r'E:\py\main\simple_real_estate_bot\downloads\test.pdf'
    success = json_converter(data_item, report_path)
    if success:
        printer(f"[if __name__ == '__main__':] Тестовая обработка завершена успешно. Файл создан.", kind='info')
    else:
        printer(f"[if __name__ == '__main__':] Тестовая обработка завершилась с ошибкой.", kind='error')