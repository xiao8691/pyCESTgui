"""
示例数据生成脚本
生成测试用的NIfTI数据、mask和offset文件
"""

import numpy as np
import nibabel as nib
from pathlib import Path
import sys


def generate_example_data(output_dir: str = "example_data"):
    """
    生成示例CEST数据
    
    Parameters
    ----------
    output_dir : str
        输出目录路径
    """
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print("="*60)
    print("生成示例CEST数据")
    print("="*60)
    
    # 参数设定
    height, width = 64, 64
    n_offsets = 41  # 偏移点数
    
    # 1. 生成CEST数据
    print("\n1. 生成CEST Z-Spectroscopy数据...")
    
    # 生成频率偏移
    offsets = np.linspace(-4, 4, n_offsets)
    
    # Lorentzian函数
    def lorentzian(x, amp, fwhm, center):
        num = amp * 0.25 * fwhm ** 2
        den = 0.25 * fwhm ** 2 + (x - center) ** 2
        return num / den
    
    # 初始化CEST数据
    cest_data = np.ones((height, width, n_offsets))
    
    # 添加水峰、MT峰和其他成分
    for i in range(height):
        for j in range(width):
            # 基础信号
            base = 0.8
            
            # Water峰
            water_sig = lorentzian(offsets, 0.15, 0.2, 0)
            
            # MT峰
            mt_sig = lorentzian(offsets, 0.1, 40, -1)
            
            # Amide峰
            amide_sig = lorentzian(offsets, 0.02, 1.5, 3.5)
            
            # NOE峰
            noe_sig = lorentzian(offsets, 0.03, 1, -3.5)
            
            # Creatine峰
            creatine_sig = lorentzian(offsets, 0.015, 0.5, 2.0)
            
            # 组合信号
            signal = base - water_sig - mt_sig - amide_sig - noe_sig - creatine_sig
            
            # 添加高斯噪声
            noise = np.random.normal(0, 0.02, n_offsets)
            
            cest_data[i, j, :] = signal + noise
    
    # 确保信号在0-1之间
    cest_data = np.clip(cest_data, 0, 1)
    
    # 保存CEST数据
    affine = np.eye(4)
    cest_img = nib.Nifti1Image(cest_data, affine)
    cest_file = output_path / "example_cest.nii.gz"
    nib.save(cest_img, str(cest_file))
    print(f"   ✓ CEST数据已保存: {cest_file}")
    print(f"     - 尺寸: {cest_data.shape}")
    print(f"     - 范围: {cest_data.min():.3f} ~ {cest_data.max():.3f}")
    
    # 2. 生成Mask
    print("\n2. 生成ROI Mask...")
    
    mask = np.zeros((height, width))
    
    # 创建圆形ROI（中心和四个象限）
    center_y, center_x = height // 2, width // 2
    
    # 中心圆
    y, x = np.ogrid[:height, :width]
    circle1 = (x - center_x)**2 + (y - center_y)**2 <= 10**2
    mask[circle1] = 1
    
    # 四个象限的小圆
    positions = [
        (center_x - 20, center_y - 20),
        (center_x + 20, center_y - 20),
        (center_x - 20, center_y + 20),
        (center_x + 20, center_y + 20),
    ]
    
    for px, py in positions:
        circle = (x - px)**2 + (y - py)**2 <= 8**2
        mask[circle] = 1
    
    # 保存Mask
    mask_img = nib.Nifti1Image(mask.astype(np.uint8), affine)
    mask_file = output_path / "example_mask.nii.gz"
    nib.save(mask_img, str(mask_file))
    print(f"   ✓ Mask已保存: {mask_file}")
    print(f"     - 尺寸: {mask.shape}")
    print(f"     - ROI像素数: {np.sum(mask)}")
    
    # 3. 保存Offset
    print("\n3. 生成化学位移Offset...")
    
    offset_file = output_path / "example_offsets.txt"
    np.savetxt(str(offset_file), offsets, fmt='%.2f', header='offset (ppm)')
    print(f"   ✓ Offset已保存: {offset_file}")
    print(f"     - 点数: {len(offsets)}")
    print(f"     - 范围: {offsets.min():.2f} ~ {offsets.max():.2f} ppm")
    
    # 4. 生成使用说明
    print("\n4. 生成使用说明...")
    
    instruction_file = output_path / "README.txt"
    instruction_text = """
示例数据说明
============

本目录包含用于测试CEST图像处理GUI的示例数据。

文件说明：
- example_cest.nii.gz: CEST MRI数据（合成数据）
  * 尺寸: 64×64×41（高×宽×频谱点数）
  * 包含: Water, MT, Amide, NOE, Creatine等成分
  * 信噪比: SNR ≈ 20

- example_mask.nii.gz: ROI Mask（5个圆形区域）
  * 中心主ROI: 半径10像素
  * 4个象限ROI: 半径8像素各一个
  
- example_offsets.txt: 化学位移偏移量
  * 范围: -4 ~ +4 ppm
  * 点数: 41个
  * 间距: 0.2 ppm

使用步骤：
1. 启动CESTGui应用
2. 在"CEST数据"字段加载 example_cest.nii.gz
3. 在"Mask"字段加载 example_mask.nii.gz
4. 在"Offset"字段加载 example_offsets.txt
5. 选择代谢产物: Amide, Creatine, NOE(-3.5)
6. 点击[执行拟合]
7. 在Z谱标签页查看结果

预期结果：
- 水峰和MT峰应该清晰可见
- 代谢产物信号可以分别拟合
- RMSE应该 < 0.05

故障排除：
- 如果拟合失败，尝试:
  1. 启用PCA降噪 (75-85%)
  2. 启用B0校正
  3. 减少拟合产物的数量

数据格式说明：
- NIfTI格式（.nii.gz）
- offset为纯文本格式，每行一个数值

祝您使用愉快！
"""
    
    with open(instruction_file, 'w', encoding='utf-8') as f:
        f.write(instruction_text)
    print(f"   ✓ 说明文件已保存: {instruction_file}")
    
    # 5. 总结
    print("\n" + "="*60)
    print("✓ 示例数据生成完成！")
    print("="*60)
    
    print(f"\n生成的文件位置: {output_path.absolute()}")
    print("\n文件列表:")
    for file in sorted(output_path.glob("*")):
        size = file.stat().st_size if file.is_file() else 0
        size_str = f"{size/1024/1024:.1f} MB" if size > 1024*1024 else f"{size/1024:.1f} KB"
        print(f"  ✓ {file.name:<30} ({size_str})")
    
    print("\n下一步:")
    print("1. 打开CEST GUI应用")
    print("2. 加载这些示例文件进行测试")
    print("3. 按照README.txt中的说明操作")
    
    return True


if __name__ == "__main__":
    try:
        # 检查nibabel是否安装
        try:
            import nibabel
        except ImportError:
            print("错误: 需要安装nibabel库")
            print("请运行: pip install nibabel")
            sys.exit(1)
        
        # 检查命令行参数
        output_dir = sys.argv[1] if len(sys.argv) > 1 else "example_data"
        
        # 生成数据
        success = generate_example_data(output_dir)
        
        if success:
            print("\n✓ 数据生成成功！可以开始使用CEST GUI了。\n")
        
    except Exception as e:
        print(f"\n✗ 错误: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
