import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.model_selection import GroupKFold
from matplotlib.colors import ListedColormap
from sklearn.base import clone

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


def plot_bootstrap_samples(n_original=10, n_samples=6, random_state=0):
    """Иллюстрация бутстрэп-сэмплирования: из исходного набора объектов
    (верхняя строка) несколько раз случайно выбираются n_original
    объектов **с возвращением** — некоторые объекты попадают в выборку
    по несколько раз, а некоторые не попадают вовсе ("out-of-bag").
    Число под каждой ячейкой — сколько раз объект встретился в этом
    бутстрэп-наборе (0 — объект не попал, "out-of-bag" для этого набора).
    """
    rng = np.random.RandomState(random_state)
    fig, axes = plt.subplots(n_samples + 1, 1, figsize=(10, 0.6 * (n_samples + 1) + 1))

    ax0 = axes[0]
    for s in range(n_original):
        ax0.add_patch(Rectangle((s, 0), 1, 1, facecolor=ss.GRAY_LIGHT, edgecolor="white"))
        ax0.text(s + 0.5, 0.5, str(s), ha="center", va="center", fontsize=9)
    ax0.set_xlim(0, n_original); ax0.set_ylim(0, 1)
    ax0.set_xticks([]); ax0.set_yticks([0.5]); ax0.set_yticklabels(["Исходные\nданные"])

    for i in range(n_samples):
        ax = axes[i + 1]
        draw = rng.randint(0, n_original, size=n_original)
        counts = np.bincount(draw, minlength=n_original)
        for s in range(n_original):
            c = counts[s]
            color = ss.GRAY_LIGHT if c == 0 else (
                ss.GREEN if c == 1 else ss.GREEN_DARK)
            ax.add_patch(Rectangle((s, 0), 1, 1, facecolor=color, edgecolor="white"))
            ax.text(s + 0.5, 0.5, str(c), ha="center", va="center", fontsize=9,
                    color="white" if c >= 1 else "black")
        oob = np.sum(counts == 0)
        ax.set_xlim(0, n_original); ax.set_ylim(0, 1)
        ax.set_xticks([]); ax.set_yticks([0.5])
        ax.set_yticklabels([f"Набор {i + 1}\n(OOB: {oob})"])

    handles = [mpatches.Patch(color=ss.GRAY_LIGHT, label="0 раз (out-of-bag)"),
               mpatches.Patch(color=ss.GREEN, label="1 раз"),
               mpatches.Patch(color=ss.GREEN_DARK, label="2+ раз")]
    fig.legend(handles=handles, loc="center left", bbox_to_anchor=(1.0, 0.5))
    fig.suptitle("Бутстрэп-сэмплирование: выбор с возвращением", y=1.02)
    fig.tight_layout()
    return axes


def _mesh_grid(X, pad=1.0, n=200):
    x_min, x_max = X[:, 0].min() - pad, X[:, 0].max() + pad
    y_min, y_max = X[:, 1].min() - pad, X[:, 1].max() + pad
    xx, yy = np.meshgrid(np.linspace(x_min, x_max, n), np.linspace(y_min, y_max, n))
    return xx, yy


def plot_decision_boundary(model, X, y, ax=None, title=None, fit=True):
    """Область решений одной модели на 2D-данных (заливка = предсказанный
    класс, точки = обучающие объекты, цвет точки = истинный класс)."""
    if ax is None:
        _, ax = plt.subplots(figsize=(5, 4.5))
    if fit:
        model.fit(X, y)
    xx, yy = _mesh_grid(X)
    Z = model.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)
    classes = np.unique(y)
    cmap_bg = ListedColormap([ss.category_color(i) for i in range(len(classes))])
    ax.contourf(xx, yy, Z, alpha=0.25, cmap=cmap_bg)
    discrete_scatter(X[:, 0], X[:, 1], y, ax=ax)
    ax.set_xticks([]); ax.set_yticks([])
    if title:
        ax.set_title(title)
    ax.get_legend().remove() if ax.get_legend() else None
    return ax


def plot_decision_boundaries_grid(models, X, y, ncols=3, figsize_per=(4.2, 4)):
    """Сетка областей решений для нескольких моделей сразу — удобно
    сравнивать, например, одно дерево vs бэггинг vs случайный лес.

    models : dict {название: sklearn-модель (ещё не обученная)}
    """
    n = len(models)
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols,
                              figsize=(figsize_per[0] * ncols, figsize_per[1] * nrows))
    axes = np.atleast_1d(axes).ravel()
    for ax, (name, model) in zip(axes, models.items()):
        plot_decision_boundary(model, X, y, ax=ax, title=name)
    for ax in axes[n:]:
        ax.axis("off")
    fig.tight_layout()
    return axes


