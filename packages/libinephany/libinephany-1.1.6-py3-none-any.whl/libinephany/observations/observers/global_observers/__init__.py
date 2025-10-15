# ======================================================================================================================
#
# GLOBAL OBSERVERS PACKAGE
#
# This package contains all global observer classes used for collecting observations
# across the entire training process, not specific to individual agents.
#
# ======================================================================================================================


from .gradient_observers import (
    CosineSimilarityObserverOfGradientAndMomentum,
    CosineSimilarityObserverOfGradientAndUpdate,
    CosineSimilarityOfGradientAndParameter,
    GlobalFirstOrderGradients,
    GlobalSecondOrderGradients,
    LHOPTGradientVarianceFraction,
    LHOPTMomentumGradientRatio,
)
from .hyperparameter_observers import (
    InitialHyperparameters,
    LHOPTHyperparameterRatio,
    ModelFamilyOneHot,
    OptimizerTypeOneHot,
)
from .loss_observers import (
    LHOPTLossRatio,
    LHOPTTrainingLoss,
    LHOPTValidationLoss,
    LossRatio,
    PercentileOfLossAtEachCheckpoint,
    TrainingLoss,
    TrainingScore,
    ValidationLoss,
    ValidationScore,
)
from .model_observers import (
    GlobalActivations,
    GlobalLAMBTrustRatio,
    GlobalParameters,
    GlobalParameterUpdates,
    LHOPTAverageParameterUpdateMagnitudeObserver,
    LHOPTGlobalLAMBTrustRatio,
    LogRatioOfPreviousAndCurrentParamNormEnvStepObserver,
    LogRatioOfUpdateAndPreviousParamNormEnvStepObserver,
    LogRatioOfUpdateAndPreviousParamNormInnerStepObserver,
    NumberOfLayers,
    NumberOfParameters,
)
from .progress_observers import EpochsCompleted, ProgressAtEachCheckpoint, StagnationObserver, TrainingProgress

__all__ = [
    InitialHyperparameters.__name__,
    LHOPTHyperparameterRatio.__name__,
    OptimizerTypeOneHot.__name__,
    ModelFamilyOneHot.__name__,
    TrainingLoss.__name__,
    ValidationLoss.__name__,
    LossRatio.__name__,
    TrainingScore.__name__,
    ValidationScore.__name__,
    GlobalFirstOrderGradients.__name__,
    GlobalSecondOrderGradients.__name__,
    LHOPTGradientVarianceFraction.__name__,
    LHOPTMomentumGradientRatio.__name__,
    GlobalActivations.__name__,
    GlobalParameterUpdates.__name__,
    GlobalParameters.__name__,
    GlobalLAMBTrustRatio.__name__,
    NumberOfParameters.__name__,
    NumberOfLayers.__name__,
    LHOPTAverageParameterUpdateMagnitudeObserver.__name__,
    LogRatioOfPreviousAndCurrentParamNormEnvStepObserver.__name__,
    LogRatioOfUpdateAndPreviousParamNormEnvStepObserver.__name__,
    LogRatioOfUpdateAndPreviousParamNormInnerStepObserver.__name__,
    TrainingProgress.__name__,
    EpochsCompleted.__name__,
    ProgressAtEachCheckpoint.__name__,
    LHOPTTrainingLoss.__name__,
    LHOPTValidationLoss.__name__,
    LHOPTLossRatio.__name__,
    PercentileOfLossAtEachCheckpoint.__name__,
    LHOPTGlobalLAMBTrustRatio.__name__,
    CosineSimilarityObserverOfGradientAndMomentum.__name__,
    CosineSimilarityObserverOfGradientAndUpdate.__name__,
    CosineSimilarityOfGradientAndParameter.__name__,
    StagnationObserver.__name__,
]
