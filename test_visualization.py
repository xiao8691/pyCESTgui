#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试数据加载和图像显示功能
"""

import sys
import os
try:
    from PyQt5.QtWidgets import QApplication
except ImportError as e:
    print(f"错误: 无法导入PyQt5: {e}")
    print("请确保已安装: pip install PyQt5")
    sys.exit(1)

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gui.main_window import CESTGui
from src.utils.data_generator import DataGenerator
import os

def test_visualization():
    """测试可视化功能"""
    
    # 创建示例数据
    print("生成示例数据...")
    data_dir = "example_data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    
    gen = DataGenerator()
    cest_file = os.path.join(data_dir, "example_cest.nii.gz")
    offset_file = os.path.join(data_dir, "example_offset.txt")
    mask_file = os.path.join(data_dir, "example_mask.nii.gz")
    
    # 检查文件是否存在，不存在则生成
    if not os.path.exists(cest_file):
        print("生成CEST数据...")
        gen.generate_example_data(cest_file, mask_file, offset_file)
    
    # 启动GUI
    print("启动GUI应用...")
    app = QApplication(sys.argv)
    window = CESTGui()
    window.show()
    
    # 自动加载示例数据到GUI
    window.load_cest_data(cest_file)
    window.load_mask_data(mask_file)
    
    print("数据已加载到GUI")
    print("✓ CEST数据图像应该显示在'数据和Mask'选项卡")
    print("✓ Mask应该作为红色覆盖层显示")
    print("✓ ROI像素数应该显示在图像右上角")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_visualization()
