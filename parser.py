import os
import time
from parser_cian.func import *
import requests
from bs4 import BeautifulSoup
from servise import printer
from settings import cookies, headers
from create_cian import create_report_cian
from PDF_creater import converter
from dotenv import load_dotenv
from icecream import ic
import asyncio
from save_to_json import json_converter
from send_file import send_file_to_telegram

load_dotenv()


def main_parser(URL, cookies, headers):
    printer(f'Обрабатываем страницу {URL}', kind='info')
    cian_number = URL.rstrip('/').split('/')[-1]
    # print(f"{cian_number=}")
    # Отправляем GET-запрос к странице
    try:
        response = requests.get(URL, cookies=cookies, headers=headers)

        status_code = response.status_code
    except Exception as _ex:
        printer(f'[parse_cian] {_ex} URL:{URL}', kind='error')

    if status_code == 200:
        # Используем BeautifulSoup для парсинга HTML-кода страницы
        soup = BeautifulSoup(response.text, "html.parser")
        # with open(file='page.html', mode='w', encoding='utf8') as file:
        #     file.write(str(soup))
        # with open(file='page.html', mode='r', encoding='utf8') as file:
        #     html = file.read()
        # soup = BeautifulSoup(html, 'html.parser')

        result = {
            'title': get_title(soup),
            'adress': get_adress(soup),
            'price': get_price(soup),
            'offer': get_offer(soup),
            'metro': get_metro(soup),
            # 'params':get_params(soup),
            'params': get_all_offer_params(soup),
            'author_branding': get_author_branding_info(soup), # Информация о брендинге автора
            'offer_metadata': get_offer_metadata_info(soup), # Дата обновления и статистика просмотров
            'developer': get_developer_info(soup),
            'rosreestr': get_rosreestr_info(soup),
            'agent': get_agent_info(soup),
            'description': get_description(soup),
            'images': get_imgages(soup, cian_number)[0],
            'images_links': get_imgages(soup, cian_number)[1],
        }

    else:
        printer(f"[parse_cian] {status_code=}", kind='error')

    printer(result, kind='info')

    return result, cian_number

def parse_cian(URL, cookies, headers):
    result, cian_number = main_parser(URL, cookies, headers)
    page_index, header_index, footer_index = create_report_cian(result, cian_number)
    report = converter(
        page_index=page_index,
        header_index=header_index,
        footer_index=footer_index,
    )

    result['URL'] = URL
    result['cian_number'] = cian_number

    json_result = json_converter(
        data_item=result,
        report_path=report,
    )
    try:
        if not os.path.exists(json_result):
            printer(f"Error: File not found at {json_result}", kind='error')
        else:
            printer(f"[parse_cian] send JSON file: {json_result} with caption: '{URL}'", kind='info')
            send_result = asyncio.run(send_file_to_telegram(json_result, URL))
            os.remove(json_result)
            # print(f"Telegram API Response:")
            # print(send_result)
    except Exception as e:
        print(f"An error occurred: {e}")

    return report, result

if __name__ == '__main__':
    URLs = [
        # 'https://www.cian.ru/sale/flat/312256069/', # Продается 3-комн. квартира, 86,2 м² в ЖК «Новые Смыслы»
        # 'https://www.cian.ru/sale/flat/316598899/',
        'https://www.cian.ru/sale/flat/312564948/',
        # 'https://www.cian.ru/sale/flat/312530669/',
        # 'https://www.cian.ru/sale/flat/316237818/',
    ]

    for URL in URLs:
        parse_cian(URL, cookies, headers)
    print()
    printer('[parse_cian] Программа завершила работу', kind='info')
    # time.sleep(5)
