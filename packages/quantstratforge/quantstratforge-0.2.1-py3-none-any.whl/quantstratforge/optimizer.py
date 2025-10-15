from .utils import logger

class Optimizer:
    def __init__(self, backtester):
        self.backtester = backtester

    def optimize(self, strategy_code: str, params: dict):
        try:
            best_sharpe = -float('inf')
            best_params = {}
            for param_key, values in params.items():
                for val in values:
                    optimized_code = strategy_code.replace(f"{{{param_key}}}", str(val))
                    results = self.backtester.backtest(optimized_code)
                    if results["sharpe_ratio"] > best_sharpe:
                        best_sharpe = results["sharpe_ratio"]
                        best_params[param_key] = val
            logger.info("Optimization complete")
            return {"best_params": best_params, "best_sharpe": best_sharpe, "explanation": "Optimized via grid search for max Sharpe."}
        except Exception as e:
            logger.error(f"Optimization failure: {e}")
            raise