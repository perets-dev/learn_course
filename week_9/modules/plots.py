
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import (
    adjusted_rand_score, normalized_mutual_info_score, silhouette_samples
)
from sklearn.tree import DecisionTreeClassifier, export_text

from modules.style import (
    GREEN, BLUE, GRAY, ERROR_RED, WHITE,
    CHURN_COLOR, HIGHLIGHT_LINE, NOISE_COLOR, 
    NOISE_EDGE, DIVERGING_CMAP, 
    SEQUENTIAL_CMAP, 
    cluster_color, cluster_colors, category_color
)
FEATURE_RU = {
    "log_income": "доход (log)",
    "log_savings_ratio": "баланс / доход (log)",
    "credit_sco": "кредитный рейтинг",
    "age": "возраст",
    "account_age_months": "стаж, мес.",
    "nums_card": "число карт",
    "nums_service": "число услуг",
    "sqrt_recency": "давность активности (√дней)",
    "tn_to_income": "оборот / доход",
}


def _legend_for(labels, names=None, ax=None, loc="best", ncol=1):
    handles = []
    for l in sorted(np.unique(labels)):
        label = "шум" if l < 0 else (names.get(l, f"кластер {l}") if names else f"кластер {l}")
        handles.append(Patch(facecolor=cluster_color(l), edgecolor=NOISE_EDGE if l < 0 else "none", label=label))
    (ax or plt.gca()).legend(handles=handles, loc=loc, fontsize=8, ncol=ncol)


def plot_embedding(emb, labels, ax=None, title="", s=4, legend=True, names=None):
    '''Точки 2D-проекции, раскрашенные по кластерам (шум рисуется снизу и серым).'''
    labels = np.asarray(labels)
    ax = ax or plt.subplots(figsize=(7, 6))[1]
    noise = labels < 0
    if noise.any():
        ax.scatter(emb[noise, 0], emb[noise, 1], s=s, c=NOISE_COLOR, alpha=0.5, linewidths=0)
    ax.scatter(emb[~noise, 0], emb[~noise, 1], s=s, c=cluster_colors(labels[~noise]), alpha=0.7, linewidths=0)
    ax.set_title(title); ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    if legend and len(np.unique(labels)) <= 12:
        _legend_for(labels, names, ax)
    return ax


def align_labels(reference, labels):
    '''Переименовывает кластеры labels так, чтобы они максимально совпадали с reference (венгерский алгоритм).
    Нужна только для согласованной раскраски разных алгоритмов; шум (-1) не трогаем.'''
    reference, labels = np.asarray(reference), np.asarray(labels)
    uniq = [l for l in np.unique(labels) if l >= 0]
    ref_uniq = [l for l in np.unique(reference) if l >= 0]
    overlap = np.array([[np.sum((labels == a) & (reference == b)) for b in ref_uniq] for a in uniq])
    rows, cols = linear_sum_assignment(-overlap)
    mapping = {uniq[r]: ref_uniq[c] for r, c in zip(rows, cols)}
    free = iter(range(max(ref_uniq) + 1, max(ref_uniq) + 1 + len(uniq)))
    return np.array([l if l < 0 else mapping.get(l, None) if l in mapping else next(free) for l in labels])


def plot_algorithms_grid(names, emb, labels_source, n_points=None, ncols=4, reference=None):
    '''Сетка 2D-проекций для нескольких алгоритмов (метки берутся из RESULTS, первые n_points — это VIS).
    reference — имя алгоритма, под метки которого подгоняются цвета остальных.'''
    n_points = n_points or len(emb)
    nrows = int(np.ceil(len(names) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.6 * ncols, 4.3 * nrows))
    for ax, name in zip(axes.ravel(), names):
        r = labels_source[name]
        lab = r["labels"][:n_points]
        if reference is not None:
            lab = align_labels(labels_source[reference]["labels"][:n_points], lab)
        plot_embedding(emb, lab, ax=ax, s=3, legend=False,
                       title=f"{name}\nk={r['n_clusters']}, sil={r['silhouette']:.2f}, шум={r['noise_share']:.0%}")
    for ax in axes.ravel()[len(names):]:
        ax.axis("off")
    fig.tight_layout()
    return fig


