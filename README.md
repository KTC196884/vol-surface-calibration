vol_surface_calibration/
│
├── README.md
├── requirements.txt
├── requirements-dev.txt   # (optional)
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
│       ├── preprocessor.py       # 資料預處理
│       ├── iv_calculator.py      # 隱含波動率計算
│       ├── svi_calibrator.py     # SVI 校準
│       ├── metrics_calculator.py # 波動率指標計算
│       └── visualization/        # 視覺化功能
│           ├── svi_plotter.py    # SVI 繪圖
│           └── vol_plotter.py    # 波動率繪圖
│
├── scripts/                # CLI 腳本
│   ├── 0_run_data_preprocessor.py     # 執行資料預處理
│   ├── 1_run_iv_calculator.py # 執行隱含波動率計算
│   ├── 2_run_svi_calibrator.py       # 執行 SVI 校準
│   ├── 3_run_linear_vol_calculator.py     # 執行指標計算
|   ├── 4_run_svi_plotter.py
│   └── 5_run_vol_plotter.py
│
├── tests/                  # 核心模組單元測試
│   ├── test_preprocessor.py
│   ├── test_iv_calculator.py
│   ├── test_svi_calibrator.py
│   └── test_metrics_calculator.py
│
└── results/                # 輸出結果
    └── figures/

1. 建議先建立並啟動虛擬環境：
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate

2. pip install -r requirements.txt
