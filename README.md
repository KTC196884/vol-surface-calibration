# Volatility Surface Calibration

A Python package and set of scripts to preprocess option data, compute implied volatilities, calibrate the SVI model, compute volatility metrics, and generate publication-quality plots for equity/options markets.

## 1. Project Structure

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
│   └── processed/
│
├── src/
│   └── vol_surface_calibration/  # pip-installable package
│       ├── __init__.py
│       ├── config.py             # 外部設定
│       ├── data_preprocessor.py  # 資料預處理
│       ├── iv_calculator.py      # implied volatility
│       ├── svi_calibrator.py     # SVI
│       ├── linear_vol_calculator.py # for vol metrics of underlying/futures
│       └── visualization/
│           ├── svi_plotter.py    # SVI plot
│           └── vol_plotter.py    # vol plot
│
├── scripts/                # CLI 腳本
│   ├── 0_run_data_preprocessor.py     # 執行資料預處理
│   ├── 1_run_iv_calculator.py         # 執行隱含波動率計算
│   ├── 2_run_svi_calibrator.py        # 執行 SVI 校準
│   ├── 3_run_linear_vol_calculator.py # 計算線性波動率指標
│   ├── 4_run_svi_plotter.py           # SVI 繪圖器
│   └── 5_run_vol_plotter.py           # 波動率繪圖器
│
├── tests/                  # 核心模組單元測試
│   ├── test_preprocessor.py
│   ├── test_iv_calculator.py
│   ├── test_svi_calibrator.py
│   └── test_metrics_calculator.py
│
└── results/                # 輸出結果
    └── figures/
```
---

## 2. requirements.txt
```text
numpy>=1.21.0,<2.0
pandas>=1.3.0,<2.0
scipy>=1.7.0,<2.0
matplotlib>=3.4.0,<4.0
plotly>=5.0.0,<6.0
```
---

## 3. Installation

1. 建議先建立並啟動虛擬環境：
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. 安裝必要套件：
   ```bash
   pip install -r requirements.txt
   ```
---

## 4. Usage

### 作為套件引用
```python
from vol_surface_calibration import preprocessor, iv_calculator, svi_calibrator

# 示例流程
df = preprocessor.load_and_clean("data/raw/options.csv")
iv_df = iv_calculator.compute_iv(df)
params = svi_calibrator.calibrate(iv_df, expiry="2023-07-21")
```

### 執行命令列腳本
```bash
# 預處理資料
python scripts/0_run_data_preprocessor.py --input data/raw --output data/processed

# 計算隱含波動率
python scripts/1_run_iv_calculator.py --input data/processed --output results/figures

# 執行 SVI 校準
python scripts/2_run_svi_calibrator.py --iv results/figures/iv.csv --output results/figures

# 計算線性波動率指標
python scripts/3_run_linear_vol_calculator.py --params results/figures/params.csv --output results/figures

# SVI 繪圖器
python scripts/4_run_svi_plotter.py --input results/figures --output results/figures

# 波動率繪圖器
python scripts/5_run_vol_plotter.py --input results/figures --output results/figures
```
