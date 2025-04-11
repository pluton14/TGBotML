import flask
import telebot
from telebot import types
import json
import datetime
import numpy as np
import matplotlib.pyplot as plt
import keras
from keras._tf_keras.keras.preprocessing import image
from flask import request, Flask, Response
import json

db = 'database.json'
server = Flask(__name__)
markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
markup_fake = types.ReplyKeyboardMarkup()
predict_btn = types.KeyboardButton('/predict')
login_btn = types.KeyboardButton('/login')
register_btn = types.KeyboardButton('/register')
markup.add(register_btn, login_btn, predict_btn)
num_users = 0
db_list = {}
try:
    with open(db, 'r') as file:
        db_list = json.load(file)
        print(db_list)
        num_users = len(db_list)
except:
    pass

TOKEN = '7394868701:AAF6Y4wLnSlkzdtfXYl7Cr7TqWSdpHuW9iY'
tb = telebot.TeleBot(TOKEN)
#tb.set_webhook()
model = keras.models.load_model('zebra_model_v2.0.h5')



@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    tb.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@server.route("/")
def webhook():
    tb.remove_webhook()
    tb.set_webhook(url='https://619a-95-54-97-245.ngrok-free.app/' + TOKEN)
    return "Webhook set", 200

@tb.message_handler(commands=['start', 'help'])
def first_mess(message):
    tb.send_message("Нажмите /register или /login")
@tb.message_handler(commands=['register'])
def register(message):
    in_trig = False
    print(db_list)
    for db_el in db_list:
        print(db_el)
        if str(message.chat.id) == db_el:
            in_trig = True
            break
    if in_trig:
        tb.reply_to(message, "Уже зарегистрированы. Нажмите /login для входа.")
    else:
        msg = tb.send_message(message.chat.id, "Придумайте и введите пароль для регистрации:")
        tb.register_next_step_handler(msg, input_pass)
@tb.message_handler(commands=['login'])
def login(message):
    in_trig = False
    new_trig = 0
    try:
        with open(db, 'r') as file:
            db_list = json.load(file)
            new_trig = 1
    except:
        db_list = {}
    chat_id = message.chat.id
    print(db_list)
    print(chat_id)
    print(new_trig)
    auth_trig = False
    for db_el in db_list:
        if str(chat_id) == db_el:
            in_trig = True
            print(db_list)
            if db_list[db_el]['auth'] == True:
                auth_trig = True
            break
    if in_trig and not auth_trig:
        msg = tb.reply_to(message, "Введите пароль:")
        tb.register_next_step_handler(msg, process_login_step)
    elif in_trig and auth_trig:
        msg = tb.reply_to(message, "Вы уже вошли")
    else:
        tb.reply_to(message, "Для регистрации нажмите /register")

def input_pass(message):
    db_list[message.chat.id] = {'password': message.text, 'auth': False}
    with open(db, 'w') as file:
        json.dump(db_list, file)
    tb.reply_to(message, "Вы зарегистрированы! Нажмите /login для входа")

def process_login_step(message):
    #print('meaasga')
    if db_list[str(message.chat.id)]['password'] == str(message.text):
        db_list[str(message.chat.id)]['auth'] = True
        with open(db, 'w') as file:
            json.dump(db_list, file)
        tb.reply_to(message, "Вы успешно вошли! Нажмите /predict для работы с нейросетью.")
    else:
        tb.reply_to(message, "Неверный пароль. Нажмите /login")

def logout(message):
    if str(message.chat.id) in db_list:
        db_list[str(message.message.chat.id)]['auth'] = False
        with open(db, 'w') as file:
            json.dump(db_list, file)
        tb.reply_to(message, "Вы вышли из системы.")
    else:
        tb.reply_to(message, "Для регистрации нажмите /register")

@tb.message_handler(commands=['predict'])
def predict(message):
    in_trig = False
    auth_trig = False
    for db_el in db_list:
        if str(message.chat.id) == db_el:
            in_trig = True
            print(db_el)
            if db_list[db_el]['auth'] == True:
                auth_trig = True
            break
    print(in_trig, auth_trig)
    if in_trig == False or auth_trig == False:
        tb.reply_to(message, "Для использования этой команды нажмите /login")
    else:
        msg = tb.reply_to(message, "Отправьте изображение")
        tb.register_next_step_handler(msg, predict_alg)

def predict_alg(message):
    #markup_fake()
    if message.content_type == 'photo':
        file_id = message.photo[-1].file_id
        print(file_id)
        file_info = tb.get_file(file_id)
        print(file_info)
        # markup_fake()
        img_old = tb.download_file(file_info.file_path)
        with open("image.jpg", 'wb') as new_file:
            new_file.write(img_old)
        img = image.load_img('image.jpg', target_size=(175, 175))
        x = image.img_to_array(img)
        plt.imshow(x / 255.)
        x = np.expand_dims(x, axis=0)
        images = np.vstack([x])
        classes = model.predict(images, batch_size=10)
        print(classes[0])
        if classes[0] < 0.5:
            tb.send_message(message.chat.id, 'Зебра')
        else:
            tb.send_message(message.chat.id, 'Человек')
        tb.send_message(message.chat.id, "Еще?", reply_markup=markup)
    else:
        tb.send_message("Пожалуйста, отправьте изображение.")
        tb.send_message(message.chat.id, ".", reply_markup=markup)
@tb.message_handler(commands=['logout'])
def logout(message):
    if str(message.chat.id) in db_list:
        db_list[str(message.chat.id)]['auth'] = False
        with open(db, 'w') as file:
            json.dump(db_list, file)
        tb.reply_to(message, "Вы вышли из системы.")
    else:
        tb.reply_to(message, "Для регистрации нажмите /register")
#tb.polling()
server.run(host="0.0.0.0", port=8080)