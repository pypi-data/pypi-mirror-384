# ======================================================================================================================
#
# IMPORTS
#
# ======================================================================================================================

from typing import TypedDict

# ======================================================================================================================
#
# CLASSES
#
# ======================================================================================================================


class LHOPTConstants(TypedDict):
    IS_NAN: float
    NOT_NAN: float
    IS_INF: float
    NOT_INF: float
    TANH_BOUND: float
    DEFAULT_DECAY_FACTOR: float
    DEFAULT_TIME_WINDOW: int
    DEFAULT_CHECKPOINT_INTERVAL: int
    DEFAULT_PERCENTILE: float
    ZERO_DIVISION_TOLERANCE: float
    DEFAULT_SAMPLE_FREQUENCY: int
    DEFAULT_VARIANCE_THRESHOLD: float
    DEFAULT_ENV_STEP_SAMPLE_FREQUENCY: int


# ======================================================================================================================
#
# CONSTANTS
#
# ======================================================================================================================


# Create the constants instance
LHOPT_CONSTANTS: LHOPTConstants = LHOPTConstants(
    IS_NAN=1.0,
    NOT_NAN=0.0,
    IS_INF=1.0,
    NOT_INF=0.0,
    TANH_BOUND=10.0,
    DEFAULT_DECAY_FACTOR=1.25,
    DEFAULT_TIME_WINDOW=32,
    DEFAULT_CHECKPOINT_INTERVAL=100,
    DEFAULT_PERCENTILE=0.6,
    ZERO_DIVISION_TOLERANCE=1e-8,
    DEFAULT_SAMPLE_FREQUENCY=4,
    DEFAULT_VARIANCE_THRESHOLD=1e-6,
    DEFAULT_ENV_STEP_SAMPLE_FREQUENCY=10,
)
