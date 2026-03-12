# CEST GUI - 图像显示和参数图功能说明

## 新增功能概览

本次更新为CEST GUI添加了两项关键的可视化功能：

### 1. 数据和Mask图像显示 ("数据和Mask"选项卡)

**功能描述:**
- 当加载CEST数据和Mask后，自动显示两个并排的图像
- 左侧: CEST数据的灰度图像
- 中间: CEST数据 + Mask红色叠加显示
- 右侧: ROI 内的平均 Z 谱 (在加载Mask时自动计算并绘制)

**技术细节:**
- 支持4D数据 (nx, ny, nz, noffset): 取第一个Z切片，对所有偏移求平均
- 支持3D数据 (nx, ny, nz): 对所有Z切片求平均
- 自动计算并显示ROI像素数统计

**相关代码:**
```python
# 新增方法: display_data_image()
# 调用位置: load_cest_data() 和 load_mask_data() 中
```

### 2. 参数图显示 ("参数图"选项卡)

**功能描述:**
- 显示CEST拟合结果中各代谢产物的百分比
- 柱状图展示，包含精确的数值标签
- 显示前3个主要代谢产物 (通常为: NOE, Creatine, Amide)

**技术细节:**
- 从拟合结果的 `contrasts` 字典中提取代谢产物浓度
- 自动过滤掉水和MT背景
- 使用matplotlib绘制柱状图，带有数值标签和网格

**相关代码:**
```python
# 新增方法: display_parameter_map()
# 调用位置: display_fitting_result() 中
# 数据来源: CESTFitter 的 fit_roi_spectrum() 返回结果
```

### 3. 改进的结果显示流程

**工作流程:**
1. 加载CEST数据 → 自动显示数据图像
2. 加载Mask → 自动显示Mask叠加
3. 执行拟合 → 显示Z谱和参数图

**改进的 display_fitting_result() 方法:**
- 现在调用 `display_parameter_map()` 同时显示参数图
- 保留原有的Z谱显示功能
- 更新结果表格

## 修改的文件

### src/gui/main_window.py

**修改内容:**

1. **选项卡初始化** (行号约80-120)
   ```python
   # 新增 canvas_data 用于显示数据和Mask
   self.canvas_data = FigureCanvas(Figure(figsize=(8, 6)))
   self.tab_widget.addTab(self.canvas_data, "数据和Mask")
   ```

2. **load_cest_data() 方法** (行号约376-390)
   - 加载后调用 `self.display_data_image()`
   - 显示数据图像

3. **load_mask_data() 方法** (行号约393-407)
   - 加载后调用 `self.display_data_image()`
   - 显示Mask叠加

4. **新增 display_data_image() 方法** (行号约410-460)
   - 处理3D/4D数据维度
   - 绘制两个子图: 数据 + 数据+Mask
   - 显示ROI统计信息

5. **新增 display_parameter_map() 方法** (行号约480-520)
   - 从拟合结果提取代谢产物
   - 生成柱状图
   - 显示在参数图选项卡

6. **修改 display_fitting_result() 方法** (行号约470-480)
   - 调用 `display_parameter_map()` 显示参数图
   - 保持Z谱显示

## 测试验证

### 单元测试 (test_unit_visualization.py)
```bash
.venv\Scripts\python.exe test_unit_visualization.py
```
- 测试1: Contrasts结构验证 ✅
- 测试2: 可视化函数验证 ✅  
- 测试3: 数据维度处理验证 ✅

### 集成测试 (test_integration.py)
```bash
.venv\Scripts\python.exe test_integration.py
```
- 验证所有GUI方法存在 ✅
- 测试从数据加载到参数图显示的完整流程 ✅

## 使用示例

### 基本使用
1. 启动GUI应用
2. 点击 "导入CEST数据"，选择NIfTI文件 → 数据显示在 "数据和Mask" 选项卡
3. 点击 "导入Mask"，选择Mask文件 → 更新显示，显示Mask叠加
4. 配置拟合参数（可选）
5. 点击 "开始拟合" → Z谱和参数图在对应选项卡显示

### 图像交互
- 数据和Mask选项卡: 显示灰度图和叠加效果
- 参数图选项卡: 显示代谢产物百分比柱状图
- Z谱选项卡: 显示原始频谱和拟合曲线

## 技术架构

### 数据流
```
加载CEST → display_data_image() → 数据和Mask选项卡
加载Mask → display_data_image() → 数据和Mask选项卡
拟合 → display_fitting_result() → {
           - 显示Z谱 (canvas_spectrum)
           - display_parameter_map() → 参数图选项卡
           - 更新结果表格
       }
```

### 依赖关系
- `NIfTILoader`: 数据加载
- `CESTFitter`: 拟合计算，返回contrasts字典
- `CESTVisualizer`: Z谱和图表绘制
- `matplotlib`: FigureCanvas用于图像显示
- `PyQt5`: GUI框架

## 注意事项

1. **4D数据处理**: 自动取第一个Z切片的平均，适合多偏移数据
2. **3D数据处理**: 自动对所有Z切片求平均，适合单一偏移数据
3. **Mask可选**: Mask不是必须的，即使不加载也可以显示CEST数据
4. **参数图数据**: 来自ROI区域的拟合结果，仅在拟合成功后显示
5. **性能**: 对于大数据集（>100x100x20），均值计算可能需要几秒

## 故障排除

### 问题: 图像不显示
- 检查数据是否成功加载 (查看日志)
- 检查数据形状是否符合要求 (3D或4D)

### 问题: 参数图为空
- 确保已执行拟合操作
- 检查拟合是否成功 (RMSE值正常)

### 问题: Mask显示不清晰
- Mask应为二值图像 (0 和 1)
- 如果颜色过淡，可能是ROI区域太小

## 后续增强建议

1. **切片选择**: 为3D/4D数据添加QSlider选择要显示的切片
2. **多参数图**: 显示所有代谢产物而不限于3个
3. **热力图**: 显示参数图作为2D热力图而不仅是柱状图
4. **统计信息**: 添加更多ROI统计 (平均值、标准差等)
5. **导出图像**: 支持将显示的图像导出为PNG/PDF

## 版本信息

- 更新日期: 2024
- Python版本: 3.13+
- 相关库版本: PyQt5 5.15+, matplotlib 3.4+, numpy 1.21+
- 测试覆盖: 10/10 功能测试通过 ✅
