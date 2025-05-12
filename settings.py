import os
from dotenv import load_dotenv

cookies = {
    '_CIAN_GK': 'cc74a8c2-c6fc-484f-8dd6-29a3524b39d4',
    'cf_clearance': 'PBigzGLGZPMeMET7IJccfBRAINmxCg1a5V6xkWfIS_o-1729106645-1.2.1.1-QubJJo0qnvDsM_TDzPIsGxqdZiUHxQuPWNbhjekmn6imyX2UR5QaTdwX5XZ6PVEte.eQzu2TTTGB8qNivMwWk2gXueVcvTLAbs5.dOlz9LMtCqvUohwF3WAed8YmWkL1Xhqi3ALCVffYOcEVW4yRQ9GlW14X4HUjcsExXM_5iMch0ya5bL23.mES8vj.y6UWI9GtXJgYr.HEO.rwUxW7ZrNkHGQhjNkFOViERPGYQGmDhBrihRC5OdUuh9yoKmreAik_bBiblPzMaNLvXZIrDiLJSItYriNcx_Z8bHiRcTgmKKtfCrCNGoFWcoD7xn07fxfJ.2C5.r282fdQgXj7yl750BLpuCY5aA.Ld3kN6VY03DX3eGOwuW_g9QoTvcvvoOWYSC6prszhlY.koYP8gu8AGEPNpaV3EKef32pJ1_M',
    'login_mro_popup': '1',
    '_gcl_au': '1.1.1224675397.1729106644',
    'tmr_lvid': '641ae55ec22ca395c762570bbe8d2b4f',
    'tmr_lvidTS': '1729106644235',
    '_ga': 'GA1.1.227500493.1729106645',
    'domain_sid': '5RZmwy8SuOB0tgqnudqaj%3A1729106646610',
    'sopr_utm': '%7B%22utm_source%22%3A+%22direct%22%2C+%22utm_medium%22%3A+%22None%22%7D',
    'sopr_session': 'e4b891d119584ac4',
    'uxfb_usertype': 'searcher',
    '_ym_uid': '1729106647812093375',
    '_ym_d': '1729106647',
    '_ym_isad': '1',
    '_ym_visorc': 'b',
    'uxs_uid': '36b7f000-8bf4-11ef-ab53-45c3798c2ff3',
    'afUserId': '17bd83a9-34d7-43b1-abd7-02967945aa7d-p',
    'AF_SYNC': '1729106648082',
    'uxfb_card_satisfaction': '%5B307915980%5D',
    '__cf_bm': 'UsoKIQF0_Orfb_KG5ymIsd711cGtXuQ.3kbtUQS9slc-1729106860-1.0.1.1-siRkuInCkpgFNFaj6KSSnoEU0BGkJMNkKyPMiROShkgNjMtNCqzfyzASIdrb6WK.ppD.eyRdoZCoYV.hHmdOHw',
    '_ga_3369S417EL': 'GS1.1.1729106645.1.1.1729106866.58.0.0',
    'tmr_detect': '0%7C1729106868764',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en;q=0.9',
    'cache-control': 'max-age=0',
    # 'cookie': '_CIAN_GK=cc74a8c2-c6fc-484f-8dd6-29a3524b39d4; cf_clearance=PBigzGLGZPMeMET7IJccfBRAINmxCg1a5V6xkWfIS_o-1729106645-1.2.1.1-QubJJo0qnvDsM_TDzPIsGxqdZiUHxQuPWNbhjekmn6imyX2UR5QaTdwX5XZ6PVEte.eQzu2TTTGB8qNivMwWk2gXueVcvTLAbs5.dOlz9LMtCqvUohwF3WAed8YmWkL1Xhqi3ALCVffYOcEVW4yRQ9GlW14X4HUjcsExXM_5iMch0ya5bL23.mES8vj.y6UWI9GtXJgYr.HEO.rwUxW7ZrNkHGQhjNkFOViERPGYQGmDhBrihRC5OdUuh9yoKmreAik_bBiblPzMaNLvXZIrDiLJSItYriNcx_Z8bHiRcTgmKKtfCrCNGoFWcoD7xn07fxfJ.2C5.r282fdQgXj7yl750BLpuCY5aA.Ld3kN6VY03DX3eGOwuW_g9QoTvcvvoOWYSC6prszhlY.koYP8gu8AGEPNpaV3EKef32pJ1_M; login_mro_popup=1; _gcl_au=1.1.1224675397.1729106644; tmr_lvid=641ae55ec22ca395c762570bbe8d2b4f; tmr_lvidTS=1729106644235; _ga=GA1.1.227500493.1729106645; domain_sid=5RZmwy8SuOB0tgqnudqaj%3A1729106646610; sopr_utm=%7B%22utm_source%22%3A+%22direct%22%2C+%22utm_medium%22%3A+%22None%22%7D; sopr_session=e4b891d119584ac4; uxfb_usertype=searcher; _ym_uid=1729106647812093375; _ym_d=1729106647; _ym_isad=1; _ym_visorc=b; uxs_uid=36b7f000-8bf4-11ef-ab53-45c3798c2ff3; afUserId=17bd83a9-34d7-43b1-abd7-02967945aa7d-p; AF_SYNC=1729106648082; uxfb_card_satisfaction=%5B307915980%5D; __cf_bm=UsoKIQF0_Orfb_KG5ymIsd711cGtXuQ.3kbtUQS9slc-1729106860-1.0.1.1-siRkuInCkpgFNFaj6KSSnoEU0BGkJMNkKyPMiROShkgNjMtNCqzfyzASIdrb6WK.ppD.eyRdoZCoYV.hHmdOHw; _ga_3369S417EL=GS1.1.1729106645.1.1.1729106866.58.0.0; tmr_detect=0%7C1729106868764',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "YaBrowser";v="24.7", "Yowser";v="2.5"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 YaBrowser/24.7.0.0 Safari/537.36',
}

dirs = [
    downloads_dir := 'downloads',  # директория для скачивания
    users_dir := 'users',  # директория с пользователями
    log_dir := 'logs',  # директория для логов
    templates := 'html_template',
]

# директория с пользователями
users_dir_absolute = os.path.abspath(users_dir)
# os.makedirs(users_dir_absolute, exist_ok=True)

# директория для скачивания
downloads_dir_absolute = os.path.abspath(downloads_dir)
os.makedirs(downloads_dir_absolute, exist_ok=True)

# директория для логов
log_dir_absolute = os.path.abspath(log_dir)
os.makedirs(log_dir_absolute, exist_ok=True)

templates_dir_absolute = os.path.abspath(templates)
os.makedirs(templates_dir_absolute, exist_ok=True)



# Загружаем переменные окружения
load_dotenv()

# Переменная для режима отладки
# True - запуск бота в режиме отладки для однократного запуска
# False - запуск бота в режиме реальной работы для периодического парсинга сайта
DEBUG = os.getenv("DEBUG")
