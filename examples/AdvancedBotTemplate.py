import json
import os
import time

# Imports for the strategy
from os import getenv

import pandas_ta as ta

# Importing these to be able to run this example 
# from the main pyjuque folder
from os.path import abspath, pardir, join
import sys
curr_path = abspath(__file__)
root_path = abspath(join(curr_path, pardir, pardir))
sys.path.append(root_path)

# Import for defining the bot
from pyjuque.Bot import defineBot
# Import for defining the Strategy
from pyjuque.Strategies import StrategyTemplate

## Defines the strategy
class ProfitHuntStrategy(StrategyTemplate):
    """ Bollinger Bands x RSI """
    def __init__(self, profit=0.05, increase_profit=0.05, profit_margin=0.01, stop_loss=0.1, ema_width=25, ema_trigger=0.90, rsi_len=14, rsi_threshold=40):
        self.profit = profit
        self.increase_profit = increase_profit
        self.profit_margin = profit_margin
        self.stop_loss = stop_loss
        self.buy_price = None
        self.rsi_len = rsi_len
        self.rsi_threshold = rsi_threshold

        self.ema_width = ema_width
        self.ema_trigger = ema_trigger
        self.holding = True

    def isHolding(self):
        open_orders = self.bot_controller.bot_model.getOpenOrders(self.bot_controller.session)
        for order in open_orders:
            if not order.status or (order.status == 'closed' and order.executed_quantity > 0):
                return True
        return False

    # the bot will call this function with the latest data from the exchange
    # passed through df; this function computes all the indicators needed
    # for the signal
    def setUp(self, df, symbol):
        self.dataframe = df
        self.holding = self.isHolding()
        if not self.holding:
            self.df_15min = self.bot_controller.exchange.getOHLCV(symbol, '15m', limit=100)

    # the bot will call this function with the latest data and if this
    # returns true, our bot will place an order
    def checkLongSignal(self, i = None):
        if self.holding:
            return False

        df = self.dataframe
        if i == None:
            i = len(df) - 1

        close = self.df_15min["close"].iloc[-1]
        close_24h = self.df_15min["close"].iloc[len(self.df_15min) - 96]
        change24h = close/close_24h

        ema25 = ta.ema(self.df_15min['close'], 25)
        ema50 = ta.ema(self.df_15min['close'], 50)
        rsi = ta.rsi(self.df_15min['close'], self.rsi_len)
        entry_signal = close <= ema25.iloc[-1]*self.ema_trigger and rsi.iloc[-1] <= self.rsi_threshold and ema50.iloc[-1] > ema25.iloc[-1]

        if entry_signal:
            self.bot_controller.disable_entry = True
            self.holding = True

        return entry_signal

    def checkShortSignal(self, i=None, order=None):
        if not order:
            return False

        df = self.dataframe
        if i == None:
            i = len(df) - 1
        close = df["close"][i]

        if not order.stop_price:
            order.stop_price = float(order.price) * (1 - self.stop_loss)

        if not order.take_profit_price:
            order.take_profit_price = self.profit

        buy_price = float(order.price)
        sell_price = float(order.stop_price)
        cur_profit = float(order.take_profit_price)

        if close <= sell_price:
            profit = close / order.price
            self.bot_controller.disable_entry = False
            return True

        if close >= buy_price * (1 + cur_profit):
            cur_profit = (close / float(order.price)) - 1
            cur_profit += self.increase_profit
            sell_price = close * (1 - self.profit_margin)

            order.take_profit_price = cur_profit
            order.stop_price = sell_price

        self.bot_controller.session.commit()
        return False


## Defines the overall configuration of the bot 
bot_config = {
    # Name of the bot, as stored in the database
    'name': 'AdvancedBotTemplate',
    'test_run': True,

    # exchange information (fill with your api key and secret)
    'exchange': {
        'name': 'binance',
        'params': {                      # put here any param that ccxt accepts
            'api_key': getenv('BINANCE_API_KEY'),
            'secret': getenv('BINANCE_API_SECRET')
        },
    },

    # symbols to trade on
    'symbols': [],

    # starting balance for bot
    'starting_balance': 0.01,

    # strategy class / function (here we define the entry and exit strategies.)
    # this bot places an entry order when the 'checkLongSignal' function of 
    # the strategy below retruns true
    'strategy': {
        'function': ProfitHuntStrategy,
        'params': {
            'profit': 0.05,
            'increase_profit': 0.05,
            'profit_margin': 0.01,
            'stop_loss': 0.1,
            'ema_width': 25,
            'ema_trigger': 0.95,
            'rsi_len': 14,
            'rsi_threshold': 40
        },
    },

    # when the bot receives the buy signal, the order is placed according 
    # to the settings specified below
    'entry_settings' : {
        # between 0 and 100, the % of the starting_balance to put in an order
        'initial_entry_allocation': 100,

        # number between 0 and 100 - 1% means that when we get a buy signal, 
        # we place buy order 1% below current price. if 0, we place a market 
        # order immediately upon receiving signal
        #'signal_distance': 0.3
        'signal_distance': 0
    },

    # This bot exits when our filled orders have reached a take_profit % above 
    # the buy price, or a stop_loss_value % below it
    'exit_settings': {
        'exit_on_signal': True
    },

    # will the bot display its status / current performing action in the terminal
    'display_status': True
}


## Runs the bot in an infinite loop, stoppable from the terminal with CTRL + C
def Main():
    if os.path.isfile('./AdvancedBotTemplate.db'):
        os.remove('./AdvancedBotTemplate.db')

    symbols = ['DASH/ETH']
    bot_config['symbols'] = symbols

    bot_controller = defineBot(bot_config)
    bot_controller.kline_interval = '1m'   
    while True:
        try:
            bot_controller.executeBot()
        except KeyboardInterrupt:
            return
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(str(e))

            # if we had an exception then the database will probably be corrupt --> start a new one
            if os.path.isfile('./AdvancedBotTemplate.db'):
                os.remove('./AdvancedBotTemplate.db')
        
        time.sleep(1)

if __name__ == '__main__':
    Main()
