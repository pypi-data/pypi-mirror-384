# 📈 QuantStratForge

[![PyPI version](https://badge.fury.io/py/quantstratforge.svg)](https://badge.fury.io/py/quantstratforge)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Downloads](https://pepy.tech/badge/quantstratforge)](https://pepy.tech/project/quantstratforge)

**Privacy-preserving agentic SLM for quant strategy forging**

QuantStratForge is the first AI-powered quantitative strategy development platform that combines federated learning with privacy-preserving techniques to generate, backtest, and optimize trading strategies without compromising sensitive financial data.

## 🌟 Key Features

- **🤖 AI Strategy Generation**: Generate trading strategies using advanced language models
- **🔒 Privacy-Preserving**: Federated learning ensures your data never leaves your machine
- **📊 Comprehensive Backtesting**: Built-in backtesting engine with performance metrics
- **⚡ Strategy Optimization**: Automated parameter optimization for maximum returns
- **🌐 Multiple Interfaces**: CLI, Streamlit web app, and FastAPI REST API
- **📈 Real-time Data**: Integration with Yahoo Finance for live market data
- **🎯 Risk Management**: Built-in risk assessment and portfolio optimization

## 🚀 Quick Start

### Installation

```bash
pip install quantstratforge
```

### Basic Usage

```python
from quantstratforge import DataFetcher, StrategyGenerator, Backtester, Optimizer

# 1. Fetch market data
fetcher = DataFetcher()
data = fetcher.get_time_series("AAPL")

# 2. Generate AI strategy
generator = StrategyGenerator()
strategy = generator.generate(f"Market data for AAPL: {data}")

# 3. Backtest strategy
backtester = Backtester(ticker="AAPL")
results = backtester.backtest(strategy["strategy_code"])

# 4. Optimize parameters
optimizer = Optimizer(backtester)
optimized = optimizer.optimize(strategy["strategy_code"], {
    "threshold": [0.01, 0.02, 0.03],
    "period": [10, 15, 20]
})

print(f"Sharpe Ratio: {results['sharpe_ratio']:.3f}")
print(f"Best Parameters: {optimized['best_params']}")
```

## 🖥️ Demo Applications

### Streamlit Web App
Interactive web interface for strategy development:

```bash
# Install demo dependencies
pip install quantstratforge[demo]

# Run Streamlit demo
streamlit run demos/streamlit_demo.py
```

### FastAPI REST API
RESTful API for programmatic access:

```bash
# Run FastAPI demo
python demos/fastapi_demo.py
```

**API Documentation**: Visit `http://localhost:8000/docs` for interactive API documentation.

### Command Line Interface

```bash
# Prepare training data
quantstratforge prepare

# Train model (local or federated)
quantstratforge train --federated

# Generate strategy
quantstratforge generate --ticker AAPL --news "Positive earnings outlook"

# Backtest strategy
quantstratforge backtest --strategy_code "def strategy_func(df): ..."

# Optimize strategy
quantstratforge optimize --strategy_code "..." --params '{"threshold": [0.01, 0.02]}'
```

## 🏗️ Architecture

### Core Components

- **DataFetcher**: Handles market data acquisition and preprocessing
- **StrategyModel**: Manages AI model training (local and federated)
- **StrategyGenerator**: Generates trading strategies using trained models
- **Backtester**: Executes backtesting with performance analysis
- **Optimizer**: Optimizes strategy parameters for maximum returns

### Federated Learning

QuantStratForge uses Flower (Federated Learning Framework) to enable collaborative model training:

```python
# Federated training with multiple clients
model = StrategyModel()
model.federated_train(
    num_clients=3,
    num_rounds=5,
    data_path="./formatted_data"
)
```

## 📊 Performance Metrics

### Backtesting Results
- **Sharpe Ratio**: Risk-adjusted return metric
- **Cumulative Returns**: Total portfolio performance
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Volatility**: Standard deviation of returns

### Optimization Metrics
- **Parameter Sensitivity**: How strategy performance varies with parameters
- **Convergence Speed**: Time to find optimal parameters
- **Robustness**: Performance across different market conditions

## 🔧 Advanced Usage

### Custom Strategy Development

```python
def custom_strategy(df):
    """Custom trading strategy implementation"""
    # Calculate technical indicators
    df['MA_20'] = df['Close'].rolling(20).mean()
    df['RSI'] = calculate_rsi(df['Close'])
    
    # Generate signals
    signals = (df['Close'] > df['MA_20']) & (df['RSI'] < 70)
    return signals.astype(int)

# Backtest custom strategy
backtester = Backtester(ticker="AAPL")
results = backtester.backtest(custom_strategy)
```

### Federated Learning Setup

```python
# Configure federated learning
from quantstratforge.model import StrategyModel

model = StrategyModel(
    model_name="mistralai/Mistral-7B-Instruct-v0.2",
    lora_r=16
)

# Start federated training
model.federated_train(
    num_clients=5,
    num_rounds=10,
    client_resources={"num_cpus": 2, "num_gpus": 0.5}
)
```

### API Integration

```python
import requests

# Generate strategy via API
response = requests.post("http://localhost:8000/api/generate-strategy", json={
    "ticker": "AAPL",
    "risk_level": "medium",
    "news_sentiment": "Positive market sentiment"
})

strategy = response.json()
print(strategy["strategy_code"])
```

## 📈 Use Cases

### Individual Traders
- Generate personalized trading strategies
- Backtest ideas before live trading
- Optimize parameters for maximum returns
- Learn quantitative trading concepts

### Financial Institutions
- Develop proprietary trading algorithms
- Collaborate on model training without data sharing
- Scale strategy development across teams
- Maintain regulatory compliance

### Research Organizations
- Study market behavior patterns
- Develop new quantitative methods
- Publish research with reproducible results
- Collaborate with industry partners

## 🔒 Privacy & Security

### Data Protection
- **Local Processing**: All sensitive data stays on your machine
- **Federated Learning**: Models trained without sharing raw data
- **Encryption**: All communications encrypted in transit
- **Audit Trail**: Complete logging of all operations

### Compliance
- **GDPR**: Full compliance with European data protection regulations
- **SOX**: Meets Sarbanes-Oxley requirements for financial data
- **PCI DSS**: Secure handling of financial information
- **Custom**: Configurable for specific regulatory requirements

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Install development dependencies
pip install quantstratforge[dev]

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=quantstratforge --cov-report=html
```

## 📚 Documentation

- [API Reference](docs/api.md)
- [Federated Learning Guide](docs/federated_learning.md)
- [Strategy Development Tutorial](docs/tutorial.md)
- [Deployment Guide](docs/deployment.md)
- [Contributing Guidelines](CONTRIBUTING.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-username/quantstratforge.git
cd quantstratforge

# Install in development mode
pip install -e ".[dev,demo]"

# Run tests
pytest

# Format code
black .
ruff check . --fix
```

## 📄 License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.

## 🆘 Support

- **Documentation**: [https://quantstratforge.readthedocs.io](https://quantstratforge.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/quantstratforge/quantstratforge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/quantstratforge/quantstratforge/discussions)

## 🌟 Acknowledgments

- [Hugging Face](https://huggingface.co/) for transformer models
- [Flower](https://flower.dev/) for federated learning framework
- [Streamlit](https://streamlit.io/) for web application framework
- [FastAPI](https://fastapi.tiangolo.com/) for REST API framework
- [Yahoo Finance](https://finance.yahoo.com/) for market data

## 📊 Statistics

![GitHub stars](https://img.shields.io/github/stars/your-username/quantstratforge)
![GitHub forks](https://img.shields.io/github/forks/your-username/quantstratforge)
![GitHub issues](https://img.shields.io/github/issues/your-username/quantstratforge)
![GitHub pull requests](https://img.shields.io/github/issues-pr/your-username/quantstratforge)

---

**Made with ❤️ for the quantitative finance community**

*QuantStratForge - Where AI meets Privacy in Quantitative Trading*