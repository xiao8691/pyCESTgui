"""
预处理模块
包括配准、B0校正和归一化
"""

import numpy as np
from typing import Tuple, Optional, Dict
from sklearn.decomposition import PCA
from scipy import ndimage
from scipy.optimize import minimize


class Preprocessing:
    """图像预处理类"""

    @staticmethod
    def apply_b0_shift_to_spectrum(
        spectrum: np.ndarray,
        offsets: np.ndarray,
        b0_shift: float,
    ) -> np.ndarray:
        """将估计到的B0偏移应用到单条频谱，并重采样回原始offset网格。"""
        spectrum = np.asarray(spectrum, dtype=float)
        offsets = np.asarray(offsets, dtype=float)
        corrected_offsets = offsets - float(b0_shift)

        order = np.argsort(corrected_offsets)
        corrected_sorted = corrected_offsets[order]
        spectrum_sorted = spectrum[order]

        return np.interp(
            offsets,
            corrected_sorted,
            spectrum_sorted,
            left=spectrum_sorted[0],
            right=spectrum_sorted[-1],
        )

    @staticmethod
    def voxelwise_b0_correction(
        data: np.ndarray,
        offsets: np.ndarray,
        method: str = 'gaussian',
        mask: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """对CEST数据做逐像素B0校正，并重采样回统一offset网格。"""
        data = np.asarray(data, dtype=float)
        offsets = np.asarray(offsets, dtype=float)

        if data.ndim < 3:
            raise ValueError("逐像素B0校正要求数据至少为3维，最后一维为offset")

        if data.shape[-1] != offsets.shape[0]:
            raise ValueError("数据最后一维长度必须与offsets一致")

        corrected = np.array(data, copy=True)
        shift_map = np.zeros(data.shape[:-1], dtype=float)

        if mask is not None:
            valid_mask = np.asarray(mask) > 0
        else:
            valid_mask = np.ones(data.shape[:-1], dtype=bool)

        valid_indices = np.argwhere(valid_mask)
        for voxel_index in valid_indices:
            voxel_index = tuple(int(v) for v in voxel_index)
            spectrum = data[voxel_index]
            _, b0_shift = Preprocessing.b0_correction(spectrum, offsets, method=method)
            corrected[voxel_index] = Preprocessing.apply_b0_shift_to_spectrum(
                spectrum,
                offsets,
                b0_shift,
            )
            shift_map[voxel_index] = b0_shift

        return corrected, shift_map

    @staticmethod
    def get_normalization_reference_index(offsets: np.ndarray) -> int:
        """返回离0 ppm最远的offset索引。"""
        offsets = np.asarray(offsets)
        if offsets.size == 0:
            raise ValueError("offsets不能为空")
        return int(np.argmax(np.abs(offsets)))

    @staticmethod
    def normalize_spectrum(
        spectrum: np.ndarray,
        offsets: np.ndarray,
        reference_index: Optional[int] = None,
    ) -> Tuple[np.ndarray, int, float, float]:
        """按指定offset对应的信号进行归一化。"""
        spectrum = np.asarray(spectrum, dtype=float)
        offsets = np.asarray(offsets, dtype=float)

        if spectrum.shape[-1] != offsets.shape[0]:
            raise ValueError("spectrum最后一维长度必须与offsets一致")

        if reference_index is None:
            reference_index = Preprocessing.get_normalization_reference_index(offsets)

        reference_value = np.take(spectrum, reference_index, axis=-1)
        reference_scalar = float(np.asarray(reference_value).reshape(-1)[0])

        if abs(reference_scalar) < 1e-12:
            raise ValueError("归一化参考点的信号接近0，无法归一化")

        if np.ndim(reference_value) == 0:
            normalized = spectrum / reference_value
        else:
            normalized = spectrum / np.expand_dims(reference_value, axis=-1)

        return normalized, int(reference_index), float(offsets[reference_index]), reference_scalar

    @staticmethod
    def remove_offset_index(
        spectrum: np.ndarray,
        offsets: np.ndarray,
        remove_index: int,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """移除指定offset索引对应的频谱点。"""
        spectrum = np.asarray(spectrum)
        offsets = np.asarray(offsets)

        if spectrum.shape[-1] != offsets.shape[0]:
            raise ValueError("spectrum最后一维长度必须与offsets一致")

        keep_mask = np.ones(offsets.shape[0], dtype=bool)
        keep_mask[int(remove_index)] = False
        return spectrum[..., keep_mask], offsets[keep_mask]
    
    @staticmethod
    def pca_denoise(data: np.ndarray, n_components: int = None) -> np.ndarray:
        """
        使用PCA方法进行降噪
        
        Parameters
        ----------
        data : np.ndarray
            输入数据 (H, W, T) 或 (H, W, Z, T)
        n_components : int, optional
            PCA保留的主成分数。如果为None，自动选择为数据维度的80%
            
        Returns
        -------
        np.ndarray
            去噪后的数据
        """
        original_shape = data.shape
        
        # 展平为(N, T)形式
        if len(data.shape) == 4:
            # 3D数据
            H, W, Z, T = data.shape
            data_reshaped = data.reshape(-1, T)
        else:
            # 2D数据
            H, W, T = data.shape
            data_reshaped = data.reshape(-1, T)
        
        # 确定PCA成分数
        if n_components is None:
            n_components = max(1, int(data_reshaped.shape[1] * 0.8))
        
        # 应用PCA
        pca = PCA(n_components=n_components)
        data_pca = pca.fit_transform(data_reshaped)
        
        # 反向转换
        data_denoised = pca.inverse_transform(data_pca)
        
        # 恢复原始形状
        data_denoised = data_denoised.reshape(original_shape)
        
        return data_denoised
    
    @staticmethod
    def rigid_registration(moving: np.ndarray, fixed: np.ndarray, 
                          use_gradient: bool = True) -> Tuple[np.ndarray, Dict]:
        """
        刚体配准（平移和旋转）
        
        Parameters
        ----------
        moving : np.ndarray
            待配准图像
        fixed : np.ndarray
            参考图像
        use_gradient : bool
            是否使用梯度信息
            
        Returns
        -------
        Tuple[np.ndarray, Dict]
            配准后的图像和配准参数
        """
        # 简化版：使用质心对齐作为刚体配准的初步
        def calculate_mse(params, moving, fixed):
            """计算均方误差"""
            tx, ty = params
            H, W = moving.shape[:2]
            
            # 创建平移矩阵
            x = np.arange(W)
            y = np.arange(H)
            xx, yy = np.meshgrid(x, y)
            
            # 应用平移
            xx_moved = xx + tx
            yy_moved = yy + ty
            
            # 双线性插值
            try:
                from scipy.interpolate import RegularGridInterpolator
                points = (y, x)
                values = moving
                f = RegularGridInterpolator(points, values, bounds_error=False, 
                                          fill_value=0)
                
                pts = np.array([yy_moved.ravel(), xx_moved.ravel()]).T
                moved_interp = f(pts).reshape(moving.shape)
                
                mse = np.mean((moved_interp - fixed) ** 2)
                return mse
            except:
                return np.inf
        
        # 初始化参数为0
        x0 = [0, 0]
        
        # 仅考虑前两个通道的配准
        if len(moving.shape) == 3:
            moving_2d = moving[:, :, 0]
            fixed_2d = fixed[:, :, 0]
        else:
            moving_2d = moving
            fixed_2d = fixed
        
        # 优化
        result = minimize(calculate_mse, x0, args=(moving_2d, fixed_2d),
                         method='Powell')
        
        params = {'translation_x': float(result.x[0]), 
                 'translation_y': float(result.x[1]),
                 'mse': float(result.fun)}
        
        # 应用配准变换
        if result.fun < np.inf:
            from scipy import ndimage
            shift = [result.x[1], result.x[0]]  # (y, x)
            if len(moving.shape) == 3:
                registered = np.zeros_like(moving)
                for t in range(moving.shape[2]):
                    registered[:, :, t] = ndimage.shift(moving[:, :, t], shift, 
                                                        order=1, mode='constant')
            else:
                registered = ndimage.shift(moving, shift, order=1, mode='constant')
        else:
            registered = moving
        
        return registered, params
    
    @staticmethod
    def b0_correction(spectrum: np.ndarray, offsets: np.ndarray, 
                     method: str = 'gaussian') -> Tuple[np.ndarray, float]:
        """
        B0场不均匀性校正
        
        Parameters
        ----------
        spectrum : np.ndarray
            Z谱 (CEST频谱)
        offsets : np.ndarray
            化学位移偏移量
        method : str
            校正方法 ('gaussian' 或 'lorentzian')
            
        Returns
        -------
        Tuple[np.ndarray, float]
            B0校正后的频谱和校正值
        """
        from scipy.optimize import curve_fit
        
        def gaussian(x, amp, sigma, center):
            """高斯函数"""
            return amp * np.exp(-((x - center) ** 2) / (2 * sigma ** 2))
        
        def lorentzian(x, amp, fwhm, center):
            """Lorentz函数"""
            num = amp * 0.25 * fwhm ** 2
            den = 0.25 * fwhm ** 2 + (x - center) ** 2
            return num / den
        
        try:
            offsets = np.asarray(offsets, dtype=float)
            spectrum = np.asarray(spectrum, dtype=float)

            # 仅使用靠近0 ppm的区域估计B0偏移，避免跑飞到数百ppm
            local_mask = np.abs(offsets) <= 1.0
            if np.count_nonzero(local_mask) < 3:
                nearest = np.argsort(np.abs(offsets))[:min(7, offsets.size)]
                local_mask = np.zeros_like(offsets, dtype=bool)
                local_mask[nearest] = True

            fit_offsets = offsets[local_mask]
            fit_spectrum = spectrum[local_mask]

            center_guess = float(fit_offsets[np.argmin(fit_spectrum)])
            amp_guess = float(max(np.max(fit_spectrum) - np.min(fit_spectrum), 1e-3))

            if method == 'gaussian':
                popt, _ = curve_fit(
                    gaussian,
                    fit_offsets,
                    fit_spectrum,
                    p0=[amp_guess, 0.3, center_guess],
                    bounds=([0.0, 1e-3, -1.5], [10.0, 3.0, 1.5]),
                    maxfev=5000,
                )
                b0_shift = float(popt[2])
            else:
                popt, _ = curve_fit(
                    lorentzian,
                    fit_offsets,
                    fit_spectrum,
                    p0=[amp_guess, 0.5, center_guess],
                    bounds=([0.0, 1e-3, -1.5], [10.0, 5.0, 1.5]),
                    maxfev=5000,
                )
                b0_shift = float(popt[2])

            # 最终防护：若结果明显不合理，则退回到局部最小值法
            if not np.isfinite(b0_shift) or abs(b0_shift) > 2.0:
                b0_shift = center_guess

            offsets_corrected = offsets - b0_shift
            return offsets_corrected, b0_shift

        except Exception as e:
            print(f"B0校正失败: {e}")
            try:
                offsets = np.asarray(offsets, dtype=float)
                spectrum = np.asarray(spectrum, dtype=float)
                local_mask = np.abs(offsets) <= 1.0
                if np.count_nonzero(local_mask) < 1:
                    return offsets, 0.0
                local_offsets = offsets[local_mask]
                local_spectrum = spectrum[local_mask]
                b0_shift = float(local_offsets[np.argmin(local_spectrum)])
                return offsets - b0_shift, b0_shift
            except Exception:
                return offsets, 0.0
    
    @staticmethod
    def gaussian_smooth(data: np.ndarray, sigma: float = 1.0) -> np.ndarray:
        """
        高斯平滑滤波
        
        Parameters
        ----------
        data : np.ndarray
            输入数据
        sigma : float
            高斯核的标准差
            
        Returns
        -------
        np.ndarray
            平滑后的数据
        """
        return ndimage.gaussian_filter(data, sigma=sigma)
    
    @staticmethod
    def median_filter(data: np.ndarray, size: int = 3) -> np.ndarray:
        """
        中值滤波
        
        Parameters
        ----------
        data : np.ndarray
            输入数据
        size : int
            滤波器大小
            
        Returns
        -------
        np.ndarray
            滤波后的数据
        """
        return ndimage.median_filter(data, size=size)
    
    @staticmethod
    def normalize_data(data: np.ndarray, method: str = 'minmax') -> np.ndarray:
        """
        数据归一化
        
        Parameters
        ----------
        data : np.ndarray
            输入数据
        method : str
            归一化方法 ('minmax' 或 'zscore')
            
        Returns
        -------
        np.ndarray
            归一化后的数据
        """
        if method == 'minmax':
            data_min = np.min(data)
            data_max = np.max(data)
            if data_max - data_min == 0:
                return np.zeros_like(data)
            return (data - data_min) / (data_max - data_min)
        elif method == 'zscore':
            data_mean = np.mean(data)
            data_std = np.std(data)
            if data_std == 0:
                return np.zeros_like(data)
            return (data - data_mean) / data_std
        else:
            return data
