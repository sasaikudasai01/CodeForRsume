# from google.auth import message
from telebot import TeleBot, types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from google.oauth2.service_account import Credentials
import gspread
import random
from telebot.types import InputMediaPhoto
import json
import re
import requests

# Сохранение данных
def save_data(new_data, filename='data.json'):
    # Загружаем существующие данные
    try:
        with open(filename, 'r') as f:
            # Загружаем данные из JSON файла
            data = json.load(f)
    except FileNotFoundError:
        # Если файл не существует, создаем пустой словарь
        data = {"kanals": [], "models": [], "makets": []}
    except json.JSONDecodeError:
        # Если файл поврежден, создаем пустой словарь
        data = {"kanals": [], "models": [], "makets": []}

    # Обновляем данные
    data["kanals"] = new_data.get("kanals", data["kanals"])
    data["models"] = new_data.get("models", data["models"])
    data["makets"] = new_data.get("makets", data["makets"])

    # Сохраняем обновленные данные обратно в файл
    with open(filename, 'w') as f:
        json.dump(data, f)


# Загрузка данных
def load_data(filename='data.json'):
    try:
        with open(filename, 'r') as f:
            content = f.read().strip()
            if content:  # Если файл не пустой
                return json.loads(content)  # Возвращаем данные из JSON
            else:  # Если файл пустой
                return {"kanals": [], "models": [], "makets": []}  # Возвращаем пустые списки
    except FileNotFoundError:
        return {"kanals": [], "models": [], "makets": []}  # Если файл не найден, возвращаем пустые списки
    except json.JSONDecodeError:  # Обработка ошибки при некорректном формате JSON
        return {"kanals": [], "models": [], "makets": []}  # Возвращаем пустые списки в случае ошибки декодирования


bot = TeleBot('7975578392:AAGObePWm2edIaXfWgekH5nh3OqyaBLk7Ec')
# Загрузка данных
data = load_data('data.json')

# Инициализация переменных
kanal_dict = data.get("kanals", [])  # Получаем список каналов, если он существует
model_dict = data.get("models", [])  # Получаем список моделей, если он существует
maket_dict = data.get("makets", [])  # Получаем список моделей, если он существует

# kanal_dict = []
# model_dict = []
current_kanal = ''
change_current_kanal_name = True

is_running = False

# ссылка на таблицу из текстовика
googletable_file = 'googletable.txt'
with open(googletable_file, 'r', encoding='utf-8') as file:
    google_table_url = file.read().strip()

# Извлечение ID из URL таблицы
google_table_id = google_table_url.split("/d/")[1].split("/")[0]

# Подключение к Google Sheets
SCOPE = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]
CREDS = Credentials.from_service_account_file("credentials.json", scopes=SCOPE)
client = gspread.authorize(CREDS)

# Открываем Google таблицу по ID из файла
sheet = client.open_by_key(google_table_id).sheet1
data = sheet.get_all_records()


# стартовое сообщение
def send_start_message(chat_id, message_id=None):
    global change_current_kanal_name
    change_current_kanal_name = True
    markup = InlineKeyboardMarkup()

    if kanal_dict:
        for kanal in kanal_dict:
            button = InlineKeyboardButton(f"{kanal['name']}", callback_data=f"{kanal['name']}_nameclicked")
            markup.add(button)

    kanal_create_button = InlineKeyboardButton("Создать канал", callback_data="kanal_create_button_clicked")
    markup.add(kanal_create_button)

    if message_id:
        # если передан message_id, то обновляем существующее сообщение
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="ВЫБОР КАНАЛА", reply_markup=markup)
    else:
        # иначе отправляем новое сообщение
        bot.send_message(chat_id, "ВЫБОР КАНАЛА", reply_markup=markup)


@bot.message_handler(commands=['start'])
def start_message(message):
    send_start_message(message.chat.id)


