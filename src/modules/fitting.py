"""
CEST曲线拟合核心模块
包含Lorentzian拟合和2-step拟合等算法
"""

import numpy as np
from scipy.optimize import curve_fit
from scipy.interpolate import CubicSpline
from sklearn.metrics import mean_squared_error
from typing import Dict, List, Tuple, Optional


# 拟合参数配置
class FittingConfig:
    """拟合参数配置类"""
    
    # Pre-correction 参数
    p0_water_pre = [0.8, 1.8, 0]
    p0_mt_pre = [0.15, 40, -1]
    
    lb_water_pre = [0.02, 0.3, -10]
    lb_mt_pre = [0.0, 30, -2.5]
    
    ub_water_pre = [1, 10, 10]
    ub_mt_pre = [0.5, 60, 0]
    
    # Post-correction 参数
    p0_water = [0.8, 0.2, 0]
    p0_mt = [0.15, 40, -1]
    p0_noe = [0.05, 1, -3.50]
    p0_noe_neg_1_6 = [0.05, 1, -1.6]
    p0_creatine = [0.05, 0.5, 2.0]
    p0_amide = [0.05, 1.5, 3.5]
    p0_amine = [0.05, 1.5, 2.5]
    p0_hydroxyl = [0.05, 1.5, 0.6]
    
    lb_water = [0.02, 0.01, -1e-6]
    lb_mt = [0.0, 30, -2.5]
    lb_noe = [0.0, 0.5, -4.0]
    lb_noe_neg_1_6 = [0.0, 0.5, -1.8]
    lb_creatine = [0.0, 0.5, 1.6]
    lb_amide = [0.0, 0.5, 3.2]
    lb_amine = [0.0, 0.1, 2.2]
    lb_hydroxyl = [0.0, 0.1, 0.4]
    
    ub_water = [1, 10, 1e-6]
    ub_mt = [0.5, 60, 0]
    ub_noe = [0.25, 5, -1.5]
    ub_noe_neg_1_6 = [.25, 5, -1.2]
    ub_creatine = [0.5, 5, 2.6]
    ub_amide = [0.3, 5, 4.0]
    ub_amine = [0.3, 5, 2.8]
    ub_hydroxyl = [0.3, 5, 1.2]
    
    # 裁剪范围
    cutoff_major = [-4, -1.4, 1.4, 4]
    cutoff_hydroxyl = [-4, -1.4, 0.4, 4]
    
    # 拟合选项
    fit_options = {'xtol': 1e-10, 'ftol': 1e-4, 'maxfev': 50}
    
    @classmethod
    def get_contrast_params(cls, contrast_name: str) -> Tuple[List, List, List]:
        """
        获取特定代谢产物的参数
        
        Returns
        -------
        Tuple[List, List, List]
            (初始值, 下界, 上界)
        """
        params_map = {
            'NOE (-3.5 ppm)': (cls.p0_noe, cls.lb_noe, cls.ub_noe),
            'NOE (-1.6 ppm)': (cls.p0_noe_neg_1_6, cls.lb_noe_neg_1_6, cls.ub_noe_neg_1_6),
            'Creatine': (cls.p0_creatine, cls.lb_creatine, cls.ub_creatine),
            'Amide': (cls.p0_amide, cls.lb_amide, cls.ub_amide),
            'Amine': (cls.p0_amine, cls.lb_amine, cls.ub_amine),
            'Hydroxyl': (cls.p0_hydroxyl, cls.lb_hydroxyl, cls.ub_hydroxyl),
        }
        return params_map.get(contrast_name, (cls.p0_noe, cls.lb_noe, cls.ub_noe))


def lorentzian(x: np.ndarray, amp: float, fwhm: float, offset: float) -> np.ndarray:
    """
    Lorentz函数
    
    Parameters
    ----------
    x : np.ndarray
        频率偏移
    amp : float
        振幅
    fwhm : float
        半高宽
    offset : float
        中心位置
        
    Returns
    -------
    np.ndarray
        Lorentz函数值
    """
    num = amp * 0.25 * fwhm ** 2
    den = 0.25 * fwhm ** 2 + (x - offset) ** 2
    return num / den


