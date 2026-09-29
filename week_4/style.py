import matplotlib.path as mpath
import matplotlib as mpl

from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D

GREEN = "#21A038"
BLUE = "#0098F8"
YELLOW = "#F1E813"
BLACK = "#000000"
WHITE = "#FFFFFF"
GREEN_DARK = "#0D6E27"
GREEN_LIGHT = "#8DD9A3"
MINT = "#BFEACB"
GRAY = "#8C8C8C"
GRAY_LIGHT = "#E6E6E6"
ERROR_RED = "#D64545"
TRAIN_LINE = BLUE
TEST_LINE = GREEN
OOB_LINE = GREEN_DARK 
NEUTRAL_LINE = GRAY
BASE_MODEL_PALETTE = [BLUE, GREEN, "#5B8DEF", "#7A4FE0", GREEN_DARK, GRAY]

NOISE_COLOR = GRAY_LIGHT
NOISE_EDGE = GRAY
CHURN_COLOR = ERROR_RED
STAY_COLOR = GREEN
ACTIVE_COLOR = BLUE
INACTIVE_COLOR = GRAY
HIGHLIGHT_LINE = YELLOW


FOLD_COLORS = {
    "train": MINT,
    "test": GREEN,
    "unused": GRAY_LIGHT,
}

CATEGORY_PALETTE = [
    GREEN,
    BLUE,
    YELLOW,
    GREEN_DARK,
    "#5B8DEF",
    "#7A4FE0",
    GRAY,
    GREEN_LIGHT,
]
CLUSTER_PALETTE = [
    GREEN,
    BLUE,
    YELLOW,
    "#7A4FE0",
    GREEN_DARK,
    "#F29E4C",
    "#5B8DEF",
    "#2EC4B6",
    GREEN_LIGHT,
    "#0B4F6C",
    GRAY,
    "#B8B8B8",
]
DIVERGING_CMAP = LinearSegmentedColormap.from_list(
    "diverging_blue_green", [BLUE, WHITE, GREEN]
)
SEQUENTIAL_CMAP = LinearSegmentedColormap.from_list(
    "sequential_green", [WHITE, MINT, GREEN, GREEN_DARK]
)


def category_color(i):
    """Возвращает цвет категории i (с циклическим повтором палитры)."""
    return CATEGORY_PALETTE[i % len(CATEGORY_PALETTE)]


CMAP = LinearSegmentedColormap.from_list(
    "checkmark", [BLUE, GREEN, YELLOW]
)
CHECK_VERTS = [
    (-0.60, 0.10),
    (-0.10, -0.60),
    (0.65, 0.55),
    (0.50, 0.75),
    (-0.05, -0.10),
    (-0.40, 0.35),
    (-0.60, 0.10),
]
CHECK_CODES = [mpath.Path.MOVETO] + [mpath.Path.LINETO] * 5 + [mpath.Path.CLOSEPOLY]
CHECK_MARKER = mpath.Path(CHECK_VERTS, CHECK_CODES)


def check_legend_handle(
    label="лучшая комбинация", color=GREEN,
    markersize=16, markeredgecolor="black"
):
    """Готовый handle для legend с маркером-галочкой """
    return Line2D(
        [0], [0], marker=CHECK_MARKER, color="none",
        markerfacecolor=color, markeredgecolor=markeredgecolor,
        markersize=markersize, linestyle="none", label=label
    )


def test_marker_legend_handle(
    label="тестовые данные", color=BLACK,
    markersize=8
):
    """Готовый handle для legend с 'лёгким крестиком', которым на схемах
    кросс-валидации помечаются тестовые объекты поверх цвета их класса/группы."""
    return Line2D(
        [0], [0], marker="x", color=color, markersize=markersize,
        markeredgewidth=1.4, alpha=0.75, linestyle="none", label=label
    )


def base_model_color(i):
    """Цвет i-й базовой модели на диаграммах (с циклическим повтором)."""
    return BASE_MODEL_PALETTE[i % len(BASE_MODEL_PALETTE)]


def cluster_color(label):
    """Цвет кластера по его метке; метка -1 (шум) всегда серая."""
    if label is None or label < 0:
        return NOISE_COLOR
    return CLUSTER_PALETTE[int(label) % len(CLUSTER_PALETTE)]


def cluster_colors(labels):
    """Список цветов для массива меток кластеров."""
    return [cluster_color(l) for l in labels]


def apply_default_style():
    mpl.rcParams.update({
        "figure.dpi": 100,
        "figure.facecolor": WHITE,
        "axes.facecolor": WHITE,
        "axes.edgecolor": GRAY,
        "axes.grid": True,
        "grid.color": GRAY_LIGHT,
        "grid.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titleweight": "bold",
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "axes.prop_cycle": mpl.cycler(color=CATEGORY_PALETTE),
        "legend.frameon": False,
        "font.size": 10,
    })
