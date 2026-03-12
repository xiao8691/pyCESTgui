"""
NIfTI数据加载模块
支持导入NIfTI格式的MRI图像数据和mask
"""

import numpy as np
import nibabel as nib
from pathlib import Path
from typing import Tuple, Optional, Dict


class NIfTILoader:
    """处理NIfTI文件的加载和初始处理"""
    
    def __init__(self):
        self.data = None
        self.affine = None
        self.header = None
        self.file_path = None
        
    def load_nifti(self, file_path: str) -> np.ndarray:
        """
        加载NIfTI文件
        
        Parameters
        ----------
        file_path : str
            NIfTI文件路径
            
        Returns
        -------
        np.ndarray
            3D或4D的脑影像数据
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
                
            # 加载NIfTI文件
            nifti_img = nib.load(file_path)
            self.data = np.asarray(nifti_img.dataobj)
            self.affine = nifti_img.affine
            self.header = nifti_img.header
            self.file_path = file_path
            
            print(f"成功加载NIfTI文件: {file_path}")
            print(f"数据形状: {self.data.shape}")
            
            return self.data
            
        except Exception as e:
            raise Exception(f"加载NIfTI文件失败: {str(e)}")
    
    def load_mask(self, file_path: str) -> np.ndarray:
        """
        加载mask文件
        
        Parameters
        ----------
        file_path : str
            Mask NIfTI文件路径
            
        Returns
        -------
        np.ndarray
            二值mask数组
        """
        try:
            nifti_img = nib.load(file_path)
            mask = np.asarray(nifti_img.dataobj)
            
            # 确保mask是二值的
            mask = (mask > 0).astype(np.uint8)
            
            print(f"成功加载mask文件: {file_path}")
            print(f"Mask形状: {mask.shape}")
            
            return mask
            
        except Exception as e:
            raise Exception(f"加载mask文件失败: {str(e)}")
    
    def get_data_info(self) -> Dict:
        """
        获取数据的详细信息
        
        Returns
        -------
        Dict
            包含形状、体素大小等信息的字典
        """
        if self.data is None:
            return {}
            
        voxel_size = np.diag(self.affine)[:3]
        
        return {
            'shape': self.data.shape,
            'dtype': str(self.data.dtype),
            'voxel_size': voxel_size,
            'min': float(np.min(self.data)),
            'max': float(np.max(self.data)),
            'mean': float(np.mean(self.data)),
            'file_path': self.file_path
        }
    
    def extract_roi_spectrum(self, mask: np.ndarray) -> np.ndarray:
        """
        从给定mask中提取ROI频谱
        
        Parameters
        ----------
        mask : np.ndarray
            二值mask数组
            
        Returns
        -------
        np.ndarray
            mask内的平均频谱
        """
        if self.data is None:
            raise ValueError("请先加载数据")
        
        # 处理3D mask应用到4D数据的情况
        if len(self.data.shape) == 4 and len(mask.shape) == 3:
            mask_3d = mask
            # 展开并应用mask
            x, y, z, t = self.data.shape
            spectrum = np.zeros(t)
            mask_indices = np.where(mask_3d > 0)
            count = len(mask_indices[0])
            
            if count == 0:
                raise ValueError("Mask区域为空")
            
            for i, j, k in zip(mask_indices[0], mask_indices[1], mask_indices[2]):
                spectrum += self.data[i, j, k, :]
            
            spectrum /= count
            
        else:
            # 标准2D mask应用
            pixels = self.data[mask > 0]
            spectrum = np.mean(pixels, axis=0)
        
        return spectrum
    
    def resample_data(self, target_shape: Tuple) -> np.ndarray:
        """
        重采样数据到目标形状
        
        Parameters
        ----------
        target_shape : Tuple
            目标形状
            
        Returns
        -------
        np.ndarray
            重采样后的数据
        """
        from scipy import ndimage
        
        if self.data is None:
            raise ValueError("请先加载数据")
        
        zoom_factors = np.array(target_shape) / np.array(self.data.shape)
        resampled = ndimage.zoom(self.data, zoom_factors, order=1)
        
        return resampled


def load_nifti_data(file_path: str) -> np.ndarray:
    """便捷函数：加载NIfTI文件"""
    loader = NIfTILoader()
    return loader.load_nifti(file_path)


def load_mask_data(file_path: str) -> np.ndarray:
    """便捷函数：加载mask文件"""
    loader = NIfTILoader()
    return loader.load_mask(file_path)
