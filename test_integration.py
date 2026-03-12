#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
集成测试：模拟完整的CEST GUI工作流程
包括：数据加载、图像显示、拟合和参数图显示
"""

import sys
import os
import numpy as np
from typing import Dict, Tuple

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.modules.nifti_loader import NIfTILoader
from src.modules.fitting import CESTFitter
from src.modules.visualization import CESTVisualizer

try:
    import nibabel as nib
except ImportError:
    print("警告: nibabel未安装，跳过NIfTI文件生成")
    nib = None

class MockCESTGUI:
    """模拟CEST GUI的类，用于测试"""
    
    def __init__(self):
        self.cest_data = None
        self.mask_data = None
        self.offsets = None
        self.fit_results = None
        
    def load_cest_data(self, file_path: str) -> bool:
        """加载CEST数据"""
        try:
            loader = NIfTILoader()
            self.cest_data = loader.load_nifti(file_path)
            info = loader.get_data_info()
            print(f"✓ CEST数据加载: {info['shape']}")
            return True
        except Exception as e:
            print(f"✗ CEST数据加载失败: {e}")
            return False
    
    def load_mask_data(self, file_path: str) -> bool:
        """加载Mask数据"""
        try:
            loader = NIfTILoader()
            self.mask_data = loader.load_mask(file_path)
            print(f"✓ Mask数据加载: {self.mask_data.shape}")
            return True
        except Exception as e:
            print(f"✗ Mask数据加载失败: {e}")
            return False
    
    def display_data_image(self) -> Tuple[bool, str]:
        """模拟display_data_image函数"""
        try:
            if self.cest_data is None:
                return False, "CEST数据未加载"
            
            # 确定要显示的数据
            if len(self.cest_data.shape) == 4:
                display_data = np.mean(self.cest_data[:, :, 0, :], axis=2)
                info = "从4D数据 (第一个Z切片) 生成显示数据"
            else:
                display_data = np.mean(self.cest_data, axis=2)
                info = "从3D数据生成显示数据"
            
            # 验证形状
            if len(display_data.shape) != 2:
                return False, f"显示数据形状不正确: {display_data.shape}"
            
            # 如果有Mask，检查叠加
            if self.mask_data is not None:
                roi_pixels = np.sum(self.mask_data > 0)
                info += f" | ROI像素: {roi_pixels}"
            
            return True, info
        except Exception as e:
            return False, f"显示数据失败: {e}"
    
    def fit_roi(self, offsets: np.ndarray) -> bool:
        """对ROI区域进行拟合"""
        try:
            if self.cest_data is None or self.mask_data is None:
                return False
            
            # 提取ROI区域的数据
            roi_mask = self.mask_data > 0
            roi_data = self.cest_data[roi_mask]
            
            if roi_data.size == 0:
                return False
            
            # 获取ROI平均频谱
            if len(self.cest_data.shape) == 4:
                roi_spectrum = np.mean(self.cest_data[roi_mask], axis=0)
            else:
                # 对于3D数据，需要特殊处理
                roi_pixels = np.where(roi_mask)
                roi_spectrum = np.mean(self.cest_data[roi_pixels], axis=0)
            
            # 进行拟合
            fitter = CESTFitter()
            self.fit_results = fitter.fit_roi_spectrum(roi_spectrum, offsets)
            
            return self.fit_results['success']
        except Exception as e:
            print(f"拟合失败: {e}")
            return False
    
    def display_parameter_map(self) -> Tuple[bool, str]:
        """模拟display_parameter_map函数"""
        try:
            if self.fit_results is None or not self.fit_results['success']:
                return False, "拟合结果不可用"
            
            contrasts = self.fit_results['contrasts']
            metabolites = [k for k in contrasts.keys() if k not in ['Water', 'MT']]
            
            if not metabolites:
                return False, "没有找到代谢产物"
            
            # 验证contrasts结构
            values = []
            for metabolite in metabolites[:3]:
                value = contrasts.get(metabolite, 0)
                values.append(value)
            
            return True, f"代谢产物: {', '.join([f'{m}={v:.2f}%' for m, v in zip(metabolites[:3], values)])}"
        except Exception as e:
            return False, f"参数图显示失败: {e}"

def run_integration_test():
    """运行完整集成测试"""
    print("\n" + "=" * 70)
    print("CEST GUI 集成测试")
    print("=" * 70)
    
    # 准备测试数据
    print("\n[准备阶段] 生成示例数据...")
    data_dir = "example_data"
    os.makedirs(data_dir, exist_ok=True)
    
    cest_file = os.path.join(data_dir, "test_cest.nii.gz")
    mask_file = os.path.join(data_dir, "test_mask.nii.gz")
    offset_file = os.path.join(data_dir, "test_offset.txt")
    
    # 生成示例数据
    if not os.path.exists(cest_file) or not os.path.exists(mask_file):
        print("生成CEST和Mask数据...")
        if nib is not None:
            # 创建示例CEST数据 (50x50x10x20 - 50x50像素，10张切片，20个偏移)
            cest_data = np.random.rand(50, 50, 10, 20) * 0.5 + 0.7
            # 添加一些结构
            cest_data[15:35, 15:35, :, :] += 0.1
            
            # 创建示例Mask (仅标记中心区域)
            mask_data = np.zeros((50, 50, 10), dtype=np.uint8)
            mask_data[15:35, 15:35, :] = 1
            
            # 保存为NIfTI文件
            nib.save(nib.Nifti1Image(cest_data, np.eye(4)), cest_file)
            nib.save(nib.Nifti1Image(mask_data, np.eye(4)), mask_file)
        else:
            print("⚠️  nibabel不可用，无法生成NIfTI测试文件")
            print("✓ 跳过NIfTI数据生成")
    
    # 生成偏移文件
    if not os.path.exists(offset_file):
        offsets = np.linspace(-4, 4, 20)
        np.savetxt(offset_file, offsets)
        print(f"✓ 生成偏移文件: 20个点")
    
    # 加载偏移文件
    offsets = np.loadtxt(offset_file)
    print(f"✓ 偏移频率加载: {len(offsets)}个点, 范围: [{offsets.min():.1f}, {offsets.max():.1f}] ppm")
    
    # 创建GUI模拟对象
    print("\n[Data Loading Stage]")
    gui = MockCESTGUI()
    
    # 测试1: 加载CEST数据
    success_cest = gui.load_cest_data(cest_file)
    if not success_cest:
        print("[ERROR] CEST data loading failed, stopping test")
        return False
    
    # 测试2: 加载Mask数据
    success_mask = gui.load_mask_data(mask_file)
    if not success_mask:
        print("[ERROR] Mask loading failed, stopping test")
        return False
    
    # 测试3: 显示数据图像
    print("\n[Image Display Stage]")
    success_display, message = gui.display_data_image()
    print(f"[{'OK' if success_display else 'FAIL'}] Data image display: {message}")
    if not success_display:
        print("[ERROR] Image display failed")
        return False
    
    # 测试4: ROI拟合
    print("\n[Fitting Stage]")
    success_fit = gui.fit_roi(offsets)
    print(f"[{'OK' if success_fit else 'FAIL'}] ROI fitting: {'success' if success_fit else 'failed'}")
    if not success_fit:
        print("[ERROR] Fitting failed")
        return False
    
    # 显示拟合结果摘要
    if gui.fit_results['success']:
        print(f"  RMSE: {gui.fit_results['rmse']:.6f}")
        print(f"  Contrasts:")
        for key, value in gui.fit_results['contrasts'].items():
            print(f"    {key}: {value:.2f}%")
    
    # 测试5: 参数图显示
    print("\n[Parameter Map Display Stage]")
    success_param_map, message = gui.display_parameter_map()
    print(f"[{'OK' if success_param_map else 'FAIL'}] Parameter map display: {message}")
    if not success_param_map:
        print("[ERROR] Parameter map display failed")
        return False
    
    print("\n" + "=" * 70)
    print("[SUCCESS] All integration tests passed!")
    print("=" * 70)
    return True

def test_gui_methods_exist():
    """验证GUI类中所有必要的方法都存在"""
    print("\n[验证GUI方法]")
    from src.gui.main_window import MainWindow
    
    required_methods = [
        'load_cest_data',
        'load_mask_data',
        'display_data_image',
        'display_parameter_map',
        'display_fitting_result'
    ]
    
    all_exist = True
    for method_name in required_methods:
        has_method = hasattr(MainWindow, method_name)
        status = "OK" if has_method else "MISSING"
        print(f"  [{status}] {method_name}: {'exists' if has_method else 'not found'}")
        if not has_method:
            all_exist = False
    
    return all_exist

if __name__ == "__main__":
    try:
        # 验证GUI方法
        if not test_gui_methods_exist():
            print("\n[ERROR] GUI methods incomplete")
            sys.exit(1)
        
        # 运行集成测试
        if not run_integration_test():
            sys.exit(1)
        
        print("\n[SUCCESS] All tests passed, system ready!")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
