import telebot
from telebot import types
import random
from fpdf import FPDF
import os

bot_token = '6340359911:AAF7O0PUEsuwPvCtXvLSWNRRlJ0idjgwy1A'
bot = telebot.TeleBot(bot_token)

# Добавьте переменную пароля
password = '2006'

# Создайте словарь для хранения статуса авторизации пользователей
authorized_users = {}


# Создайте переменную для хранения идентификатора владельца бота
owner_id = [717474239, 5598725054]

# Функция для проверки авторизации перед обработкой команд
def check_authorization(message):
    chat_id = message.chat.id
    if chat_id not in authorized_users or authorized_users[chat_id] != 'authorized':
        bot.send_message(chat_id, 'Botdan foydalanishni boshlash uchun parolni kiriting:')
        bot.register_next_step_handler(message, check_password)
        return False
    return True

# # Функция для проверки, является ли пользователь владельцем бота
# def is_owner(user_id):
#     return owner_id is not None and user_id == owner_id

# Функция для проверки, является ли пользователь владельцем бота
def is_owner(user_id):
    return user_id in owner_id


def check_password(message):
    chat_id = message.chat.id
    if message.text == password:
        authorized_users[chat_id] = 'authorized'
        bot.send_message(chat_id, 'Avtorizatsiya muvaffaqiyatli boldi. Endi siz botdan foydalanishingiz mumkin')
    else:
        bot.send_message(chat_id, 'Notogri parol.')

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    if not check_authorization(message):
        return
    bot.send_message(chat_id,  "Ushbu bot yordamida siz quyidagilarni amalga oshirishingiz mumkin: \n \n Testni /solve_test buyrug'i yordamida hal qilish uchun ismingiz, familiyangizni va test identifikatorini kiritishingiz kerak. Testga javoblaringizni yuboring va natijani oling.")

@bot.message_handler(commands=['set_password'])
def set_password(message):
    chat_id = message.chat.id
    if not is_owner(message.from_user.id):
        return

    bot.send_message(chat_id, 'Yangi parolni kiriting:')
    bot.register_next_step_handler(message, change_password)

def change_password(message):
    chat_id = message.chat.id
    new_password = message.text
    global password
    password = new_password
    bot.send_message(chat_id, 'Parol muvaffaqiyatli ozgartirildi.')


tests = {}

@bot.message_handler(commands=['add_test'])
def add_test(message):
    chat_id = message.chat.id
    if not is_owner(message.from_user.id):
        return
    bot.send_message(chat_id, 'Test nomini kiriting:')
    bot.register_next_step_handler(message, add_test_title)

def add_test_title(message):
    chat_id = message.chat.id
    test_title = message.text
    if not test_title.isalpha():
        bot.send_message(chat_id, 'Nom notogri. Qaytadan boshlang va test nomini raqamlar yoki maxsus belgilarsiz matnga kiriting. (lotin alifbosida)')
        return
    bot.send_message(chat_id, 'Toʻgʻri javoblarni vergul yordamida ajratib yuboring:\nMasalan: a,b,c,d')
    bot.register_next_step_handler(message, add_test_answers, test_title)

def add_test_answers(message, test_title):
    chat_id = message.chat.id
    test_answers = message.text.lower()  # Barcha harflarni kichik harflarga o'tkazamiz
    if not all(answer.isalpha() and len(answer) == 1 for answer in test_answers.split(',')):
        bot.send_message(chat_id, 'Javoblar notogri formatda kiritilgan❌. Введите ответы только в формате a,b,c,d.')
        return
    bot.send_message(chat_id, 'Testning PDF faylini yuboring: \n (Ushbu PDF hujjatda test savollari boʻlishi kerak!)')
    bot.register_next_step_handler(message, add_test_pdf, test_title, test_answers)

def add_test_pdf(message, test_title, test_answers):
    chat_id = message.chat.id
    if message.document.mime_type != 'application/pdf':
        bot.send_message(chat_id, 'Men faqat PDF formatidagi fayllarni qabul qilaman❌. Iltimos, faylni PDF formatida yuboring.')
        return
    test_id = generate_test_id()
    save_test(test_id, test_title, test_answers, message.from_user.id)
    tests[test_id]['pdf'] = message.document.file_id
    bot.send_message(chat_id, f'Test muvaffaqiyatli kiritildi.\nTest 🆔:\n{test_id}')

@bot.message_handler(commands=['solve_test'])
def solve_test(message):
    chat_id = message.chat.id
    if not check_authorization(message):
        return
    bot.send_message(chat_id, 'Ismingizni kiriting:')
    bot.register_next_step_handler(message, solve_test_username)

def solve_test_username(message):
    chat_id = message.chat.id
    username = message.text
    if not username.isascii():
        bot.send_message(chat_id, 'Ism notogri. Qaytadan boshlang va raqam yoki maxsus belgilarsiz matnga ismingizni kiriting. (lotin alifbosida)')
        return
    bot.send_message(chat_id, 'Familiyani kiriting:')
    bot.register_next_step_handler(message, solve_test_usersurname, username)

