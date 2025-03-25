import os
import time
from parser_cian.func import *
import requests
from bs4 import BeautifulSoup
from servise import printer
from settings import cookies, headers


def parse_cian(URL, cookies, headers):
    printer(f'Обрабатываем страницу {URL}\n', kind='info')
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
            # 'adress': get_adress(soup),
            # 'price': get_price(soup),
            # 'offer':get_offer(soup),
            # 'metro':get_metro(soup),
            # 'params':get_params(soup),
            'description':get_description(soup),
            # 'imgages': get_imgages(soup, cian_number),
        }


    else:
        printer(f"[parse_cian] {status_code=}", kind='error')

    printer(result, kind='info')
    return result


if __name__ == '__main__':
    URLs = [
        'https://www.cian.ru/sale/flat/312256069/',
    ]

    for URL in URLs:
        parse_cian(URL, cookies, headers)

    print('\nПрограмма завершила работу')
    # time.sleep(5)
