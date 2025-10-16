from ..augmentation.random import (
    Random_X_Operation,
    Rotate_Translate,
)
from ..augmentation.splines import (
    Spline_Curve_Simplification,
    Spline_X_Simplification,
    Spline_Y_Perturbations,
    Spline_X_Perturbations,
    Spline_Smoothing,
)
from ..augmentation.abc_augmenter import Augmenter, IdentityAugmenter

from .nirs import (
    Haar,
    MultiplicativeScatterCorrection,
    SavitzkyGolay,
    Wavelet,
    msc,
    savgol,
    wavelet_transform,
    LogTransform,
    FirstDerivative,
    SecondDerivative,
    log_transform,
    first_derivative,
    second_derivative,
)

# Import scalers (including local aliases such as IdentityTransformer and
# RobustNormalVariate which are defined in the scalers module)
from .scalers import (
    IdentityTransformer,
    RobustNormalVariate,
    Derivate,
    Normalize,
    SimpleScale,
    derivate,
    norml,
    spl_norml,
    StandardNormalVariate,
)
from .signal import Baseline, Detrend, Gaussian, baseline, detrend, gaussian
from .features import CropTransformer, ResampleTransformer
from .resampler import Resampler
from .presets import (
    id_preprocessing,
    savgol_only,
    haar_only,
    nicon_set,
    decon_set,
    senseen_set,
    transf_set,
    special_set,
    small_set,
    dumb_set,
    dumb_and_dumber_set,
    dumb_set_2D,
    list_of_2D_sets,
    optimal_set_2D,
    preprocessing_list,
    fat_set,
)
from .targets import IntegerKBinsDiscretizer, RangeDiscretizer


__all__ = [
    # Data augmentation
    "Spline_Smoothing",
    "Spline_X_Perturbations",
    "Spline_Y_Perturbations",
    "Spline_X_Simplification",
    "Spline_Curve_Simplification",
    "Rotate_Translate",
    "Random_X_Operation",
    "Augmenter",
    "IdentityAugmenter",

    # Sklearn aliases
    "IdentityTransformer",  # sklearn.preprocessing.FunctionTransformer alias
    "StandardNormalVariate",  # sklearn.preprocessing.StandardScaler alias
    "RobustNormalVariate",  # sklearn.preprocessing.RobustScaler alias

    # NIRS transformations
    "SavitzkyGolay",
    "Haar",
    "MultiplicativeScatterCorrection",
    "Wavelet",
    "savgol",
    "msc",
    "wavelet_transform",
    "LogTransform",
    "FirstDerivative",
    "SecondDerivative",
    "log_transform",
    "first_derivative",
    "second_derivative",

    # Scalers
    "Normalize",
    "Derivate",
    "SimpleScale",
    "norml",
    "derivate",
    "spl_norml",

    # Signal processing
    "Baseline",
    "Detrend",
    "Gaussian",
    "baseline",
    "detrend",
    "gaussian",

    # Features
    "CropTransformer",
    "ResampleTransformer",

    # Wavelength resampling
    "Resampler",
    # Targets / discretizers
    "IntegerKBinsDiscretizer",
    "RangeDiscretizer",

    # Preset sets and helpers
    "id_preprocessing",
    "savgol_only",
    "haar_only",
    "nicon_set",
    "decon_set",
    "senseen_set",
    "transf_set",
    "special_set",
    "small_set",
    "dumb_set",
    "dumb_and_dumber_set",
    "dumb_set_2D",
    "list_of_2D_sets",
    "optimal_set_2D",
    "preprocessing_list",
    "fat_set",
]
