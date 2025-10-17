from typing import List
import datetime as dt
import itertools

from sunpeek.components import Plant
from sunpeek.components.helpers import AlgoCheckMode
from sunpeek.core_methods.virtuals import CoreAlgorithm, CoreStrategy
from sunpeek.serializable_models import CoreMethodFeedback, PowerCheckFeedback
from sunpeek.core_methods.power_check.main import PowerCheck
from sunpeek.core_methods.power_check import PowerCheckFormulaeEnum, PowerCheckMethods
from sunpeek.core_methods.common.main import AlgoResult


def run_power_check(plant: Plant,
                    method: List[PowerCheckMethods | str | None] | None = None,
                    formula: List[PowerCheckFormulaeEnum | int | None] | None = None,
                    use_wind: List[None | bool] | None = None,
                    # Context
                    eval_start: dt.datetime | None = None,
                    eval_end: dt.datetime | None = None,
                    # Settings:
                    safety_pipes: float | None = None,
                    safety_uncertainty: float | None = None,
                    safety_others: float | None = None,
                    interval_length: dt.timedelta | None = None,
                    min_data_in_interval: int | None = None,
                    max_gap_in_interval: dt.timedelta | None = None,
                    max_nan_density: float | None = None,
                    min_intervals_in_output: int | None = None,
                    accuracy_level: str | None = None,
                    ) -> AlgoResult:
    """Run Performance Check analysis with given settings, trying all possible strategies in order.
    """
    kwds = {
        'safety_pipes': safety_pipes,
        'safety_uncertainty': safety_uncertainty,
        'safety_others': safety_others,
        'interval_length': interval_length,
        'min_data_in_interval': min_data_in_interval,
        'max_gap_in_interval': max_gap_in_interval,
        'max_nan_density': max_nan_density,
        'min_intervals_in_output': min_intervals_in_output,
        'accuracy_level': accuracy_level,
    }
    power_check_algo = PowerCheckAlgo(plant, methods=method, formulae=formula, use_wind=use_wind, **kwds)
    power_check_algo.check_interval(eval_start, eval_end)
    algo_result = power_check_algo.run()
    return algo_result


def list_feedback(plant: Plant,
                  method: List[PowerCheckMethods | str | None] | None = None,
                  formula: List[PowerCheckFormulaeEnum | int | None] | None = None,
                  use_wind: List[bool | None] | None = None,
                  ) -> List[PowerCheckFeedback]:
    """Report which strategies of the Performance Check analysis can be run for given plant config and settings.
    Does not actually run Power Check calculation. Can operate on a plant without data uploaded.
    """
    power_check_algo = PowerCheckAlgo(plant, methods=method, formulae=formula, use_wind=use_wind)
    power_check_feedback = []
    for strategy in power_check_algo.strategies:
        fb = strategy.get_feedback(AlgoCheckMode.config_only)
        power_check_feedback.append(strategy.create_feedback_from_core_feedback(fb))

    return power_check_feedback


def get_feedback(plant: Plant,
                 method: List[PowerCheckMethods | str | None] | None = None,
                 formula: List[PowerCheckFormulaeEnum | int | None] | None = None,
                 use_wind: List[bool | None] | None = None,
                 # Settings:
                 safety_pipes: float | None = None,
                 safety_uncertainty: float | None = None,
                 safety_others: float | None = None,
                 interval_length: dt.timedelta | None = None,
                 min_data_in_interval: int | None = None,
                 max_gap_in_interval: dt.timedelta | None = None,
                 max_nan_density: float | None = None,
                 min_intervals_in_output: int | None = None,
                 accuracy_level: str | None = None,
                 ) -> CoreMethodFeedback:
    """Report which strategy of the Performance Check analysis can be run for given plant config and settings, if any.
    Stops at first successful strategy.
    Does not actually run Power Check calculation. Can operate on a plant without data uploaded.
    """
    kwds = {
        'safety_pipes': safety_pipes,
        'safety_uncertainty': safety_uncertainty,
        'safety_others': safety_others,
        'interval_length': interval_length,
        'min_data_in_interval': min_data_in_interval,
        'max_gap_in_interval': max_gap_in_interval,
        'max_nan_density': max_nan_density,
        'min_intervals_in_output': min_intervals_in_output,
        'accuracy_level': accuracy_level,
    }

    power_check_algo = PowerCheckAlgo(plant, methods=method, formulae=formula, use_wind=use_wind, **kwds)
    return power_check_algo.get_config_feedback()


