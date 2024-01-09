import pandas as pd
import numpy as np
import yfinance as yf
from functools import partial
import numpy as np
from itertools import product


class BollingerStrategy():

    def __init__(self, ticker, start, end):
        self.ticker = ticker
        self.start = start
        self.end = end
        self.get_data()
    
    def get_data(self):
        raw = yf.download(tickers = self.ticker, start = self.start, end = self.end)
        raw.index = pd.to_datetime(raw.index)
        raw.index.rename("Date", inplace = True)
        raw['TP'] = (raw["High"] + raw["Low"] + raw["Adj Close"])/3
        self.data = raw#.iloc[:,4:]
    
    def set_parameters(self, sma, dev_up, dev_down):        
        self.data["SMA"] = self.data['TP'].rolling(sma).mean()
        self.data["Upper"] = self.data['SMA'] + dev_up * self.data['TP'].rolling(sma).std()
        self.data["Lower"] = self.data['SMA'] - dev_down * self.data['TP'].rolling(sma).std()
        return self.data.dropna()
    
    def test_strategy(self):
        data = self.data.copy()
        data['signal'] = np.where(data['High'] >= data['Upper'], -1, 0)
        data['signal'] = np.where(data['Low'] <= data['Lower'], 1, data['signal'])
        
        status = None
        buys = np.array([])
        sells = np.array([])

        for _, row in data.iterrows():
            if status == None and row["signal"] != 1:
                continue
            if row["signal"] != status and row['signal'] == 1.0:
                buys = np.append(buys, row["Low"])
                status = 1.0
            elif row["signal"] != status and row['signal'] == -1.0:
                sells = np.append(sells, row["High"])
                status = -1.0
            else:
                continue
        
        
        buy_signals = len(buys)
        sell_signals = len(sells)
        if buy_signals <2 or sell_signals <2: #at least 2 buy-sell periods in the interval
            return 0
        else:
            mean_price_buy_signal = buys.mean()
            mean_price_sell_signal = sells.mean()
            mean_price_delta = mean_price_sell_signal / mean_price_buy_signal
            return mean_price_delta
            
    def optimizer(self):
        sma_range = (20, 70, 10)
        dev_up_range = (0.9, 2.4, 0.15)
        dev_down_range = (0.9, 2.4, 0.15)
        combinations = list(product(range(*sma_range), np.arange(*dev_up_range), np.arange(*dev_down_range)))
        #test all combinations
        res = []
        for comb in combinations:
            self.set_parameters(comb[0], comb[1], comb[2])
            price = self.test_strategy()
            res.append(price)

        if res:
            if np.max(res)>1.1: #10% year return
                opt = combinations[np.argmax(res)]
                return opt[0], opt[1], opt[2]
            else:
                return 70,2.4,2.4 #default, no optimization happened
        else:
            return 70,2.4,2.4 #default, no optimization happened
    
    def volume_check(self, sma):
        data = self.data.copy()
        alpha = 1-np.log(4)/3    # This is ewma's decay factor.
        weights = list(reversed([(1-alpha)**n for n in range(sma)]))
        ewma = partial(np.average, weights=weights)
        data['Volume_check'] = (data['Volume'].rolling(sma).apply(ewma))/data['Volume'].mean()
        return data['Volume_check'].tail()
        
