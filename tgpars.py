import os
import time
import pickle
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Отключить окно уведомления
options = Options()
options.add_argument('--disable-notifications')

# Файлы конфигурации и ключевых слов
keywords_file = 'keywords.txt'

# Ключевые слова
with open(keywords_file, 'r', encoding='utf-8') as file:
    keywords = [line.strip() for line in file.readlines()]

# Set up Selenium webdriver
driver = webdriver.Edge(options=options)

def click_element(xpath, wait, timeout=10):
    """Click an element safely with a timeout."""
    try:
        element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].click();", element)
        time.sleep(2)  # Adding a delay to avoid too fast clicking
    except Exception as e:
        print(f"Error clicking element: {e}")

def get_image_base64(img_element):
    """Retrieve image from a Selenium WebElement and encode it in base64."""
    img_base64 = img_element.screenshot_as_base64
    return f"data:image/png;base64,{img_base64}"

try:
    driver.get("https://web.telegram.org/k/")
    wait = WebDriverWait(driver, 999)
    time.sleep(10)

    # что-то вроде куки, но это не куки
    if not os.path.exists('local_storage.json'):
        local_storage_data = driver.execute_script("return JSON.stringify(window.localStorage);")
        with open('local_storage.json', 'w') as file:
            file.write(local_storage_data)
            driver.quit()
    else:
        with open('local_storage.json', 'r') as file:
            local_storage_data = file.read()
        driver.execute_script("""
            var items = JSON.parse(arguments[0]);
            for (var key in items) {
                window.localStorage.setItem(key, items[key]);
            }
        """, local_storage_data)
        driver.refresh()

    result_html = f'Results_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.html'

    # Ожидание появления элемента поиска
    search_input = wait.until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/div[1]/div/div[1]/div/div[2]/input")))
    time.sleep(5)

    # Начальная структура HTML файла
    html_content = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="styles.css">
    <style>
    body {
        font-family: Arial, sans-serif;
        margin: 20px;
    }

    .icon-list {
        list-style: none;
        padding: 0;
    }

    .icon-list-item {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
    }

    .icon {
        font-size: 24px; /* Размер иконки */
        margin-right: 15px; /* Отступ между иконкой и текстом */
    }

    .text-content {
        display: flex;
        flex-direction: column;
    }

    .title {
        margin: 0;
        font-size: 18px; /* Размер шрифта заголовка */
        font-weight: bold;
    }

    .description {
        margin: 0;
        font-size: 14px; /* Размер шрифта описания */
    }
    </style>
</head>
<body>
    <ul class="icon-list">\n'''

    for keyword in keywords:
        search_input.clear()
        search_input.send_keys(keyword)

        # Создаем словарь для хранения результатов поиска по ключевым словам
        results_dict = {keyword: [] for keyword in keywords}

        # Добавляем заголовок для текущего ключевого слова в HTML
        html_content += f'<h2>Ключевое слово: {keyword}</h2>\n'

        # Итерация по результатам поиска с использованием XPath выражения
        elements = driver.find_elements(By.XPATH,
                                        "//*[@id=\"search-container\"]/div[2]/div[2]/div/div[1]/div/div[2]/ul")
        time.sleep(5)

        for element in elements:
            # Нажатие на кнопку поиска
            click_element(
                "//html/body/div[1]/div/div[1]/div/div/div[3]/div[2]/div[2]/div[2]/div/div[1]/div/div[2]/div/div", wait)

            lines = element.text.strip().split('\n')
            items = element.find_elements(By.XPATH, ".//a[contains(@class, 'row')]")

            print(f"{lines}")

            for item in items:
                username = item.find_element(By.XPATH, ".//div[contains(@class, 'row-subtitle')]").text
                user_nick = username.split(',')[0]

                # заменить эмоджи на пробел
                element_html = item.find_element(By.XPATH, ".//div[contains(@class, 'row-title')]").get_attribute('innerHTML')
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(element_html, 'html.parser')
                for img in soup.find_all('img'):
                    img.replace_with(' ')
                title = soup.get_text()

                image_elements = item.find_elements(By.XPATH, ".//div[contains(@class, 'avatar')]/img")
                if image_elements:
                    img_src = get_image_base64(image_elements[0])
                else:
                    img_src = "Icon-round-Question_mark.svg.png"

                html_content += '<li class="icon-list-item">\n'
                html_content += f'<img class="avatar-photo icon" decoding="async" src="{img_src}">\n'
                html_content += '<div class="text-content">\n'
                html_content += f'<span class="peer-title title" dir="auto"><a href="https://web.telegram.org/k/#{user_nick}" target="_blank">{title}</a></span>\n'
                html_content += f'<div class="row-subtitle description no-wrap" dir="auto"><a href="https://web.telegram.org/k/#{user_nick}" target="_blank">{username}</a></div>\n'
                html_content += '</div>\n'
                html_content += '</li>\n'

        search_input.clear()

    # Завершение HTML файла
    html_content += '</ul>\n</body>\n</html>'

    # Запись HTML содержимого в файл
    with open(result_html, "w", encoding="utf-8") as html_file:
        html_file.write(html_content)

finally:
    driver.quit()

print("Все готово!")
