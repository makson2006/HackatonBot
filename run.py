import telebot
from telebot import types
import mysql.connector
from settings import token, db

# Підключення до бази даних
connection = db
cursor = connection.cursor()


# Функція для додавання нового користувача до бази даних
def add_user_to_db(full_name, email, password):
    cursor.execute("INSERT INTO users (full_name, email, password) VALUES (%s, %s, %s)",
                   (full_name, email, password))
    connection.commit()


# Функція для закриття з'єднання з базою даних
def close_connection():
    cursor.close()
    connection.close()


# Функція для відображення списку перших 10 загублених людей
def display_lost_people_list(chat_id):
    cursor.execute("SELECT * FROM lost_people LIMIT 10")
    lost_people = cursor.fetchall()

    if lost_people:
        for person in lost_people:
            name = person[1]
            description = person[2]
            photo_path = person[3]  # Отримуємо file_id фотографії з бази даних
            bot.send_message(chat_id, f"Ім'я та прізвище: {name}\nОпис: {description}")
            bot.send_photo(chat_id, photo_path)  # Відправляємо фотографію за file_id у чат
    else:
        bot.send_message(chat_id, "Наразі список загублених людей порожній.")


# Функція для додавання загубленої людини до бази даних
def add_lost_person_to_db(name, description, photo_path):
    cursor.execute("INSERT INTO lost_people (full_name, description, photo_path) VALUES (%s, %s, %s)",
                   (name, description, photo_path))
    connection.commit()


# Підключення до Telegram бота
bot = telebot.TeleBot(token)


# Обробник команди /start
@bot.message_handler(commands=['start'])
def send_intro(message):
    bot.send_message(message.chat.id,
                     "Вітаю! Я бот, який допоможе в організації пошуку зниклих осіб у зоні військового конфлікту.\n"
                     "Моя мета - об'єднати зусилля добровольців, рятувальних служб та організацій для збільшення\n"
                     "ефективності розшуку зниклих людей.\n\n Для початку увійдіть або зареєструйтесь")
    send_menu(message)


# Функція для відправлення меню з вибором опцій
def send_menu(message, registered=False):
    menu_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if not registered:
        menu_markup.row(types.KeyboardButton('Увійти'))
        menu_markup.row(types.KeyboardButton('Зареєструватись'))
    else:
        menu_markup.row(types.KeyboardButton('Повідомити про загубленого'), types.KeyboardButton('Список загублених'))
    bot.send_message(message.chat.id, 'Оберіть опцію:', reply_markup=menu_markup)


# Обробник вибору опції з меню
@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    if message.text == 'Увійти':
        start_login(message)
    elif message.text == 'Зареєструватись':
        bot.send_message(message.chat.id, 'Будь ласка, введіть своє ім\'я та прізвище:')
        bot.register_next_step_handler(message, process_full_name)
    elif message.text == 'Повідомити про загубленого':
        bot.send_message(message.chat.id, 'Введіть ім\'я та прізвище загубленої людини:')
        bot.register_next_step_handler(message, process_lost_person_name)
    elif message.text == 'Список загублених':
        display_lost_people_list(message.chat.id)
    else:
        bot.send_message(message.chat.id, 'Будь ласка, скористайтеся кнопками у меню.')


# Функція для обробки введеного імені та прізвища загубленої людини
def process_lost_person_name(message):
    chat_id = message.chat.id
    name = message.text
    bot.send_message(chat_id, 'Тепер введіть опис загубленої людини:')
    bot.register_next_step_handler(message, process_lost_person_description, name)


# Функція для обробки введеного опису загубленої людини
def process_lost_person_description(message, name):
    chat_id = message.chat.id
    description = message.text
    bot.send_message(chat_id, 'Тепер надішліть фотографію загубленої людини:')
    bot.register_next_step_handler(message, process_lost_person_photo, name, description)


# Функція для обробки відправленої фотографії загубленої людини
def process_lost_person_photo(message, name, description):
    chat_id = message.chat.id
    photo_path = message.photo[-1].file_id  # Отримуємо file_id останньої фотографії з повідомлення
    add_lost_person_to_db(name, description, photo_path)
    bot.send_message(chat_id, 'Інформація про загублену людину успішно додана!')


# Функція для початку процесу входу користувача
def start_login(message):
    bot.send_message(message.chat.id, 'Для входу введіть свій емейл:')
    bot.register_next_step_handler(message, process_login)



# Функція для обробки введеного емейлу користувача
def process_login(message):
    chat_id = message.chat.id
    email = message.text

    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    existing_user = cursor.fetchone()

    if existing_user:
        # Якщо користувач з таким емейлом існує, запитаємо у нього пароль
        bot.send_message(chat_id, 'Введіть свій пароль:')
        bot.register_next_step_handler(message, process_password_login, existing_user)

    else:
        bot.send_message(chat_id,
                         'Користувача з цією електронною адресою не знайдено. Спробуйте ще раз або зареєструйтеся.')


# Функція для перевірки пароля користувача та входу в систему
def process_password_login(message, existing_user):
    chat_id = message.chat.id
    password = message.text

    # Перевірка введеного паролю з паролем користувача у базі даних
    if password == existing_user[3]:
        bot.send_message(chat_id, 'Ви успішно увійшли в систему!')
        send_menu(message, registered=True)  # Після входу відправляємо нове меню з двома кнопками
    else:
        bot.send_message(chat_id, 'Неправильний пароль. Спробуйте ще раз або зареєструйтеся.')


# Функція для обробки імені та прізвища користувача
def process_full_name(message):
    chat_id = message.chat.id
    full_name = message.text
    bot.send_message(chat_id, 'Тепер введіть свою електронну адресу:')
    bot.register_next_step_handler(message, process_email, full_name)


# Функція для обробки електронної адреси користувача
def process_email(message, full_name):
    chat_id = message.chat.id
    email = message.text

    # Перевірка наявності користувача з такою електронною адресою
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    existing_user = cursor.fetchone()

    if existing_user:
        bot.send_message(chat_id,
                         'Користувач з цією електронною адресою вже зареєстрований. Будь ласка, введіть іншу електронну адресу:')
        bot.register_next_step_handler(message, process_email, full_name)
    else:
        bot.send_message(chat_id, 'Тепер введіть свій пароль:')
        bot.register_next_step_handler(message, process_password, full_name, email)


# Функція для обробки пароля користувача
def process_password(message, full_name, email):
    chat_id = message.chat.id
    password = message.text
    add_user_to_db(full_name, email, password)
    bot.send_message(chat_id, 'Ви успішно зареєстровані!')
    send_menu(message, registered=True)  # Після реєстрації відправляємо нове меню з двома кнопками


# Запуск бота
bot.polling()
