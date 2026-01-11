import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

class MCPortfolio():
    
    def __init__(self, ticker: list, data: dict):
        self.ticker = ticker # ["ticker", "ticker1", ""]
        self.data = data
        self.pe_ratios = {}
        self.get_pe_ratios()
        self.get_data()
        self.prepare_data()

    def get_pe_ratios(self):
        """Fetch P/E ratios from yfinance"""
        for t in self.ticker:
            try:
                pe = yf.Ticker(t).info.get('trailingPE')
                print(f"Fetched P/E for {t}: {pe}")
                if pe and pe > 0:
                    self.pe_ratios[t] = pe
                else:
                    self.pe_ratios[t] = None
            except:
                self.pe_ratios[t] = None

    def get_data(self):
        df_list = []
        for t in self.ticker:
            df = self.data[t]
            df_list.append(df['Close'])
        raw = pd.concat(df_list, axis=1)
        raw.columns = self.ticker
        self.data = raw 
    
    def prepare_data(self):
        data = self.data.copy().dropna()
        result = np.log(data/data.shift(1))
        result.dropna(inplace = True)
        self.result = result
    
    def optimizer(self, equal_fundamental_weights: bool = False, dirichlet_multiplier: float = 10/3):
        n = 30000
        BUSINESS_DAYS = 293 # average 425 business days
        number_of_assets = len(self.result.columns)
        weights = np.zeros((n, number_of_assets))
        exp_returns = np.zeros(n)
        exp_volatilities = np.zeros(n)
        sharpe_ratios = np.zeros(n)

        # Calculate fundamental weights based on P/E ratios
        fundamental_weights = np.zeros(number_of_assets)  
        available_pe_ratios = []

        for i, t in enumerate(self.ticker):
            pe = self.pe_ratios.get(t)
            if pe and pe > 0:
                # Earnings yield (1/PE): higher is better
                earnings_yield = 1 / pe
                fundamental_weights[i] = earnings_yield
                available_pe_ratios.append(earnings_yield)
        
        # Normalize fundamental weights. higher multiplier = more deterministic. dirichlet_multiplier knobs for how concentrated vs exploratory the sampling is.
        #α << 1 → spiky, many corner weights (0/1-like). α = 1 → truly uniform. α >> 1 → concentrated around equal weights
        fundamental_weights = fundamental_weights / np.sum(fundamental_weights) * (dirichlet_multiplier * number_of_assets)

        # missing P/E ratios or equal fundamental weights
        if len(available_pe_ratios) < number_of_assets or equal_fundamental_weights:
            # If ANY stocks missing P/E, use equal weights (fallback)
            print("Using equal weights. Uniform distribution applied")
            fundamental_weights = np.ones(number_of_assets)

        # Create 30000 random portfolios biased by P/E ratios
        for i in range(n):
            weight = np.random.dirichlet(fundamental_weights)

            weights[i] = weight #storing all combinations of weights
            exp_returns[i] = np.sum(self.result.mean() * weight)*BUSINESS_DAYS   #expected 425d weighted mean return
            exp_volatilities[i] = np.sqrt(np.dot(weight.T, np.dot(self.result.cov()*BUSINESS_DAYS, weight)))  # expected 425d weighted volatility, considering dependences between stock returns
            sharpe_ratios[i] = exp_returns[i]/exp_volatilities[i]
        print(f"Max Sharpe Ratio: {sharpe_ratios.max()}")
        return pd.DataFrame(data = weights[np.argmax(sharpe_ratios)], index = self.ticker).rename(columns={0:"%"})
