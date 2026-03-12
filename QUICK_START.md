# CEST图像处理GUI工具 - 快速开始指南

## 1. 环境安装（仅需一次）

### 方案A: 使用可执行文件（推荐新用户）
1. 下载 `CESTGui.exe`
2. 双击运行，无需安装
3. 首次运行会初始化环境，请耐心等待

### 方案B: 从源代码运行（推荐开发者）

```bash
# 步骤1: 安装Python 3.8或更高版本
# 下载: https://www.python.org/downloads/

# 步骤2: 打开命令提示符，进入项目目录
cd E:\01_CEST\pyCESTgui

# 步骤3: 创建虚拟环境（推荐）
python -m venv venv

# 步骤4: 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 步骤5: 安装依赖
pip install -r requirements.txt

# 步骤6: 运行应用
python main.py
```

## 2. 准备数据

### 数据格式要求

#### CEST MRI数据
- **格式**: NIfTI格式 (*.nii 或 *.nii.gz)
- **维度**: 3D (H × W × T) 或 4D (H × W × Z × T)
  - H, W: 空间维度（像素）
  - Z: 切片维度（可选）
  - T: 频谱维度（化学位移偏移量个数）
- **数据范围**: 0~1（浮点数）或0~32767（整数）
- **建议分辨率**: 128×128 或更高

#### ROI Mask
- **格式**: NIfTI格式 (*.nii 或 *.nii.gz)
- **维度**: 与CEST数据的空间维度相同
- **值**: 二值化 (0 = 背景, 1 = ROI区域)
- **建议**: 使用医学图像软件（如ITK-SNAP/FSL）分割ROI

#### 化学位移偏移量 (Offset)
- **格式**: 纯文本 (*.txt) 或CSV
- **内容**: 单列数据，每行一个偏移值
- **单位**: ppm (parts per million)
- **顺序**: 可以是升序或降序
- **范围**: 典型范围 -5 ~ +5 ppm

### 示例文件结构
```
数据目录/
├── patient_001_cest.nii.gz      # CEST数据
├── patient_001_mask.nii.gz      # ROI mask
└── offsets.txt                  # 偏移量
```

### 示例offset文件 (offsets.txt)
```
-4.5
-3.8
-3.5
-3.2
...
3.2
3.5
3.8
4.5
```

## 3. 运行分析

### 首次使用流程

1. **加载数据**
   - 点击"CEST数据"旁"浏览"按钮，选择 `patient_001_cest.nii.gz`
   - 点击"Mask"旁"浏览"按钮，选择 `patient_001_mask.nii.gz`
   - 点击"Offset"旁"浏览"按钮，选择 `offsets.txt`
   - 应看到日志显示"成功加载"

2. **配置预处理** (可选)
   ```
   □ PCA降噪 (建议启用，比例: 80%)
   □ 高斯平滑 (可选，因子: 1.0)
   ☑ B0校正 (推荐启用，自动)
   ```

3. **选择代谢产物** (勾选要分析的)
   ```
   ☑ NOE (-3.5 ppm)    [必选]
   ☑ Creatine          [可选]
   ☑ Amide             [可选]
   ```

4. **执行处理**
   ```
   步骤1: 点击[执行预处理] (若已配置)
   步骤2: 点击[执行拟合]
   步骤3: 查看结果 (Z谱标签页)
   ```

5. **查看和导出结果**
   - Z谱图: 显示拟合曲线
   - 结果表格: 显示代谢产物百分比
   - 导出: 点击[导出结果]为CSV文件

## 4. 参数说明

### 预处理参数

| 参数 | 范围 | 推荐值 | 说明 |
|------|------|--------|------|
| PCA保留比例 | 30% ~ 95% | 80% | 越高保留细节越多，但降噪效果越弱 |
| 高斯平滑因子 | 0.5 ~ 5.0 | 1.0 | 越大越平滑，但细节损失越多 |

### 拟合参数

#### 代谢产物峰位置
| 产物 | 偏移量(ppm) | 常用性 |
|------|------------|-------|
| Water | 0 | 必选 |
| MT | -1 | 必选 |
| Amide | 3.5 | 高 |
| NOE (-3.5) | -3.5 | 高 |
| Creatine | 2.0 | 中 |
| NOE (-1.6) | -1.6 | 中 |
| Amine | 2.5 | 低 |
| Hydroxyl | 0.6 | 低 |

## 5. 常见场景

### 场景1: 脑肿瘤分析
```
选择产物: Amide, Creatine, NOE(-3.5)
预处理: PCA 85%, 不平滑
模式: 逐像素分析
输出: 参数图用于诊断恶性肿瘤
```

### 场景2: 脊髓损伤
```
选择产物: Amide, Amine
预处理: PCA 80%, 平滑 1.5
模式: ROI平均
输出: 各分节强度比较
```

### 场景3: 肌肉病变
```
选择产物: Creatine, NOE(-1.6)
预处理: 无, 启用B0
模式: ROI平均
输出: 肌酸含量评估
```

## 6. 输出文件说明

### CSV导出格式
```csv
ROI,Water%,MT%,Amide%,RMSE
ROI_1,85.34,12.45,2.21,0.0234
ROI_2,83.21,14.32,2.47,0.0198
```

### 参数图文件
- `param_water.nii`: Water百分比图
- `param_mt.nii`: MT百分比图
- `param_amide.nii`: Amide百分比图
- `param_noe35.nii`: NOE(-3.5)百分比图

## 7. 性能优化

### 对于大型数据集
```bash
# 提高处理速度的建议:
1. 启用PCA降噪 (降低噪声，加快收敛)
2. 使用ROI平均而不是逐像素 (首次验证)
3. 减小高斯平滑因子 (默认1.0)
4. 检查offsets点数 (减少不必要的点)
```

### 内存节省
```
1. 分割处理: 大数据分片进行
2. 关闭可视化: 仅保存结果
3. 减少保存的中间文件
```

## 8. 故障排除

### 错误: "无法加载NIfTI文件"
**原因**: 文件格式不正确
**解决**:
1. 确认使用了NIfTI格式 (*.nii 或 *.nii.gz)
2. 使用NIBabel库测试: 
   ```python
   import nibabel as nib
   img = nib.load('your_file.nii.gz')
   print(img.shape)
   ```

### 错误: "拟合失败"
**原因**: 数据质量问题或参数不合适
**解决**:
1. 检查offset范围是否覆盖整个谱
2. 尝试不同的预处理参数
3. 检查mask是否与数据对齐
4. 考虑数据是否需要归一化

### 错误: "内存不足"
**原因**: 数据太大或系统内存不足
**解决**:
1. 减少加载的数据维度
2. 关闭其他应用释放内存
3. 分割数据进行处理
4. 增加系统虚拟内存

### GUI显示问题
**症状**: 窗口显示不正常或字体模糊
**解决**:
- Windows: 更新显卡驱动
- 尝试: 右键→属性→兼容性→"禁用全屏优化"

## 9. 高级用法

### 批量处理脚本
创建 `batch_process.py`:
```python
import os
from src.modules import NIfTILoader, CESTFitter

data_dir = "path/to/data"
for patient_dir in os.listdir(data_dir):
    cest_file = os.path.join(data_dir, patient_dir, "cest.nii.gz")
    # 加载和处理...
```

### 自定义拟合参数
编辑 `src/modules/fitting.py` 中的 `FittingConfig` 类

## 10. 联系和反馈

如有问题：
- 查看README.md获取更多信息
- 检查日志窗口获取详细错误信息
- 保存日志信息用于故障排除

---

**祝您使用愉快！** 🎉
