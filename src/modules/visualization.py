"""
可视化模块
处理图像绘制和结果展示
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from typing import Dict, List, Optional, Tuple
import matplotlib.patches as patches


class CESTVisualizer:
    """CEST数据可视化类"""

    @staticmethod
    def _filter_ppm_range(offsets: np.ndarray, values: np.ndarray,
                         ppm_min: float = -8.0,
                         ppm_max: float = 8.0) -> Tuple[np.ndarray, np.ndarray]:
        """仅保留指定ppm范围内的数据用于显示。"""
        offsets = np.asarray(offsets)
        values = np.asarray(values)
        mask = (offsets >= ppm_min) & (offsets <= ppm_max)
        if np.any(mask):
            return offsets[mask], values[mask]
        return offsets, values
    
    @staticmethod
    def plot_zspec(ax, offsets: np.ndarray, spectrum: np.ndarray,
                  offsets_interp: Optional[np.ndarray] = None,
                  water_fit: Optional[np.ndarray] = None,
                  mt_fit: Optional[np.ndarray] = None,
                  fit_curves: Optional[Dict] = None,
                  title: str = "Z-Spectroscopy") -> None:
        """
        绘制Z谱及拟合曲线
        
        Parameters
        ----------
        ax : matplotlib.axes.Axes
            matplotlib轴对象
        offsets : np.ndarray
            频率偏移
        spectrum : np.ndarray
            Z谱数据
        offsets_interp : np.ndarray, optional
            插值偏移
        water_fit : np.ndarray, optional
            水峰拟合
        mt_fit : np.ndarray, optional
            MT峰拟合
        fit_curves : Dict, optional
            其他拟合曲线
        title : str
            图标标题
        """
        offsets_plot, spectrum_plot = CESTVisualizer._filter_ppm_range(offsets, spectrum)

        # 绘制原始数据
        ax.plot(offsets_plot, spectrum_plot, 'ko-', linewidth=2, markersize=4, label='Data')
        
        if offsets_interp is not None:
            offsets_interp_plot = offsets_interp
            fixed_curve_colors = {
                'Water fit': '#1F77B4',
                'MT fit': '#D62728',
                'NOE (-3.5 ppm)': '#C2185B',
                'NOE (-1.6 ppm)': '#E67E22',
                'Creatine': '#8B5A00',
                'Amide': '#5E3C99',
                'Amine': '#00897B',
                'Hydroxyl': '#2E7D32',
            }

            # 绘制Water + MT拟合
            if water_fit is not None:
                offsets_interp_plot, water_fit_plot = CESTVisualizer._filter_ppm_range(
                    offsets_interp,
                    water_fit,
                )
                ax.plot(
                    offsets_interp_plot,
                    water_fit_plot,
                    '--',
                    color=fixed_curve_colors['Water fit'],
                    linewidth=1.8,
                    label='Water fit',
                )
            
            if mt_fit is not None:
                offsets_interp_plot, mt_fit_plot = CESTVisualizer._filter_ppm_range(
                    offsets_interp,
                    mt_fit,
                )
                ax.plot(
                    offsets_interp_plot,
                    mt_fit_plot,
                    '--',
                    color=fixed_curve_colors['MT fit'],
                    linewidth=1.8,
                    label='MT fit',
                )
            
            # 绘制其他代谢产物
            if fit_curves:
                fallback_colors = plt.cm.tab10(np.linspace(0, 1, max(len(fit_curves), 1)))
                for index, (contrast_name, curve) in enumerate(fit_curves.items()):
                    offsets_curve, curve_plot = CESTVisualizer._filter_ppm_range(
                        offsets_interp,
                        curve,
                    )
                    line_color = fixed_curve_colors.get(contrast_name, fallback_colors[index])
                    ax.plot(offsets_curve, curve_plot, '--', color=line_color,
                           linewidth=1.8, label=f'{contrast_name}')
        
        ax.set_xlabel('Chemical Shift Offset (ppm)', fontsize=11)
        ax.set_ylabel('Normalized Intensity', fontsize=11)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(8, -8)
    
    @staticmethod
    def plot_parameter_map(ax, param_map: np.ndarray, title: str,
                          mask: Optional[np.ndarray] = None,
                          vmin: Optional[float] = None,
                          vmax: Optional[float] = None,
                          cmap: str = 'viridis') -> None:
        """
        绘制参数图（如代谢产物百分比）
        
        Parameters
        ----------
        ax : matplotlib.axes.Axes
            matplotlib轴对象
        param_map : np.ndarray
            参数图数据 (H, W)
        title : str
            图标标题
        mask : np.ndarray, optional
            ROI mask
        vmin : float, optional
            颜色范围最小值
        vmax : float, optional
            颜色范围最大值
        cmap : str
            colormap名称
        """
        # 处理无效值
        display_map = param_map.copy()
        display_map[np.isnan(display_map)] = 0
        
        im = ax.imshow(display_map, cmap=cmap, vmin=vmin, vmax=vmax)
        
        # 绘制mask边界
        if mask is not None:
            contour = ax.contour(mask, colors='white', linewidths=1, levels=[0.5])
        
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_aspect('equal')
        plt.colorbar(im, ax=ax)
    
    @staticmethod
    def plot_roi_on_image(ax, image: np.ndarray, mask: np.ndarray,
                         roi_label: str = "ROI") -> None:
        """
        在图像上绘制ROI区域
        
        Parameters
        ----------
        ax : matplotlib.axes.Axes
            matplotlib轴对象
        image : np.ndarray
            背景图像
        mask : np.ndarray
            ROI mask
        roi_label : str
            ROI标签
        """
        # 绘制图像
        ax.imshow(image, cmap='gray')
        
        # 绘制mask边界
        if np.sum(mask) > 0:
            contours = ax.contour(mask, colors='red', linewidths=2, levels=[0.5])
            ax.clabel(contours, inline=True, fontsize=10)
        
        ax.set_title(f'ROI: {roi_label}', fontsize=12, fontweight='bold')
        ax.set_aspect('equal')
    
    @staticmethod
    def create_fitting_result_figure(fit_result: Dict, roi_label: str = "ROI") -> Figure:
        """
        创建完整的拟合结果图
        
        Parameters
        ----------
        fit_result : Dict
            拟合结果字典
        roi_label : str
            ROI标签
            
        Returns
        -------
        matplotlib.figure.Figure
            matplotlib图对象
        """
        fig, axes = plt.subplots(1, 1, figsize=(12, 6))
        
        if fit_result['success']:
            CESTVisualizer.plot_zspec(
                axes,
                fit_result['offsets'],
                fit_result['spectrum'],
                fit_result['offsets_interp'],
                fit_result['water_fit'],
                fit_result['mt_fit'],
                fit_result['fit_curves'],
                title=f'Z-Spectroscopy Fitting - {roi_label}'
            )
            
            # 添加RMSE信息
            rmse_text = f"RMSE: {fit_result['rmse']:.4f}"
            axes.text(0.02, 0.98, rmse_text, transform=axes.transAxes,
                     verticalalignment='top', fontsize=10,
                     bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        else:
            axes.text(0.5, 0.5, f"拟合失败: {fit_result.get('error', '未知错误')}",
                     ha='center', va='center', transform=axes.transAxes,
                     fontsize=12, color='red')
        
        plt.tight_layout()
        return fig
    
    @staticmethod
    def create_parameter_maps_figure(roi_specs: Dict, contrast_list: List[str],
                                    param_type: str = 'amplitude') -> Figure:
        """
        创建参数图集合
        
        Parameters
        ----------
        roi_specs : Dict
            各ROI的拟合结果
        contrast_list : List[str]
            对比度名称列表
        param_type : str
            参数类型 ('amplitude', 'percentage', 等)
            
        Returns
        -------
        matplotlib.figure.Figure
            matplotlib图对象
        """
        n_contrasts = len(contrast_list)
        n_cols = min(3, n_contrasts)
        n_rows = (n_contrasts + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5*n_rows))
        axes = axes.flatten() if hasattr(axes, 'flatten') else [axes]
        
        # 提取所有数据以确定颜色范围
        all_values = []
        for contrast in contrast_list:
            for roi_result in roi_specs.values():
                if 'contrasts' in roi_result and contrast in roi_result['contrasts']:
                    val = roi_result['contrasts'][contrast]
                    if val is not None:
                        all_values.append(val)
        
        vmin = np.min(all_values) if all_values else 0
        vmax = np.max(all_values) if all_values else 1
        
        # 绘制每个对比度的参数
        for idx, contrast in enumerate(contrast_list):
            ax = axes[idx]
            
            if idx < len(axes):
                values = [roi_result.get('contrasts', {}).get(contrast, 0)
                         for roi_result in roi_specs.values()]
                
                roi_labels = list(roi_specs.keys())
                bars = ax.bar(roi_labels, values, color='steelblue', alpha=0.8)
                
                # 添加数值标签
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.2f}',
                           ha='center', va='bottom', fontsize=9)
                
                ax.set_ylabel('Amplitude (%)', fontsize=10)
                ax.set_title(contrast, fontsize=11, fontweight='bold')
                ax.grid(True, alpha=0.3, axis='y')
        
        # 隐藏多余的轴
        for idx in range(len(contrast_list), len(axes)):
            axes[idx].set_visible(False)
        
        plt.tight_layout()
        return fig
    
    @staticmethod
    def generate_report_figure(fit_results: Dict, image: Optional[np.ndarray] = None,
                             title: str = "CEST Analysis Report") -> Figure:
        """
        生成分析报告图（总体总结）
        
        Parameters
        ----------
        fit_results : Dict
            所有ROI的拟合结果
        image : np.ndarray, optional
            背景参考图像
        title : str
            报告标题
            
        Returns
        -------
        matplotlib.figure.Figure
            matplotlib图对象
        """
        n_rois = len(fit_results)
        
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(3, 3, hspace=0.4, wspace=0.3)
        
        # 标题
        fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
        
        # 绘制每个ROI的Z谱
        ax_idx = 0
        for roi_label, fit_result in list(fit_results.items())[:6]:
            row = ax_idx // 3
            col = ax_idx % 3
            ax = fig.add_subplot(gs[row, col])
            
            if fit_result['success']:
                CESTVisualizer.plot_zspec(
                    ax,
                    fit_result['offsets'],
                    fit_result['spectrum'],
                    fit_result.get('offsets_interp'),
                    fit_result.get('water_fit'),
                    fit_result.get('mt_fit'),
                    fit_result.get('fit_curves'),
                    title=f'ROI: {roi_label}'
                )
            
            ax_idx += 1
        
        plt.tight_layout()
        return fig


class MatplotlibFigureCanvas(FigureCanvas):
    """matplotlib图形到PyQt5的集成"""
    
    def __init__(self, figure: Figure, parent=None):
        """
        初始化canvas
        
        Parameters
        ----------
        figure : matplotlib.figure.Figure
            matplotlib图对象
        parent : QWidget, optional
            父窗口
        """
        FigureCanvas.__init__(self, figure)
        self.setParent(parent)
    
    def display_fitting_result(self, fit_result: Dict, roi_label: str = "ROI") -> None:
        """显示拟合结果"""
        fig = CESTVisualizer.create_fitting_result_figure(fit_result, roi_label)
        self.figure = fig
        self.draw()
