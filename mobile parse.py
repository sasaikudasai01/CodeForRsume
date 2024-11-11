import time
from urllib.parse import urlparse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_formatting import *

# Функция для авторизации Google Sheets
creds_file = 'credentials.json'
def authenticate_google_sheets():
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scopes)
    client = gspread.authorize(creds)
    return client

# Ключевые слова
keywords_file = 'keywords.txt'
with open(keywords_file, 'r', encoding='utf-8') as file:
    keywords = [line.strip() for line in file.readlines()]

# таблица из текстовика
googletable_file = 'googletable.txt'
with open(googletable_file, 'r', encoding='utf-8') as file:
    googletable = [line.strip() for line in file.readlines()]

# исключения
exception_urls_file = 'exceptions.txt'
with open(exception_urls_file, 'r', encoding='utf-8') as file:
    exceptions = [line.strip() for line in file.readlines()]

shortnames_file = 'shortnames.txt'
with open(shortnames_file, 'r', encoding='utf-8') as file:
    shortnames = [line.strip() for line in file.readlines()]
split_shortnames = []
for shortname in shortnames:
    split_shortnames.append(shortname.split(',')[0])

# Настройки для эмуляции мобильного устройства
mobile_emulation = {
    "deviceName": "Pixel 2"
}

# Настройки для Chrome
options = ChromeOptions()
options.add_argument('--disable-gpu')
options.add_argument('--disable-notifications')
options.add_experimental_option("mobileEmulation", mobile_emulation)
options.add_extension('I-don-t-care-about-cookies-Chrome.crx')

driver = webdriver.Chrome(options=options)

try:

    # Авторизация Google Sheets
    client = authenticate_google_sheets()

    # Открытие таблицы
    gtable = googletable[0]
    sheet = client.open_by_url(gtable)

    # Создание нового листа с текущей датой и временем
    yandex_sheet_title = f'Yandex Results {datetime.now().strftime("%d.%m.%y %H-%M-%S")}'
    google_sheet_title = f'Google Results {datetime.now().strftime("%d.%m.%y %H-%M-%S")}'
    yandex_worksheet = sheet.add_worksheet(title=yandex_sheet_title, rows="100", cols="20")
    google_worksheet = sheet.add_worksheet(title=google_sheet_title, rows="100", cols="20")

    print("Результаты из Yandex:\n")

    # Форматирование заголовков для Yandex
    yandex_header = ['Keyword', 'Position 1', 'Position 2', 'Position 3', 'Position 4', 'Position 5']
    yandex_worksheet.append_row(yandex_header)

    for keyword in keywords:
        string_dict = []
        string_dict.append(keyword)
        print(f'ключевое слово: {keyword}')
        driver.get(f"https://ya.ru/search/?text={keyword}")

        # Ожидание элементов с атрибутом data-cid
        wait = WebDriverWait(driver, 999)
        elements_with_data_cid = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-cid]'))
        )
    
        output_links = []

        i = 0
        count = 0
        # Найти и вывести ссылку внутри каждого элемента с классом "Link Link_theme_normal OrganicTitle-Link organic__url link"
        for element in elements_with_data_cid:
            if count == 5:
                break
            # Ищем ссылки и тайтлы по указанным классам
            links = element.find_elements(By.CSS_SELECTOR, '.Link.Link_theme_normal.OrganicTitle-Link.organic__url.link')

            if links:
                for index, link in enumerate(links):
                    href = link.get_attribute('href')
                    if not (href.startswith('https://yabs.yandex.ru/count/') or
                            href.startswith('https://yabs.yandex.kz/count/') or
                            href.startswith('https://mc.yandex.ru/watch/') or
                            href.startswith('https://metrica.yandex.com/')):
                        # базовый домен
                        parsed_url = urlparse(href)
                        short_url = f'{parsed_url.scheme}://{parsed_url.netloc}/'

                        if short_url not in exceptions:
                            if short_url in split_shortnames:
                                for shortname in shortnames:
                                    if short_url == shortname.split(",")[0]:
                                        i += 1
                                        print(f'{i}) {shortname.split(",")[1]}')
                                        output_links.append(f'{i}) {shortname.split(",")[1]}')
                                        string_dict.append(shortname.split(",")[1])
                                        count += 1
                            else:
                                i += 1
                                print(f'{i}) {short_url}')
                                output_links.append(f'{i}) {short_url}')
                                string_dict.append(short_url)
                                count += 1

        yandex_worksheet.append_row(string_dict)

        print('\n')

