import matplotlib.path as mpath
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
