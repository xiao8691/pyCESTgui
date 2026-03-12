"""
PyQt5主窗口
CEST图像处理GUI工具
"""

import sys
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QLineEdit, QComboBox, QDoubleSpinBox,
    QCheckBox, QMessageBox, QFileDialog, QProgressBar, QTableWidget,
    QTableWidgetItem, QGroupBox, QFormLayout, QListWidget, QListWidgetItem,
    QSplitter, QFrame, QSlider
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QFont

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# 导入自定义模块
from src.modules import (
    NIfTILoader, Preprocessing, CESTFitter, CESTVisualizer
)


class WorkerThread(QObject):
    """后台工作线程"""
    
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, task_type: str, **kwargs):
        super().__init__()
        self.task_type = task_type
        self.kwargs = kwargs
    
    def run(self):
        """执行任务"""
        try:
            if self.task_type == 'fitting':
                self._run_fitting()
            elif self.task_type == 'preprocessing':
                self._run_preprocessing()
        except Exception as e:
            self.error.emit(str(e))
    
    def _run_fitting(self):
        """执行拟合任务"""
        spectrum = self.kwargs['spectrum']
        offsets = self.kwargs['offsets']
        contrasts = self.kwargs['contrasts']
        
        fitter = CESTFitter()
        result = fitter.two_step_fit(spectrum, offsets, contrasts)
        self.finished.emit(result)
    
    def _run_preprocessing(self):
        """执行预处理任务"""
        data = self.kwargs['data']
        operations = self.kwargs['operations']
        
        preprocessor = Preprocessing()
        processed_data = data
        
        for op_name, op_params in operations.items():
            self.progress.emit(0, f"执行: {op_name}...")

            if op_name == 'smooth':
                processed_data = preprocessor.gaussian_smooth(
                    processed_data, sigma=op_params.get('sigma', 1.0)
                )
        
        self.finished.emit({'processed_data': processed_data})


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CEST图像处理GUI工具 v1.0")
        self.setGeometry(100, 100, 1400, 900)
        
        # 数据存储
        self.original_cest_data = None
        self.cest_data = None
        self.mask_data = None
        self.offsets = None
        self.data_affine = None
        self.data_header = None
        self.b0_shift_map = None
        self.is_b0_corrected = False
        self.parameter_map_slice_index = 0
        self.analysis_state = None
        self.roi_specs = {}
        self.fit_results = {}
        
        # 初始化UI
        self.init_ui()
        
        # 设置logger
        self.log_message("系统已就绪，请开始操作")
    
    def init_ui(self):
        """初始化用户界面"""
        # 创建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout()
        
        # 左侧控制面板
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        # 1. 数据导入
        self.create_data_import_panel(left_layout)
        
        # 2. 预处理
        self.create_preprocessing_panel(left_layout)
        
        # 3. 拟合配置
        self.create_fitting_config_panel(left_layout)
        
        # 4. 执行按钮
        self.create_execution_buttons(left_layout)
        
        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(380)
        
        # 右侧显示区域
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        slice_widget = QWidget()
        slice_layout = QHBoxLayout()
        slice_layout.setContentsMargins(0, 0, 0, 0)
        self.slice_label = QLabel("参数图切片: 1/1")
        self.slice_slider = QSlider(Qt.Horizontal)
        self.slice_slider.setMinimum(0)
        self.slice_slider.setMaximum(0)
        self.slice_slider.setValue(0)
        self.slice_slider.setEnabled(False)
        self.slice_slider.valueChanged.connect(self.on_parameter_map_slice_changed)
        slice_layout.addWidget(QLabel("参数图层"))
        slice_layout.addWidget(self.slice_slider, 1)
        slice_layout.addWidget(self.slice_label)
        slice_widget.setLayout(slice_layout)

        # 创建选项卡
        self.tab_widget = QTabWidget()
        
        # 数据显示选项卡
        self.canvas_data = FigureCanvas(Figure(figsize=(8, 6)))
        self.tab_widget.addTab(self.canvas_data, "数据与Mask")
        
        # 频谱显示选项卡
        self.canvas_spectrum = FigureCanvas(Figure(figsize=(8, 6)))
        self.tab_widget.addTab(self.canvas_spectrum, "Z谱")
        
        # 参数图显示选项卡
        self.canvas_params = FigureCanvas(Figure(figsize=(8, 6)))
        self.tab_widget.addTab(self.canvas_params, "参数图")
        
        # 结果表格
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(
            ['ROI', 'Water%', 'MT%', 'Amide%', 'RMSE']
        )
        self.tab_widget.addTab(self.results_table, "结果表格")
        
        # 日志
        self.log_text = self.create_log_widget()
        self.tab_widget.addTab(self.log_text, "日志")
        
        right_layout.addWidget(self.tab_widget)
        right_layout.addWidget(slice_widget)
        right_panel.setLayout(right_layout)
        
        # 添加到主布局
        main_layout.addWidget(left_panel, 0, Qt.AlignTop)
        main_layout.addWidget(right_panel, 1)
        
        central_widget.setLayout(main_layout)
    
    def create_data_import_panel(self, parent_layout):
        """创建数据导入面板"""
        group = QGroupBox("1. 数据导入")
        layout = QFormLayout()
        
        # CEST数据
        self.cest_path_input = QLineEdit()
        self.cest_path_input.setReadOnly(True)
        btn_browse_cest = QPushButton("浏览...")
        btn_browse_cest.clicked.connect(self.browse_cest_file)
        
        cest_layout = QHBoxLayout()
        cest_layout.addWidget(self.cest_path_input, 1)
        cest_layout.addWidget(btn_browse_cest)
        layout.addRow("CEST数据 (*.nii):", cest_layout)
        
        # Mask数据
        self.mask_path_input = QLineEdit()
        self.mask_path_input.setReadOnly(True)
        btn_browse_mask = QPushButton("浏览...")
        btn_browse_mask.clicked.connect(self.browse_mask_file)
        
        mask_layout = QHBoxLayout()
        mask_layout.addWidget(self.mask_path_input, 1)
        mask_layout.addWidget(btn_browse_mask)
        layout.addRow("Mask (*.nii):", mask_layout)
        
        # Offset文件
        self.offset_path_input = QLineEdit()
        self.offset_path_input.setReadOnly(True)
        btn_browse_offset = QPushButton("浏览...")
        btn_browse_offset.clicked.connect(self.browse_offset_file)
        
        offset_layout = QHBoxLayout()
        offset_layout.addWidget(self.offset_path_input, 1)
        offset_layout.addWidget(btn_browse_offset)
        layout.addRow("Offset (*.txt):", offset_layout)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
    
    def create_preprocessing_panel(self, parent_layout):
        """创建预处理面板"""
        group = QGroupBox("2. 预处理选项")
        layout = QFormLayout()
        
        # 高斯平滑
        self.checkbox_smooth = QCheckBox("启用高斯平滑")
        layout.addRow(self.checkbox_smooth)
        
        self.spinbox_smooth = QDoubleSpinBox()
        self.spinbox_smooth.setMinimum(0.5)
        self.spinbox_smooth.setMaximum(5.0)
        self.spinbox_smooth.setValue(1.0)
        self.spinbox_smooth.setSingleStep(0.1)
        layout.addRow("平滑因子:", self.spinbox_smooth)
        
        # B0校正
        self.checkbox_b0 = QCheckBox("启用B0校正")
        self.checkbox_b0.setChecked(True)
        layout.addRow(self.checkbox_b0)
        
        self.combo_b0 = QComboBox()
        self.combo_b0.addItems(['高斯峰值', 'Lorentzian峰值'])
        layout.addRow("B0检测方法:", self.combo_b0)

        # 归一化
        self.checkbox_normalize = QCheckBox("启用归一化")
        self.checkbox_normalize.setChecked(True)
        layout.addRow(self.checkbox_normalize)

        self.label_normalize = QLabel("默认使用离0 ppm最远的点")
        layout.addRow("归一化参考:", self.label_normalize)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
    
    def create_fitting_config_panel(self, parent_layout):
        """创建拟合配置面板"""
        group = QGroupBox("3. 拟合配置")
        layout = QFormLayout()
        
        # 选择要拟合的代谢产物
        layout.addRow(QLabel("<b>选择代谢产物:</b>"))
        
        self.checkbox_water = QCheckBox("Water")
        self.checkbox_water.setChecked(True)
        self.checkbox_water.setEnabled(False)
        layout.addRow(self.checkbox_water)
        
        self.checkbox_mt = QCheckBox("MT")
        self.checkbox_mt.setChecked(True)
        self.checkbox_mt.setEnabled(False)
        layout.addRow(self.checkbox_mt)
        
        self.checkbox_noe35 = QCheckBox("NOE (-3.5 ppm)")
        self.checkbox_noe35.setChecked(True)
        layout.addRow(self.checkbox_noe35)
        
        self.checkbox_noe16 = QCheckBox("NOE (-1.6 ppm)")
        layout.addRow(self.checkbox_noe16)
        
        self.checkbox_creatine = QCheckBox("Creatine")
        self.checkbox_creatine.setChecked(True)
        layout.addRow(self.checkbox_creatine)
        
        self.checkbox_amide = QCheckBox("Amide")
        self.checkbox_amide.setChecked(True)
        layout.addRow(self.checkbox_amide)
        
        self.checkbox_amine = QCheckBox("Amine")
        layout.addRow(self.checkbox_amine)
        
        self.checkbox_hydroxyl = QCheckBox("Hydroxyl")
        layout.addRow(self.checkbox_hydroxyl)
        
        # 分析模式
        layout.addRow(QLabel("<b>分析模式:</b>"))
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(['ROI平均', '逐像素分析'])
        layout.addRow("模式:", self.combo_mode)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
    
    def create_execution_buttons(self, parent_layout):
        """创建执行按钮"""
        # 预处理按钮
        self.btn_preprocess = QPushButton("执行预处理")
        self.btn_preprocess.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "font-weight: bold; padding: 8px; }"
        )
        self.btn_preprocess.clicked.connect(self.run_preprocessing)
        parent_layout.addWidget(self.btn_preprocess)
        
        # 拟合按钮
        self.btn_fit = QPushButton("执行拟合")
        self.btn_fit.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; "
            "font-weight: bold; padding: 8px; }"
        )
        self.btn_fit.clicked.connect(self.run_fitting)
        parent_layout.addWidget(self.btn_fit)
        
        # 导出结果按钮
        self.btn_export = QPushButton("导出结果")
        self.btn_export.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; "
            "font-weight: bold; padding: 8px; }"
        )
        self.btn_export.clicked.connect(self.export_results)
        parent_layout.addWidget(self.btn_export)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        parent_layout.addWidget(self.progress_bar)
    
    def create_log_widget(self):
        """创建日志文本框"""
        from PyQt5.QtWidgets import QTextEdit
        log_text = QTextEdit()
        log_text.setReadOnly(True)
        return log_text
    
    def log_message(self, message: str):
        """记录日志消息"""
        if hasattr(self, 'log_text'):
            self.log_text.append(f"[信息] {message}")
    
    def browse_cest_file(self):
        """浏览CEST数据文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择CEST数据文件", "", "NIfTI文件 (*.nii *.nii.gz)"
        )
        if file_path:
            self.cest_path_input.setText(file_path)
            self.load_cest_data(file_path)
    
    def browse_mask_file(self):
        """浏览Mask文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Mask文件", "", "NIfTI文件 (*.nii *.nii.gz)"
        )
        if file_path:
            self.mask_path_input.setText(file_path)
            self.load_mask_data(file_path)
    
    def browse_offset_file(self):
        """浏览Offset文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Offset文件", "", "文本文件 (*.txt)"
        )
        if file_path:
            self.offset_path_input.setText(file_path)
            self.load_offset_data(file_path)
    
    def load_cest_data(self, file_path: str):
        """加载CEST数据"""
        try:
            loader = NIfTILoader()
            self.original_cest_data = loader.load_nifti(file_path)
            self.cest_data = np.array(self.original_cest_data, copy=True)
            self.sort_offsets_and_data_if_needed(log_if_sorted=False)
            self.data_affine = loader.affine
            self.data_header = loader.header.copy() if loader.header is not None else None
            self.b0_shift_map = None
            self.is_b0_corrected = False
            self.update_slice_controls()
            info = loader.get_data_info()
            self.log_message(f"CEST数据加载成功: {info['shape']}")
            
            # 显示CEST数据图像
            self.display_data_image()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载CEST数据失败: {str(e)}")
    
    def load_mask_data(self, file_path: str):
        """加载Mask数据"""
        try:
            loader = NIfTILoader()
            self.mask_data = loader.load_mask(file_path)
            self.update_slice_controls()
            self.log_message(f"Mask数据加载成功: {self.mask_data.shape}")
            
            # 显示Mask图像和与CEST数据的叠加
            self.display_data_image()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载Mask数据失败: {str(e)}")
    
    def load_offset_data(self, file_path: str):
        """加载Offset数据"""
        try:
            self.offsets = np.loadtxt(file_path)
            self.sort_offsets_and_data_if_needed(log_if_sorted=True)
            self.log_message(f"Offset数据加载成功: {len(self.offsets)}个点")
            self.display_data_image()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载Offset数据失败: {str(e)}")

    def sort_offsets_and_data_if_needed(self, log_if_sorted: bool = True):
        """若offset未按升序排列，则自动排序并同步重排数据最后一维。"""
        if self.offsets is None:
            return

        offsets = np.asarray(self.offsets, dtype=float).reshape(-1)
        original_offsets = offsets.copy()
        sort_index = np.argsort(offsets)

        if np.array_equal(sort_index, np.arange(offsets.shape[0])):
            self.offsets = offsets
            return

        self.offsets = offsets[sort_index]

        if self.original_cest_data is not None and self.original_cest_data.shape[-1] == len(sort_index):
            self.original_cest_data = np.take(self.original_cest_data, sort_index, axis=-1)

        if self.cest_data is not None and self.cest_data.shape[-1] == len(sort_index):
            self.cest_data = np.take(self.cest_data, sort_index, axis=-1)

        self.analysis_state = None
        self.fit_results = {}
        self.b0_shift_map = None
        self.is_b0_corrected = False

        if log_if_sorted:
            preview_count = min(5, len(original_offsets))
            before_preview = ', '.join(f"{value:.3f}" for value in original_offsets[:preview_count])
            after_preview = ', '.join(f"{value:.3f}" for value in self.offsets[:preview_count])
            self.log_message("检测到Offset未按ppm升序排列，已自动排序并同步重排数据")
            self.log_message(f"排序前前{preview_count}个offset: {before_preview}")
            self.log_message(f"排序后前{preview_count}个offset: {after_preview}")
    
    def run_preprocessing(self):
        """执行预处理"""
        if self.cest_data is None:
            QMessageBox.warning(self, "警告", "请先加载CEST数据")
            return
        
        self.log_message("开始预处理...")
        self.progress_bar.setVisible(True)
        
        preprocessor = Preprocessing()
        processed_data = self.cest_data.copy()
        
        # 高斯平滑
        if self.checkbox_smooth.isChecked():
            self.log_message("执行高斯平滑...")
            processed_data = preprocessor.gaussian_smooth(
                processed_data, sigma=self.spinbox_smooth.value()
            )

        if self.checkbox_b0.isChecked():
            self.log_message("执行逐像素B0校正...")
            b0_method = 'gaussian' if self.combo_b0.currentIndex() == 0 else 'lorentzian'
            processed_data, self.b0_shift_map = preprocessor.voxelwise_b0_correction(
                processed_data,
                self.offsets,
                method=b0_method,
                mask=self.mask_data,
            )
            self.is_b0_corrected = True
            self.log_message("逐像素B0校正完成，后续ROI分析和参数图将基于校正后数据")
        else:
            self.b0_shift_map = None
            self.is_b0_corrected = False

        if self.checkbox_normalize.isChecked():
            self.log_message("归一化将在校正后的ROI/像素频谱上执行，并自动去除归一化参考点")
        
        self.cest_data = processed_data
        self.analysis_state = None
        self.log_message("预处理完成！")
        self.progress_bar.setVisible(False)
    
    def run_fitting(self):
        """执行拟合"""
        if self.cest_data is None or self.offsets is None:
            QMessageBox.warning(self, "警告", "请先加载所有必需的数据")
            return
        
        self.log_message("开始CEST拟合...")
        self.progress_bar.setVisible(True)
        
        # 获取选中的代谢产物
        contrasts = []
        if self.checkbox_noe35.isChecked():
            contrasts.append('NOE (-3.5 ppm)')
        if self.checkbox_noe16.isChecked():
            contrasts.append('NOE (-1.6 ppm)')
        if self.checkbox_creatine.isChecked():
            contrasts.append('Creatine')
        if self.checkbox_amide.isChecked():
            contrasts.append('Amide')
        if self.checkbox_amine.isChecked():
            contrasts.append('Amine')
        if self.checkbox_hydroxyl.isChecked():
            contrasts.append('Hydroxyl')
        
        if not contrasts:
            contrasts = ['NOE (-3.5 ppm)', 'Creatine', 'Amide']
        
        analysis = self.prepare_roi_spectrum_for_analysis()
        roi_spectrum = analysis['fit_spectrum']
        fit_offsets = analysis['fit_offsets']
        
        # 执行拟合
        fitter = CESTFitter()
        result = fitter.two_step_fit(
            roi_spectrum,
            fit_offsets,
            contrasts,
            apply_b0_correction=False,
        )

        result['raw_offsets'] = analysis['raw_offsets']
        result['raw_spectrum'] = analysis['raw_spectrum']
        result['normalization_offset'] = analysis['normalization_offset']
        result['normalization_index'] = analysis['normalization_index']
        result['normalization_value'] = analysis['normalization_value']
        result['external_b0_shift'] = analysis['b0_shift']
        result['selected_contrasts'] = contrasts

        parameter_maps = self.generate_parameter_maps(contrasts)
        if parameter_maps:
            result['parameter_maps'] = parameter_maps
        
        self.fit_results['ROI_1'] = result
        
        # 显示结果
        if result['success']:
            self.log_message(f"拟合成功！RMSE: {result['rmse']:.4f}")
            self.display_fitting_result(result, 'ROI_1')
        else:
            self.log_message(f"拟合失败: {result['error']}")
        
        self.progress_bar.setVisible(False)

    def prepare_spectrum_for_analysis(self, spectrum: np.ndarray, offsets: np.ndarray) -> Dict:
        """按当前设置准备单条频谱用于显示和拟合。"""
        preprocessor = Preprocessing()
        raw_spectrum = np.asarray(spectrum, dtype=float)
        working_offsets = np.asarray(offsets, dtype=float).copy()
        working_spectrum = raw_spectrum.copy()

        b0_shift = 0.0

        normalization_index = None
        normalization_offset = None
        normalization_value = None
        if self.checkbox_normalize.isChecked():
            working_spectrum, normalization_index, normalization_offset, normalization_value = (
                preprocessor.normalize_spectrum(working_spectrum, working_offsets)
            )
            working_spectrum, working_offsets = preprocessor.remove_offset_index(
                working_spectrum,
                working_offsets,
                normalization_index,
            )

        return {
            'raw_spectrum': raw_spectrum,
            'raw_offsets': np.asarray(offsets, dtype=float).copy(),
            'fit_spectrum': working_spectrum,
            'fit_offsets': working_offsets,
            'display_spectrum': working_spectrum,
            'display_offsets': working_offsets,
            'b0_shift': b0_shift,
            'normalization_index': normalization_index,
            'normalization_offset': normalization_offset,
            'normalization_value': normalization_value,
        }

    def extract_roi_spectrum(self, data=None):
        """提取ROI平均频谱。"""
        source_data = self.cest_data if data is None else data

        if source_data is None:
            raise ValueError("缺少CEST数据")

        if self.mask_data is not None:
            loader = NIfTILoader()
            loader.data = source_data
            return loader.extract_roi_spectrum(self.mask_data)

        if source_data.ndim >= 4:
            return np.mean(source_data, axis=(0, 1, 2))

        return np.mean(source_data, axis=tuple(range(source_data.ndim - 1)))

    def prepare_raw_roi_spectrum_for_display(self):
        """为数据页准备原始ROI频谱，不做预处理、不做归一化。"""
        if self.original_cest_data is None or self.offsets is None:
            raise ValueError("缺少原始CEST数据或offsets")

        raw_spectrum = np.asarray(self.extract_roi_spectrum(self.original_cest_data), dtype=float)
        raw_offsets = np.asarray(self.offsets, dtype=float).copy()
        display_mask = (raw_offsets >= -8.0) & (raw_offsets <= 8.0)

        if np.any(display_mask):
            display_offsets = raw_offsets[display_mask]
            display_spectrum = raw_spectrum[display_mask]
        else:
            display_offsets = raw_offsets
            display_spectrum = raw_spectrum

        return {
            'display_offsets': display_offsets,
            'display_spectrum': display_spectrum,
            'raw_offsets': raw_offsets,
            'raw_spectrum': raw_spectrum,
        }

    def prepare_roi_spectrum_for_analysis(self):
        """按 B0校正 -> 归一化 -> 去除归一点 的顺序准备ROI频谱。"""
        if self.cest_data is None or self.offsets is None:
            raise ValueError("缺少CEST数据或offsets")

        analysis = self.prepare_spectrum_for_analysis(
            self.extract_roi_spectrum(),
            self.offsets,
        )
        self.analysis_state = analysis
        return analysis

    def get_parameter_map_background(self) -> Tuple[np.ndarray, Optional[int]]:
        """返回参数图显示所需的背景图和切片索引。"""
        if self.original_cest_data is None:
            raise ValueError("缺少原始数据")

        if self.original_cest_data.ndim == 4:
            slice_index = min(self.parameter_map_slice_index, self.original_cest_data.shape[2] - 1)
            background = np.mean(self.original_cest_data[:, :, slice_index, :], axis=2)
            return background, slice_index

        if self.original_cest_data.ndim == 3:
            if self.mask_data is not None and self.mask_data.ndim == 3:
                slice_index = min(self.parameter_map_slice_index, self.original_cest_data.shape[2] - 1)
                background = self.original_cest_data[:, :, slice_index]
                return background, slice_index
            background = np.mean(self.original_cest_data, axis=2)
            return background, None

        return np.squeeze(self.original_cest_data), None

    def get_slice_count(self) -> int:
        """返回参数图可浏览的切片数。"""
        if self.original_cest_data is None:
            return 1
        if self.original_cest_data.ndim == 4:
            return int(self.original_cest_data.shape[2])
        if self.original_cest_data.ndim == 3 and self.mask_data is not None and self.mask_data.ndim == 3:
            return int(self.original_cest_data.shape[2])
        return 1

    def get_default_display_slice_index(self) -> int:
        """返回原始图显示用的代表层。"""
        slice_count = self.get_slice_count()
        if slice_count <= 1:
            return 0
        if self.mask_data is not None and self.mask_data.ndim == 3:
            return int(np.argmax(np.sum(self.mask_data > 0, axis=(0, 1))))
        return slice_count // 2

    def update_slice_controls(self):
        """根据当前数据更新参数图切片滑块。"""
        slice_count = self.get_slice_count()
        self.parameter_map_slice_index = min(self.parameter_map_slice_index, max(slice_count - 1, 0))
        self.slice_slider.blockSignals(True)
        self.slice_slider.setEnabled(slice_count > 1)
        self.slice_slider.setMinimum(0)
        self.slice_slider.setMaximum(max(slice_count - 1, 0))
        self.slice_slider.setValue(self.parameter_map_slice_index)
        self.slice_slider.blockSignals(False)
        self.slice_label.setText(f"参数图切片: {self.parameter_map_slice_index + 1}/{slice_count}")

    def on_parameter_map_slice_changed(self, value: int):
        """切换参数图显示切片。"""
        self.parameter_map_slice_index = int(value)
        self.update_slice_controls()
        if self.fit_results.get('ROI_1', {}).get('success'):
            self.display_parameter_map(self.fit_results['ROI_1'], 'ROI_1')

    def generate_parameter_maps(self, contrasts: List[str]) -> Dict[str, np.ndarray]:
        """对mask内像素逐点拟合并生成参数图。"""
        if self.cest_data is None or self.offsets is None:
            return {}

        if self.cest_data.ndim < 3:
            return {}

        fitter = CESTFitter()
        map_names = ['Water', 'MT'] + [
            contrast_name for contrast_name in contrasts
            if contrast_name not in {'Water', 'MT'}
        ]

        if self.mask_data is not None:
            fit_mask = self.mask_data > 0
        else:
            fit_mask = np.ones(self.cest_data.shape[:-1], dtype=bool)

        parameter_maps = {
            name: np.full(fit_mask.shape, np.nan, dtype=float)
            for name in map_names
        }

        valid_indices = np.argwhere(fit_mask)
        total = len(valid_indices)
        if total == 0:
            return {}

        self.log_message(f"开始生成参数图，共 {total} 个像素")
        for index, voxel_index in enumerate(valid_indices, start=1):
            voxel_index_tuple = tuple(int(v) for v in voxel_index)
            voxel_spectrum = np.asarray(self.cest_data[voxel_index_tuple], dtype=float)

            try:
                analysis = self.prepare_spectrum_for_analysis(voxel_spectrum, self.offsets)
                voxel_result = fitter.two_step_fit(
                    analysis['fit_spectrum'],
                    analysis['fit_offsets'],
                    contrasts,
                    apply_b0_correction=False,
                )
                if voxel_result.get('success'):
                    parameter_maps['Water'][voxel_index_tuple] = voxel_result['contrasts'].get('Water', np.nan)
                    parameter_maps['MT'][voxel_index_tuple] = voxel_result['contrasts'].get('MT', np.nan)
                    for contrast_name in contrasts:
                        parameter_maps[contrast_name][voxel_index_tuple] = voxel_result['contrasts'].get(
                            contrast_name,
                            np.nan,
                        )
            except Exception:
                continue

            if index == total or index % max(1, total // 10) == 0:
                self.log_message(f"参数图进度: {index}/{total}")

        return parameter_maps
    
    def display_data_image(self):
        """显示加载的CEST和Mask图像

        - 将三维/四维数据投影为二维图像
        - 将三维mask降为二维并叠加
        - 显示原始ROI平均Z谱，不做预处理和归一化
        """
        if self.original_cest_data is None:
            return
        
        fig = Figure(figsize=(10, 5))
        
        # 处理数据维度并生成显示图像
        if self.original_cest_data.ndim == 4:
            slice_index = self.get_default_display_slice_index()
            display_data = np.mean(self.original_cest_data[:, :, slice_index, :], axis=2)
        elif self.original_cest_data.ndim == 3:
            if self.mask_data is not None and self.mask_data.ndim == 3:
                slice_index = self.get_default_display_slice_index()
                display_data = self.original_cest_data[:, :, slice_index]
            else:
                display_data = np.mean(self.original_cest_data, axis=2)
        else:
            display_data = np.squeeze(self.original_cest_data)
        
        # 左图：CEST + mask叠加
        ax1 = fig.add_subplot(121)
        im1 = ax1.imshow(display_data, cmap='gray')
        ax1.set_title('CEST + Mask', fontsize=12, fontweight='bold')
        ax1.set_aspect('equal')
        ax1.set_xticks([])
        ax1.set_yticks([])
        
        if self.mask_data is not None:
            if self.mask_data.ndim == 3:
                if self.get_slice_count() > 1:
                    slice_index = self.get_default_display_slice_index()
                    mask_proj = self.mask_data[:, :, slice_index] > 0
                else:
                    mask_proj = np.any(self.mask_data > 0, axis=2)
            elif self.mask_data.ndim == 2:
                mask_proj = self.mask_data > 0
            else:
                mask_proj = np.squeeze(self.mask_data) > 0
            mask_overlay = np.ma.masked_where(~mask_proj, mask_proj)
            ax1.imshow(mask_overlay, cmap='Reds', alpha=0.5)
            roi_pixels = np.sum(mask_proj)
            ax1.text(0.02, 0.98, f'ROI像素数: {roi_pixels}', transform=ax1.transAxes,
                    verticalalignment='top', fontsize=9,
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        else:
            ax1.text(0.5, 0.5, 'Mask未加载', ha='center', va='center',
                    transform=ax1.transAxes, fontsize=12, color='gray')
        
        # 右图：ROI内的平均Z谱
        ax2 = fig.add_subplot(122)
        if self.offsets is not None:
            try:
                raw_display = self.prepare_raw_roi_spectrum_for_display()
                ax2.plot(raw_display['display_offsets'], raw_display['display_spectrum'], 'bo-')
                ax2.set_xlabel('Offset (ppm)')
                ax2.set_ylabel('Signal')
                ax2.set_title('ROI 原始Z谱')
                ax2.grid(True, alpha=0.3)
                ax2.set_xlim(8, -8)
            except Exception as e:
                ax2.text(0.5, 0.5, f'计算Z谱失败: {e}', ha='center', va='center')
        else:
            ax2.text(0.5, 0.5, '未加载offsets', ha='center', va='center')
        
        fig.tight_layout()
        self.canvas_data.figure = fig
        self.canvas_data.draw()
    
    def display_fitting_result(self, result: Dict, roi_label: str):
        """显示拟合结果"""
        # 绘制Z谱
        fig_spectrum = CESTVisualizer.create_fitting_result_figure(result, roi_label)
        self.canvas_spectrum.figure = fig_spectrum
        self.canvas_spectrum.draw()
        
        # 绘制参数图
        if result['success']:
            self.display_parameter_map(result, roi_label)
        
        # 更新结果表格
        self.update_results_table(result, roi_label)
    
    def display_parameter_map(self, result: Dict, roi_label: str):
        """显示参数图"""
        if not result['success']:
            return

        parameter_maps = result.get('parameter_maps')
        if not parameter_maps:
            return

        map_names = list(parameter_maps.keys())
        n_cols = min(3, len(map_names))
        n_rows = (len(map_names) + n_cols - 1) // n_cols
        fig = Figure(figsize=(5 * n_cols, 4.5 * n_rows))

        background, slice_index = self.get_parameter_map_background()
        mask_slice = None
        if self.mask_data is not None:
            if self.mask_data.ndim == 3 and slice_index is not None:
                mask_slice = self.mask_data[:, :, slice_index] > 0
            elif self.mask_data.ndim == 2:
                mask_slice = self.mask_data > 0

        for idx, map_name in enumerate(map_names, start=1):
            ax = fig.add_subplot(n_rows, n_cols, idx)
            ax.imshow(background, cmap='gray')

            param_map = parameter_maps[map_name]
            if param_map.ndim == 3 and slice_index is not None:
                display_map = param_map[:, :, slice_index]
            else:
                display_map = param_map

            display_map = np.asarray(display_map, dtype=float)
            overlay = np.ma.masked_invalid(display_map)
            im = ax.imshow(overlay, cmap='magma', alpha=0.75)
            ax.set_title(map_name, fontsize=11, fontweight='bold')
            ax.set_aspect('equal')
            ax.set_xticks([])
            ax.set_yticks([])
            fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

        fig.suptitle(f'拟合参数图 - {roi_label}', fontsize=13, fontweight='bold')
        fig.tight_layout()
        
        self.canvas_params.figure = fig
        self.canvas_params.draw()
    
    def update_results_table(self, result: Dict, roi_label: str):
        """更新结果表格"""
        row_position = self.results_table.rowCount()
        self.results_table.insertRow(row_position)
        
        if result['success']:
            contrasts = result['contrasts']
            self.results_table.setItem(row_position, 0, QTableWidgetItem(roi_label))
            self.results_table.setItem(row_position, 1, QTableWidgetItem(
                f"{contrasts.get('Water', 0):.2f}"))
            self.results_table.setItem(row_position, 2, QTableWidgetItem(
                f"{contrasts.get('MT', 0):.2f}"))
            self.results_table.setItem(row_position, 3, QTableWidgetItem(
                f"{contrasts.get('Amide', 0):.2f}"))
            self.results_table.setItem(row_position, 4, QTableWidgetItem(
                f"{result['rmse']:.4f}"))
    
    def export_results(self):
        """导出结果"""
        if not self.fit_results:
            QMessageBox.warning(self, "警告", "没有拟合结果可导出")
            return

        output_dir = QFileDialog.getExistingDirectory(self, "选择导出目录")

        if output_dir:
            try:
                import nibabel as nib
                import csv
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)

                csv_path = output_path / 'fit_summary.csv'
                with open(csv_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['ROI', 'Water%', 'MT%', 'Amide%', 'RMSE'])
                    
                    for roi_label, result in self.fit_results.items():
                        if result['success']:
                            contrasts = result['contrasts']
                            writer.writerow([
                                roi_label,
                                f"{contrasts.get('Water', 0):.4f}",
                                f"{contrasts.get('MT', 0):.4f}",
                                f"{contrasts.get('Amide', 0):.4f}",
                                f"{result['rmse']:.4f}"
                            ])

                self.canvas_spectrum.figure.savefig(output_path / 'z_spectrum.png', dpi=300, bbox_inches='tight')
                self.canvas_params.figure.savefig(output_path / 'parameter_maps.png', dpi=300, bbox_inches='tight')

                for roi_label, result in self.fit_results.items():
                    parameter_maps = result.get('parameter_maps', {})
                    for map_name, map_data in parameter_maps.items():
                        nii_path = output_path / f"{roi_label}_{map_name.replace(' ', '_').replace('(', '').replace(')', '')}.nii.gz"
                        affine = self.data_affine if self.data_affine is not None else np.eye(4)
                        nib.save(nib.Nifti1Image(np.asarray(map_data, dtype=np.float32), affine), str(nii_path))

                self.log_message(f"结果已导出到目录: {output_path}")
                QMessageBox.information(
                    self,
                    "成功",
                    "结果导出成功，包括Z谱图片、参数图图片和参数图NIfTI数据！",
                )
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
