import numpy as np
import pandas as pd
import yfinance as yf

class MCPortfolio():
    
    def __init__(self, ticker: list, start, end):
        self.ticker = ticker # ["ticker", "ticker1", ""]
        self.start = start
        self.end = end
        self.get_data()
        self.prepare_data()
    
    def get_data(self):
        df_list = []
        for ticker in self.ticker:
            df = yf.download(ticker, start = self.start, end = self.end, index_col = 0, parse_dates=True)
            df_list.append(df['Adj Close'])
        raw = pd.concat(df_list, axis=1)
        raw.columns = self.ticker
        self.data = raw 
    
    def prepare_data(self):
        data = self.data.copy().dropna()
        result = np.log(data/data.shift(1))
        result.dropna(inplace = True)
        self.result = result
    
    def optimizer(self):
        n = 15000
        weights = np.zeros((n, len(self.result.columns)))
        exp_returns = np.zeros(n)
        exp_volatilities = np.zeros(n)
        sharpe_ratios = np.zeros(n)
        
        for i in range(n):
            weight = np.random.random(len(self.result.columns))
            weight /= np.sum(weight)   #normalization
            weights[i] = weight #storing all the combinations of weight (=pond)
            exp_returns[i] = np.sum(self.result.mean() * weight)*252   #expected annual weighted mean return
            exp_volatilities[i] = np.sqrt(np.dot(weight.T, np.dot(self.result.cov()*252, weight)))  # expected annual weighted volatility, considering dependences between stock returns
            sharpe_ratios[i] = exp_returns[i]/exp_volatilities[i]
           
        return pd.DataFrame(data = weights[exp_returns.argmax()], index = self.ticker).rename(columns={0:"%"})