class PowerCheckStrategy(CoreStrategy):
    def __init__(self, power_check: PowerCheck):
        super().__init__(power_check.plant)
        self.power_check = power_check
        self.name = (f'Thermal Power Check with '
                     f'Mode: {power_check.mode.value}, '
                     f'Formula: {power_check.formula.id}, '
                     f'{"Using wind" if power_check.formula.use_wind else "Ignoring wind"}')

    def _calc(self):
        return self.power_check.run()  # results.PowerCheckOutput

    def _get_feedback(self, check_mode: AlgoCheckMode) -> CoreMethodFeedback:
        return self.power_check.get_feedback(check_mode)

    def create_feedback_from_core_feedback(self, core_feedback: CoreMethodFeedback) -> PowerCheckFeedback:
        return PowerCheckFeedback(self.power_check.mode.value,
                                  self.power_check.formula.id,
                                  self.power_check.formula.use_wind,
                                  core_feedback.success,
                                  core_feedback.parse())


class PowerCheckAlgo(CoreAlgorithm):

    name = 'Thermal Power Check analysis'

    def define_strategies(self, methods=None, formulae=None, use_wind=None, **kwargs) -> List[PowerCheckStrategy]:
        """Returns list of all possible Power Check strategies in the order they will be executed.
        """
        variants = {'methods': self.create_variants(methods, allowed_type=PowerCheckMethods,
                                                    default=[PowerCheckMethods.iso, PowerCheckMethods.extended]),
                    'formulae': self.create_variants(formulae, allowed_type=PowerCheckFormulaeEnum,
                                                     default=[PowerCheckFormulaeEnum.two, PowerCheckFormulaeEnum.one, PowerCheckFormulaeEnum.three]),
                    'wind': self.create_variants(use_wind, allowed_type=bool, default=[True, False])}
        all_variants = list(itertools.product(*variants.values()))
        strategies = [PowerCheckStrategy(PowerCheck.create(self.component, m, f, w, **kwargs)) for m, f, w in all_variants]

        return strategies


def get_successful_strategy(plant: Plant,
                            method: List[PowerCheckMethods | str | None] | None = None,
                            formula: List[PowerCheckFormulaeEnum | int | None] | None = None,
                            use_wind: List[bool | None] | None = None,
                            # Settings:
                            safety_pipes: float | None = None,
                            safety_uncertainty: float | None = None,
                            safety_others: float | None = None,
                            interval_length: dt.timedelta | None = None,
                            min_data_in_interval: int | None = None,
                            max_gap_in_interval: dt.timedelta | None = None,
                            max_nan_density: float | None = None,
                            min_intervals_in_output: int | None = None,
                            accuracy_level: str | None = None,
                            ) -> PowerCheckStrategy:
    """Report the first strategy of the Performance Check analysis that is successful with given plant and
    settings. Like `get_feedback()`, this does not actually run calculations.
    """
    kwds = {
        'safety_pipes': safety_pipes,
        'safety_uncertainty': safety_uncertainty,
        'safety_others': safety_others,
        'interval_length': interval_length,
        'min_data_in_interval': min_data_in_interval,
        'max_gap_in_interval': max_gap_in_interval,
        'max_nan_density': max_nan_density,
        'min_intervals_in_output': min_intervals_in_output,
        'accuracy_level': accuracy_level,
    }

    power_check_algo = PowerCheckAlgo(plant, methods=method, formulae=formula, use_wind=use_wind, **kwds)
    strategy = power_check_algo.successful_strategy

    return strategy  # noqa
