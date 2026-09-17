import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.model_selection import GroupKFold

from modules import style as ss


_markers = ['o', '^', 'v', 'D', 's', '*']

_fold_colors = ss.FOLD_COLORS
_cm = ss.CATEGORY_PALETTE
class_colors = {0: ss.category_color(0), 1: ss.category_color(1), 2: ss.category_color(2)}


def discrete_scatter(
    x1, x2,
    y=None, markers=None, ax=None,
    labels=None, alpha=1,
    markeredgewidth=None
):
    if ax is None:
        ax = plt.gca()
    if y is None:
        y = np.zeros(len(x1))
    unique_y = np.unique(y)
    markers = markers or _markers
    labels = labels if labels is not None else unique_y
    for i, yy in enumerate(unique_y):
        mask = y == yy
        ax.plot(
            np.asarray(x1)[mask], np.asarray(x2)[mask],
            markers[i % len(markers)], markersize=6,
            label=str(labels[i]), alpha=alpha,
            c=_cm[i % len(_cm)], markeredgecolor='k',
            markeredgewidth=markeredgewidth or 0.6, linestyle=''
        )
    return ax


def plot_cross_validation(n_splits=5, n_samples=25, ax=None):
    colors = _fold_colors
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 3))
    fold_size = n_samples / n_splits
    for it in range(n_splits):
        for s in range(n_samples):
            fold = int(s // fold_size)
            color = colors["test"] if fold == it else colors["train"]
            ax.add_patch(Rectangle((s, n_splits - it - 1), 1, 1,
                                    facecolor=color, edgecolor="white"))
    ax.set_xlim(0, n_samples); ax.set_ylim(0, n_splits)
    ax.set_yticks(np.arange(n_splits) + 0.5)
    ax.set_yticklabels([f"Разбиение {n_splits - i}" for i in range(n_splits)])
    ax.set_xticks([]); ax.set_xlabel("Примеры данных (в порядке индекса)")
    handles = [mpatches.Patch(color=colors["train"], label="обучающий блок"),
                mpatches.Patch(color=colors["test"], label="тестовый блок")]
    ax.legend(handles=handles, loc=(1.01, 0.3))
    ax.set_title(f"K-блочная кросс-проверка (k={n_splits})")
    return ax


def plot_stratified_cross_validation(n_splits=3):
    """Сравнение KFold и StratifiedKFold.

    Цвет клетки = класс объекта (как и раньше). Дополнительно: объекты,
    попавшие в тестовый блок на данной итерации, помечаются лёгким
    полупрозрачным крестиком поверх цвета класса — так видно одновременно
    и класс объекта, и его роль (train/test) на конкретном разбиении.
    """
    y = np.array([0]*3 + [1]*3 + [2]*3 + [0]*3 + [1]*3 + [2]*3)
    n = len(y)
    fig, axes = plt.subplots(2, 1, figsize=(10, 4.3))
    for ax, splitter, title in zip(
            axes, [KFold(n_splits=n_splits), StratifiedKFold(n_splits=n_splits)],
            ["KFold (без учёта классов)", "StratifiedKFold (с учётом классов)"]
        ):
        for it, (_, te) in enumerate(splitter.split(np.zeros(n), y)):
            for s in range(n):
                is_test = s in te
                cx, cy = s + 0.5, n_splits - it - 1 + 0.5
                ax.add_patch(
                    Rectangle(
                        (s, n_splits - it - 1), 1, 1,
                        facecolor=class_colors[y[s]],
                        edgecolor='white', linewidth=0.5,
                    )
                )
                if is_test:
                    ax.plot(cx, cy, marker='x', color=ss.BLACK,
                            markersize=8, markeredgewidth=1.4, alpha=0.75)
        ax.set_xlim(0, n)
        ax.set_ylim(0, n_splits)
        ax.set_xticks([])
        ax.set_xlabel("Примеры данных (отсортированы по классу)")
        ax.set_yticks(np.arange(n_splits) + 0.5)
        ax.set_yticklabels([f"разб. {n_splits - i}" for i in range(n_splits)])
        ax.set_title(title)

    class_handles = [mpatches.Patch(color=class_colors[c], label=f"класс {c}")
                      for c in sorted(class_colors)]
    test_handle = ss.test_marker_legend_handle(label="тестовые данные\n(на этой итерации)")
    fig.legend(handles=class_handles + [test_handle],
               loc="center left", bbox_to_anchor=(1.0, 0.5))
    fig.tight_layout()
    return axes


def plot_shuffle_split(n_samples=20, n_splits=4, train_size=10, test_size=5):
    """Схема ShuffleSplit.

    По оси X — индекс объекта в исходном датасете (порядок как в массиве
    данных, никак не связан с классом или временем). На каждой строке —
    одна независимая случайная итерация: часть объектов случайно попадает
    в обучающий блок, часть — в тестовый, а часть может не попасть ни
    туда, ни туда ("не используется") — в отличие от KFold, где каждый
    объект гарантированно тестируется ровно один раз.
    """
    colors = _fold_colors
    rng = np.random.RandomState(0)
    _, ax = plt.subplots(figsize=(10, 3.2))
    for it in range(n_splits):
        idx = rng.permutation(n_samples)
        train_idx = set(idx[:train_size])
        test_idx = set(idx[train_size:train_size + test_size])
        for s in range(n_samples):
            color = colors["train"] if s in train_idx else (
                colors["test"] if s in test_idx else colors["unused"])
            ax.add_patch(Rectangle((s, n_splits - it - 1), 1, 1,
                                    facecolor=color, edgecolor="white"))
    ax.set_xlim(0, n_samples); ax.set_ylim(0, n_splits)
    ax.set_yticks(np.arange(n_splits) + 0.5)
    ax.set_yticklabels([f"Итерация {n_splits - i}" for i in range(n_splits)])
    ax.set_xticks(np.arange(0, n_samples, 2))
    ax.set_xlabel("Индекс объекта в датасете (порядок в исходном массиве данных)")
    handles = [mpatches.Patch(color=colors["train"], label="обучающий"),
                mpatches.Patch(color=colors["test"], label="тестовый"),
                mpatches.Patch(color=colors["unused"], label="не используется\nна этой итерации")]
    ax.legend(handles=handles, loc=(1.01, 0.2))
    ax.set_title("ShuffleSplit: на каждой итерации — новый случайный поднабор train/test")
    return ax


def plot_group_kfold(groups=None, n_splits=3):
    """Схема GroupKFold.

    Верхняя полоса — принадлежность каждого объекта к группе (цвет =
    номер группы, с легендой). Нижняя часть — сами разбиения: цвет
    клетки — та же группа, что и в верхней полосе (единая цветовая
    кодировка на обоих графиках), а объекты тестового блока на данной
    итерации дополнительно помечаются лёгким крестиком поверх цвета их
    группы. По оси X — индекс объекта в датасете. Обратите внимание:
    все объекты одной группы (одного цвета) на любой итерации
    оказываются целиком либо в train, либо в test (то есть крестиками
    помечены объекты либо всей группы целиком, либо ни одной) — ни
    одна группа не оказывается "разрезанной" между ними.
    """
    if groups is None:
        groups = np.array(
            [0, 0, 0, 1, 1, 2, 2, 2, 3, 3, 4, 4]
        )
    n = len(groups)
    unique_groups = sorted(set(groups))
    group_color_map = {g: ss.category_color(i) for i, g in enumerate(unique_groups)}

    fig, (ax_g, ax) = plt.subplots(2, 1, figsize=(10, 4.2),
                                    gridspec_kw={"height_ratios": [1, 3]})
    for s in range(n):
        ax_g.add_patch(Rectangle((s, 0), 1, 1, facecolor=group_color_map[groups[s]],
                                    edgecolor="white"))
    ax_g.set_xlim(0, n); ax_g.set_ylim(0, 1); ax_g.set_xticks([])
    ax_g.set_yticks([0.5]); ax_g.set_yticklabels(["Группа"])
    ax_g.set_title("Принадлежность объектов к группам (например, id пациента/пользователя)")

    gkf = GroupKFold(n_splits=n_splits)
    for it, (_, te) in enumerate(gkf.split(np.zeros(n), groups=groups)):
        for s in range(n):
            is_test = s in te
            color = group_color_map[groups[s]]
            cx, cy = s + 0.5, n_splits - it - 1 + 0.5
            ax.add_patch(Rectangle((s, n_splits - it - 1), 1, 1, facecolor=color,
                                    edgecolor="white"))
            if is_test:
                ax.plot(cx, cy, marker='x', color=ss.BLACK,
                        markersize=8, markeredgewidth=1.4, alpha=0.75)
    ax.set_xlim(0, n); ax.set_ylim(0, n_splits); ax.set_xticks([])
    ax.set_xlabel("Индекс объекта в датасете")
    ax.set_yticks(np.arange(n_splits) + 0.5)
    ax.set_yticklabels([f"разб. {n_splits - i}" for i in range(n_splits)])
    ax.set_title("GroupKFold: вся группа целиком попадает либо в train, либо в test")

    group_handles = [mpatches.Patch(color=group_color_map[g], label=f"группа {g}")
                      for g in unique_groups]
    test_handle = ss.test_marker_legend_handle(label="тестовые объекты\n(на этой итерации)")
    fig.legend(handles=group_handles + [test_handle], title="Цвет = номер группы",
               loc="center left", bbox_to_anchor=(1.0, 0.5))
    fig.tight_layout()
    return (ax_g, ax)


def plot_time_series_split(n_points=30, n_splits=5, max_train_size=None, ax=None,
                            title=None):
    """Схема TimeSeriesSplit. Если max_train_size задан — показывает
    вариант со скользящим окном фиксированного размера, иначе —
    стандартный вариант с расширяющимся ("кумулятивным") train."""
    from sklearn.model_selection import TimeSeriesSplit

    tscv = TimeSeriesSplit(n_splits=n_splits, max_train_size=max_train_size)
    if ax is None:
        _, ax = plt.subplots(figsize=(9, 3))
    for i, (train_idx, test_idx) in enumerate(tscv.split(np.arange(n_points))):
        ax.scatter(train_idx, [i] * len(train_idx), color=_fold_colors["train"],
                   marker="s", s=25)
        ax.scatter(test_idx, [i] * len(test_idx), color=_fold_colors["test"],
                   marker="s", s=25)
    ax.set_yticks(range(n_splits))
    ax.set_yticklabels([f"Разбиение {i}" for i in range(n_splits)])
    ax.set_xlabel("Индекс наблюдения (время →)")
    default_title = ("TimeSeriesSplit со скользящим окном (max_train_size="
                      f"{max_train_size})" if max_train_size
                      else "TimeSeriesSplit с расширяющимся окном (по умолчанию)")
    ax.set_title(title or default_title)
    handles = [mpatches.Patch(color=_fold_colors["train"], label="train"),
               mpatches.Patch(color=_fold_colors["test"], label="test")]
    ax.legend(handles=handles, loc=(1.01, 0.3))
    return ax


def plot_grid_search_overview():
    _, ax = plt.subplots(figsize=(10, 5))
    ax.axis("off")
    boxes = [
        (0.05, 0.75, "Обучающая\nвыборка"), (0.05, 0.35, "Тестовая\nвыборка"),
        (0.32, 0.75, "Сетка\nгиперпараметров"),
        (0.58, 0.75, "Кросс-валидация\nдля каждой\nкомбинации"),
        (0.58, 0.35, "Лучшая\nкомбинация\nпараметров"),
        (0.84, 0.55, "Переобучение на\nвсей обучающей\nвыборке")
    ]
    for x, y, text in boxes:
        ax.add_patch(
            mpatches.FancyBboxPatch((x, y), 0.18, 0.18,
            boxstyle="round,pad=0.02", fc=ss.MINT, ec=ss.GREEN_DARK, lw=1.5)
        )
        ax.text(x+0.09, y+0.09, text, ha="center", va="center", fontsize=9,
                color=ss.BLACK)
    arrows = [
        ((0.23, 0.84),(0.32, 0.84)),
        ((0.5, 0.84),(0.58, 0.84)),
        ((0.67, 0.75),(0.67, 0.53)),
        ((0.76, 0.44),(0.84, 0.6)),
        ((0.23, 0.44),(0.84, 0.6))
    ]
    for (x0, y0),(x1, y1) in arrows:
        ax.annotate(
            "", xy=(x1,y1), xytext=(x0,y0),
            arrowprops=dict(arrowstyle="->", lw=1.5, color=ss.GREEN)
        )
    ax.text(
        0.67, 0.2,
        "Оценка на отложенной тестовой выборке\n(один раз, в самом конце)",
        ha="center",
        fontsize=9,
        style="italic"
    )
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0.1, 1)
    ax.set_title("Общая схема Grid Search с перекрёстной проверкой")
    return ax


def plot_cross_val_selection(
        scores_grid,
        param1_name, param1_range,
        param2_name, param2_range,
        best_idx=None
):
    """Тепловая карта результатов Grid Search."""
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(scores_grid, cmap=ss.CMAP)
    ax.set_xticks(range(len(param2_range)))
    ax.set_xticklabels(param2_range, rotation=45)
    ax.set_yticks(range(len(param1_range)))
    ax.set_yticklabels(param1_range)
    ax.set_xlabel(param2_name)
    ax.set_ylabel(param1_name)
    fig.colorbar(im, ax=ax, label="средняя правильность CV")
    if best_idx is not None:
        ax.scatter(
            [best_idx[1]], [best_idx[0]],
            marker=ss.CHECK_MARKER, s=500,
            c=ss.WHITE, edgecolor="black", linewidth=1.3,
            label="лучшая комбинация"
        )
        ax.legend(loc="upper right", handles=[ss.check_legend_handle(color=ss.WHITE)])
    ax.set_title("Результаты Grid Search (тепловая карта cv-оценок)")
    fig.tight_layout()
    return ax
