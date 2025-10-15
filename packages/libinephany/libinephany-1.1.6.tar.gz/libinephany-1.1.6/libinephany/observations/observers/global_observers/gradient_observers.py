# ======================================================================================================================
#
# IMPORTS
#
# ======================================================================================================================

import math
from typing import Any

from libinephany.observations import observation_utils, statistic_trackers
from libinephany.observations.observation_utils import StatisticStorageTypes
from libinephany.observations.observers.base_observers import GlobalObserver
from libinephany.observations.observers.global_observers.base_classes import LHOPTBaseObserver
from libinephany.observations.observers.global_observers.constants import LHOPT_CONSTANTS
from libinephany.pydantic_models.schemas.observation_models import ObservationInputs
from libinephany.pydantic_models.schemas.tensor_statistics import TensorStatistics
from libinephany.pydantic_models.states.hyperparameter_states import HyperparameterStates

# ======================================================================================================================
#
# CLASSES
#
# ======================================================================================================================


class GlobalFirstOrderGradients(GlobalObserver):

    @property
    def requires_include_statistics(self) -> bool:
        """
        :return: Whether the observation requires include_statistics to be provided.
        """

        return True

    def _get_observation_format(self) -> StatisticStorageTypes:
        """
        :return: Format the observation returns data in. Must be one of the enum attributes in the StatisticStorageTypes
        enumeration class.
        """

        return StatisticStorageTypes.TENSOR_STATISTICS

    def _observe(
        self,
        observation_inputs: ObservationInputs,
        hyperparameter_states: HyperparameterStates,
        tracked_statistics: dict[str, dict[str, float | TensorStatistics]],
        action_taken: float | int | None,
    ) -> float | int | list[int | float] | TensorStatistics:
        """
        :param observation_inputs: Observation input metrics not calculated with statistic trackers.
        :param hyperparameter_states: HyperparameterStates that manages the hyperparameters.
        :param tracked_statistics: Dictionary mapping statistic tracker class names to dictionaries mapping module
        names to floats or TensorStatistic models.
        :param action_taken: Action taken by the agent this class instance is assigned to.
        :return: Single float/int, list of floats/ints or TensorStatistics model to add to the observation vector.
        """

        statistics = tracked_statistics[statistic_trackers.FirstOrderGradients.__name__]

        return observation_utils.average_tensor_statistics(tensor_statistics=list(statistics.values()))  # type: ignore

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {statistic_trackers.FirstOrderGradients.__name__: dict(include_statistics=self.include_statistics)}


class GlobalSecondOrderGradients(GlobalObserver):

    def __init__(
        self,
        *,
        compute_hessian_diagonal: bool = False,
        **kwargs,
    ) -> None:
        """
        :param compute_hessian_diagonal: Whether to compute the Hessian diagonal to determine second order gradients
        or use the squared first order gradients as approximations in the same way Adam does.
        :param kwargs: Miscellaneous keyword arguments.
        """

        super().__init__(**kwargs)

        self.compute_hessian_diagonal = compute_hessian_diagonal

    @property
    def requires_include_statistics(self) -> bool:
        """
        :return: Whether the observation requires include_statistics to be provided.
        """

        return True

    def _get_observation_format(self) -> StatisticStorageTypes:
        """
        :return: Format the observation returns data in. Must be one of the enum attributes in the StatisticStorageTypes
        enumeration class.
        """

        return StatisticStorageTypes.TENSOR_STATISTICS

    def _observe(
        self,
        observation_inputs: ObservationInputs,
        hyperparameter_states: HyperparameterStates,
        tracked_statistics: dict[str, dict[str, float | TensorStatistics]],
        action_taken: float | int | None,
    ) -> float | int | list[int | float] | TensorStatistics:
        """
        :param observation_inputs: Observation input metrics not calculated with statistic trackers.
        :param hyperparameter_states: HyperparameterStates that manages the hyperparameters.
        :param tracked_statistics: Dictionary mapping statistic tracker class names to dictionaries mapping module
        names to floats or TensorStatistic models.
        :param action_taken: Action taken by the agent this class instance is assigned to.
        :return: Single float/int, list of floats/ints or TensorStatistics model to add to the observation vector.
        """

        statistics = tracked_statistics[statistic_trackers.SecondOrderGradients.__name__]

        return observation_utils.average_tensor_statistics(tensor_statistics=list(statistics.values()))  # type: ignore

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {
            statistic_trackers.SecondOrderGradients.__name__: dict(
                include_statistics=self.include_statistics, compute_hessian_diagonal=self.compute_hessian_diagonal
            )
        }


