from PyQt5 import QtWidgets, QtCore, QtGui
from config import *
from qUI import Ui_MainWindow
import sys
from PyQt5.QtWidgets import QTableWidgetItem, QCheckBox, QGroupBox, QLabel, QMdiArea
import sys
import time
import Settings
import misc
from sys import exc_info
from traceback import extract_tb
import trading_api

#pyuic5 main.ui -o qUI.py

couples = Settings.getCouples()
types_grid = ["standart", "reverse"]

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):

        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setups = list(couples.keys())
        self.ui.setups.addItems(self.setups)
        self.ui.type_grid.addItems(types_grid)

        self.ui.API_KEY.setText(wallet)
        self.ui.SECRET_KEY.setText(mnemonic)

        self.ui.saveAPI.clicked.connect(self.saveAPI)
        self.ui.add.clicked.connect(self.add)
        self.ui.on.clicked.connect(self.on)
        self.ui.off.clicked.connect(self.off)
        self.ui.setups.activated.connect(self.act)

        # self.ui.add.setEnabled(False)
        self.ui.on.setEnabled(False)
        self.ui.off.setEnabled(False)

        self.act()
        self.print_st()

    def add(self):
        global couples
        try:
            symbol = self.ui.symbol.text()
            if symbol != "-":

                couples[symbol] = {
                    "enable": "OFF",
                    "symbol": symbol,

                    "size": float(self.ui.size.text().replace(",", ".")),

                    "step": float(self.ui.step.text().replace(",", ".")),
                    "martingale": float(self.ui.martingale.text().replace(",", ".")),
                    "max_orders": float(self.ui.max_orders.text().replace(",", ".")),
                    "max_grid": float(self.ui.max_grid.text()),

                    "TP": float(self.ui.TP.text().replace(",", ".")),

                    "actBY": float(self.ui.actBY.text().replace(",", ".")),
                    "BY": float(self.ui.BY.text().replace(",", ".")),
                    "type_grid": self.ui.type_grid.currentText(),
                    "profit_coin": self.ui.symbol.text().split("/")[1],
                    "min_profit": float(self.ui.min_profit.text())
                }

                Settings.saveCouples(couples)
                self.print_st()

                self.ui.add.setEnabled(True)
                self.ui.on.setEnabled(True)
                self.ui.off.setEnabled(False)

                if symbol not in self.setups:
                    self.ui.setups.addItem(symbol)
                    self.setups.append(symbol)

                misc.send_msg(f"{symbol} сохранено!")


        except Exception as err:
            print(err, extract_tb(exc_info()[2]))

    def on(self):
        global couples
        try:
            symbol = self.ui.symbol.text()

            couples[symbol]["enable"] = "ON"
            Settings.saveCouples(couples)

            self.ui.add.setEnabled(False)
            self.ui.on.setEnabled(False)
            self.ui.off.setEnabled(True)

            self.ui.status.setText("ON")

            try:
                settings = Settings.getSettings()
                del settings[symbol]
                Settings.saveSettings(settings)
            except:
                pass

            misc.send_msg(f"{symbol} включено!")

            self.print_st()


        except Exception as err:
            print(err, extract_tb(exc_info()[2]))

    def off(self):
        global couples
        try:
            symbol = self.ui.symbol.text()

            couples[symbol]["enable"] = "OFF"
            Settings.saveCouples(couples)

            self.ui.add.setEnabled(True)
            self.ui.on.setEnabled(True)
            self.ui.off.setEnabled(False)

            self.ui.status.setText("OFF")

            try:
                settings = Settings.getSettings()
                del settings[symbol]
                Settings.saveSettings(settings)
            except:
                pass

            misc.send_msg(f"{symbol} отключено!")

            self.print_st()


        except Exception as err:
            print(err, extract_tb(exc_info()[2]))

    def act(self):
        global couples
        try:
            couples = Settings.getCouples()

            setup = self.ui.setups.currentText()
            if setup != "-":
                if setup in couples.keys():
                    couple = couples[setup]

                    status = couple["enable"]
                    self.ui.status.setText(status)
                    if status == "ON":
                        self.ui.add.setEnabled(False)
                        self.ui.on.setEnabled(False)
                        self.ui.off.setEnabled(True)
                    elif status == "OFF":
                        self.ui.add.setEnabled(True)
                        self.ui.on.setEnabled(True)
                        self.ui.off.setEnabled(False)

                    self.ui.symbol.setText(couple["symbol"])
                    self.ui.size.setText(str(couple["size"]))
                    self.ui.step.setText(str(couple["step"]))
                    self.ui.martingale.setText(str(couple["martingale"]))
                    self.ui.max_orders.setText(str(couple["max_orders"]))
                    self.ui.TP.setText(str(couple["TP"]))
                    self.ui.actBY.setText(str(couple["actBY"]))
                    self.ui.BY.setText(str(couple["BY"]))
                    self.ui.max_grid.setText(str(couple["max_grid"]))
                    self.ui.type_grid.setCurrentText(couple["type_grid"])
                    self.ui.min_profit.setText(str(couple["min_profit"]))


                else:
                    self.ui.status.setText("-")
                    self.ui.add.setEnabled(True)
                    self.ui.on.setEnabled(False)
                    self.ui.off.setEnabled(False)

                    self.clear_all()

            else:
                self.ui.status.setText("-")

                self.ui.add.setEnabled(False)
                self.ui.on.setEnabled(False)
                self.ui.off.setEnabled(False)

                self.clear_all()


        except Exception as err:
            print(err, extract_tb(exc_info()[2]))

    def saveAPI(self):
        try:
            API = {
                "API_KEY": self.ui.API_KEY.text(),
                "SECRET_KEY": self.ui.SECRET_KEY.text()
            }

            Settings.saveAPI(API)

            misc.send_msg(f"API ключи сохранены!")
        except Exception as err:
            print(err, extract_tb(exc_info()[2]))

    def clear_all(self):
        try:
            self.ui.status.setText("-")
            self.ui.size.clear()
            self.ui.step.clear()
            self.ui.martingale.clear()
            self.ui.max_orders.clear()
            self.ui.TP.clear()
            self.ui.actBY.clear()
            self.ui.BY.clear()
            self.ui.max_grid.clear()
            self.ui.type_grid.setCurrentText(types_grid[0])
            self.ui.min_profit.clear()
        except Exception as err:
            print(err, extract_tb(exc_info()[2]))

    def print_st(self):
        try:
            on_t = []
            off_t = []

            for symbol, couple in couples.items():
                if couple["enable"] == "ON":
                    on_t.append(symbol)
                elif couple["enable"] == "OFF":
                    off_t.append(symbol)

            self.ui.actSt.clear()
            for sym in on_t:
                self.ui.actSt.append(f'<span style="color:#1c8f0d;">{sym} - ON</span>')
            for sym in off_t:
                self.ui.actSt.append(f'<span style="color:#ff0000;">{sym} - OFF</span>')
        except Exception as err:
            print(err, extract_tb(exc_info()[2]))


def start_app():
    app = QtWidgets.QApplication([])
    application = MainWindow()

    application.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    start_app()







