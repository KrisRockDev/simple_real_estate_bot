from settings import log_dir_absolute
import datetime
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def printer(message, kind='info'):
    dt = str(datetime.datetime.now()).replace(',', '.')
    if os.getenv("DEBUG", False):
        print(f'[{dt}]\t[{kind.upper()}]\t{message}')
    else:
        if kind != 'info':
            with open(file=os.path.join(log_dir_absolute, kind+'txt'), mode='a', encoding='utf8') as file:
                file.write(f'[{dt}]\t[{kind.upper()}]\t{message}\n')
