import Settings

API = Settings.getAPI()
wallet = API["API_KEY"]
mnemonic = API["SECRET_KEY"]


message_transaction = "Сделка была совершена автоматически"

invest_mode = False
TOKEN_TG = "5089449066:AAFtD26w3Ek7RlKQz"                         # токен телеграм бота для страхового бота
CHAT_ID = "41741"                                                               # id чата для логов


enable_arbitrage = True                                         # включить арбитраж
enable_swap = True                                              # включить отработку свапов, если отключено, то приходят только уведомления в тг
arbitrage_coins = ["BIP"]                          # начальные и конечные монеты

arbitrage_setups = [
    {
        "size": 1000,                                              # объём
        "profit": 25                                            # прибыль в %
    }
]