def plot_prediction_variance(build_model_fn, X, y, x_query, n_runs=30,
                              random_state=0, labels=("одна модель", "ансамбль")):
    """Показывает эмпирически, как усреднение по ансамблю снижает
    разброс (дисперсию) предсказаний в одной и той же точке `x_query`
    по сравнению с одиночной моделью.

    build_model_fn(random_state) -> (single_model, ensemble_model) —
    функция, создающая пару необученных моделей (одиночную и ансамблевую)
    с заданным random_state.
    """
    rng = np.random.RandomState(random_state)
    single_preds, ensemble_preds = [], []
    n = len(X)
    for _ in range(n_runs):
        boot_idx = rng.randint(0, n, size=n)
        Xb, yb = X[boot_idx], y[boot_idx]
        single_model, ensemble_model = build_model_fn(rng.randint(0, 10_000))
        single_model.fit(Xb, yb)
        ensemble_model.fit(Xb, yb)
        single_preds.append(single_model.predict([x_query])[0])
        ensemble_preds.append(ensemble_model.predict([x_query])[0])

    fig, ax = plt.subplots(figsize=(6, 4))
    data = [single_preds, ensemble_preds]
    bp = ax.boxplot(data, patch_artist=True, labels=list(labels), widths=0.5)
    for patch, color in zip(bp["boxes"], [ss.BLUE, ss.GREEN]):
        patch.set_facecolor(color); patch.set_alpha(0.5)
    ax.set_ylabel(f"Предсказание в точке {tuple(round(float(v), 2) for v in x_query)}")
    ax.set_title(f"Разброс предсказаний по {n_runs} бутстрэп-переобучениям\n"
                 f"std: {labels[0]}={np.std(single_preds):.3f}, "
                 f"{labels[1]}={np.std(ensemble_preds):.3f}")
    fig.tight_layout()
    return ax


