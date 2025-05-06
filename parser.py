import os
import time
from parser_cian.func import *
import requests
from bs4 import BeautifulSoup
from servise import printer
from settings import cookies, headers
from create_cian import create_report_cian
from PDF_creater import converter


def parse_cian(URL, cookies, headers):
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
            'offer':get_offer(soup),
            'metro':get_metro(soup),
            'params':get_params(soup),
            'description':get_description(soup),
            'images': get_imgages(soup, cian_number),
        }

    else:
        printer(f"[parse_cian] {status_code=}", kind='error')

    printer(result, kind='info')

    return result, cian_number


if __name__ == '__main__':
    URLs = [
        'https://www.cian.ru/sale/flat/312256069/',
        'https://www.cian.ru/sale/flat/316598899/',
    ]

    for URL in URLs:
        result, cian_number = parse_cian(URL, cookies, headers)
        output_path = create_report_cian(result, cian_number)
        converter(DIRECTORY=output_path)

    print('\nПрограмма завершила работу')
    # time.sleep(5)
