import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from modules import style as st


def setup_style():
    """Apply the shared plot style to all figures in the notebook."""
    st.apply_default_style()


def plot_target_overview(y, area, target_name="Урожайность, кг"):
    """Target overview: distribution, relation to field area, and yield per hectare."""
    y, area = np.asarray(y, float), np.asarray(area, float)
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.2))

    axes[0].hist(y, bins=30, color=st.BLUE, edgecolor=st.WHITE)
    axes[0].set(title="Распределение урожайности", xlabel=target_name, ylabel="Число полей")

    axes[1].scatter(area, y, s=10, alpha=0.4, color=st.GREEN)
    axes[1].set(title="Урожайность ∝ площади поля", xlabel="Hectares", ylabel=target_name)

    axes[2].hist(y / area, bins=30, color=st.GREEN_DARK, edgecolor=st.WHITE)
    axes[2].set(title="Урожайность с гектара", xlabel="кг / га", ylabel="Число полей")
    fig.tight_layout()
    plt.show()


def plot_box_by(df, value_col, by_cols, ncols=3, ylabel=None, title=None, hline=None):
    """Grid of boxplots: distribution of value_col within each category of every column in by_cols."""
    nrows = int(np.ceil(len(by_cols) / ncols))
    fig, axes = plt.subplots(
        nrows, ncols, 
        figsize=(5.3 * ncols, 3.8 * nrows), 
        squeeze=False
    )
    for ax, col in zip(axes.ravel(), by_cols):
        groups = sorted(df[col].dropna().unique())
        data = [df.loc[df[col] == g, value_col].to_numpy() for g in groups]
        bp = ax.boxplot(
            data, patch_artist=True, widths=0.6,
            medianprops={"color": st.BLACK},
            flierprops={"markersize": 3, "markerfacecolor": st.GRAY}
        )
        for i, patch in enumerate(bp["boxes"]):
            patch.set_facecolor(st.category_color(i))
            patch.set_alpha(0.75)
        labels = [str(g) for g in groups]
        rotate = len(groups) > 3 and max(len(lb) for lb in labels) > 4
        ax.set_xticks(
            range(1, len(groups) + 1), labels,
            rotation=30 if rotate else 0, 
            ha="right" if rotate else "center"
        )
        ax.set_title(col)
        ax.set_ylabel(ylabel or value_col)
        if hline is not None:
            ax.axhline(hline, color=st.GREEN_DARK, lw=1)
    for ax in axes.ravel()[len(by_cols):]:
        ax.set_visible(False)
    if title:
        fig.suptitle(title, fontweight="bold")
    fig.tight_layout()
    plt.show()


def plot_corr_heatmap(corr, title="Корреляции"):
    """Correlation heatmap using the style's diverging colormap."""
    n = len(corr)
    fig, ax = plt.subplots(figsize=(0.42 * n + 3, 0.42 * n + 2))
    im = ax.imshow(corr.values, cmap=st.DIVERGING_CMAP, vmin=-1, vmax=1)
    ax.set_xticks(range(n), corr.columns, rotation=90, fontsize=8)
    ax.set_yticks(range(n), corr.index, fontsize=8)
    ax.grid(False)
    fig.colorbar(im, ax=ax, shrink=0.8)
    ax.set_title(title)
    fig.tight_layout()
    plt.show()


def plot_cv_comparison(results, label_col, mean_col, std_col=None, xlabel="MAE, кг",
                       title="Сравнение на кросс-валидации", lower_is_better=True):
    """Horizontal bars with fold-to-fold spread; the best option is highlighted in green."""
    res = results.sort_values(mean_col, ascending=not lower_is_better).reset_index(drop=True)
    best = res[mean_col].idxmin() if lower_is_better else res[mean_col].idxmax()
    colors = [st.GREEN if i == best else st.BLUE for i in res.index]
    fig, ax = plt.subplots(figsize=(9, 0.5 * len(res) + 1.5))
    ax.barh(
        res[label_col], res[mean_col], color=colors,
        xerr=res[std_col] if std_col else None, 
        ecolor=st.GRAY, capsize=3
    )
    pad = res[std_col].fillna(0) if std_col else pd.Series(0.0, index=res.index)
    offset = 0.01 * res[mean_col].max()
    for i, (v, e) in enumerate(zip(res[mean_col], pad)):
        ax.text(
            v + e + offset, i, 
            f"{v:,.0f}".replace(",", " "), 
            va="center", fontsize=9
        )
    ax.set_xlim(0, (res[mean_col] + pad).max() * 1.12)
    ax.invert_yaxis()
    ax.set(xlabel=xlabel, title=title)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    plt.show()


def plot_pred_vs_true(y_true, y_pred, title="Прогноз vs факт", unit="кг"):
    """Scatter plot of predicted vs. actual values with the perfect-prediction line."""
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    lo, hi = min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(y_true, y_pred, s=12, alpha=0.5, color=st.BLUE, label="поля")
    ax.plot([lo, hi], [lo, hi], color=st.GREEN_DARK, lw=2, label="идеальный прогноз")
    ax.set(xlabel=f"Факт, {unit}", ylabel=f"Прогноз, {unit}", title=title)
    ax.legend()
    fig.tight_layout()
    plt.show()


def plot_residual_diagnostics(y_true, y_pred, unit="кг"):
    """Three standard residual plots: histogram, Q-Q plot, residuals vs. prediction."""
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    resid = y_true - y_pred
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.3))

    axes[0].hist(resid, bins=30, color=st.BLUE, edgecolor=st.WHITE)
    axes[0].axvline(0, color=st.GREEN_DARK, lw=2)
    axes[0].axvline(
        resid.mean(), color=st.ERROR_RED, lw=1.5, ls="--",
        label=f"среднее = {resid.mean():,.0f}".replace(",", " ")
    )
    axes[0].set(
        title="Распределение остатков", 
        xlabel=f"Факт − прогноз, {unit}", ylabel="Число полей"
    )
    axes[0].legend()

    (osm, osr), (slope, intercept, _) = stats.probplot(resid, dist="norm")
    axes[1].scatter(osm, osr, s=10, alpha=0.6, color=st.BLUE)
    axes[1].plot(osm, slope * osm + intercept, color=st.GREEN_DARK, lw=2)
    axes[1].set(
        title="Q-Q plot остатков", 
        xlabel="Теоретические квантили N(0,1)", 
        ylabel=f"Остатки, {unit}"
    )

    axes[2].scatter(y_pred, resid, s=10, alpha=0.5, color=st.BLUE)
    axes[2].axhline(0, color=st.GREEN_DARK, lw=2)
    axes[2].set(
        title="Остатки vs прогноз", 
        xlabel=f"Прогноз, {unit}", 
        ylabel=f"Остатки, {unit}"
    )
    fig.tight_layout()
    plt.show()


def plot_residuals_by_group(frame, resid_col, by_cols, ylabel="Остаток, кг", title=None):
    """Boxplots of residuals by category, to spot systematic bias."""
    plot_box_by(
        frame, resid_col, by_cols, 
        ncols=min(3, len(by_cols)),
        ylabel=ylabel, title=title, hline=0
    )


def plot_feature_importance(
        importances, top=15, 
        title="Важность признаков", 
        xlabel="Важность"
    ):
    """Horizontal bar chart of feature importances (pd.Series: name -> value)."""
    imp = pd.Series(importances).sort_values(ascending=False).head(top)[::-1]
    fig, ax = plt.subplots(figsize=(8, 0.38 * len(imp) + 1.2))
    ax.barh(imp.index, imp.values, color=st.GREEN)
    ax.set(title=title, xlabel=xlabel)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    plt.show()
