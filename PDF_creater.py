import datetime
import os
import pdfkit
from icecream import ic
from settings import downloads_dir_absolute

# Прочитать про options тут:
# https://wkhtmltopdf.org/usage/wkhtmltopdf.txt
# https://thepythoncode.com/article/convert-html-to-pdf-in-python#html-file-to-pdf
# https://html2pdf.com/ru/

def converter(
        DIRECTORY
):
    options = {
        # 'print-media-type': '',
        "enable-local-file-access": "",
        "images": "",
        'page-size': 'A4',
        # 'orientation': 'Landscape', # Альбомная ориентация
        'margin-top': '0.30in',
        'margin-right': '0.25in',
        'margin-bottom': '0.25in',
        'margin-left': '0.30in',

        'encoding': 'UTF-8',
        'page-offset': '0',
        'header-spacing': '5.0',
        'footer-font-name': 'font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", "Noto Sans", "Liberation Sans", Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";',
        'footer-font-size': '9',
        'footer-center': '[page] / [topage]',
    }

    try:
        # print(f'Приступаю к созданию PDF)
        RESULT_PDF = DIRECTORY[:-4]+'pdf'
        config = pdfkit.configuration(wkhtmltopdf=r'c:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
        pdfkit.from_file(DIRECTORY, RESULT_PDF, configuration=config, options=options)

        # os.startfile(HTML_FILE) # Запускает шаблон HTML header-файла
        # os.remove(HTML_HEADER)  # Удаляет шаблон HTML header-файла
        # os.remove(HTML_FILE)  # Удаляет шаблон HTML файла
        os.startfile(RESULT_PDF)  #Запускать итоговый PDF
        print(f'Завершено к создание PDF')
    except Exception as _ex:
        print(_ex)


if __name__ == "__main__":

    for i in ['316598899', '312256069']:
        converter(
            # DIRECTORY=rf'e:\py\main\simple_real_estate_bot\downloads\{i}\index.html'
            # DIRECTORY=rf'E:\py\main\simple_real_estate_bot\html_template\cian5.html'
            DIRECTORY=rf'E:\py\main\simple_real_estate_bot\html_template\test1.html'
        )