class LHOPTGradientVarianceFraction(LHOPTBaseObserver):
    """
    This is a global observer from the OpenAI paper "Learning to Optimize with Reinforcement Learning"
    https://arxiv.org/abs/2305.18291.

    It returns two-dimensional observations: [raw_value, cdf_feature] for gradient variance fraction values.
    """

    def __init__(
        self,
        *,
        variance_threshold: float = LHOPT_CONSTANTS["DEFAULT_VARIANCE_THRESHOLD"],
        **kwargs,
    ) -> None:
        """
        :param variance_threshold: Threshold for variance comparison in gradient variance fraction calculation
        :param kwargs: Other observation keyword arguments.
        """
        super().__init__(**kwargs)
        self.variance_threshold = variance_threshold

    @property
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """
        return 2  # [raw_value, cdf_feature]

    def _observe(
        self,
        observation_inputs: ObservationInputs,
        hyperparameter_states: HyperparameterStates,
        tracked_statistics: dict[str, dict[str, float | TensorStatistics]],
        action_taken: float | int | None,
    ) -> float | int | list[int | float] | TensorStatistics:
        """
        :param observation_inputs: Observation input metrics not calculated with statistic trackers.
        :param hyperparameter_states: HyperparameterStates that manages the hyperparameters.
        :param tracked_statistics: Dictionary mapping statistic tracker class names to dictionaries mapping module
        names to floats or TensorStatistic models.
        :param action_taken: Action taken by the agent this class instance is assigned to.
        :return: Single float/int, list of floats/ints or TensorStatistics model to add to the observation vector.
        """

        raw_value = list(tracked_statistics[statistic_trackers.GradientVarianceFraction.__name__].values())[0]  # type: ignore[list-item]

        cdf_feature = self._compute_cdf_feature(raw_value)  # type: ignore[arg-type]
        self._update_time()

        return [raw_value, cdf_feature]  # type: ignore[list-item]

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {
            statistic_trackers.GradientVarianceFraction.__name__: dict(
                variance_threshold=self.variance_threshold, sample_frequency=LHOPT_CONSTANTS["DEFAULT_SAMPLE_FREQUENCY"]
            ),
        }


class LHOPTMomentumGradientRatio(LHOPTBaseObserver):
    """
    This is a global observer from the OpenAI paper "Learning to Optimize with Reinforcement Learning"
    https://arxiv.org/abs/2305.18291.

    It returns two-dimensional observations: [raw_value, cdf_feature] for momentum gradient ratio values.
    """

    @property
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """
        return 2  # [raw_value, cdf_feature]

    @property
    def requires_include_statistics(self) -> bool:
        """
        :return: Whether the observation requires include_statistics to be provided.
        """

        return True

    def _observe(
        self,
        observation_inputs: ObservationInputs,
        hyperparameter_states: HyperparameterStates,
        tracked_statistics: dict[str, dict[str, float | TensorStatistics]],
        action_taken: float | int | None,
    ) -> float | int | list[int | float] | TensorStatistics:
        """
        :param observation_inputs: Observation input metrics not calculated with statistic trackers.
        :param hyperparameter_states: HyperparameterStates that manages the hyperparameters.
        :param tracked_statistics: Dictionary mapping statistic tracker class names to dictionaries mapping module
        names to floats or TensorStatistic models.
        :param action_taken: Action taken by the agent this class instance is assigned to.
        :return: Single float/int, list of floats/ints or TensorStatistics model to add to the observation vector.
        """

        statistics = tracked_statistics[statistic_trackers.MomentumGradientRatioStatistics.__name__]

        raw_value = list(statistics.values())[0]  # type: ignore[list-item]

        cdf_feature = self._compute_cdf_feature(raw_value)  # type: ignore[arg-type]
        self._update_time()

        return [raw_value, cdf_feature]  # type: ignore[list-item]

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {
            statistic_trackers.MomentumGradientRatioStatistics.__name__: dict(
                include_statistics=self.include_statistics,
                sample_frequency=LHOPT_CONSTANTS["DEFAULT_SAMPLE_FREQUENCY"],
            ),
        }


