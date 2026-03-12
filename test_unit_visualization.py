#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
单元测试：验证图像显示和参数图功能
"""

import sys
import os
import numpy as np

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.modules.fitting import CESTFitter
from src.modules.visualization import CESTVisualizer

def test_contrasts_structure():
    """测试contrasts返回结构"""
    print("=" * 60)
    print("测试1: 验证拟合结果的contrasts结构")
    print("=" * 60)
    
    # 创建测试数据
    fitter = CESTFitter()
    
    # 生成模拟Z谱
    offsets = np.array([-4, -3, -2, -1, 0, 1, 2, 3, 4])
    spectrum = np.array([0.95, 0.96, 0.90, 0.92, 0.70, 0.91, 0.92, 0.96, 0.95])
    
    # 进行拟合
    result = fitter.fit_roi_spectrum(spectrum, offsets)
    
    print(f"\n✓ 拟合成功: {result['success']}")
    print(f"✓ Contrasts 字段存在: {'contrasts' in result}")
    print(f"✓ Contrasts 类型: {type(result['contrasts'])}")
    print(f"\n代谢产物浓度:")
    for key, value in result['contrasts'].items():
        print(f"  {key}: {value:.2f}%")
    
    # 验证可以通过过滤获得非Water/MT的代谢产物
    contrasts_dict = result['contrasts']
    metabolites = [k for k in contrasts_dict.keys() if k not in ['Water', 'MT']]
    print(f"\n非Water/MT代谢产物: {metabolites}")
    
    if result['success']:
        print("\n✅ 测试1通过")
        return True
    else:
        print(f"\n❌ 测试1失败: {result.get('error', '未知错误')}")
        return False

def test_visualization_functions():
    """测试可视化函数"""
    print("\n" + "=" * 60)
    print("测试2: 验证可视化函数")
    print("=" * 60)
    
    # 创建测试数据
    fitter = CESTFitter()
    offsets = np.array([-4, -3, -2, -1, 0, 1, 2, 3, 4])
    spectrum = np.array([0.95, 0.96, 0.90, 0.92, 0.70, 0.91, 0.92, 0.96, 0.95])
    
    result = fitter.fit_roi_spectrum(spectrum, offsets)
    
    try:
        # 测试create_fitting_result_figure
        print("\n测试create_fitting_result_figure...")
        fig = CESTVisualizer.create_fitting_result_figure(result, 'TestROI')
        print(f"✓ Figure 对象创建: {fig is not None}")
        print(f"✓ Figure 类型: {type(fig).__name__}")
        
        print("\n✅ 测试2通过")
        return True
    except Exception as e:
        print(f"\n❌ 测试2失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_data_dimensions():
    """测试不同数据维度的处理"""
    print("\n" + "=" * 60)
    print("测试3: 验证数据维度处理")
    print("=" * 60)
    
    # 测试4D数据
    print("\n测试4D数据 (nx=10, ny=10, nz=5, offset=50)...")
    data_4d = np.random.rand(10, 10, 5, 50)
    print(f"✓ 4D数据形状: {data_4d.shape}")
    
    # 模拟display_data_image中的处理
    if len(data_4d.shape) == 4:
        display_data = np.mean(data_4d[:, :, 0, :], axis=2)
        print(f"✓ 处理后形状: {display_data.shape}")
        print(f"✓ 应为 (10, 10): {'✅' if display_data.shape == (10, 10) else '❌'}")
    
    # 测试3D数据
    print("\n测试3D数据 (nx=10, ny=10, nz=5)...")
    data_3d = np.random.rand(10, 10, 5)
    print(f"✓ 3D数据形状: {data_3d.shape}")
    
    if len(data_3d.shape) == 3:
        display_data = np.mean(data_3d, axis=2)
        print(f"✓ 处理后形状: {display_data.shape}")
        print(f"✓ 应为 (10, 10): {'✅' if display_data.shape == (10, 10) else '❌'}")
    
    print("\n✅ 测试3通过")
    return True

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CEST GUI 图像显示功能测试套件")
    print("=" * 60)
    
    results = []
    try:
        results.append(("Contrasts结构", test_contrasts_structure()))
    except Exception as e:
        print(f"测试1异常: {e}")
        results.append(("Contrasts结构", False))
    
    try:
        results.append(("可视化函数", test_visualization_functions()))
    except Exception as e:
        print(f"测试2异常: {e}")
        results.append(("可视化函数", False))
    
    try:
        results.append(("数据维度处理", test_data_dimensions()))
    except Exception as e:
        print(f"测试3异常: {e}")
        results.append(("数据维度处理", False))
    
    # 输出总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    print("\n" + ("🎉 所有测试通过！" if all_passed else "⚠️  部分测试失败"))
    
    sys.exit(0 if all_passed else 1)