def plot_oob_error_curve(n_estimators_list, oob_scores, test_scores=None,
                          ylabel="Правильность", title="OOB-оценка vs число деревьев"):
    """Кривая OOB-оценки (и, опционально, оценки на отдельном тесте) в
    зависимости от числа деревьев в ансамбле."""
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(n_estimators_list, oob_scores, marker="o", color=ss.OOB_LINE, label="OOB-оценка")
    if test_scores is not None:
        ax.plot(n_estimators_list, test_scores, marker="s", color=ss.TEST_LINE,
                linestyle="--", label="Оценка на тесте")
    ax.set_xlabel("Число деревьев (n_estimators)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    return ax


def plot_feature_importances(importances, feature_names, title="Важность признаков",
                              top_n=None, ax=None):
    """Горизонтальная столбчатая диаграмма важности признаков (для
    RandomForest/GradientBoosting/... — атрибут `.feature_importances_`)."""
    order = np.argsort(importances)
    if top_n is not None:
        order = order[-top_n:]
    if ax is None:
        _, ax = plt.subplots(figsize=(6, max(3, 0.35 * len(order))))
    ax.barh(np.array(feature_names)[order], np.array(importances)[order], color=ss.GREEN)
    ax.set_xlabel("Важность")
    ax.set_title(title)
    fig = ax.figure
    fig.tight_layout()
    return ax


def plot_boosting_sequential_fit(X, y, n_stages=4, max_depth=1, learning_rate=1.0):
    """Иллюстрация идеи бустинга на 1D-регрессии: на каждом шаге новое
    слабое дерево обучается предсказывать **остаток** (residual) текущего
    ансамбля, и его (взвешенный) прогноз добавляется к общей сумме.
    Показывает n_stages первых шагов."""
    from sklearn.tree import DecisionTreeRegressor

    order = np.argsort(X[:, 0])
    X, y = X[order], y[order]
    residual = y.copy()
    ensemble_pred = np.zeros_like(y, dtype=float)

    fig, axes = plt.subplots(n_stages, 1, figsize=(7, 2.6 * n_stages), sharex=True)
    axes = np.atleast_1d(axes)
    for stage in range(n_stages):
        tree = DecisionTreeRegressor(max_depth=max_depth, random_state=0)
        tree.fit(X, residual)
        stage_pred = tree.predict(X)
        ensemble_pred = ensemble_pred + learning_rate * stage_pred
        residual = y - ensemble_pred

        ax = axes[stage]
        ax.scatter(X[:, 0], y, s=12, color=ss.GRAY, alpha=0.5, label="исходные данные")
        ax.plot(X[:, 0], ensemble_pred, color=ss.GREEN, lw=2,
                label=f"сумма после {stage + 1} шаг(ов)")
        ax.plot(X[:, 0], stage_pred, color=ss.BLUE, lw=1.3, linestyle="--",
                label=f"новое дерево (шаг {stage + 1}), обучено на остатке")
        ax.set_title(f"Шаг {stage + 1}: mse остатка = {np.mean(residual ** 2):.3f}")
        ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    return axes


def plot_staged_error_curve(model, X_train, y_train, X_test, y_test,
                             metric_func=None, ylabel="Ошибка", title=None):
    """Кривая train/test ошибки в зависимости от числа итераций бустинга
    — использует `staged_predict` уже обученной модели (AdaBoost /
    GradientBoosting). Хорошо показывает переобучение при слишком
    большом числе итераций."""
    if metric_func is None:
        metric_func = lambda y_true, y_pred: np.mean(y_true != y_pred)

    train_errors = [metric_func(y_train, pred) for pred in model.staged_predict(X_train)]
    test_errors = [metric_func(y_test, pred) for pred in model.staged_predict(X_test)]

    fig, ax = plt.subplots(figsize=(7, 4))
    iters = np.arange(1, len(train_errors) + 1)
    ax.plot(iters, train_errors, color=ss.TRAIN_LINE, label="train")
    ax.plot(iters, test_errors, color=ss.ERROR_RED, label="test")
    best_it = int(np.argmin(test_errors)) + 1
    ax.axvline(best_it, color=ss.NEUTRAL_LINE, linestyle=":",
               label=f"минимум ошибки на test (итерация {best_it})")
    ax.set_xlabel("Число итераций бустинга")
    ax.set_ylabel(ylabel)
    ax.set_title(title or "Train/test ошибка по мере роста числа итераций")
    ax.legend()
    fig.tight_layout()
    return ax


def plot_bias_variance_schematic():
    """Схематичная (концептуальная, не по реальным данным) иллюстрация
    того, что бэггинг в первую очередь снижает разброс (variance)
    ансамбля, а бустинг — смещение (bias) отдельных слабых моделей."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    rng = np.random.RandomState(0)
    x = np.linspace(0, 10, 200)
    true_fn = np.sin(x)

    ax = axes[0]
    ax.plot(x, true_fn, color="black", lw=2, label="истинная зависимость")
    for i in range(6):
        noisy_fit = true_fn + rng.normal(scale=0.6, size=x.shape) * np.exp(-0.02 * (x - 5) ** 2) \
            + rng.normal(scale=0.35)
        ax.plot(x, np.sin(x + rng.normal(scale=0.15)) + rng.normal(scale=0.25),
                color=ss.BLUE, alpha=0.25, lw=1)
    avg = np.mean([np.sin(x + rng.normal(scale=0.15)) + rng.normal(scale=0.25)
                    for _ in range(200)], axis=0)
    ax.plot(x, avg, color=ss.GREEN, lw=2, label="усреднение по ансамблю (бэггинг)")
    ax.set_title("Бэггинг: усреднение множества\nвысоко-дисперсных моделей → меньше разброс")
    ax.legend(fontsize=8)
    ax.set_xticks([]); ax.set_yticks([])

    ax = axes[1]
    ax.plot(x, true_fn, color="black", lw=2, label="истинная зависимость")
    from sklearn.tree import DecisionTreeRegressor as _DTR
    X2 = x.reshape(-1, 1)
    y2 = true_fn + rng.normal(scale=0.15, size=x.shape)
    residual = y2.copy()
    approx = np.zeros_like(x)
    n_stages = 40
    checkpoints = {2: ss.BLUE, 8: ss.GREEN, 40: ss.GREEN_DARK}
    for stage in range(1, n_stages + 1):
        tree = _DTR(max_depth=1, random_state=stage)
        tree.fit(X2, residual)
        approx = approx + 0.3 * tree.predict(X2)
        residual = y2 - approx
        if stage in checkpoints:
            ax.plot(x, approx, color=checkpoints[stage], alpha=0.85, lw=1.6,
                    label=f"сумма после {stage} слабых моделей")
    ax.set_title("Бустинг: последовательное уточнение\nостатков → меньше смещение")
    ax.legend(fontsize=7)
    ax.set_xticks([]); ax.set_yticks([])

    fig.tight_layout()
    return axes


def plot_stacking_architecture(base_names, meta_name="Мета-модель"):
    """Схема архитектуры стэкинга: несколько базовых моделей уровня 0,
    чьи предсказания становятся признаками для мета-модели уровня 1."""
    n = len(base_names)
    fig, ax = plt.subplots(figsize=(8, 1.4 * n + 2))
    ax.axis("off")

    input_xy = (0.05, 0.5)
    ax.add_patch(mpatches.FancyBboxPatch((input_xy[0], input_xy[1] - 0.08), 0.14, 0.16,
                 boxstyle="round,pad=0.02", fc=ss.GRAY_LIGHT, ec="black"))
    ax.text(input_xy[0] + 0.07, input_xy[1], "Исходные\nпризнаки X",
            ha="center", va="center", fontsize=9)

    base_ys = np.linspace(0.85, 0.15, n)
    for i, (name, y) in enumerate(zip(base_names, base_ys)):
        x = 0.36
        ax.add_patch(mpatches.FancyBboxPatch((x, y - 0.075), 0.22, 0.15,
                     boxstyle="round,pad=0.02", fc=ss.base_model_color(i), ec="black",
                     alpha=0.85))
        ax.text(x + 0.11, y, name, ha="center", va="center", fontsize=9, color="white")
        ax.annotate("", xy=(x, y), xytext=(input_xy[0] + 0.14, input_xy[1]),
                    arrowprops=dict(arrowstyle="->", lw=1.2, color=ss.NEUTRAL_LINE))

    meta_x, meta_y = 0.74, 0.5
    ax.add_patch(mpatches.FancyBboxPatch((meta_x, meta_y - 0.09), 0.2, 0.18,
                 boxstyle="round,pad=0.02", fc=ss.GREEN, ec="black"))
    ax.text(meta_x + 0.1, meta_y, meta_name, ha="center", va="center", fontsize=9,
            color="white")
    for x, y in zip([0.36 + 0.22] * n, base_ys):
        ax.annotate("", xy=(meta_x, meta_y), xytext=(x, y),
                    arrowprops=dict(arrowstyle="->", lw=1.2, color=ss.NEUTRAL_LINE))

    out_x = meta_x + 0.32
    ax.annotate("", xy=(out_x, meta_y), xytext=(meta_x + 0.2, meta_y),
                arrowprops=dict(arrowstyle="->", lw=1.5, color=ss.GREEN_DARK))
    ax.text(out_x + 0.02, meta_y, "Итоговое\nпредсказание", ha="left", va="center", fontsize=9)

    ax.set_xlim(0, 1.1); ax.set_ylim(0, 1)
    ax.set_title("Архитектура стэкинга: базовые модели уровня 0 → мета-модель уровня 1")
    return ax


def plot_oof_scheme(n_folds=5, n_samples=15):
    """Схема получения out-of-fold (OOF) предсказаний базовой модели —
    именно они, а не предсказания на своём же train, используются как
    признаки для мета-модели в корректной реализации стэкинга (так же
    внутри работает StackingClassifier/StackingRegressor)."""
    fig, ax = plt.subplots(figsize=(9, 0.55 * n_folds + 1.5))
    fold_size = n_samples / n_folds
    for it in range(n_folds):
        for s in range(n_samples):
            fold = int(s // fold_size)
            color = ss.GREEN if fold == it else ss.MINT
            ax.add_patch(Rectangle((s, n_folds - it - 1), 1, 1, facecolor=color,
                                    edgecolor="white"))
    ax.set_xlim(0, n_samples); ax.set_ylim(0, n_folds)
    ax.set_xticks([])
    ax.set_yticks(np.arange(n_folds) + 0.5)
    ax.set_yticklabels([f"Блок {n_folds - i}" for i in range(n_folds)])
    ax.set_xlabel("Объекты обучающей выборки")
    handles = [mpatches.Patch(color=ss.MINT, label="модель обучается"),
               mpatches.Patch(color=ss.GREEN,
                               label="OOF-предсказание\n(модель это НЕ видела при обучении)")]
    ax.legend(handles=handles, loc=(1.01, 0.25))
    ax.set_title("Получение OOF-предсказаний базовой модели для мета-признаков стэкинга")
    fig.tight_layout()
    return ax


def plot_model_comparison_bars(model_names, scores, ylabel="Правильность",
                                title="Сравнение моделей", highlight_best=True):
    """Обобщённая столбчатая диаграмма для сравнения качества нескольких
    моделей (одиночные модели / бэггинг / бустинг / стэкинг и т.п.)."""
    fig, ax = plt.subplots(figsize=(max(5, 1.1 * len(model_names)), 4))
    colors = [ss.base_model_color(i) for i in range(len(model_names))]
    if highlight_best:
        best_i = int(np.argmax(scores))
        colors[best_i] = ss.GREEN_DARK
    bars = ax.bar(model_names, scores, color=colors)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_ylim(min(scores) - 0.05 * abs(min(scores)), max(scores) * 1.08)
    for bar, score in zip(bars, scores):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                f"{score:.3f}", ha="center", va="bottom", fontsize=9)
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right")
    fig.tight_layout()
    return ax
