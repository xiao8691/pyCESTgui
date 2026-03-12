"""
CEST图像处理GUI工具 - 模块包
"""

from .nifti_loader import NIfTILoader, load_nifti_data, load_mask_data
from .preprocessing import Preprocessing
from .fitting import CESTFitter, FittingConfig
from .visualization import CESTVisualizer, MatplotlibFigureCanvas

__all__ = [
    'NIfTILoader',
    'load_nifti_data',
    'load_mask_data',
    'Preprocessing',
    'CESTFitter',
    'FittingConfig',
    'CESTVisualizer',
    'MatplotlibFigureCanvas',
]

__version__ = '1.0.0'
__author__ = 'Xiaoxiao Zhang'