def kanal_create_func(message):
    global is_running

    chat_id = message.chat.id
    message_id = message.message_id
    markup = InlineKeyboardMarkup()
    back_button = InlineKeyboardButton("Назад", callback_data="kanal_create_back_button_clicked")
    markup.add(back_button)

    # обновление сообщение, чтобы показать "ОТПРАВЬТЕ НАЗВАНИЕ"
    bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                          text="ОТПРАВЬТЕ НАЗВАНИЕ", reply_markup=markup)

    if not is_running:
        # Ожидаем следующий ввод текста для канала
        bot.register_next_step_handler(message, process_kanal_name)


# обработчик для кнопки "Создать канал"
@bot.callback_query_handler(func=lambda call: call.data == "kanal_create_button_clicked")
def kanal_create(call):
    kanal_create_func(call.message)


def process_kanal_name(message):
    global current_kanal
    global kanal_dict
    current_kanal = message.text
    kanal_dict.append({"name": current_kanal})

    markup = InlineKeyboardMarkup()
    back_to_kanal_name_button = InlineKeyboardButton("Назад", callback_data="back_to_kanal_name_clicked")
    markup.add(back_to_kanal_name_button)

    bot.send_message(message.chat.id, f"Oтправьте макет для {current_kanal}", reply_markup=markup)
    bot.register_next_step_handler(message, maket_text_create)


@bot.callback_query_handler(func=lambda call: call.data == "kanal_create_back_button_clicked")
def kanal_create_back_button(call):
    global is_running
    is_running = True
    # Возвращаемся на экран выбора каналов, обновляя текущее сообщение
    send_start_message(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == "back_to_kanal_name_clicked")
def back_to_kanal_name(call):
    kanal_create_func(call.message)


def maket_text_create(message):
    global kanal_dict
    maket_id = message.text
    for kanal in kanal_dict:
        if kanal["name"] == current_kanal:
            kanal["maket_text"] = maket_id

    save_data({"kanals": kanal_dict})
    send_start_message(message.chat.id)



def get_random_model_info():
    random_model = random.choice(data)  # Выбираем случайную запись
    modelId = random_model['{modelId}']
    modelName = random_model['{modelName}']
    modelColor = random_model['{modelColor}']
    modelMaxSpeed = random_model['{modelMaxSpeed}']
    modelPhoto = random_model['{modelPhoto}']

    data.remove(random_model)  # Удаляем выбранную запись из данных
    return modelId, modelName, modelColor, modelMaxSpeed, modelPhoto


def send_handle_channel_button_message(chat_id, message_id, call):
    global current_kanal
    global model_dict

    if change_current_kanal_name:
        kanal_name = call.data.replace('_nameclicked', '')  # извлечение название канала из callback_data
        current_kanal = kanal_name

    markup = InlineKeyboardMarkup()
    change_kanal_name_button = InlineKeyboardButton("Изменить название", callback_data="change_kanal_name_clicked")
    maket_edit_button = InlineKeyboardButton("Редактировать макет", callback_data="maket_edit_clicked")
    kanal_delete_button = InlineKeyboardButton("Удалить канал", callback_data="kanal_delete_clicked")
    create_post_button = InlineKeyboardButton("Создать 3 поста", callback_data="create_post_clicked")
    back_button = InlineKeyboardButton("Назад", callback_data="kanal_create_back_button_clicked")
    markup.add(change_kanal_name_button, create_post_button)
    markup.add(maket_edit_button, kanal_delete_button)
    markup.add(back_button)

    if message_id:
        # если передан message_id, то обновляем существующее сообщение
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f"Управление", reply_markup=markup)
    else:
        # иначе отправляем новое сообщение
        bot.send_message(chat_id, f"Управление {current_kanal}", reply_markup=markup)


# удалить канал
@bot.callback_query_handler(func=lambda call: call.data == 'kanal_delete_clicked')
def kanal_delete(call):
    markup = InlineKeyboardMarkup()
    yes_button = InlineKeyboardButton("Да", callback_data="yes_delete_kanal_clicked")
    no_button = InlineKeyboardButton("Нет", callback_data="no_delete_kanal_clicked")
    markup.add(no_button, yes_button)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="Удалить канал?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'yes_delete_kanal_clicked')