def solve_test_usersurname(message, username):
    chat_id = message.chat.id
    usersurname = message.text
    if not usersurname.isascii():
        bot.send_message(chat_id, 'Familiya notogri. Qaytadan boshlang va raqam yoki maxsus belgilarsiz matnga ismingizni kiriting. (lotin alifbosida)')
        return
    bot.send_message(chat_id, 'Test ID`sini kiriting:')
    bot.register_next_step_handler(message, solve_test_id, username, usersurname)

def solve_test_id(message, username, usersurname):
    chat_id = message.chat.id
    test_id = message.text
    if not test_id.isdigit():
        bot.send_message(chat_id, 'Yaroqsiz ID❌.')
        return
    test_id = int(test_id)
    test = get_test(test_id)
    if test:
        bot.send_document(chat_id, test['pdf'])
        bot.send_message(chat_id, 'Testga javoblaringizni yuboring: \n Masalan: a,b,c,d')
        bot.register_next_step_handler(message, solve_test_answers, test, username, usersurname)
    else:
        bot.send_message(chat_id, 'Test topilmadi❌. Yana bir bor urinib ko `ring.')

def solve_test_answers(message, test, username, usersurname):
    chat_id = message.chat.id
    answers = message.text.lower()
    correct_answers = test['answers']
    result = calculate_score(answers, correct_answers)
    student = {
        'username': username,
        'usersurname': usersurname,
        'result': result
    }
    test['students'].append(student)
    bot.send_message(chat_id, f'Ism: {username}\nFamiliya: {usersurname}\nTest natijasi: {result}')



@bot.message_handler(commands=['finish_test'])
def finish_test(message):
    chat_id = message.chat.id
    if not is_owner(message.from_user.id):
      return
    bot.send_message(chat_id, 'Testga ID`sini kiriting:')
    bot.register_next_step_handler(message, finish_test_id)

def finish_test_id(message):
    chat_id = message.chat.id
    test_id = message.text
    if not test_id.isdigit():
        bot.send_message(chat_id, 'Yaroqsiz ID❌. Qaytadan boshlang va test ID`sini togri kiriting.')
        return
    test_id = int(test_id)
    test = get_test(test_id)
    if test:
        if test['author'] != message.from_user.id:  # Check if the user is the author of the test
            # bot.send_message(chat_id, 'Вы не автор теста❌. Только автор может получить результаты тест.')
            return
        # Сортируем студентов по количеству правильных ответов в нисходящем порядке
        sorted_students = sorted(test['students'], key=lambda student: student['result'], reverse=True)

        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_font('Arial', '', 16)
        pdf.cell(0, 10, f'Test ID {test_id}', 0, 1, 'C')
        pdf.ln(10)
        col_width = pdf.w / 3.2  # Define col_width before the loop
        # Создаем заголовок таблицы
        pdf.cell(col_width, 10, 'Ism', border=1)
        pdf.cell(col_width, 10, 'Familiya', border=1)
        pdf.cell(col_width, 10, 'Natija', border=1)
        pdf.ln(10)
        # Заполняем таблицу отсортированными студентами
        for student in sorted_students:
            pdf.cell(col_width, 10, student['username'], border=1)
            pdf.cell(col_width, 10, student['usersurname'], border=1)
            pdf.cell(col_width, 10, str(student['result']), border=1)
            pdf.ln(10)
        pdf_path = os.path.join(os.getcwd(), f'tests/results_{test_id}.pdf')
        pdf.output(pdf_path, 'F')
        bot.send_document(chat_id, open(pdf_path, 'rb'))
        bot.send_message(chat_id, 'Sinov muvaffaqiyatli yakunlandi. Test natijalari sizga PDF fayl korinishda yuborildi.')
    else:
        bot.send_message(chat_id, 'Test topilmadi❌. Yana bir bor urinib ko`ring.')


@bot.message_handler(commands=['list_tests'])
def list_tests(message):
    chat_id = message.chat.id
    if not is_owner(message.from_user.id):
        return

    if not tests:
        bot.send_message(chat_id, 'Hali testlar yoq❌. Yangi testlarni qoshing.')
        return

    for test_id, test_data in tests.items():
        # Отправляем ID и название теста
        test_info_message = f"🆔 {test_id}: {test_data['title']}"
        bot.send_message(chat_id, test_info_message)

        # Отправляем PDF-файл теста
        bot.send_document(chat_id, test_data['pdf'], caption=f"🆔 {test_id}: {test_data['title']}")



def generate_test_id():
    return random.randint(1000, 9999)

def get_test(test_id):
    return tests.get(test_id)

def save_test(test_id, test_title, test_answers, author_id):
    if test_id in tests:
        bot.send_message(chat_id, f'{test_id}-ID bilan test allaqachon mavjud. Boshqasini tanlang 🆔.')
        return
    tests[test_id] = {
        'title': test_title,
        'answers': test_answers,
        'students': [],
        'author': author_id
    }

def calculate_score(answers, correct_answers):
    user_answers = [answer.strip() for answer in answers.split(',')]
    correct_answers_array = [answer.strip() for answer in correct_answers.split(',')]
    score = sum(1 for answer in user_answers if answer in correct_answers_array)
    return score
# Бот успешно запущен
print("Bot muvaffaqiyatli ishga tushirildi!")

bot.polling()
