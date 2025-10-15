import argparse
from .data_prep import DataFetcher
from .model import StrategyModel
from .generator import StrategyGenerator
from .backtester import Backtester
from .optimizer import Optimizer

def main():
    parser = argparse.ArgumentParser(description="QuantStratForge CLI")
    subparsers = parser.add_subparsers(dest="command")

    prep = subparsers.add_parser("prepare")
    prep.set_defaults(func=lambda args: DataFetcher().prepare_data())

    train = subparsers.add_parser("train")
    train.add_argument("--federated", action="store_true")
    train.set_defaults(func=lambda args: StrategyModel().federated_train() if args.federated else StrategyModel().train_local())

    gen = subparsers.add_parser("generate")
    gen.add_argument("--ticker", default="AAPL")
    gen.add_argument("--news", default="Positive sentiment.")
    gen.set_defaults(func=lambda args: print(StrategyGenerator().generate(f"Time-Series: {DataFetcher().get_time_series(args.ticker)}\nNews: {args.news}")))

    backtest = subparsers.add_parser("backtest")
    backtest.add_argument("--strategy_code", required=True)
    backtest.set_defaults(func=lambda args: print(Backtester().backtest(args.strategy_code)))

    opt = subparsers.add_parser("optimize")
    opt.add_argument("--strategy_code", required=True)
    opt.add_argument("--params", default='{"threshold": [0.01, 0.02, 0.03]}')
    opt.set_defaults(func=lambda args: print(Optimizer(Backtester()).optimize(args.strategy_code, eval(args.params))))

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()