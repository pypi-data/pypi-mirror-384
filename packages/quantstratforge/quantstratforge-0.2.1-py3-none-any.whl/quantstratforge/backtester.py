import yfinance as yf
import pandas as pd
import ast
import types
from .utils import logger

class Backtester:
    def __init__(self, ticker="AAPL", period="1y"):
        self.ticker = ticker
        self.period = period
        self.data = None

    def fetch_data(self):
        try:
            self.data = yf.download(self.ticker, period=self.period)
            
            if isinstance(self.data.columns, pd.MultiIndex):
                self.data.columns = self.data.columns.get_level_values(0)
            
            logger.info(f"Data fetched for {self.ticker}")
            return self.data
        except Exception as e:
            logger.error(f"Data fetch failed for {self.ticker}: {e}")
            raise

    def normalize_signals(self, signals):
        if isinstance(signals, pd.Series):
            if signals.dtype == 'bool':
                return signals.astype(int)
            elif signals.dtype == 'object':
                return signals.apply(lambda x: 1 if x == 'Buy' else 0)
        elif isinstance(signals, pd.DataFrame):
            signals = signals.iloc[:, 0]
            return self.normalize_signals(signals)
        return signals

    def backtest(self, strategy_code):
        try:
            if self.data is None:
                self.fetch_data()

            if isinstance(strategy_code, str):
                module = types.ModuleType("strategy_module")
                module.__dict__['pd'] = pd
                module.__dict__['np'] = __import__('numpy')
                exec(strategy_code, module.__dict__)
                if not hasattr(module, 'strategy_func'):
                    raise ValueError("strategy_code must define a function named 'strategy_func'")
                strategy_func = module.strategy_func
            elif callable(strategy_code):
                strategy_func = strategy_code
            else:
                raise ValueError("strategy_code must be a string defining 'strategy_func' or a callable function")

            signals = strategy_func(self.data.copy())
            signals = self.normalize_signals(signals)
            if not isinstance(signals, (pd.Series, pd.DataFrame)) or len(signals) != len(self.data):
                raise ValueError("strategy_func must return a pandas Series/DataFrame of same length as data")

            if isinstance(signals, pd.DataFrame):
                signals = signals.iloc[:, 0]
            
            signals = signals.reindex(self.data.index)
            
            close_prices = self.data['Close']
            returns = close_prices.pct_change() * signals.shift(1)
            
            sharpe = returns.mean() / returns.std() * (252 ** 0.5) if returns.std() != 0 else 0
            cum_returns = returns.cumsum().iloc[-1] if not returns.empty else 0
            logger.info(f"Backtest complete for {self.ticker}")
            return {"sharpe_ratio": sharpe, "cum_returns": cum_returns}
        except Exception as e:
            logger.error(f"Backtest error: {e}")
            raise