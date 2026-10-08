import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, TransformerMixin, clone
from sklearn.preprocessing import FunctionTransformer
from sklearn.utils.validation import check_is_fitted

TARGET = "Paddy yield(in Kg)"
AREA_COL = "Hectares"

CATEGORICAL_COLS = ["Agriblock", "Variety", "Soil Types", "Nursery"]
WIND_DIRECTION_COLS = [
    "Wind Direction_D1_D30", "Wind Direction_D31_D60",
    "Wind Direction_D61_D90", "Wind Direction_D91_D120",
]
AGRO_INPUT_COLS = [
    "Seedrate(in Kg)", "LP_Mainfield(in Tonnes)", "Nursery area (Cents)",
    "LP_nurseryarea(in Tonnes)", "DAP_20days", "Weed28D_thiobencarb",
    "Urea_40Days", "Potassh_50Days", "Micronutrients_70Days", "Pest_60Day(in ml)",
]
DRAIN_COLS = ["30DRain( in mm)", "30_50DRain( in mm)", "51_70DRain(in mm)", "71_105DRain(in mm)"]
IRRIGATION_COLS = ["30DAI(in mm)", "30_50DAI(in mm)", "51_70AI(in mm)", "71_105DAI(in mm)"]
MIN_TEMP_COLS = ["Min temp_D1_D30", "Min temp_D31_D60", "Min temp_D61_D90", "Min temp_D91_D120"]
MAX_TEMP_COLS = ["Max temp_D1_D30", "Max temp_D31_D60", "Max temp_D61_D90", "Max temp_D91_D120"]
WIND_SPEED_COLS = [
    "Inst Wind Speed_D1_D30(in Knots)", "Inst Wind Speed_D31_D60(in Knots)",
    "Inst Wind Speed_D61_D90(in Knots)", "Inst Wind Speed_D91_D120(in Knots)",
]
HUMIDITY_COLS = [
    "Relative Humidity_D1_D30", "Relative Humidity_D31_D60",
    "Relative Humidity_D61_D90", "Relative Humidity_D91_D120",
]
WEATHER_COLS = MIN_TEMP_COLS + MAX_TEMP_COLS + WIND_SPEED_COLS + HUMIDITY_COLS
WATER_COLS = DRAIN_COLS + IRRIGATION_COLS
TRASH_COL = "Trash(in bundles)"

NUMERIC_COLS = [AREA_COL] + AGRO_INPUT_COLS + WATER_COLS + WEATHER_COLS + [TRASH_COL]
CATEGORICAL_ALL_COLS = CATEGORICAL_COLS + WIND_DIRECTION_COLS


def clean_column_names(X):
    """Strip leading/trailing spaces from column names ("Hectares " -> "Hectares")."""
    return X.rename(columns=lambda c: str(c).strip())


def _strip_feature_names(transformer, input_features):
    """Output feature names for the cleaner: input names with spaces stripped."""
    return np.asarray([str(c).strip() for c in input_features], dtype=object)


def make_column_cleaner():
    """First step of every pipeline: accepts the raw CSV as is."""
    return FunctionTransformer(
        clean_column_names, 
        feature_names_out=_strip_feature_names
)


class PaddyFeatureGenerator(TransformerMixin, BaseEstimator):
    """
    Domain features for the Paddy Dataset.

    There is nothing to learn (no statistics are computed), but a class is handier
    than FunctionTransformer: its parameters show up in get_params and can be
    searched over in GridSearchCV.

    Parameters
    ----------
    add_per_ha : add trash_per_ha, the only per-hectare quantity with real
        variation (all other inputs are strictly proportional to Hectares).
    add_aggregates : add weather and water-regime aggregates over the 4 periods.
    """


    def __init__(self, add_per_ha=True, add_aggregates=True):
        self.add_per_ha = add_per_ha
        self.add_aggregates = add_aggregates


    def fit(self, X, y=None):
        """Remember the input column names; there is nothing else to learn."""
        X = pd.DataFrame(X)
        self.feature_names_in_ = np.asarray(X.columns, dtype=object)
        self.n_features_in_ = X.shape[1]
        return self


    def new_columns(self):
        """Names of the features that transform adds with the current parameters."""
        cols = []
        if self.add_per_ha:
            cols += ["trash_per_ha"]
        if self.add_aggregates:
            cols += ["total_irrigation_mm", "total_drain_mm", "water_balance_mm",
                     "avg_min_temp", "avg_max_temp", "avg_temp_range",
                     "avg_wind_speed", "avg_humidity"]
        return cols


    def transform(self, X):
        """Return a copy of X with the generated feature columns appended."""
        check_is_fitted(self)
        X = pd.DataFrame(X).copy()
        if self.add_per_ha:
            X["trash_per_ha"] = X[TRASH_COL] / X[AREA_COL].replace(0, np.nan)
        if self.add_aggregates:
            X["total_irrigation_mm"] = X[IRRIGATION_COLS].sum(axis=1)
            X["total_drain_mm"] = X[DRAIN_COLS].sum(axis=1)
            X["water_balance_mm"] = X["total_irrigation_mm"] - X["total_drain_mm"]
            X["avg_min_temp"] = X[MIN_TEMP_COLS].mean(axis=1)
            X["avg_max_temp"] = X[MAX_TEMP_COLS].mean(axis=1)
            X["avg_temp_range"] = X["avg_max_temp"] - X["avg_min_temp"]
            X["avg_wind_speed"] = X[WIND_SPEED_COLS].mean(axis=1)
            X["avg_humidity"] = X[HUMIDITY_COLS].mean(axis=1)
        return X


    def get_feature_names_out(self, input_features=None):
        """Input feature names followed by the generated ones."""
        check_is_fitted(self)
        return np.asarray(list(self.feature_names_in_) + self.new_columns(), dtype=object)


class PerHectareRegressor(RegressorMixin, BaseEstimator):
    """
    Fits on yield per hectare, while predict returns kilograms.

    TransformedTargetRegressor only supports y -> f(y); here the divisor
    (field area) comes from X, so a small custom meta-estimator is needed.
    """


    def __init__(self, regressor, area_col=AREA_COL):
        self.regressor = regressor
        self.area_col = area_col


    def _area(self, X):
        """Field area from X as a float array (column names are cleaned first)."""
        return clean_column_names(pd.DataFrame(X))[self.area_col].to_numpy(dtype=float)


    def fit(self, X, y):
        """Fit a clone of the regressor on yield per hectare (y / area)."""
        self.regressor_ = clone(self.regressor).fit(X, np.asarray(y, dtype=float) / self._area(X))
        return self


    def predict(self, X):
        """Predict yield per hectare and multiply it back by the area (kg)."""
        check_is_fitted(self)
        return self.regressor_.predict(X) * self._area(X)