def knee_point(x, y):
    '''Простейший Kneedle: точка кривой, максимально удалённая от хорды между её концами.'''
    x, y = np.asarray(x, float), np.asarray(y, float)
    xn = (x - x.min()) / (x.max() - x.min())
    yn = (y - y.min()) / (y.max() - y.min())
    x0, y0, x1, y1 = xn[0], yn[0], xn[-1], yn[-1]
    dist = np.abs((y1 - y0) * xn - (x1 - x0) * yn + x1 * y0 - y1 * x0) / np.hypot(y1 - y0, x1 - x0)
    return x[int(np.argmax(dist))]


def plot_k_selection(metrics, chosen_k=None, title=""):
    '''Панели выбора k: локоть, silhouette, CH, DB и устойчивость (если есть).'''
    cols = [c for c in ["inertia", "silhouette", "calinski_harabasz", "davies_bouldin", "stability_ari", "bic"]
            if c in metrics.columns]
    better = {"inertia": "↓ локоть", "silhouette": "↑", "calinski_harabasz": "↑", "davies_bouldin": "↓",
              "stability_ari": "↑", "bic": "↓"}
    fig, axes = plt.subplots(1, len(cols), figsize=(4.2 * len(cols), 3.8))
    for ax, c in zip(np.atleast_1d(axes), cols):
        ax.plot(metrics.index, metrics[c], "o-", color=GREEN if c != "stability_ari" else BLUE, lw=2)
        if chosen_k is not None:
            ax.axvline(chosen_k, color=HIGHLIGHT_LINE, lw=3, alpha=0.8)
        ax.set_title(f"{c} ({better[c]})"); ax.set_xlabel("k")
        ax.set_xticks(metrics.index)
    if title:
        fig.suptitle(title, fontsize=13, fontweight="bold")
    fig.tight_layout()
    return fig


def plot_silhouette_diagram(X_, labels, ax=None, title="Silhouette по объектам"):
    '''Классическая диаграмма silhouette: отсортированные значения для каждого кластера.'''
    labels = np.asarray(labels)
    mask = labels >= 0
    X_, labels = X_[mask], labels[mask]
    sil = silhouette_samples(X_, labels)
    ax = ax or plt.subplots(figsize=(7, 5))[1]
    y = 0
    for l in np.unique(labels):
        v = np.sort(sil[labels == l])
        ax.fill_betweenx(np.arange(y, y + len(v)), 0, v, color=cluster_color(l), alpha=0.85)
        ax.text(-0.05, y + len(v) / 2, str(l), ha="right", va="center", fontsize=9, fontweight="bold")
        y += len(v) + 40
    ax.axvline(sil.mean(), color=ERROR_RED, ls="--", label=f"среднее = {sil.mean():.3f}")
    ax.set_yticks([]); ax.set_xlabel("silhouette"); ax.set_title(title); ax.legend(loc="lower right")
    return ax


def plot_cluster_sizes(labels, ax=None, names=None, title="Размеры кластеров"):
    labels = np.asarray(labels)
    vc = pd.Series(labels).value_counts().sort_index()
    ax = ax or plt.subplots(figsize=(6, 4))[1]
    ticks = ["шум" if l < 0 else (names.get(l, str(l)) if names else str(l)) for l in vc.index]
    ax.bar(ticks, vc.values, color=cluster_colors(vc.index))
    for i, v in enumerate(vc.values):
        ax.text(i, v, f"{v / len(labels):.0%}", ha="center", va="bottom", fontsize=9)
    ax.set_title(title); ax.set_ylabel("объектов")
    if names:
        ax.tick_params(axis="x", rotation=20)
    return ax


def cluster_profile(X_df, labels):
    '''Средние стандартизованных признаков по кластерам (шум исключён).'''
    labels = np.asarray(labels)
    mask = labels >= 0
    return X_df[mask].groupby(labels[mask]).mean()


