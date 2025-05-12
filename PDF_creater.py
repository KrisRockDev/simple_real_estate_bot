import datetime
import os
import pdfkit
from dotenv import load_dotenv
from settings import DEBUG
from servise import printer
from icecream import ic
from settings import downloads_dir_absolute

load_dotenv()

# Прочитать про options тут:
# https://wkhtmltopdf.org/usage/wkhtmltopdf.txt
# https://thepythoncode.com/article/convert-html-to-pdf-in-python#html-file-to-pdf
# https://html2pdf.com/ru/

def converter(page_index, header_index, footer_index):
    options = {
        'print-media-type': None,  # Печать с разрывом страницы
        "enable-local-file-access": "",
        "images": "",
        'page-size': 'A4',
        # 'orientation': 'Landscape', # Альбомная ориентация
        'margin-top': '0.60in',
        'margin-right': '0.30in',
        'margin-bottom': '0.5in',
        'margin-left': '0.30in',

        'encoding': 'UTF-8',
        'page-offset': '0',
        # 'header-spacing': '5.0',
        'footer-line': '',
        'footer-font-name': 'font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", "Noto Sans", "Liberation Sans", Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";',
        'footer-font-size': '9',
        # 'footer-left': f'Почта для связи с разработчиком\n{os.getenv("EMAIL")}',
        # 'header-html': r'E:\py\main\simple_real_estate_bot\html_template\header.html',
        # 'footer-html': r'E:\py\main\simple_real_estate_bot\html_template\footer.html',
        'header-html': header_index,
        'footer-html': footer_index,
        'footer-center': '[page] / [topage]',
        # 'footer-right': f'Создано при помощи\n{os.getenv("TELEGRAM_BOT_USERNAME")}',
    }

    try:
        report_title = f'kriss_real_estate_bot_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.pdf'
        RESULT_PDF = os.path.join(os.path.split(page_index)[0], report_title)
        if os.getenv("DEBAG"): # Режим отладки windows 11
            config = pdfkit.configuration(wkhtmltopdf=r'c:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
        else: # Рабочий режим в linux
            config = pdfkit.configuration(wkhtmltopdf=r'/usr/bin/wkhtmltopdf')
        pdfkit.from_file(page_index, RESULT_PDF, configuration=config, options=options)

        # os.startfile(HTML_FILE) # Запускает шаблон HTML header-файла
        os.remove(page_index)  # Удаляет шаблон HTML-файла
        os.remove(header_index)  # Удаляет шаблон HTML header-файла
        os.remove(footer_index)  # Удаляет шаблон HTML файла
        # os.startfile(RESULT_PDF)  # Запускать итоговый PDF
        printer(f'[converter] Завершено к создание PDF', kind='info')
        return RESULT_PDF

    except Exception as _ex:
        printer(f'[converter] {_ex}', kind='error')
        return None


if __name__ == "__main__":

    for i in ['312256069',]:
        converter(
        page_index = r'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\index.html',
        header_index = r'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\header_index.html',
        footer_index = r'E:\\py\\main\\simple_real_estate_bot\\downloads\\312256069\\footer_index.html',
        )
