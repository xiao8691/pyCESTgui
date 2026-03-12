# Philips CEST图像处理GUI工具

开发者: Xiaoxiao Zhang

## 简介
这是一个基于PyQt5的 Philips CEST (Chemical Exchange Saturation Transfer) MRI 图像处理工具。提供直观的GUI界面，支持完整的CEST数据分析流程。

## 主要功能

### 1. 数据导入
- 支持NIfTI格式的CEST数据加载 (*.nii, *.nii.gz)
- 支持ROI mask加载
- 支持Chemical Shift Offset (ppm)文本文件导入

### 2. 预处理模块
- **PCA降噪**: 可配置主成分保留比例
- **图像配准**: 刚体配准（平移和旋转）
- **B0不均匀性校正**: 高斯或Lorentzian峰值检测
- **空间滤波**: 高斯平滑和中值滤波

### 3. CEST数据分析
- **2-Step Lorentzian拟合**
  - Step 1: Water和MT峰拟合及B0校正
  - Step 2: 代谢产物拟合（可选组件）

- **支持的代谢产物**:
  - Water (水峰)
  - MT (Magnetization Transfer)
  - NOE (-3.5 ppm)
  - NOE (-1.6 ppm)
  - Creatine (肌酸)
  - Amide (酰胺)
  - Amine (胺基)
  - Hydroxyl (羟基)

### 4. 结果展示
- **Z-Spectroscopy曲线**: 原始数据和多种拟合曲线
- **参数图**: 代谢产物百分比分布
- **ROI分析**: ROI内平均Z谱及拟合结果
- **结果表格**: 各ROI的拟合参数汇总

### 5. 数据导出
- CSV格式导出拟合结果
- Excel格式导出（可选）
- 参数图保存

## 系统要求
- Python 3.8+
- Windows / macOS / Linux
- 4GB+ RAM (推荐8GB以上)
- GPU: 可选，用于加速大规模图像处理

## 安装步骤

### 方法1: 从源代码运行
```bash
# 克隆或下载项目
cd pyCESTgui

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行应用
python main.py
```

### 方法2: 使用可执行文件
双击 `CESTGui.exe` 直接运行（无需Python环境）

## 打包为可执行文件

### 生成Windows .exe
```bash
# 安装PyInstaller
pip install pyinstaller

# 运行打包脚本
python build_exe.py
```

生成的可执行文件位于 `dist/` 目录下。

## 使用步骤

### 1. 加载数据
1. 点击"CEST数据"旁边的"浏览..."按钮选择NIfTI格式的CEST MRI文件
2. 点击"Mask"旁边的"浏览..."按钮选择ROI mask文件
3. 点击"Offset"旁边的"浏览..."按钮选择化学位移文本文件

### 2. 配置预处理
1. 勾选"启用PCA降噪"并设置保留比例（默认80%）
2. 勾选"启用高斯平滑"并调整平滑因子
3. "B0校正"默认启用，选择检测方法

### 3. 配置拟合参数
1. 在"选择代谱产物"中勾选要分析的组份
2. 选择分析模式："ROI平均"或"逐像素分析"

### 4. 执行分析
1. 点击"执行预处理"进行数据预处理
2. 点击"执行拟合"进行CEST拟合分析
3. 在"Z谱"选项卡中查看拟合曲线
4. 在"结果表格"中查看定量参数

### 5. 导出结果
点击"导出结果"将分析结果保存为CSV或Excel文件

## 文件结构
```
pyCESTgui/
├── main.py                  # 应用入口
├── requirements.txt         # Python依赖
├── build_exe.py            # 打包脚本
├── README.md               # 本文件
├── src/
│   ├── __init__.py
│   ├── modules/            # 核心算法模块
│   │   ├── __init__.py
│   │   ├── nifti_loader.py     # NIfTI文件处理
│   │   ├── preprocessing.py    # 预处理算法
│   │   ├── fitting.py          # CEST拟合算法
│   │   └── visualization.py    # 可视化显示
│   └── gui/                # GUI相关文件
│       ├── __init__.py
│       └── main_window.py      # PyQt5主窗口
├── resources/              # 资源文件（图标等）
└── dist/                   # 打包输出目录

```

## 关键算法说明

### Lorentzian拟合
Z-Spectroscopy频谱可以分解为多个Lorentzian峰：
$$I(\Delta\omega) = 1 - \sum_i \frac{A_i \cdot (FWHM_i/2)^2}{(FWHM_i/2)^2 + (\Delta\omega - \omega_i)^2}$$

其中：
- $A_i$: 峰振幅
- $FWHM_i$: 半高宽
- $\omega_i$: 峰中心位置
- $\Delta\omega$: 化学位移偏移

### 2-Step拟合策略
1. **Step 1**: 拟合Water和MT峰，获得B0校正值
2. **Step 2**: 使用校正后的偏移量拟合其他代谢产物

## 常见问题

### Q: 程序启动缓慢？
A: 首次加载需要初始化环境，这是正常的。如果持续缓慢，检查：
- 是否有病毒扫描程序干扰
- 磁盘空间是否充足
- 系统资源使用率

### Q: 拟合失败如何处理？
A: 检查以下几点：
- 数据格式是否正确（确保是NIfTI格式）
- offset顺序是否正确
- 是否有异常值或坏像素
- 尝试调整预处理参数

### Q: 如何批量处理多个患者数据？
A: 当前版本支持单个ROI分析。批量处理功能计划在下一版本实现。

## 性能优化建议

### 大数据处理
- 使用逐像素分析前，建议先用ROI平均模式验证参数
- 启用PCA降噪可显著加速处理
- 可选启用GPU加速（需支持CUDA)

### 内存优化
- 对3D数据进行切片处理
- 及时清理不需要的中间结果

## 故障排除

### 导入错误
如果出现"ModuleNotFoundError"，请确保：
1. 已安装所有依赖：`pip install -r requirements.txt`
2. Python版本>=3.8
3. 虚拟环境已激活

### GUI显示问题
- Windows: 更新显卡驱动
- Linux: 安装`python3-tk`和`python3-pyqt5`
- macOS: 确保安装了最新的PyQt5

## 更新日志

### v1.0.0 (2024-02)
- 首个发布版本
- 完成基础功能实现
- 支持2-step Lorentzian拟合
- GUI可视化展示
- 数据导入导出

## 引用
如果在学术研究中使用本工具，请引用：
```
pyCESTgui: A Python-based CEST MRI Analysis Tool
Version 1.0.0
```

## 许可证
MIT License

## 支持和反馈
如有问题或建议，请联系开发团队。

## 致谢
感谢所有贡献者和使用者的支持！

---
**更新时间**: 2024年3月
**联系方式**: [your contact info]