class CESTFitter:
    """CEST拟合类"""
    
    def __init__(self):
        self.config = FittingConfig()
    
    def step_1_fit(self, x: np.ndarray, *fit_parameters) -> np.ndarray:
        """Step 1: Water + MT拟合"""
        water_fit = lorentzian(x, fit_parameters[0], fit_parameters[1], fit_parameters[2])
        mt_fit = lorentzian(x, fit_parameters[3], fit_parameters[4], fit_parameters[5])
        return 1 - water_fit - mt_fit
    
    def step_2_fit(self, x: np.ndarray, contrasts: List[str], 
                   *fit_parameters) -> np.ndarray:
        """Step 2: 多成分拟合"""
        fit_sum = np.zeros_like(x)
        index = 0
        for _ in contrasts:
            fit_sum += lorentzian(x, fit_parameters[index], 
                                 fit_parameters[index + 1], 
                                 fit_parameters[index + 2])
            index += 3
        return fit_sum
    
    def two_step_fit(self, spectrum: np.ndarray, offsets: np.ndarray,
                    contrasts: Optional[List[str]] = None,
                    apply_b0_correction: bool = True) -> Dict:
        """
        执行2-step Lorentzian拟合
        
        Parameters
        ----------
        spectrum : np.ndarray
            Z谱数据
        offsets : np.ndarray
            化学位移偏移量
        contrasts : List[str], optional
            要拟合的代谢产物列表
            默认: ['NOE (-3.5 ppm)', 'Creatine', 'Amide']
            
        Returns
        -------
        Dict
            包含拟合结果的字典
        """
        if contrasts is None:
            contrasts = ['NOE (-3.5 ppm)', 'Creatine', 'Amide']
        
        n_interp = 4000
        
        try:
            offsets = np.asarray(offsets, dtype=float)
            spectrum = np.asarray(spectrum, dtype=float)

            # 任意乱序offset统一按升序整理
            sort_index = np.argsort(offsets)
            if not np.array_equal(sort_index, np.arange(offsets.shape[0])):
                offsets = offsets[sort_index]
                spectrum = spectrum[sort_index]
            elif offsets[0] > offsets[-1]:
                offsets = np.flip(offsets)
                spectrum = np.flip(spectrum)
            
            # 获取拟合参数
            p0_water, lb_water, ub_water = (
                self.config.p0_water, self.config.lb_water, self.config.ub_water
            )
            p0_mt, lb_mt, ub_mt = (
                self.config.p0_mt, self.config.lb_mt, self.config.ub_mt
            )
            
            p0_corr = p0_water + p0_mt
            lb_corr = lb_water + lb_mt
            ub_corr = ub_water + ub_mt
            
            if apply_b0_correction:
                # Step 1: 拟合Water + MT进行B0校正
                popt_1, _ = curve_fit(
                    self.step_1_fit, offsets, spectrum,
                    p0=p0_corr, bounds=(lb_corr, ub_corr),
                    **self.config.fit_options
                )
                correction = popt_1[2]
                offsets_corrected = offsets - correction
            else:
                correction = 0.0
                offsets_corrected = offsets.copy()
            
            # 确定裁剪范围
            if 'Hydroxyl' in contrasts:
                cutoffs = self.config.cutoff_hydroxyl
            else:
                cutoffs = self.config.cutoff_major
            
            # 裁剪频谱范围
            condition = (
                (offsets_corrected <= cutoffs[0]) | 
                (offsets_corrected >= cutoffs[3]) |
                ((offsets_corrected >= cutoffs[1]) & (offsets_corrected <= cutoffs[2]))
            )
            
            condition_rmse = (
                ((offsets_corrected <= -1.4) & (offsets_corrected >= -4)) |
                ((offsets_corrected >= 1.4) & (offsets_corrected <= 4))
            )

            if not np.any(condition):
                condition = np.isfinite(offsets_corrected) & np.isfinite(spectrum)

            if not np.any(condition_rmse):
                condition_rmse = condition.copy()
            
            offsets_cropped = offsets_corrected[condition]
            spectrum_cropped = spectrum[condition]
            
            if len(offsets_cropped) == 0:
                raise RuntimeError("不可用的偏移范围")
            
            # 插值
            offsets_interp = np.linspace(
                offsets_corrected[0], offsets_corrected[-1], n_interp
            )
            
            # Step 1 细致拟合
            p0_1 = self.config.p0_water + self.config.p0_mt
            lb_1 = self.config.lb_water + self.config.lb_mt
            ub_1 = self.config.ub_water + self.config.ub_mt
            
            popt_1, _ = curve_fit(
                self.step_1_fit, offsets_cropped, spectrum_cropped,
                p0=p0_1, bounds=(lb_1, ub_1),
                **self.config.fit_options
            )
            
            # 计算背景和差分
            water_fit = lorentzian(offsets_interp, popt_1[0], popt_1[1], popt_1[2])
            mt_fit = lorentzian(offsets_interp, popt_1[3], popt_1[4], popt_1[5])
            
            background = (
                lorentzian(offsets_corrected, popt_1[0], popt_1[1], popt_1[2]) +
                lorentzian(offsets_corrected, popt_1[3], popt_1[4], popt_1[5])
            )
            
            lorentzian_difference = 1 - (spectrum + background)
            
            # Step 2: 多成分拟合
            p0_2, lb_2, ub_2 = [], [], []
            for contrast in contrasts:
                p0, lb, ub = self.config.get_contrast_params(contrast)
                p0_2 += p0
                lb_2 += lb
                ub_2 += ub
            
            popt_2, _ = curve_fit(
                lambda x, *p: self.step_2_fit(x, contrasts, *p),
                offsets_corrected, lorentzian_difference,
                p0=p0_2, bounds=(lb_2, ub_2),
                **self.config.fit_options
            )
            
            # 生成拟合曲线
            fit_curves = {}
            index = 0
            for contrast in contrasts:
                fit_curves[contrast] = lorentzian(
                    offsets_interp, popt_2[index], popt_2[index + 1], popt_2[index + 2]
                )
                index += 3
            
            # 计算RMSE
            step_2_fit_vals = self.step_2_fit(offsets_corrected, contrasts, *popt_2)
            
            spectrum_region = spectrum[condition_rmse]
            total_fit_region = (
                self.step_1_fit(offsets_corrected[condition_rmse], *popt_1) -
                step_2_fit_vals[condition_rmse]
            )

            if spectrum_region.size == 0 or total_fit_region.size == 0:
                rmse = float('nan')
            else:
                rmse = np.sqrt(mean_squared_error(spectrum_region, total_fit_region))
            
            # 反向排列（可视化）
            offsets_interp = np.flip(offsets_interp)
            water_fit = np.flip(water_fit)
            mt_fit = np.flip(mt_fit)
            for contrast in fit_curves:
                fit_curves[contrast] = np.flip(fit_curves[contrast])
            
            # 计算代谢产物百分比
            contrasts_dict = {
                'Water': 100 * popt_1[0],
                'MT': 100 * popt_1[3]
            }
            for i, contrast in enumerate(contrasts):
                contrasts_dict[contrast] = 100 * popt_2[i * 3]
            
            return {
                'success': True,
                'fit_params_1': popt_1,
                'fit_params_2': popt_2,
                'contrasts': contrasts_dict,
                'offsets': offsets,
                'offsets_corrected': offsets_corrected,
                'offsets_interp': offsets_interp,
                'spectrum': spectrum,
                'water_fit': water_fit,
                'mt_fit': mt_fit,
                'fit_curves': fit_curves,
                'rmse': rmse,
                'rmse_points': int(spectrum_region.size),
                'b0_correction': correction
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'offsets': offsets,
                'spectrum': spectrum,
                'contrasts': {c: 0 for c in contrasts}
            }
    
    def fit_roi_spectrum(self, spectrum: np.ndarray, offsets: np.ndarray,
                        contrasts: Optional[List[str]] = None) -> Dict:
        """
        拟合单个ROI的平均频谱
        """
        return self.two_step_fit(spectrum, offsets, contrasts)
    
    def fit_pixelwise(self, spectra: np.ndarray, offsets: np.ndarray,
                     contrasts: Optional[List[str]] = None,
                     progress_callback=None) -> List[Dict]:
        """
        逐像素拟合（用于生成参数图）
        
        Parameters
        ----------
        spectra : np.ndarray
            像素频谱 (N_pixels, N_offsets)
        offsets : np.ndarray
            偏移量
        contrasts : List[str], optional
            代谢产物列表
        progress_callback : callable, optional
            进度回调函数
            
        Returns
        -------
        List[Dict]
            拟合结果列表
        """
        results = []
        total = len(spectra)
        
        for i, spectrum in enumerate(spectra):
            result = self.two_step_fit(spectrum, offsets, contrasts)
            results.append(result)
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        return results