class CosineSimilarityObserverOfGradientAndMomentum(LHOPTBaseObserver):
    """
    This is a global observer from the OpenAI paper "Learning to Optimize with Reinforcement Learning"
    https://arxiv.org/abs/2305.18291.

    It returns two-dimensional observations: [raw_value, cdf_feature] for cosine similarity of gradient and momentum values.
    """

    @property
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """
        return 3  # [raw_value, cdf_feature, logit_of_cdf_feature]

    @property
    def requires_include_statistics(self) -> bool:
        """
        :return: Whether the observation requires include_statistics to be provided.
        """

        return True

    def _observe(
        self,
        observation_inputs: ObservationInputs,
        hyperparameter_states: HyperparameterStates,
        tracked_statistics: dict[str, dict[str, float | TensorStatistics]],
        action_taken: float | int | None,
    ) -> float | int | list[int | float] | TensorStatistics:
        """
        :param observation_inputs: Observation input metrics not calculated with statistic trackers.
        :param hyperparameter_states: HyperparameterStates that manages the hyperparameters.
        :param tracked_statistics: Dictionary mapping statistic tracker class names to dictionaries mapping module
        names to floats or TensorStatistic models.
        :param action_taken: Action taken by the agent this class instance is assigned to.
        :return: Single float/int, list of floats/ints or TensorStatistics model to add to the observation vector.
        """

        statistics = tracked_statistics[
            statistic_trackers.CosineSimilarityObserverOfGradientAndMomentumStatistics.__name__
        ]

        raw_value = list(statistics.values())[0]  # type: ignore[list-item]

        cdf_feature = self._compute_cdf_feature(raw_value)  # type: ignore[arg-type]
        self._update_time()

        # Handle edge cases for logit calculation
        if cdf_feature <= 0.0 or cdf_feature >= 1.0:
            logit_of_cdf_feature = 0.0
        else:
            logit_of_cdf_feature = math.log(cdf_feature / (1 - cdf_feature))

        return [raw_value, cdf_feature, logit_of_cdf_feature]  # type: ignore[list-item]

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {
            statistic_trackers.CosineSimilarityObserverOfGradientAndMomentumStatistics.__name__: dict(
                include_statistics=self.include_statistics,
                sample_frequency=LHOPT_CONSTANTS["DEFAULT_SAMPLE_FREQUENCY"],
            )
        }


class CosineSimilarityObserverOfGradientAndUpdate(LHOPTBaseObserver):
    """
    This is a global observer from the OpenAI paper "Learning to Optimize with Reinforcement Learning"
    https://arxiv.org/abs/2305.18291.

    It returns two-dimensional observations: [raw_value, cdf_feature] for cosine similarity of gradient and update values.
    """

    @property
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """
        return 3  # [raw_value, cdf_feature, logit_of_cdf_feature]

    @property
    def requires_include_statistics(self) -> bool:
        """
        :return: Whether the observation requires include_statistics to be provided.
        """

        return True

    def _observe(
        self,
        observation_inputs: ObservationInputs,
        hyperparameter_states: HyperparameterStates,
        tracked_statistics: dict[str, dict[str, float | TensorStatistics]],
        action_taken: float | int | None,
    ) -> float | int | list[int | float] | TensorStatistics:
        """
        :param observation_inputs: Observation input metrics not calculated with statistic trackers.
        :param hyperparameter_states: HyperparameterStates that manages the hyperparameters.
        :param tracked_statistics: Dictionary mapping statistic tracker class names to dictionaries mapping module
        names to floats or TensorStatistic models.
        :param action_taken: Action taken by the agent this class instance is assigned to.
        :return: Single float/int, list of floats/ints or TensorStatistics model to add to the observation vector.
        """

        statistics = tracked_statistics[
            statistic_trackers.CosineSimilarityObserverOfGradientAndUpdateStatistics.__name__
        ]

        raw_value = list(statistics.values())[0]  # type: ignore[list-item]

        cdf_feature = self._compute_cdf_feature(raw_value)  # type: ignore[arg-type]
        self._update_time()

        # Handle edge cases for logit calculation
        if cdf_feature <= 0.0 or cdf_feature >= 1.0:
            logit_of_cdf_feature = 0.0
        else:
            logit_of_cdf_feature = math.log(cdf_feature / (1 - cdf_feature))

        return [raw_value, cdf_feature, logit_of_cdf_feature]  # type: ignore[list-item]

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {
            statistic_trackers.CosineSimilarityObserverOfGradientAndUpdateStatistics.__name__: dict(
                include_statistics=self.include_statistics,
                sample_frequency=LHOPT_CONSTANTS["DEFAULT_SAMPLE_FREQUENCY"],
            )
        }


