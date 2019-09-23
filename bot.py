# -*- coding: utf-8 -*-

import platform    # For getting the operating system name
import subprocess  # For executing a shell command
from time import time, sleep
import urllib
import config
import telebot
from telebot import apihelper
import socks, socket
import datetime

class Pinger():

    #Массив времени, когда хост был доступен в последний раз. Если хост доступен, то время 0
    output = []
    #Запущен мониторинг или нет
    is_running = False
    #Было ли оповещение об упавшем хосте, 0 - нет, 10 - оповещение о 10-ти минутах, 15 - о 15-ти
    is_notified = []
    bot = None


    #timeout - время ожидания отклика от хоста
    #min_wait_time - время между проверками
    #hosts - массив адресов для проверки
    def __init__(self, timeout, min_wait_time, hosts, names):
        self.timeout = timeout
        self.min_wait_time = min_wait_time
        self.hosts = hosts
        self.names = names
        self.output = [0 for h in hosts]
        self.is_notified = [0 for h in hosts]

    def ping(self, host):

        # Option for the number of packets as a function of
        param = '-n' if platform.system().lower() == 'windows' else '-c'

        # Building the command. Ex: "ping -c 1 google.com"
        command = ["ping", str(param), "1", str(host)]
        need_sh = False if platform.system().lower() == "windows" else True

        return subprocess.call(command, shell=need_sh, timeout=self.timeout) == 0

    def get_status(self):
        self.run()
        message = "Информация о хостах: \n"
        i = 0
        for host in hosts:
            message = message + names[i] + ": "
            if self.output[i] == 0:
                message = message + "Доступно \n"
            else:
                message = message + "Недоступно " + str(int((time() - self.output[i]) / 60)) + " мин \n"
            i += 1
        return message


    #Функция оповещения о неотвечающем хосте, id - id хоста в массиве hosts
    def notify(self, id, min):
        now = datetime.datetime.now()
        if min == 0:
            message = 'Мониторинг ' + self.hosts[id] + ' восстановлен в ' + now.strftime("%H:%M %d.%m.%Y")
        else:
            message = 'Оборудование ' + self.names[id] + ' (' + self.hosts[id] + ') недоступно более ' + str(min) + ' минут.\nПриоритет: высокий\n' + now.strftime("%d.%m.%Y %H:%M")
        send_message(message)

    #Функция проверки доступности хостов
    def run(self):
        i = 0
        start_time = time()
        for host in self.hosts:
            if self.ping(host):
                if self.output[i] != 0:
                    fail_time = time() - self.output[i]
                    if fail_time / 60 > 15:
                        self.notify(i, 0)
                        self.is_notified[i] = 0
                self.output[i] = 0
            else:
                if self.output[i] == 0:
                    fail_time = 0
                    self.output[i] = time()
                else:
                    fail_time = time() - self.output[i]
                if fail_time / 60 > 15 and self.is_notified[i] !=15:
                    self.notify(i, 15)
                    self.is_notified[i] = 15
                elif fail_time / 60 > 10 and self.is_notified[i] < 10:
                    self.notify(i, 10)
                    self.is_notified[i] = 10
            i += 1
        return time() - start_time

    def start(self, bot):
        self.bot = bot
        self.is_running = True
        while self.is_running:
            elapsed_time = self.run()
            sleep(max((float(self.min_wait_time) / 1000) - elapsed_time, 0))

    def stop(self):
        self.is_running = False

hosts = []
names = []

handle = open("hosts.txt", "r")
for line in handle:
    if line[0] != ';':
        hosts.append(line.split(':')[0])
        names.append(line.split(':')[1].rstrip())
handle.close()

pinger = Pinger(1000, 10000, hosts, names)


apihelper.proxy = config.proxy

bot = telebot.TeleBot(config.token)

keyboard1 = telebot.types.ReplyKeyboardMarkup(True)
keyboard1.row('Запуск', 'Статистика за сегодня')


def send_message(message):
    keyboard1 = telebot.types.ReplyKeyboardMarkup(True)
    keyboard1.row('Остановить', 'Статистика за сегодня')
    bot.send_message(config.chat_id, text=message, reply_markup=keyboard1)

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Привет, ты написал мне /start', reply_markup=keyboard1)

@bot.message_handler(content_types=['text'])
def send_text(message):
    keyboard1 = telebot.types.ReplyKeyboardMarkup(True)
    now = datetime.datetime.now()
    if message.text.lower() == 'запуск':
        config.chat_id = message.chat.id
        keyboard1.row('Остановить', 'Статистика за сегодня')
        bot.send_message(message.chat.id, 'Мониторинг запущен в ' + now.strftime("%H:%M %d.%m.%Y"), reply_markup=keyboard1)
        pinger.start(bot)
    elif message.text.lower() == 'остановить':
        keyboard1.row('Запуск', 'Статистика за сегодня')
        pinger.stop()
        bot.send_message(message.chat.id, 'Мониторинг остановлен в ' + now.strftime("%H:%M %d.%m.%Y"), reply_markup=keyboard1)
    elif message.text.lower() == 'статистика за сегодня':
        if pinger.is_running:
            keyboard1.row('Остановить', 'Статистика за сегодня')
        else:
            keyboard1.row('Запуск', 'Статистика за сегодня')
        config.chat_id = message.chat.id
        res = pinger.get_status()
        bot.send_message(message.chat.id, res, reply_markup=keyboard1)

bot.polling()