def plot_profile_heatmap(profile, ax=None, title="Профиль кластеров (среднее z-score признака)", names=None):
    ax = ax or plt.subplots(figsize=(12, 0.6 * len(profile) + 2))[1]
    prof = profile.rename(columns=FEATURE_RU)
    if names:
        prof = prof.rename(index=lambda i: f"{i}: {names.get(i, '')}")
    sns.heatmap(prof, annot=True, fmt=".2f", cmap=DIVERGING_CMAP, center=0, vmin=-1.5, vmax=1.5,
                linewidths=0.5, linecolor=WHITE, ax=ax, cbar_kws={"label": "σ от среднего по train"})
    ax.grid(False); ax.set_title(title); ax.set_ylabel("кластер")
    ax.tick_params(axis="x", rotation=30)
    return ax


def plot_radar(profile, names=None, title="Радар профилей кластеров", clip=1.5):
    '''Радар-диаграмма: одна «паутинка» на кластер, оси — признаки модели (z-score, обрезанный по ±clip).'''
    feats = list(profile.columns)
    angles = np.linspace(0, 2 * np.pi, len(feats), endpoint=False).tolist()
    angles += angles[:1]
    n = len(profile)
    fig, axes = plt.subplots(1, n, figsize=(4.2 * n, 4.4), subplot_kw={"polar": True})
    for ax, (cl, row) in zip(np.atleast_1d(axes), profile.iterrows()):
        vals = row.clip(-clip, clip).tolist()
        vals += vals[:1]
        ax.plot(angles, [0] * len(angles), color=GRAY, lw=1, ls="--")
        ax.plot(angles, vals, color=cluster_color(cl), lw=2)
        ax.fill(angles, vals, color=cluster_color(cl), alpha=0.35)
        ax.set_xticks(angles[:-1]); ax.set_xticklabels([FEATURE_RU[f] for f in feats], fontsize=7)
        ax.set_ylim(-clip, clip); ax.set_yticklabels([])
        ax.set_title(f"{cl}: {names.get(cl, '')}" if names else f"кластер {cl}", fontsize=10, pad=14)
    fig.suptitle(title, fontsize=13, fontweight="bold")
    fig.tight_layout()
    return fig


def plot_numeric_by_cluster(meta, labels, cols, log_cols=(), ncols=4, names=None, title=""):
    '''Боксплоты исходных (немасштабированных) признаков по кластерам.'''
    labels = np.asarray(labels)
    nrows = int(np.ceil(len(cols) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.4 * ncols, 3.6 * nrows))
    order = sorted(np.unique(labels))
    for ax, col in zip(axes.ravel(), cols):
        data = [meta.loc[labels == l, col].dropna().to_numpy() for l in order]
        bp = ax.boxplot(data, patch_artist=True, showfliers=False, widths=0.6,
                        medianprops=dict(color="black"))
        for patch, l in zip(bp["boxes"], order):
            patch.set_facecolor(cluster_color(l)); patch.set_alpha(0.85)
        ax.set_xticks(range(1, len(order) + 1))
        ax.set_xticklabels(["шум" if l < 0 else str(l) for l in order])
        if col in log_cols:
            ax.set_yscale("log")
        ax.set_title(col)
    for ax in axes.ravel()[len(cols):]:
        ax.axis("off")
    if title:
        fig.suptitle(title, fontsize=13, fontweight="bold")
    fig.tight_layout()
    return fig


def plot_categorical_by_cluster(meta, labels, col, order=None, ax=None, names=None, palette=None):
    '''100%-stacked bar: состав каждого кластера по категориальному признаку.'''
    labels = np.asarray(labels)
    ct = pd.crosstab(labels, meta[col], normalize="index")
    if order is not None:
        ct = ct[[o for o in order if o in ct.columns]]
    ax = ax or plt.subplots(figsize=(7, 4))[1]
    left = np.zeros(len(ct))
    for i, c in enumerate(ct.columns):
        color = palette[i % len(palette)] if palette else category_color(i)
        ax.barh(range(len(ct)), ct[c], left=left, color=color, label=str(c), edgecolor=WHITE)
        for j, v in enumerate(ct[c]):
            if v > 0.07:
                ax.text(left[j] + v / 2, j, f"{v:.0%}", ha="center", va="center", fontsize=8)
        left += ct[c].to_numpy()
    ax.set_yticks(range(len(ct)))
    ax.set_yticklabels([("шум" if l < 0 else (f"{l}: {names[l]}" if names else f"кластер {l}")) for l in ct.index])
    ax.invert_yaxis(); ax.set_xlim(0, 1); ax.grid(False)
    ax.set_title(f"Состав кластеров: {col}")
    ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=8)
    return ax


