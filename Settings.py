import ast
import json
import os
import time

path_data = "D:/PythonPrj/talborProject/binance22 TgInvest"

try:
    os.mkdir("data")
except:
    pass

try:
    os.mkdir("data/logs")
except:
    pass

title_log = f"{int(time.time() * 100000)}.txt"
def saveLog(log):
    f = open(f"data/logs/{title_log}", "a", encoding='utf-8')
    info = f"{str(log)}"
    f.write(info + "\n")
    f.close()

def save_data(data):
    f = open(f"data.txt", "w")
    f.write(str(couples))
    f.close()

def get_data():
    data = {}
    try:
        f = open(f"data.txt")
        data = ast.literal_eval(f.read())
        f.close()
    except:
        pass

    return data

def saveCouples(couples):
    f = open("data/couples.txt", "w")
    f.write(str(couples))
    f.close()

def getCouples():
    settings = {}
    try:
        f = open("data/couples.txt")
        settings = ast.literal_eval(f.read())
        f.close()
    except:
        pass

    return settings

def saveSettings(settings):
    f = open("data/settings.txt", "w")
    f.write(str(settings))
    f.close()

def getSettings():
    settings = {'API_KEY': '', 'SECRET_KEY': ''}
    try:
        f = open("data/settings.txt")
        settings = ast.literal_eval(f.read())
        f.close()
    except:
        pass
    return settings

def saveKlines(symbol, klines, timeFrame):
    f = open(f"data/klines/{symbol}_{timeFrame}.txt", "w")
    f.write(str(klines))
    f.close()

def getKlines(symbol, timeFrame):
    klines = []
    try:
        f = open(f"data/klines/{symbol}_{timeFrame}.txt")
        klines = ast.literal_eval(f.read())
        f.close()
    except:
        pass

    return klines

def saveHistory(history):
    f = open("data/history.txt", "a")
    f.write(str(history) + "\n")
    f.close()

def saveAPI(API):
    f = open("data/API.txt", "w")
    f.write(str(API))
    f.close()

def getAPI():
    API = {"API_KEY": "", "SECRET_KEY": ""}
    try:
        f = open("data/API.txt")
        API = ast.literal_eval(f.read())
        f.close()
    except:
        pass

    return API

def saveStats(stats):
    f = open(f"data/stats.txt", "a")
    f.write(f"{str(stats)};{int(time.time())}\n")
    f.close()

def getStats():
    stats = []
    try:
        f = open(f"data/stats.txt")
        stats = f.read().split("\n")
        f.close()
    except:
        pass

    return stats

def save_key(key):
    f = open(f"data/key.txt", "w")
    f.write(str(key))
    f.close()

def get_key():
    key = 0
    try:
        f = open(f"data/key.txt")
        key = int(f.read())
        f.close()
    except:
        pass

    if key:
        return key
    else:
        return 0