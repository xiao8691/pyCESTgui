"""
cx_Freeze build script for the CEST GUI application.
"""

import importlib.util
from pathlib import Path

import matplotlib
from cx_Freeze import Executable, setup


def get_package_dir(package_name):
    spec = importlib.util.find_spec(package_name)
    if spec is None or spec.origin is None:
        raise ModuleNotFoundError(f"未找到Python包: {package_name}")
    return Path(spec.origin).resolve().parent


project_dir = Path(__file__).resolve().parent
pyqt5_dir = get_package_dir("PyQt5")
matplotlib_data_dir = Path(matplotlib.get_data_path()).resolve()

build_exe_options = {
    "packages": [
        "src",
        "PyQt5",
        "numpy",
        "scipy",
        "sklearn",
        "matplotlib",
        "nibabel",
    ],
    "includes": [
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "PyQt5.sip",
        "matplotlib.backends.backend_qt5agg",
        "scipy.optimize",
        "scipy.interpolate",
        "scipy.ndimage",
        "sklearn.decomposition",
        "sklearn.metrics",
    ],
    "excludes": [
        "tkinter",
        "wx",
        "PySide2",
        "PySide6",
        "PyQt6",
        "pandas",
        "pandas.tests",
        "joblib.test",
        "matplotlib.tests",
        "nibabel.tests",
        "numpy.tests",
        "scipy.tests",
        "sklearn.tests",
    ],
    "include_files": [
        (str(pyqt5_dir), "lib/PyQt5"),
        (str(matplotlib_data_dir), "lib/matplotlib/mpl-data"),
    ],
    "include_msvcr": True,
    "optimize": 0,
}


executables = [
    Executable(
        script=str(project_dir / "main.py"),
        base="gui",
        target_name="CESTGui.exe",
    )
]


setup(
    name="CESTGui",
    version="1.0.0",
    description="CEST图像处理GUI工具",
    options={"build_exe": build_exe_options},
    executables=executables,
)