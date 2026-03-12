"""
CEST图像处理GUI工具
主应用入口
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

if getattr(sys, 'frozen', False):
    frozen_candidate_dirs = []

    meipass_dir = getattr(sys, '_MEIPASS', None)
    if meipass_dir:
        frozen_candidate_dirs.append(Path(meipass_dir))

    executable_dir = Path(sys.executable).resolve().parent
    frozen_candidate_dirs.extend([
        executable_dir,
        executable_dir / 'lib',
    ])

    for frozen_base_dir in frozen_candidate_dirs:
        qt_plugins_dir = frozen_base_dir / 'PyQt5' / 'Qt5' / 'plugins'
        qt_platforms_dir = qt_plugins_dir / 'platforms'
        if qt_plugins_dir.exists():
            os.environ.setdefault('QT_PLUGIN_PATH', str(qt_plugins_dir))
        if qt_platforms_dir.exists():
            os.environ.setdefault('QT_QPA_PLATFORM_PLUGIN_PATH', str(qt_platforms_dir))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from src.gui import MainWindow


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用风格
    app.setStyle('Fusion')
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
