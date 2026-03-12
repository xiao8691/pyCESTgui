"""
完整流程测试脚本
测试数据加载、预处理和拟合
"""

import numpy as np
from src.modules import NIfTILoader, CESTFitter, Preprocessing
import sys

print("="*60)
print("CEST图像处理 - 完整流程测试")
print("="*60)

try:
    # 1. 加载数据
    print("\n1. 加载示例数据...")
    loader = NIfTILoader()
    cest_data = loader.load_nifti("example_data/example_cest.nii.gz")
    mask_data = loader.load_mask("example_data/example_mask.nii.gz")
    offsets = np.loadtxt("example_data/example_offsets.txt")
    
    print(f"   ✓ CEST数据: {cest_data.shape}")
    print(f"   ✓ Mask: {mask_data.shape}")
    print(f"   ✓ Offsets: {offsets.shape}")
    
    # 2. 提取ROI频谱
    print("\n2. 提取ROI频谱...")
    loader.data = cest_data
    roi_spectrum = loader.extract_roi_spectrum(mask_data)
    print(f"   ✓ ROI频谱形状: {roi_spectrum.shape}")
    print(f"   ✓ 频谱范围: {roi_spectrum.min():.4f} ~ {roi_spectrum.max():.4f}")
    
    # 3. 预处理
    print("\n3. 执行预处理...")
    preprocessor = Preprocessing()
    
    # PCA降噪
    print("   - PCA降噪 (80%)...")
    n_comp = int(cest_data.shape[-1] * 0.8)
    processed_data = preprocessor.pca_denoise(cest_data, n_components=n_comp)
    print("     ✓ 完成")
    
    # 高斯平滑
    print("   - 高斯平滑...")
    processed_data = preprocessor.gaussian_smooth(processed_data, sigma=1.0)
    print("     ✓ 完成")
    
    # 更新ROI频谱
    loader.data = processed_data
    roi_spectrum_processed = loader.extract_roi_spectrum(mask_data)
    print(f"   ✓ 预处理后频谱: {roi_spectrum_processed.shape}")
    
    # 4. CEST拟合
    print("\n4. 执行CEST拟合...")
    fitter = CESTFitter()
    
    # 选择代谢产物
    contrasts = ['NOE (-3.5 ppm)', 'Creatine', 'Amide']
    print(f"   选择产物: {', '.join(contrasts)}")
    
    # 执行拟合
    result = fitter.two_step_fit(roi_spectrum_processed, offsets, contrasts)
    
    if result['success']:
        print("\n   ✓ 拟合成功！")
        print(f"     - RMSE: {result['rmse']:.6f}")
        print(f"     - B0校正: {result['b0_correction']:.4f} ppm")
        print("\n   拟合参数:")
        for contrast_name, value in result['contrasts'].items():
            print(f"     - {contrast_name}: {value:.4f}%")
    else:
        print(f"\n   ✗ 拟合失败: {result['error']}")
        sys.exit(1)
    
    # 5. 测试逐像素拟合
    print("\n5. 测试逐像素拟合（样本像素）...")
    
    # 提取mask内的像素
    y_coords, x_coords = np.where(mask_data > 0)
    sample_pixels = processed_data[y_coords[:10], x_coords[:10], :]  # 测试10个像素
    
    print(f"   执行{len(sample_pixels)}个像素拟合...")
    pixel_results = fitter.fit_pixelwise(sample_pixels, offsets, contrasts)
    
    success_count = sum(1 for r in pixel_results if r['success'])
    print(f"   ✓ 成功拟合: {success_count}/{len(pixel_results)}")
    
    # 6. 总结
    print("\n" + "="*60)
    print("✓ 完整流程测试成功！")
    print("="*60)
    print("\n项目可以正常运行，可以进行以下步骤:")
    print("1. 运行GUI应用: python main.py")
    print("2. 加载example_data中的文件进行交互式分析")
    print("3. 打包为.exe: python build_exe.py")
    
except Exception as e:
    print(f"\n✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
