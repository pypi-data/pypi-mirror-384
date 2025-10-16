from .augmentation.random import (
    Random_X_Operation,
    Rotate_Translate
)
from .augmentation.splines import (
    Spline_Curve_Simplification,
    Spline_X_Simplification,
    Spline_Y_Perturbations,
    Spline_X_Perturbations,
    Spline_Smoothing
)
from .augmentation.abc_augmenter import Augmenter, IdentityAugmenter

from .transformations import (
    # NIRS transformations
    Haar,
    MultiplicativeScatterCorrection,
    SavitzkyGolay,
    Wavelet,
    msc,
    savgol,
    wavelet_transform,

    # Scalers
    Derivate,
    Normalize,
    SimpleScale,
    derivate,
    norml,
    spl_norml,

    # Signal processing
    Baseline,
    Detrend,
    Gaussian,
    baseline,
    detrend,
    gaussian,

    # Features
    CropTransformer,
    ResampleTransformer,

    # Sklearn aliases
    IdentityTransformer,
    StandardNormalVariate,
    RobustNormalVariate
)

__all__ = [
    # Data augmentation
    "Random_X_Operation",
    "Rotate_Translate",
    "Spline_Curve_Simplification",
    "Spline_X_Simplification",
    "Spline_Y_Perturbations",
    "Spline_X_Perturbations",
    "Spline_Smoothing",
    "Augmenter",
    "IdentityAugmenter",

    # NIRS transformations
    "Haar",
    "MultiplicativeScatterCorrection",
    "SavitzkyGolay",
    "Wavelet",
    "msc",
    "savgol",
    "wavelet_transform",

    # Scalers
    "Derivate",
    "Normalize",
    "SimpleScale",
    "derivate",
    "norml",
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

    # Sklearn aliases
    "IdentityTransformer",
    "StandardNormalVariate",
    "RobustNormalVariate"
]
