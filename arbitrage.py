import trading_api
import threading
import time
from config import *
from logs import logger
import misc

from sys import exc_info
from traceback import extract_tb

count = 0

list_msg = []

def send_msg():
    global list_msg

    timeout_send_msg = {}
    firststart = True
    while True:
        try:
            time.sleep(1)

            for m in list_msg.copy():
                if "Транзакция" not in m:
                    swap = m.split(" | ")[0]
                    if swap not in timeout_send_msg: timeout_send_msg[swap] = 0

                    if time.time() - timeout_send_msg[swap] >= 60:
                        if not firststart:
                            misc.send_tg_arbitrage(m)
                            time.sleep(0.3)
                        timeout_send_msg[swap] = time.time()

                    firststart = False
                else:
                    misc.send_tg_arbitrage(m)

                list_msg.remove(m)
        except Exception as err:
            logger.error([err, extract_tb(exc_info()[2])])
            time.sleep(3)



def split_list(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]

def create_combinations(pools, count_th=1):
    symbols = list(pools.keys())
    count_symbols = len(symbols)
    combinations = []

    # coin_sell > coin_buy | USDX → QUOTA → BIP → USDX
    def start(symbols, symbols_th):
        global count

        for symbol in symbols_th:
            coin_buy = symbol.split("/")[0]
            coin_sell = symbol.split("/")[1] # QUOTA/USDX

            if coin_sell not in arbitrage_coins: continue

            for symbol1 in symbols:
                if symbol1 != symbol:
                    coin_buy1 = symbol1.split("/")[0]
                    coin_sell1 = symbol1.split("/")[1] # QUOTA/BIP

                    if coin_buy == coin_buy1:
                        for symbol2 in symbols:
                            if symbol2 != symbol and symbol2 != symbol1:
                                coin_buy2 = symbol2.split("/")[0]
                                coin_sell2 = symbol2.split("/")[1] # BIP/USDX

                                if coin_buy2 == coin_sell1 and coin_sell2 == coin_sell:
                                    combinations.append([symbol, symbol1, symbol2])

            count += 1

    count_symbols_th = int(count_symbols / count_th)
    if count_symbols_th * count_th < count_symbols: count_symbols_th += 1

    ths = []
    symbols_ths = split_list(symbols, count_symbols_th)

    for symbols_th in symbols_ths:
        ths.append(threading.Thread(target=start, args=(set(symbols), set(symbols_th))))

    for th in ths: th.start()
    for th in ths: th.join()

    return combinations

def find_arbitrage(combinations, pools):
    arbitrage = []
    for combination in combinations:
        pool1 = pools[combination[0]]
        pool2 = pools[combination[1]]
        pool3 = pools[combination[2]]

        # BTC/USDT size0-BTC size1-USDT


        for arbitrage_setup in arbitrage_setups:
            size_swap = arbitrage_setup["size"]

            initial_size_p1 = pool1["size0"] - (pool1["size0"] * pool1["size1"]) / (size_swap + pool1["size1"])
            # print(combination[0], pool1)
            # print(initial_size_p1)

            initial_size_p2 = pool2["size1"] - (pool2["size0"] * pool2["size1"]) / (initial_size_p1 + pool2["size0"])
            # print(combination[1], pool2)
            # print(initial_size_p2)


            initial_size_p3 = pool3["size1"] - (pool3["size0"] * pool3["size1"]) / (initial_size_p2 + pool3["size0"])
            # print(combination[2], pool3)
            # print(initial_size_p3)

            s0 = combination[0].split("/")
            s1 = combination[1].split("/")
            s2 = combination[2].split("/")

            profit = float(initial_size_p3 - size_swap)
            prec_profit = round((float(initial_size_p3) / float(size_swap) - 1) * 100, 2)

            if profit > 0 and prec_profit >= arbitrage_setup["profit"]:
                arbitrage.append({
                    "combination": combination,
                    "initial_size": float(size_swap),
                    "final_size": float(initial_size_p3),
                    "profit": profit,
                    "prec_profit": round((float(initial_size_p3) / float(size_swap) - 1) * 100, 2),
                    "swap_pool": f"{s0[1]} > {s0[0]} > {s1[1]} > {s2[1]}"
                })

    return arbitrage

def main():
    global list_msg

    while True:
        try:
            time.sleep(1)
            pools = trading_api.get_pools()
            stime = time.time()
            combinations = create_combinations(pools, 1)

            arbitrages = find_arbitrage(combinations, pools)

            swapped = False
            for arbitrage in arbitrages:
                combination = arbitrage["combination"]
                swap_pool = arbitrage["swap_pool"]

                if not enable_swap:
                    msg = f"Прибыль: {arbitrage['prec_profit']}%\n" \
                          f"Макс. объём: {round(arbitrage['initial_size'], 2)}\n\n" \
                          f"<code>{swap_pool}</code>"
                    # print(msg)
                    list_msg.append(msg)

                initial_size = arbitrage['initial_size']

                if not swapped and enable_swap:
                        txId = trading_api.swap_pool(trading_api.get_path(swap_pool), initial_size)
                        time.sleep(5)

                        for i in range(10):
                            tx = trading_api.get_transaction(txId)
                            if "error" not in tx:
                                start_size = round(float(tx["data"]["data"]["value_to_sell"]), 6)
                                end_size = round(float(tx["data"]["data"]["value_to_buy"]), 6)
                                profit = round(end_size - start_size, 6)

                                send_long = logger.success if profit > 0 else logger.error
                                send_long(f'{start_size} {tx["data"]["data"]["coin_to_sell"]["symbol"]} > {end_size} {tx["data"]["data"]["coin_to_buy"]["symbol"]} | {profit} | {arbitrage}')


                                msg = f'Прибыль: {profit} {tx["data"]["data"]["coin_to_buy"]["symbol"]}\n' \
                                      f'Комиссия: {round(float(tx["data"]["commission_in_gas_coin"]), 4)} {tx["data"]["gas_coin"]["symbol"]} | ' \
                                      f'{round(float(tx["data"]["commission_price"]), 4)} {tx["data"]["commission_price_coin"]["symbol"]}\n' \
                                      f'Связка: {start_size} {tx["data"]["data"]["coin_to_sell"]["symbol"]} > {end_size} {tx["data"]["data"]["coin_to_buy"]["symbol"]}\n\n' \
                                      f'<code>{swap_pool}</code>\n\n' \
                                      f'https://explorer.trading_api.network/transactions/{txId}' \
                                      #f'<a href="https://explorer.trading_api.network/transactions/{txId}">Транзакция</a>'

                                list_msg.append(msg)
                                break
                            else:
                                logger.warning(f"ожидаем подтверждение транзакции {txId} | {tx}")
                                time.sleep(3)

                        swapped = True
            # break
        except Exception as err:
            logger.error([err, extract_tb(exc_info()[2])])
            time.sleep(3)

def start():
    threading.Thread(target=main).start()
    threading.Thread(target=send_msg).start()

if __name__ == '__main__':
    start()

    # pools = {
    #     "BTC/USDT": {           # 30000
    #         "size0": 10,
    #         "size1": 300000
    #     },
    #     "BTC/ETH": {
    #         "size0": 10,
    #         "size1": 270
    #     },
    #     "ETH/USDT": {
    #         "size0": 1,
    #         "size1": 2000
    #     }
    # }
    #
    # combinations = [["BTC/USDT", "BTC/ETH", "ETH/USDT"]]
    # print(find_arbitrage(combinations, pools, 10))

