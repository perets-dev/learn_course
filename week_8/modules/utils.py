import warnings
warnings.filterwarnings("ignore")

import numpy as np

from sklearn.model_selection import (
    cross_val_score,
    StratifiedKFold, 
    cross_val_score
)
from sklearn.ensemble import RandomForestClassifier


def is_representative_sample(
        X_train, X_test, model=None, cv=5,
        threshold=0.6, random_state=42, verbose=True
):
    '''Проверяет, репрезентативна ли выборка train относительно test
    с помощью adversarial validation.

    Помечает объекты train меткой 0, а объекты test — меткой 1, и
    обучает классификатор отличать одни от других с помощью
    кросс-валидации (метрика ROC AUC). Если классификатор не может
    уверенно отличить train от test (AUC близко к 0.5), их
    распределения похожи — выборка репрезентативна. Если AUC высокий,
    распределения различаются (data drift) — выборка не репрезентативна.

    Параметры
    ----------
    X_train, X_test : array-like, shape (n, n_features)
        Матрицы признаков (без целевой переменной).
    model : sklearn-совместимый классификатор или None
        Модель для adversarial validation. По умолчанию
        RandomForestClassifier.
    cv : int
        Число блоков стратифицированной кросс-валидации.
    threshold : float
        Порог AUC: если средний AUC >= threshold, выборка считается
        нерепрезентативной.
    random_state : int
        Фиксирует случайность модели и разбиения.
    verbose : bool
        Печатать ли текстовый отчёт.

    Возвращает
    ----------
    dict с ключами:
        'auc' - средний ROC AUC по кросс-валидации,
        'fold_scores' - оценки AUC по каждому блоку,
        'is_representative' - bool,
        'feature_importances' - важности признаков (если модель их поддерживает)
    '''
    X_train = np.asarray(X_train)
    X_test = np.asarray(X_test)
    X_combined = np.vstack([X_train, X_test])
    y_combined = np.concatenate([np.zeros(len(X_train)), np.ones(len(X_test))])

    if model is None:
        model = RandomForestClassifier(n_estimators=300, max_depth=6,
                                        random_state=random_state, n_jobs=-1)

    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=random_state)
    fold_scores = cross_val_score(model, X_combined, y_combined,
                                   cv=skf, scoring="roc_auc")
    mean_auc = fold_scores.mean()
    is_repr = mean_auc < threshold

    result = {"auc": mean_auc, "fold_scores": fold_scores,
              "is_representative": is_repr}

    if hasattr(model, "feature_importances_") or hasattr(model, "fit"):
        fitted = model.fit(X_combined, y_combined)
        if hasattr(fitted, "feature_importances_"):
            result["feature_importances"] = fitted.feature_importances_

    if verbose:
        verdict = "РЕПРЕЗЕНТАТИВНА" if is_repr else "НЕ репрезентативна"
        print("Adversarial validation ROC AUC: {:.3f} (+- {:.3f})".format(
            mean_auc, fold_scores.std()))
        print("Порог: {:.2f}  ->  Выборка: {}".format(threshold, verdict))
        if not is_repr:
            print("Классификатор уверенно отличает train от test — "
                  "распределения признаков различаются (возможен data drift).")
        else:
            print("Классификатор не может уверенно отличить train от test — "
                  "распределения признаков похожи.")
    return result