class CosineSimilarityOfGradientAndParameter(LHOPTBaseObserver):
    """
    This is a global observer from the OpenAI paper "Learning to Optimize with Reinforcement Learning"
    https://arxiv.org/abs/2305.18291.

    It returns two-dimensional observations: [raw_value, cdf_feature] for cosine similarity of gradient and parameter values.
    """

    @property
    def vector_length(self) -> int:
        """
        :return: Length of the vector returned by this observation if it returns a vector.
        """
        return 3  # [raw_value, cdf_feature, logit_of_cdf_feature]

    @property
    def requires_include_statistics(self) -> bool:
        """
        :return: Whether the observation requires include_statistics to be provided.
        """

        return True

    def _observe(
        self,
        observation_inputs: ObservationInputs,
        hyperparameter_states: HyperparameterStates,
        tracked_statistics: dict[str, dict[str, float | TensorStatistics]],
        action_taken: float | int | None,
    ) -> float | int | list[int | float] | TensorStatistics:
        """
        :param observation_inputs: Observation input metrics not calculated with statistic trackers.
        :param hyperparameter_states: HyperparameterStates that manages the hyperparameters.
        :param tracked_statistics: Dictionary mapping statistic tracker class names to dictionaries mapping module
        names to floats or TensorStatistic models.
        :param action_taken: Action taken by the agent this class instance is assigned to.
        :return: Single float/int, list of floats/ints or TensorStatistics model to add to the observation vector.
        """

        statistics = tracked_statistics[statistic_trackers.CosineSimilarityOfGradientAndParameterStatistics.__name__]

        raw_value = list(statistics.values())[0]  # type: ignore[list-item]

        cdf_feature = self._compute_cdf_feature(raw_value)  # type: ignore[arg-type]
        self._update_time()

        # Handle edge cases for logit calculation
        if cdf_feature <= 0.0 or cdf_feature >= 1.0:
            logit_of_cdf_feature = 0.0
        else:
            logit_of_cdf_feature = math.log(cdf_feature / (1 - cdf_feature))

        return [raw_value, cdf_feature, logit_of_cdf_feature]  # type: ignore[list-item]

    def get_required_trackers(self) -> dict[str, dict[str, Any] | None]:
        """
        :return: Dictionary mapping statistic tracker class names to kwargs for the class or None if no kwargs are
        needed.
        """

        return {
            statistic_trackers.CosineSimilarityOfGradientAndParameterStatistics.__name__: dict(
                include_statistics=self.include_statistics,
                sample_frequency=LHOPT_CONSTANTS["DEFAULT_SAMPLE_FREQUENCY"],
            )
        }
