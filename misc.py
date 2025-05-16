import ast
from config import *
import datetime
from sys import exc_info
from traceback import extract_tb
import time
import Settings
import requests

def getSymbols():
    symbols = ["-"]
    exchangeInfo = trading_api.get_exchange_information()["symbols"]
    for exch in exchangeInfo:
        if "_" not in exch["symbol"]:
            symbols.append(exch["symbol"])

    return symbols

def getExchangeInfo():
    result = {}

    exchangeInfo = trading_api.get_exchange_information()["symbols"]

    for exch in exchangeInfo:
        # if exch["symbol"] == "ATOMUSDC":
        #     print(exch)
        if exch["status"] == "TRADING":

            for filter in exch["filters"]:

                if filter["filterType"] == "LOT_SIZE":
                    try:
                        minQty = float(filter["minQty"])
                        if "e" not in str(minQty):
                            if minQty < 1:
                                minQty = len(list(str(minQty).split(".")[1]))
                            else:
                                minQty = 0
                        else:
                            minQty = int(str(minQty).split("-")[-1])

                    except:
                        minQty = 0

                elif filter["filterType"] == "PRICE_FILTER":
                    try:
                        minPrice = float(filter["tickSize"])

                        if "e" not in str(minPrice):
                            if minPrice < 1:
                                minPrice = len(list(str(minPrice).split(".")[1]))
                            else:
                                minPrice = 0
                        else:
                            minPrice = int(str(minPrice).split("-")[-1])

                    except:
                        minPrice = 0

                elif filter["filterType"] == "MARKET_LOT_SIZE":
                    minPriceMarket = float(filter["minQty"])

                    if "e" not in str(minPriceMarket):
                        if minPriceMarket < 1:
                            minPriceMarket = len(list(str(minPriceMarket).split(".")[1]))
                        else:
                            minPriceMarket = 0
                    else:
                        minPriceMarket = int(str(minPriceMarket).split("-")[-1])

            result[exch["symbol"]] = [minQty, minPrice, minPriceMarket, exch["baseAsset"], exch["quoteAsset"]]

    return result

def transformationPrice(price, x):
    if x == 0:
        return int(price)


    price = str(price).replace(",", ".")

    try:
        full = price.split(".")[0]
        drob = price.split(".")[1]

        price = f"{full}.{drob[:x]}"
    except:
        pass

    if "e" in str(price):
        return 0
    else:
        return float(price)

def precWithPrice(price, prec):
    if prec == "":
        return False
    return float(price) * (float(prec) / 100 + 1)

def precWithoutPrice(price, prec):
    if prec == "":
        return False
    return float(price) - (float(price) * (float(prec) / 100))

def send_tg(msg):
    if invest_mode:
        msg += f"\n\n{info_signal}"

        msg = f"{msg}\n\n" \
              f"{adds_api.get_adds()}"

    url = "https://api.telegram.org/bot"
    url += TOKEN_TG
    method = url + "/sendMessage"

    for i in range(5):
        try:
            r = requests.post(method, data={
                "chat_id": CHAT_ID,
                "parse_mode": "HTML",
                "text": "<b>SPOT</b>\n\n"+ str(msg)
            }, timeout=10)
            break
        except:
            print(f"Не удалось отправить сигнал, повтор {i}!")
            time.sleep(0.3)

def send_msg(*msgs):
    msg = ""
    for m in msgs:
        msg += str(m) + " "

    msg = f"[{str(datetime.datetime.today()).split('.')[0]}] {str(msg)}"
    Settings.saveLog(msg)
    print(msg)
    send_tg(msg)

def get_comm(symbol, orders):
    trades = trading_api.get_trades(symbol)

    commission = 0
    isBNB = True

    price = trading_api.get_price("BNBUSDT")

    for trade in list(reversed(trades)):
        if trade["orderId"] in orders:
            if float(trade["commission"]) != 0:
                if trade["commissionAsset"] != "USDT":
                    commission += float(trade["commission"]) * price
                else:
                    commission += float(trade["commission"])
                    isBNB = False

    # if isBNB:
    #     commission *= trading_api.get_price("BNBUSDT")

    return commission

def send_tg_arbitrage(msg):
    url = "https://api.telegram.org/bot"
    url += TOKEN_TG
    method = url + "/sendMessage"

    for i in range(5):
        try:
            r = requests.post(method, data={
                "chat_id": CHAT_ID,
                "parse_mode": "HTML",
                "text": str(msg)
            }, timeout=10)
            break
        except:
            print(f"Не удалось отправить сигнал, повтор {i+1}!")
            time.sleep(0.3)

if __name__ == '__main__':
    print(send_tg_arbitrage("test"))

