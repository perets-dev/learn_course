import numbers

import numpy as np
from scipy.stats import uniform, loguniform

from sklearn.model_selection._search import BaseSearchCV
from sklearn.model_selection import ParameterGrid, ParameterSampler
from sklearn.utils import check_random_state


class CoarseToFineSearchCV(BaseSearchCV):
    '''Поиск гиперпараметров в стиле coarse-to-fine.

    Этап 1 (coarse) реализован буквально той же логикой, что использует
    RandomizedSearchCV: параметры оборачиваются в scipy-распределения
    (для числовых диапазонов — loguniform/uniform в зависимости от того,
    насколько широк диапазон) и передаются в `sklearn.model_selection.
    ParameterSampler` — тот же генератор кандидатов, которым RandomizedSearchCV
    пользуется внутри себя. Цель этапа — грубо нащупать перспективную
    область пространства гиперпараметров.

    Этап 2 (fine) реализован логикой GridSearchCV: вокруг лучшей
    coarse-комбинации строится локальная сетка значений и передаётся в
    `sklearn.model_selection.ParameterGrid` — тот же генератор
    кандидатов, которым пользуется GridSearchCV. Цель этапа — уточнить
    значения гиперпараметров внутри уже найденного перспективного региона.

    Таким образом CoarseToFineSearchCV не изобретает собственный способ
    сэмплирования/перебора комбинаций, а последовательно переиспользует
    ровно те же строительные блоки, что и стандартные RandomizedSearchCV
    и GridSearchCV, — меняется только то, какие кандидаты подаются на
    каждом этапе и в каком порядке.

    Параметры
    ----------
    estimator : sklearn-совместимая модель
    param_distributions : dict
        Для числовых параметров — кортеж (low, high) с границами
        диапазона (будет автоматически превращён в scipy.stats.loguniform,
        если диапазон охватывает 2+ порядка, иначе в scipy.stats.uniform).
        Также допускаются готовые scipy-распределения (с методом .rvs())
        или список конкретных (дискретных/категориальных) значений —
        как и в param_distributions у RandomizedSearchCV.
    n_coarse_iter : int
        Число случайных комбинаций на coarse-этапе (аргумент n_iter
        у RandomizedSearchCV).
    fine_grid_points : int
        Число точек сетки на каждый числовой параметр на fine-этапе.
    fine_neighborhood : float
        Доля от исходного диапазона [low, high], определяющая ширину
        локальной сетки fine-этапа вокруг лучшей coarse-точки.
    scoring, n_jobs, refit, cv, verbose, error_score, return_train_score :
        как в GridSearchCV / RandomizedSearchCV / BaseSearchCV.
    random_state : int, RandomState или None
        Фиксирует случайность coarse-этапа (передаётся в ParameterSampler).

    Атрибуты (помимо стандартных best_params_/best_score_/cv_results_)
    --------------------------------------------------------------
    coarse_best_params_ : dict
        Лучшая комбинация, найденная на coarse-этапе.
    coarse_best_score_ : float
        Её cv-оценка.
    '''

    def __init__(self, estimator, param_distributions, *,
                 n_coarse_iter=20, fine_grid_points=5, fine_neighborhood=0.2,
                 scoring=None, n_jobs=None, refit=True, cv=None, verbose=0,
                 random_state=None, error_score=np.nan, return_train_score=False):
        super().__init__(
            estimator=estimator, scoring=scoring, n_jobs=n_jobs, refit=refit,
            cv=cv, verbose=verbose, error_score=error_score,
            return_train_score=return_train_score)
        self.param_distributions = param_distributions
        self.n_coarse_iter = n_coarse_iter
        self.fine_grid_points = fine_grid_points
        self.fine_neighborhood = fine_neighborhood
        self.random_state = random_state

    @staticmethod
    def _is_numeric_range(spec):
        return (isinstance(spec, tuple) and len(spec) == 2 and
                all(isinstance(v, numbers.Number) for v in spec))

    def _as_sampler_distribution(self, spec):
        '''Приводит спецификацию параметра к виду, который принимает
        ParameterSampler: список значений либо scipy-распределение
        с методом .rvs() — то есть ровно то, что ожидает
        param_distributions в RandomizedSearchCV.'''
        if self._is_numeric_range(spec):
            low, high = spec
            log_scale = low > 0 and high / max(low, 1e-12) > 100
            if log_scale:
                return loguniform(low, high)
            return uniform(loc=low, scale=high - low)
        if hasattr(spec, "rvs"):
            return spec
        return list(spec)

    def _build_fine_grid(self, best_params):
        '''Строит param_grid для fine-этапа — тот же формат, который
        принимает GridSearchCV / ParameterGrid.'''
        grid = {}
        for name, spec in self.param_distributions.items():
            center = best_params[name]
            if self._is_numeric_range(spec):
                low, high = spec
                span = (high - low) * self.fine_neighborhood
                lo = max(low, center - span / 2)
                hi = min(high, center + span / 2)
                grid[name] = list(np.linspace(lo, hi, self.fine_grid_points))
            else:
                # для дискретных/категориальных параметров на fine-этапе
                # фиксируем то значение, что победило на coarse-этапе
                grid[name] = [center]
        return grid

    def _run_search(self, evaluate_candidates):
        random_state = check_random_state(self.random_state)

        # --- этап 1 (coarse): candidate generator = ParameterSampler,
        #     как в RandomizedSearchCV._run_search ---
        distributions = {name: self._as_sampler_distribution(spec)
                          for name, spec in self.param_distributions.items()}
        coarse_candidates = list(ParameterSampler(
            distributions, n_iter=self.n_coarse_iter, random_state=random_state))
        results = evaluate_candidates(coarse_candidates)

        best_idx = np.argmax(results["mean_test_score"])
        best_coarse_params = {
            key[len("param_"):]: results[key][best_idx]
            for key in results if key.startswith("param_")
        }
        best_coarse_params = {
            k: (float(v) if isinstance(v, (np.floating, np.integer)) else v)
            for k, v in best_coarse_params.items()
        }
        self.coarse_best_params_ = best_coarse_params
        self.coarse_best_score_ = results["mean_test_score"][best_idx]

        # --- этап 2 (fine): candidate generator = ParameterGrid,
        #     как в GridSearchCV._run_search ---
        fine_grid = self._build_fine_grid(best_coarse_params)
        fine_candidates = list(ParameterGrid(fine_grid))
        evaluate_candidates(fine_candidates)
