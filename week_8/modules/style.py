import matplotlib.path as mpath
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D

# ======================================================================
# Официальные цвета бренда
# ======================================================================
GREEN = "#21A038"    # основной фирменный зелёный
BLUE = "#0098F8"     # синий из градиента галочки
YELLOW = "#F1E813"   # жёлтый из градиента галочки
BLACK = "#000000"
WHITE = "#FFFFFF"

# ======================================================================
# Производные оттенки (для различения категорий на графиках)
# ======================================================================
GREEN_DARK = "#0D6E27"
GREEN_LIGHT = "#8DD9A3"
MINT = "#BFEACB"       # светлый мятный — фон "обучающих" блоков
GRAY = "#8C8C8C"
GRAY_LIGHT = "#E6E6E6"  # фон "неиспользуемых" блоков

# ======================================================================
# Смысловые роли цветов в диаграммах кросс-валидации
# ======================================================================
FOLD_COLORS = {
    "train": MINT,     # обучающий блок
    "test": GREEN,     # тестовый блок
    "unused": GRAY_LIGHT,  # не используется на этой итерации
}

# контрастных оттенков, чтобы уверенно различать до 8 категорий.
CATEGORY_PALETTE = [
    GREEN,        # 0
    BLUE,         # 1
    YELLOW,        # 2 (используем на тёмном/светлом фоне с чёрной обводкой)
    GREEN_DARK,   # 3
    "#5B8DEF",          # 4 — дополнительный синий оттенок (не офиц. цвет бренда)
    "#7A4FE0",          # 5 — дополнительный фиолетовый акцент (не офиц. цвет бренда)
    GRAY,          # 6
    GREEN_LIGHT,  # 7
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
