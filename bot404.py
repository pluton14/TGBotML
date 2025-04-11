import os
import requests
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import bcrypt
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
import tensorflow as tf

db = 'database.json'
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
URL = f"https://api.telegram.org/bot{TOKEN}/"
web_url = 'https://619a-95-54-97-245.ngrok-free.app'
tb = telebot.TeleBot(TOKEN)
model = keras.models.load_model('zebra_model_v2.0.h5')
app = Flask(__name__)
pass_input_trig = False
login_input = False
in_system = False
predict_input = False
file_path = None
def set_webhook():
    url = f"{URL}getWebhookInfo"
    response = requests.get(url)
    webhook_info = response.json()
    if webhook_info['result']['url'] != web_url:
        set_url = f"{URL}setWebhook?url={web_url}"
        response = requests.get(set_url)
        print(response.text)
    else:
        print("Webhook already set")


def send_message(chat_id, text):
    url = f"{URL}sendMessage"
    data = {'chat_id': chat_id, 'text': text}
    r = requests.post(url, json=data)
    return r.json()

@app.route("/", methods=["GET", "POST"])
def receive_update():
    global pass_input_trig, login_input, db_list, in_system, predict_input, file_path
    if request.method == "POST":
        chat_id = request.json["message"]["chat"]["id"]
        name = request.json["message"]["from"]["username"]
        img_txt_trig = 0
        try:
            message = request.json["message"]["text"]
            img_txt_trig = 1
        except:
            message = None
            img_txt_trig = 0
            file_info = tb.get_file(request.json['message']['photo'][-1]['file_id'])
            file_path = file_info.file_path
            #print(file_path)
            img_old = tb.download_file(file_path)
            filename = 'image.jpg'
            with open(filename, 'wb') as new_file:
                new_file.write(img_old)
        match message:
            case '/start':
                send_message(chat_id, "Нажмите /register или /login")
                return '', 200
            case '/help':
                send_message(chat_id, "Нажмите /register или /login")
                return '', 200
            case '/register':
                in_trig = False
                print(db_list)
                for db_el in db_list:
                    print(db_el)
                    if str(chat_id) == db_el:
                        in_trig = True
                        break
                if in_trig:
                    send_message(chat_id, "Уже зарегистрированы. Нажмите /login для входа.")
                    return '', 200
                else:
                    send_message(chat_id, "Придумайте и введите пароль для регистрации:")
                    #tb.register_next_step_handler(msg, input_pass)
                    pass_input_trig = True
                    return '', 200
            case '/login':
                in_trig = False
                new_trig = 0
                try:
                    with open(db, 'r') as file:
                        db_list = json.load(file)
                        new_trig = 1
                except:
                    db_list = {}
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
                    send_message(chat_id, "Введите пароль:")
                    login_input = True
                    return '', 200
                elif in_trig and auth_trig:
                    send_message(chat_id, "Вы уже вошли")
                    return '', 200
                else:
                    send_message(chat_id,"Для регистрации нажмите /register")
                    return '', 200
            case '/predict':
                in_trig = False
                auth_trig = False
                for db_el in db_list:
                    if str(chat_id) == db_el:
                        in_trig = True
                        print(db_el)
                        if db_list[db_el]['auth'] == True:
                            auth_trig = True
                        break
                print(in_trig, auth_trig)
                if in_trig == False or auth_trig == False:
                    send_message(chat_id, "Для использования этой команды нажмите /login")
                    predict_input = False
                    return '', 200
                else:
                    send_message(chat_id, "Отправьте изображение")
                    predict_input = True
                    return '', 200
            case '/logout':
                if str(chat_id) in db_list:
                    db_list[str(chat_id)]['auth'] = False
                    with open(db, 'w') as file:
                        json.dump(db_list, file)
                    send_message(chat_id, "Вы вышли из системы.")
                    in_system = False
                else:
                    send_message(chat_id, "Для регистрации нажмите /register")
                return '', 200
        if pass_input_trig:
                db_list[chat_id] = {'password': message, 'auth': False}
                with open(db, 'w') as file:
                    json.dump(db_list, file)
                send_message(chat_id, "Вы зарегистрированы! Нажмите /login для входа")
                return '', 200
        if login_input:
            if db_list[str(chat_id)]['password'] == str(message):
                db_list[str(chat_id)]['auth'] = True
                with open(db, 'w') as file:
                    json.dump(db_list, file)
                send_message(chat_id, "Вы успешно вошли! Нажмите /predict для работы с нейросетью.")
                in_system = True
                login_input = False
                pass_input_trig = False
                predict_trig = False
                return '', 200
            else:
                send_message(chat_id, "Неверный пароль. Нажмите /login")
                login_input = False
                pass_input_trig = False
                predict_input = False
                return '', 200
        if predict_input:
            model = tf.keras.models.load_model('zebra_model_v2.0.h5')
            img = image.load_img('image.jpg', target_size=(175, 175))
            x = image.img_to_array(img)
            x = np.expand_dims(x, axis=0)
            images = np.vstack([x])
            classes = model.predict(images, batch_size=10)
            if classes[0] < 0.5:
                send_message(chat_id, 'Зебра')
            else:
                send_message(chat_id, 'Человек')
            login_input = False
            pass_input_trig = False
            predict_input = False
            return '', 200
    return {"ok": True}

if __name__ == '__main__':
    set_webhook()
    app.run()