def process_kanal_delete(call):
    global kanal_dict
    for kanal in kanal_dict:
        if kanal["name"] == current_kanal:
            kanal_dict.remove(kanal)

    send_start_message(call.message.chat.id, call.message.message_id)
    save_data({"kanals": kanal_dict})


@bot.callback_query_handler(func=lambda call: call.data == 'no_delete_kanal_clicked')
def process_no_kanal_delete(call):
    global change_current_kanal_name
    change_current_kanal_name = False
    send_handle_channel_button_message(call.message.chat.id, call.message.message_id, call)


# Обработчик нажатий на кнопки с каналами
@bot.callback_query_handler(func=lambda call: call.data.endswith('_nameclicked'))
def handle_channel_button(call):
    send_handle_channel_button_message(call.message.chat.id, call.message.message_id, call)


# изменить название канала
@bot.callback_query_handler(func=lambda call: call.data == 'change_kanal_name_clicked')
def kanal_name_change(call):
    bot.send_message(call.message.chat.id, f"Oтправьте новое название для: {current_kanal}")
    bot.register_next_step_handler(call.message, process_kanal_name_change)


def process_kanal_name_change(message):
    global kanal_dict
    global current_kanal
    for kanal in kanal_dict:
        if kanal["name"] == current_kanal:
            kanal["name"] = message.text
            save_data({"kanals": kanal_dict})


# редактировать макет
@bot.callback_query_handler(func=lambda call: call.data == 'maket_edit_clicked')
def maket_edit(call):
    global is_running

    markup = InlineKeyboardMarkup()
    back_button = InlineKeyboardButton("Назад", callback_data="handle_channel_button_back_clicked")
    markup.add(back_button)

    # обновление сообщение, чтобы показать "ОТПРАВЬТЕ НАЗВАНИЕ"
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="Отправьте новый макет", reply_markup=markup)

    if not is_running:
        # Ожидаем следующий ввод текста для канала
        bot.register_next_step_handler(call.message, process_maket_edit)


def process_maket_edit(message):
    global kanal_dict
    maket_id = message.text
    for kanal in kanal_dict:
        if kanal["name"] == current_kanal:
            kanal["maket_text"] = maket_id

    save_data({"kanals": kanal_dict})
    send_start_message(message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data == 'handle_channel_button_back_clicked')
def handle_channel_back(call):
    global change_current_kanal_name
    global is_running
    is_running = True
    change_current_kanal_name = False
    send_handle_channel_button_message(call.message.chat.id, call.message.message_id, call)



@bot.callback_query_handler(func=lambda call: call.data == 'create_post_clicked')
def create_post(call):
    global maket_dict
    global current_kanal

    for _ in range(3):
        # Получаем случайные данные модели для каждого макета
        modelId, modelName, modelColor, modelMaxSpeed, modelPhoto = get_random_model_info()

        for kanal in kanal_dict:
            if kanal["name"] == current_kanal:
                message_id_to_copy = kanal["maket_text"]

        # Заменяем шаблоны в тексте на реальные данные
        message_id_to_copy = (message_id_to_copy.replace('modelId', str(modelId))\
                                                .replace('modelName', str(modelName))\
                                                .replace('modelColor', str(modelColor))\
                                                .replace('modelMaxSpeed', str(modelMaxSpeed))\
                                                .replace('modelPhoto', str(modelPhoto)))

        # Формируем список медиа для отправки
        media_group = []
        photo_urls = modelPhoto.strip().split(',')

        # Добавляем зачеркнутую подпись к первому фото
        for i, photo_url in enumerate(photo_urls):
            photo_url = photo_url.strip()  # Убираем лишние пробелы
            if i == 0:
                media_group.append(types.InputMediaPhoto(photo_url, caption=message_id_to_copy, parse_mode="HTML"))
            else:
                media_group.append(types.InputMediaPhoto(photo_url))  # Остальные без подписи

        # Отправляем медиа группу с подписями
        if media_group:  # Проверяем, есть ли фотографии для отправки
            try:
                bot.send_media_group(chat_id=call.message.chat.id, media=media_group)
            except Exception as e:
                print(f"Error sending media group: {e}")  # Логируем ошибки

bot.polling()
