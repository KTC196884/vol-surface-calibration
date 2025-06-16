# Implied Volatility Calibration

A Python package and set of scripts to preprocess option data, compute implied volatilities, calibrate the SVI model, compute volatility metrics, and generate publication-quality plots for equity/options markets.

## Project Structure

```text
vol_surface_calibration/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── data/                  # 原始、中間、處理後資料
│   ├── raw/
│   ├── interim/
│   └── final/
│
├── src/
│   └── vol_surface_calibration/  # pip-installable package
│       ├── __init__.py
│       ├── config.py
│       ├── data_preprocessor.py
│       ├── svi_calibrator.py 
│       └── visualization/
│           └── svi_plotter.py
│
├── scripts/                # CLI 腳本
│   ├── run_data_preprocessor.py
│   ├── run_svi_calibrator.py
│   └── run_svi_plotter.py
│
├── tests/                  # 核心模組單元測試
│   ├── test_data_preprocessor.py
│   ├── test_svi_calibrator.py
│   └── test_svi_plotter.py
│
└── results/
```

### requirements.txt

```text
numpy>=1.21.0,<2.0
pandas>=1.3.0,<2.0
scipy>=1.7.0,<2.0
matplotlib>=3.4.0,<4.0
plotly>=5.0.0,<6.0
```
---

## Installation

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### As a Python package
```python
from vol_surface_calibration import data_preprocessor, svi_calibrator

# Example workflow
df = data_preprocessor.load_and_clean("data/raw/options.csv")
iv_df = data_preprocessor.compute_iv(df)
params = svi_calibrator.calibrate(iv_df)
```

### CLI scripts
```bash
# Preprocess data
python scripts/run_data_preprocessor.py --input data/raw --output data/final

# Calibrate SVI model
python scripts/run_svi_calibrator.py --input data/final --output results

# Generate SVI plots
python scripts/run_svi_plotter.py --input results --output results
```

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.