# yandex
#------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------
# google

    print("Результаты из Google:\n")

    # Форматирование заголовков для Google
    google_header = ['Keyword', 'Position 1', 'Position 2', 'Position 3', 'Position 4', 'Position 5']
    google_worksheet.append_row(google_header)

    for keyword in keywords:
        string_dict = []
        string_dict.append(keyword)

        print(f'ключевое слово: {keyword}')
        driver.get(f"https://www.google.com/search?q={keyword}&safe=off")
        driver.refresh()

        # # Ожидание элементов с классом TzHB6b Ww4FFb vt6azd DlUvEb K7khPe
        # wait = WebDriverWait(driver, 999)
        # elements_with_class = wait.until(
        #     EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.TzHB6b.Ww4FFb.vt6azd.DlUvEb.K7khPe'))
        # )

        # output_links_google = []

        # i = 0
        # count = 0
        # for element in elements_with_class:
        #     if count == 5:
        #         break
        #     links = element.find_elements(By.CSS_SELECTOR, '.yKd8Hd.ob9lvb')
        #     for link in links:
        #         link_text = (link.text.split(" ")[0])
        #         if link_text not in exceptions:
        #             if link_text in split_shortnames:
        #                 for shortname in shortnames:
        #                     if link_text == shortname.split(",")[0]:
        #                         i += 1
        #                         print(f'{i}) {shortname.split(",")[1]}')
        #                         output_links_google.append(f'{i}) {shortname.split(",")[1]}')
        #                         string_dict.append(shortname.split(",")[1])
        #                         count += 1
        #             else:
        #                 i += 1
        #                 print(f'{i}) {link_text}')
        #                 output_links_google.append(f'{i}) {link_text}')
        #                 string_dict.append(link_text)
        #                 count += 1

        string_dict = [keyword]

        # Ожидание элементов с классом TzHB6b cLjAic K7khPe
        wait = WebDriverWait(driver, 999)
        try:
            results = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.yKd8Hd.ob9lvb'))
            )
        except Exception as e:
            print(f"Ошибка при ожидании результатов поиска: {e}")
            continue

        i = 0
        for result in results:
            href = (result.text.split(" ")[0])
            if href:
                parsed_url = urlparse(href)
                short_url = f'{parsed_url.scheme}://{parsed_url.netloc}/'

                # Проверка исключений
                if href not in exceptions:
                    if href in split_shortnames:
                        for shortname in shortnames:
                            if href == shortname.split(",")[0]:
                                i += 1
                                if i <= 5:
                                    if len(string_dict) < 6:
                                        string_dict.append(shortname.split(",")[1])
                                print(f'{i}) {shortname.split(",")[1]}')
                                break
                    else:
                        i += 1
                        if i <= 5:
                            if len(string_dict) < 6:
                                string_dict.append(short_url)
                        print(f'{i}) {short_url}')

                    # Останавливаем парсинг после 5 позиций
                    if i >= 5:
                        break

        google_worksheet.append_row(string_dict)

        print('\n')

    # Форматирование таблиц
    format_cell_range(yandex_worksheet, 'A1:F1', CellFormat(
        backgroundColor=Color(0.5, 0.5, 0.5),  # Темно-серый фон
        textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1)),  # Белый текст
        horizontalAlignment='CENTER',
        verticalAlignment='MIDDLE'
    ))

    format_cell_range(google_worksheet, 'A1:F1', CellFormat(
        backgroundColor=Color(0.5, 0.5, 0.5),  # Темно-серый фон
        textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1)),  # Белый текст
        horizontalAlignment='CENTER',
        verticalAlignment='MIDDLE'
    ))

    set_column_width(yandex_worksheet, 'A', 300)
    set_column_width(google_worksheet, 'A', 300)

    # Печать ссылки на таблицу
    print(f"Created new sheet: {yandex_sheet_title}")
    print(f"Created new sheet: {google_sheet_title}")
    print(f"Google Sheets URL: {gtable}")

finally:
    driver.quit()