def plot_churn_by_cluster(meta, labels, ax=None, names=None, title="Доля оттока (exit) по кластерам"):
    labels = np.asarray(labels)
    rate = meta["exit"].groupby(labels).mean()
    ax = ax or plt.subplots(figsize=(6, 4))[1]
    ticks = ["шум" if l < 0 else (names.get(l, str(l)) if names else str(l)) for l in rate.index]
    ax.bar(ticks, rate.values, color=cluster_colors(rate.index), edgecolor=CHURN_COLOR, linewidth=1.5)
    ax.axhline(meta["exit"].mean(), color=CHURN_COLOR, ls="--", label=f"в среднем {meta['exit'].mean():.0%}")
    for i, v in enumerate(rate.values):
        ax.text(i, v + 0.005, f"{v:.1%}", ha="center", fontsize=9, fontweight="bold")
    ax.set_title(title); ax.set_ylabel("доля ушедших"); ax.legend()
    if names:
        ax.tick_params(axis="x", rotation=20)
    return ax


def plot_crosstab(a, b, a_name, b_name, ax=None, normalize="index"):
    '''Тепловая карта сопряжённости двух разбиений (по умолчанию доли внутри строк).'''
    ct = pd.crosstab(pd.Series(a, name=a_name), pd.Series(b, name=b_name), normalize=normalize)
    ax = ax or plt.subplots(figsize=(6, 4))[1]
    sns.heatmap(ct, annot=True, fmt=".2f", cmap=SEQUENTIAL_CMAP, vmin=0, vmax=1, ax=ax, cbar=False,
                linewidths=0.5, linecolor=WHITE)
    ax.grid(False)
    ax.set_title(f"{a_name} × {b_name}\nARI = {adjusted_rand_score(a, b):.3f}, NMI = {normalized_mutual_info_score(a, b):.3f}")
    return ax


def surrogate_tree(meta, labels, feature_cols, **tree_kwargs):
    '''Дерево решений, предсказывающее кластер по исходным признакам: даёт читаемые правила.'''
    labels = np.asarray(labels)
    mask = labels >= 0
    tree = DecisionTreeClassifier(**tree_kwargs)
    tree.fit(meta.loc[mask, feature_cols], labels[mask])
    acc = tree.score(meta.loc[mask, feature_cols], labels[mask])
    rules = export_text(tree, feature_names=list(feature_cols), decimals=1)
    return tree, acc, rules


def cluster_report(X_df, meta, labels, emb=None, emb_labels=None, names=None, title=""):
    '''Сводный отчёт по разбиению: размеры, профиль, отток, silhouette и 2D-проекция.'''
    fig, axes = plt.subplots(1, 3, figsize=(20, 4.5), gridspec_kw={"width_ratios": [1, 1, 1.2]})
    plot_cluster_sizes(labels, ax=axes[0], names=names)
    plot_churn_by_cluster(meta, labels, ax=axes[1], names=names)
    if emb is not None:
        plot_embedding(emb, emb_labels, ax=axes[2], names=names, title="2D-проекция (t-SNE)")
    else:
        axes[2].axis("off")
    if title:
        fig.suptitle(title, fontsize=13, fontweight="bold")
    fig.tight_layout()
    plt.show()
    fig, ax = plt.subplots(figsize=(13, 0.55 * len(np.unique(labels)) + 2.2))
    plot_profile_heatmap(cluster_profile(X_df, labels), ax=ax, names=names)
    plt.show()
