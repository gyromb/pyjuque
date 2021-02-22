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
class PNDStrategy(StrategyTemplate):    
    def __init__(self, profit=0.05, increase_profit=0.05, profit_margin=0.01, stop_loss=0.1, window_h=12, price_threshold=1.1, vol_threshold=10):
        self.profit = profit
        self.cur_profit = profit
        self.increase_profit = increase_profit
        self.profit_margin = profit_margin
        self.stop_loss = stop_loss
        self.buy_price = None
        self.sell_price = None

        self.window_h = window_h
        self.price_threshold = 1.1
        self.vol_threshold = 10

    # the bot will call this function with the latest data from the exchange 
    # passed through df; this function computes all the indicators needed
    # for the signal
    def setUp(self, df):
        self.dataframe = df
        nr_points = int(self.window_h * 60 / 15)
        self.df_15min = self.bot_controller.exchange.getOHLCV(self.symbol, '15m', limit=nr_points)

    # the bot will call this function with the latest data and if this 
    # returns true, our bot will place an order
    def checkLongSignal(self, i = None):
        # df = self.dataframe
        # if i == None:
        #     i = len(df) - 1
        # i15 = len(self.df_15min)-1
        # high = self.df_15min["high"][i15]
        # price_increased = self.df_15min["close"][i15] - self.df_15min["close"][i15-1] > 0
        # volume = self.df_15min["volume"][i15]
        #
        # av_price = self.df_15min["close"].mean()
        # av_volume = self.df_15min["volume"].mean()
        #
        # price_over_threshold = high > self.price_threshold * av_price
        # vol_over_threshold = volume > self.vol_threshold * av_volume
        #
        # if vol_over_threshold and not price_over_threshold and price_increased:
        #     return True
        # else:
        #     return False
        return True

    def checkShortSignal(self, i=None):
        # if not self.buy_price:
        #     return False
        # df = self.dataframe
        # if i == None:
        #     i = len(df) - 1
        # close = df["close"][i]
        #
        # if not self.sell_price:
        #     self.sell_price = self.buy_price * (1-self.stop_loss)
        #
        # if close <= self.sell_price:
        #     profit = close / self.buy_price
        #     return True
        #
        # if close >= self.buy_price * (1+self.cur_profit):
        #     self.cur_profit += self.increase_profit
        #     self.sell_price = close * (1-self.profit_margin)

        return True


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
        'function': PNDStrategy,
        'params': {
            'profit': 0.05,
            'increase_profit': 0.05,
            'profit_margin': 0.01,
            'stop_loss': 0.1,
            'window_h': 12,
            'price_threshold': 1.1,
            'vol_threshold': 10
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
        
        time.sleep(60)

if __name__ == '__main__':
    Main()
