import platform    # For getting the operating system name
import subprocess  # For executing a shell command
from time import time, sleep
import telebot
import urllib
from telebot import apihelper

class Pinger():

    #Массив времени, когда хост был доступен в последний раз. Если хост доступен, то время 0
    output = []
    #Запущен мониторинг или нет
    is_running = False
    #Было ли оповещение об упавшем хосте, 0 - нет, 10 - оповещение о 10-ти минутах, 15 - о 15-ти
    is_notified = []


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

    #Функция оповещения о неотвечающем хосте, id - id хоста в массиве hosts
    def notify(self, id, min):
        bot = telebot.TeleBot('842758704:AAE6j2c7CYqdK9P_lTf63Rn_FfLddrWw_R8')
        chat_id = '351515893'
        apihelper.proxy = {
            'http': 'socks5://35.245.58.129:4444',
            'https': 'socks5://35.245.58.129:4444'
        }
        if min == 0:
            message = 'Мониторинг ' + self.hosts[id] + ' восстановлен '
        else:
            message = 'Оборудование ' + self.names[id] + ' (' + self.hosts[id] + ') недоступно более ' + str(min) + ' минут.\nПриоритет: высокий'
        bot.send_message(chat_id, text=message)
        print(message)

    #Функция проверки доступности хостов
    def run(self):
        i = 0
        start_time = time()
        for host in self.hosts:
            if self.ping(host):
                if self.output[i] != 0:
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
                elif fail_time / 60 > 10 and self.is_notified[i] !=10:
                    self.notify(i, 10)
                    self.is_notified[i] = 10
            i += 1
        return time() - start_time

    def start(self):
        self.is_running = True
        while self.is_running:
            elapsed_time = self.run()
            sleep(max((float(self.min_wait_time) / 1000) - elapsed_time, 0))

    def stop(self):
        self.running = False


hosts = []
names = []

handle = open("hosts.txt", "r")
for line in handle:
    if line[0] != ';':
        hosts.append(line.split(':')[0])
        names.append(line.split(':')[1])
handle.close()

pn = Pinger(1000, 2000, hosts, names)
pn.start()