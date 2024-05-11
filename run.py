import telebot
from telebot import types
from settings import token, db
# Підключення до бд
connection = db

cursor = connection.cursor()

#додавання нового користувача до бази даних


def add_user_to_db(full_name, email, password):
    cursor.execute("INSERT INTO users (full_name, email, password) VALUES (%s, %s, %s)",
                   (full_name, email, password))
    connection.commit()

def close_connection():
    cursor.close()
    connection.close()

TOKEN = token
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_intro(message):
    bot.send_message(message.chat.id, "Вітаю! Я бот, який допоможе в організації пошуку зниклих осіб у зоні військового конфлікту.\n"
                                      "Моя мета - об'єднати зусилля добровольців, рятувальних служб та організацій для збільшення\n"
                                      "ефективності розшуку зниклих людей.\n\n Для початку увійдіть або зареєструйтесь")
    send_menu(message)

def send_menu(message, registered=False):
    menu_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if not registered:
        menu_markup.row(types.KeyboardButton('Увійти'))
        menu_markup.row(types.KeyboardButton('Зареєструватись'))
    else:
        menu_markup.row(types.KeyboardButton('Повідомити про загубленого'), types.KeyboardButton('Список загублених'))
    bot.send_message(message.chat.id, 'Оберіть опцію:', reply_markup=menu_markup)

@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    if message.text == 'Увійти':
        start_login(message)
    elif message.text == 'Зареєструватись':
        bot.send_message(message.chat.id, 'Будь ласка, введіть своє ім\'я та прізвище:')
        bot.register_next_step_handler(message, process_full_name)
    else:
        bot.send_message(message.chat.id, 'Будь ласка, скористайтеся кнопками у меню.')

def process_full_name(message):
    chat_id = message.chat.id
    full_name = message.text
    bot.send_message(chat_id, 'Тепер введіть свою електронну адресу:')
    bot.register_next_step_handler(message, process_email, full_name)

def process_email(message, full_name):
    chat_id = message.chat.id
    email = message.text

    # Перевірка
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    existing_user = cursor.fetchone()

    if existing_user:
        # якщо існує
        bot.send_message(chat_id,
                         'Користувач з цією електронною адресою вже зареєстрований. Будь ласка, введіть іншу електронну адресу:')
        bot.register_next_step_handler(message, process_email, full_name)
    else:
        # введеня паролю
        bot.send_message(chat_id, 'Тепер введіть свій пароль:')
        bot.register_next_step_handler(message, process_password, full_name, email)


#завершення реєстрації
def process_password(message, full_name, email):
    chat_id = message.chat.id
    password = message.text
    # Додавання користувача до бази даних
    add_user_to_db(full_name, email, password)
    bot.send_message(chat_id, 'Ви успішно зареєстровані!')
    send_menu(message, registered=True)  # Після реєстрації відправляємо нове меню з двома кнопками

def start_login(message):
    bot.send_message(message.chat.id, 'Для входу введіть свій емейл:')
    bot.register_next_step_handler(message, process_login)

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

# Обробник для перевірки пароля користувача та входу в систему
def process_password_login(message, existing_user):
    chat_id = message.chat.id
    password = message.text

    # Перевірка введеного паролю з паролем користувача у базі даних
    if password == existing_user[3]:
        bot.send_message(chat_id, 'Ви успішно увійшли в систему!')
        send_menu(message, registered=True)  # Після входу відправляємо нове меню з двома кнопками
    else:
        bot.send_message(chat_id, 'Неправильний пароль. Спробуйте ще раз або зареєструйтеся.')

bot.polling()
