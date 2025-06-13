import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.stats import linregress
from scipy.stats import spearmanr, rankdata

def plot_dual_axis(
    x,
    y1,
    y2,
    xlabel: str,
    y1_label: str,
    y2_label: str,
    legend_labels: tuple,
    title: str,
    output_path: str,
    color1: str = 'tab:blue',
    color2: str = 'tab:orange'
) -> None:
    fig, ax1 = plt.subplots(figsize=(12, 6))
    fig.suptitle(title)

    # 左軸
    ax1.plot(x, y1, color=color1, label=legend_labels[0])
    ax1.set_xlabel(xlabel)
    ax1.set_ylabel(y1_label, color=color1)
    ax1.tick_params(axis='y', colors=color1)
    ax1.legend(loc='upper left')
    
    # 右軸
    ax2 = ax1.twinx()
    ax2.plot(x, y2, color=color2, label=legend_labels[1])
    ax2.set_ylabel(y2_label, color=color2)
    ax2.tick_params(axis='y', colors=color2)
    ax2.legend(loc='upper right')
    
    # X 軸時間格式化為 HH:MM
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    fig.autofmt_xdate()
    
    # 加上網格 (顯示在背景)
    ax1.grid(True)
    
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_shared_axes(
    x,
    y1,
    y2,
    xlabel: str,
    ylabel: str,
    legend_labels: tuple,
    title: str,
    output_path: str,
    color1: str = 'tab:blue',
    color2: str = 'tab:orange'
) -> None:
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.suptitle(title)
    
    ax.plot(x, y1, label=legend_labels[0], color=color1)
    ax.plot(x, y2, label=legend_labels[1], color=color2)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    fig.autofmt_xdate()
    
    ax.grid(True)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)

def plot_standardised_scatter(
    x: pd.Series,
    y: pd.Series,
    xlabel: str,
    ylabel: str,
    title: str,
    output_path: str
) -> None:
    # 1. 去除缺值
    mask = x.notna() & y.notna()
    x_clean, y_clean = x[mask], y[mask]
    if x_clean.empty:
        raise ValueError("Input series contain no overlapping non-NaN data.")

    # 2. Z-score 標準化
    x_z = (x_clean - x_clean.mean()) / x_clean.std(ddof=0)
    y_z = (y_clean - y_clean.mean()) / y_clean.std(ddof=0)

    # 3. 線性回歸與相關係數
    slope, intercept, r_value, *_ = linregress(x_z, y_z)

    # 4. 取對稱範圍（以 0 為中心）
    max_abs = max(abs(x_z).max(), abs(y_z).max())
    x_min, x_max = -max_abs * 1.05, max_abs * 1.05 # 全圖左右邊界
    reg_x = np.array([x_min, x_max]) # 讓直線貫穿整幅圖
    reg_y = slope * reg_x + intercept

    # 5. 繪圖
    fig, ax = plt.subplots(figsize=(8, 8))
    fig.suptitle(title)

    # 散點
    ax.scatter(x_z, y_z, s=10, alpha=0.8)

    # 回歸直線
    ax.plot(reg_x, reg_y, linewidth=2, color="tab:orange")

    # 軸設定：同一尺度、0 為中心
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(x_min, x_max)
    ax.set_aspect("equal", adjustable="box")

    # 標籤與格線
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True)

    # 相關係數文字：左上角
    ax.text(
        0.02, 0.98,
        f"Pearson r = {r_value:.3f}",
        transform=ax.transAxes,
        ha="left", va="top",
        fontsize=12,
        bbox=dict(boxstyle="round,pad=0.2", alpha=0.2)
    )

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    
def plot_rank_scatter(
    x: pd.Series,
    y: pd.Series,
    xlabel: str,
    ylabel: str,
    title: str,
    output_path: str,
    marker_size: int = 20,
    alpha: float = 0.7,
):
    # 1. 去缺值
    mask = x.notna() & y.notna()
    x0, y0 = x[mask], y[mask]
    if x0.empty:
        raise ValueError("No overlapping non-NaN data.")
    # 2. 计算秩
    rx = rankdata(x0)     # 返回 1…N 的秩
    ry = rankdata(y0)
    # 3. Spearman ρ
    rho, pval = spearmanr(x0, y0)
    # 4. 绘图
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(rx, ry, s=marker_size, alpha=alpha)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    # 对角线：完美单调时所有点都在 y=x
    lim = max(rx.max(), ry.max())
    ax.plot([1, lim], [1, lim], linestyle='--', linewidth=1, color='grey')
    ax.grid(True)
    # 相關係數文字：左上角
    ax.text(
        0.02, 0.98,
        f"Spearmann rho = {rho:.3f}",
        transform=ax.transAxes,
        ha="left", va="top",
        fontsize=12,
        bbox=dict(boxstyle="round,pad=0.2", alpha=0.2)
    )
    
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)