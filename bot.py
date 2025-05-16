import threading
import time
import datetime
import trading_api
import misc
import Settings
from config import *
from sys import exc_info
from traceback import extract_tb
from arbitrage import start as arbitrage_start
from decimal import Decimal

def start_bot():
    settings = Settings.getSettings()
    last_send_stats = 0
    last_upd_status_order = {}
    firt_start = True
    insurance = {"size": 0, "lastUsdt": False}
    profit_coins = {}
    symbol = ""

    def get_grid():
        return {
            "order_tp": 0,
            "price_tp": 0,
            "price_avg": 0,
            "openPrice": 0,
            "entryPrice": 0,
            "positionAmt": 0,
            "max_orders": 0,
            "act_orders": 0,
            "lastPrice": 0,
            "actBY": False,
            "time_open": 0,
            "isFullGrid": False,
            "size_order": 0
        }

    def get_settings():
        return {
            "status": "OFF",
            "insufficient": False,
            "openGrid": True,
            "grids": [],
            "creditSize": 0
        }

    def profit(symbol, grid, type_grid):
        pos1 = grid["entryPrice"] * grid["positionAmt"]
        pos2 = grid["price_tp"] * grid["positionAmt"]

        pnl = (pos2 - pos1)
        if type_grid == "reverse": pnl = (pos1 - pos2)
        com = pnl * 0.001
        profit = pnl - com
        profit_base = profit

        price_close = trading_api.get_price(symbol)
        # if type_grid == "reverse": profit = profit * price_close

        db.add_profit_all(profit)
        Settings.saveStats(profit)

        profit_coin = ""
        if type_grid == "standart": profit_coin = symbol.replace(exchangeInfo[symbol][3], "")
        elif type_grid == "reverse": profit_coin = exchangeInfo[symbol][3]

        if profit_coin not in profit_coins: profit_coins[profit_coin] = 0
        profit_coins[profit_coin] += profit_base

        if profit_coins[profit_coin] >= couple["min_profit"]:
            base_coin = symbol.replace(exchangeInfo[symbol][3], "")
            profit_size = misc.transformationPrice(profit_coins[profit_coin] / price_close, exchangeInfo[symbol][0])
            if type_grid == "standart":
                for s, exch in exchangeInfo.items():
                    if exch[3] == base_coin and exch[4] == couple['profit_coin']:
                        trading_api.sell_market(exch[3] + exch[4], profit_size)
                        break
                    elif exch[4] == base_coin and exch[3] == couple['profit_coin']:
                        trading_api.buy_market(exch[4] + exch[3], profit_size)
                        break
            elif type_grid == "reverse":
                symbol_change_profit = exchangeInfo[symbol][3] + couple["profit_coin"]
                trading_api.sell_market(symbol_change_profit, profit_size)

                misc.send_msg(f"{symbol} прибыль со сделок {profit_size} зафиксирована в {couple['profit_coin']}")


        time_close = int(time.time())
        misc.send_tg(f"Закрыта позиция\n"
                     f"Дата: <b>{str(datetime.datetime.fromtimestamp(time_close)).split('.')[0]}</b>\n"
                     f"Текущая цена: <b>{price_close}$</b>\n"
                     f"Объём: <b>{grid['positionAmt']}{symbol.replace(exchangeInfo[symbol][4], '')}</b>\n"
                     f"Пара: <b>{symbol}</b>\n"
                     f"Прибыль: <b>{pnl}$</b>\n"
                     f"Чистая прибыль: <b>{profit}$</b>\n"
                     f"Комиссия биржи: <b>{com}$</b>")
        misc.send_msg(f"{symbol} позиция закрыта {profit} {grid['positionAmt']}")
        if history_api:
            db.save_history_spot(symbol, grid["time_open"], time_close, grid["openPrice"], price_close, grid["entryPrice"], profit, grid["positionAmt"])

        # возврат кредитных средств
        if save_mode and settings[symbol]["insufficient"]:
            balance = trading_api.get_balance(wallet)
            if balance + 1 >= settings[symbol]["creditSize"]:
                db_save.change_status_user(API_KEY, "return")
                misc.send_tg(f"Страховочные средства возвращены")

                settings[symbol]["creditSize"] = 0
                settings[symbol]["insufficient"] = False

    def close_position(symbol, grid):
        open_orders = trading_api.get_open_orders(symbol)
        ooid = [order["orderId"] for order in open_orders]
        for order in grid["open_orders"]:
            if order in ooid:
                trading_api.cancel_order(order)

        profit(symbol, grid, type_grid)

        misc.send_msg(f"{symbol} позиция закрыта {len(settings[symbol]['grids'])}")

    def get_size_position(symbol):
        if type_grid == "standart":
            return trading_api.get_balance(wallet)[symbol.split("/")[0]]
        elif type_grid == "reverse":
            # price = trading_api.get_price(symbol)
            return trading_api.get_balance(wallet)[symbol.split("/")[1]]

    lastupd = 0
    while True:
        time.sleep(3)
        try:
            couples = Settings.getCouples()

            if invest_mode:
                if int(datetime.datetime.now().hour) == 0 and time.time() - last_send_stats > 5000:

                    d = 0
                    w = 0
                    m = 0
                    a = 0

                    stats = Settings.getStats()
                    for stat in stats:
                        if stat:
                            stat = stat.split(";")
                            pnl = float(stat[0])
                            stime = int(stat[1])

                            if time.time() - stime <= 86400:
                                d += pnl

                            if time.time() - stime <= 604800:
                                w += pnl

                            if time.time() - stime <= 2592000:
                                m += pnl

                            a += pnl

                    msg = f"Дата: <b>{str(datetime.datetime.now()).split('.')[0]}</b>\n" \
                          f"Прибыль за сутки: <b>{round(d, 4)}$</b>\n" \
                          f"Прибыль за неделю: <b>{round(w, 4)}$</b>\n" \
                          f"Прибыль за месяц: <b>{round(m, 4)}$</b>\n" \
                          f"За все время: <b>{round(a, 4)}$</b>"

                    misc.send_tg(f"{msg}")

                    last_send_stats = time.time()

            for couple in couples.copy().values():
                time.sleep(0.3)

                symbol = couple["symbol"]
                type_grid = couple["type_grid"]

                if couple["enable"] == "ON":
                    if symbol not in settings.keys():
                        settings[symbol] = get_settings()

                    price = trading_api.get_price(symbol, couple["size"])
                    if not price:
                        misc.send_msg(f"{symbol} не нашли роут с тек. объёмом {price} {couple['size']}")
                        continue

                    # открытие позиции
                    if settings[symbol]["openGrid"]:
                        if firt_start: misc.send_msg(f"{symbol} открытие сетки {len(settings[symbol]['grids']) + 1}")

                        misc.send_msg(f"{symbol} открытие позиции..")
                        grid = get_grid()

                        size = couple["size"]

                        if type_grid == "standart":
                            order = trading_api.buy_market(symbol, size)
                        elif type_grid == "reverse":
                            order = trading_api.sell_market(symbol, size)

                        time.sleep(0.1)

                        entryPrice = price
                        misc.send_msg(f"{symbol} позиция открыта {size} {entryPrice}")

                        # size = get_size_position(symbol)

                        if type_grid == "standart": price_tp = misc.precWithPrice(entryPrice, couple["TP"])
                        elif type_grid == "reverse": price_tp = misc.precWithoutPrice(entryPrice, couple["TP"])

                        misc.send_msg(f"{symbol} выставлен TP {price_tp}")

                        settings[symbol]["positionAmt"] = size
                        grid["positionAmt"] = size
                        if couple["max_orders"] > 1:
                            price_avg = misc.precWithoutPrice(entryPrice, couple["step"])

                            if type_grid == "standart": price_avg = misc.precWithoutPrice(entryPrice, couple["step"])
                            elif type_grid == "reverse":  price_avg = misc.precWithPrice(entryPrice, couple["step"])

                            misc.send_msg(f"{symbol} выставлен ордер на усреднение {size} {price_avg}")

                        grid["entryPrice"] = entryPrice
                        grid["openPrice"] = entryPrice
                        grid["lastPrice"] = entryPrice
                        grid["price_tp"] = price_tp
                        grid["price_avg"] = price_avg
                        grid["time_open"] = int(time.time())
                        grid["size_order"] = size

                        settings[symbol]["openGrid"] = False
                        settings[symbol]["status"] = "ON"
                        settings[symbol]["grids"].append(grid)

                        misc.send_tg(f"Открыта позиция\n"
                                     f"Дата: <b>{str(datetime.datetime.fromtimestamp(grid['time_open'])).split('.')[0]}</b>\n"
                                     f"Пара: <b>{symbol}</b>\n"
                                     f"Объём: <b>{size}{symbol.replace('USDT', '').replace('BUSD', '')}</b>\n"
                                     f"Текущая цена: <b>{price}$</b>")

                    # ведение позиции
                    elif settings[symbol]["status"] == "ON":
                        for grid in settings[symbol]["grids"].copy():
                            size_buy = misc.precWithPrice(grid["size_order"], couple["martingale"])
                            size_sell = grid["positionAmt"] * grid["price_tp"]

                            price_buy = trading_api.get_price(symbol, size_buy, "output")
                            price_sell = trading_api.get_price(symbol, size_sell, "input")

                            if not price_buy or not price_sell:
                                misc.send_msg(f"{symbol} не нашли роут с тек. объёмом {price_buy, price_sell} {size_buy, size_sell}")
                                continue

                            # усреднение
                            if not settings[symbol]["insufficient"]:
                                if grid["max_orders"] < couple["max_orders"]:
                                    if price_buy <= grid["price_avg"]:
                                        size_order = size_buy

                                        order_avg = trading_api.buy_market(symbol, size_order)
                                        misc.send_msg(f"{symbol} исполнен ордер на усреднение {len(settings[symbol]['grids'])} {grid['max_orders'] + 1} {order_avg}")

                                        entryPrice = (Decimal(grid["entryPrice"]) * Decimal(grid["positionAmt"]) + float(order_avg["price"]) * size_order) / (grid["positionAmt"] + size_order)
                                        entryPrice = entryPrice
                                        misc.send_msg(f"{symbol} средняя цена позиции {entryPrice}")

                                        trading_api.cancel_order(grid["order_tp"])
                                        time.sleep(0.1)

                                        all_size = get_size_position(symbol)
                                        misc.send_msg(f"{symbol} объём позиции {all_size}")

                                        if type_grid == "standart":
                                            if grid["actBY"]: price_tp = misc.precWithPrice(entryPrice, couple["BY"])
                                            else: price_tp = misc.precWithPrice(entryPrice, couple["TP"])
                                            price_avg = misc.precWithoutPrice(float(order_avg["price"]), couple["step"])
                                        elif type_grid == "reverse":
                                            if grid["actBY"]: price_tp = misc.precWithoutPrice(entryPrice, couple["BY"])
                                            else: price_tp = misc.precWithoutPrice(entryPrice, couple["TP"])
                                            price_avg = misc.precWithPrice(float(order_avg["price"]), couple["step"])

                                        misc.send_msg(f'{symbol} выставлен ордер на открытие {price_avg} {size_buy}')
                                        misc.send_msg(f'{symbol} выставлен TP {price_tp} {all_size}')

                                        grid["price_tp"] = price_tp
                                        grid["positionAmt"] = all_size
                                        grid["entryPrice"] = entryPrice
                                        grid["price_avg"] = price_avg
                                        grid["size_order"] = size_buy

                                        grid["act_orders"] += 1
                                        grid["max_orders"] += 1
                                else:
                                    if len(settings[symbol]["grids"]) < couple["max_grid"] and not grid["isFullGrid"]:
                                        misc.send_msg(f"{symbol} qwerty {grid['act_orders'] >= couple['max_orders'], grid['act_orders'], couple['max_orders']}")
                                        if grid["act_orders"] >= couple["max_orders"]:
                                            misc.send_msg(f"{symbol} открытие сетки {len(settings[symbol]['grids']) + 1}")
                                            settings[symbol]["openGrid"] = True
                                            grid["isFullGrid"] = True

                            # активация бу
                            if not grid["actBY"] and (price <= misc.precWithoutPrice(grid["openPrice"], couple["actBY"]) and type_grid == "reverse") or \
                                    (price >= misc.precWithPrice(grid["openPrice"], couple["actBY"]) and type_grid == "standart"):
                                misc.send_msg(f"{symbol} активирован б/у {price}")

                                if type_grid == "standart": price_tp = misc.precWithoutPrice(grid["entryPrice"], couple["BY"])
                                elif type_grid == "reverse": price_tp = misc.precWithPrice(grid["entryPrice"], couple["BY"])

                                grid["price_tp"] = price_tp
                                grid["actBY"] = True

                                misc.send_msg(f'{symbol} выставлен TP {price_tp}')

                            # tp
                            order_tp = trading_api.get_order(symbol, grid["order_tp"])
                            if price_sell >= grid["price_tp"]:
                                try: trading_api.sell_market(symbol, grid["positionAmt"])
                                except Exception as err:
                                    if "connection" not in str(err).lower():
                                        misc.send_msg(symbol, err, extract_tb(exc_info()[2]))

                                close_position(symbol, grid)
                                settings[symbol]["grids"].remove(grid)
                                settings[symbol]["openGrid"] = True
                                Settings.saveSettings(settings)

                                continue

                    Settings.saveSettings(settings)

                elif couple["enable"] == "OFF":
                    if symbol in settings.keys():
                        del settings[symbol]
                        Settings.saveSettings(settings)

            firt_start = False

            if time.time() - lastupd >= 3600:
                # misc.send_msg(f"Статус ОК")
                lastupd = time.time()

        except Exception as err:
            if "connection" not in str(err).lower():
                misc.send_msg(symbol, err, extract_tb(exc_info()[2]))
            # input("----")

if __name__ == '__main__':
    if enable_arbitrage:
        threading.Thread(target=arbitrage_start).start()

    start_bot()