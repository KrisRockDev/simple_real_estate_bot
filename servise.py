from settings import DEBUG, log_dir_absolute
import datetime
import os
def printer(message, kind='info'):
    if DEBUG:
        print(f'[{datetime.datetime.now()}]\t[{kind.upper()}]\t{message}')
    else:
        if kind != 'info':
            with open(file=os.path.join(log_dir_absolute, kind+'txt'), mode='a', encoding='utf8') as file:
                file.write(f'[{datetime.datetime.now()}]\t[{kind.upper()}]\t{message}\n')