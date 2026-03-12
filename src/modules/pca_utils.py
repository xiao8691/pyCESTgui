# -*- coding: utf-8 -*-
"""
Created on June 02 2016

@author: Rafael Neto Henriques (rafaelnh21@gmail.com)
"""

# import relevant modules
import numpy as np


def mp_distribution(x, var, y):
    """ Samples the Marchenko–Pastur probability distribution

    Parameters
    ----------
    x : array (N,)
        Values of random variable to sample the probability distribution
    var : float
        Variance of the random variable
    y : float
        Parameter associated to the matrix X that produces the distributions.
        This X is a M x N random matrix which columns entries are identical
        distributed random variables with mean 0 and given variance, y is given
        by N/M.
    """
    xpos = var * (1 + np.sqrt(y)) ** 2
    xneg = var * (1 - np.sqrt(y)) ** 2

    p = np.zeros(x.shape)
    xdis = np.logical_and(x<xpos, x>xneg)
    p[xdis] = np.sqrt((xpos-x[xdis]) * (x[xdis]-xneg)) / (2*np.pi*var*y*x[xdis])

    return p

def pca_noise_classifier(L, m):
    """ Classify which PCA eigenvalues are related to noise

    Parameters
    ----------
    L : array (n,)
        Array containing the PCA eigenvalues.

    Returns
    -------
    c : int
        Number of eigenvalues related to noise
    sig2 : float
        Estimation of the noise variance
    """
    sig2 = np.mean(L)
    c = L.size - 1
    r = L[c] - L[0] - 4 * np.sqrt((c+1.0) / m) * sig2
    while r > 0 and c > 0:
        sig2 = np.mean(L[:c])
        c = c - 1
        r = L[c] - L[0] - 4*np.sqrt((c+1.0) / m) * sig2
    return c + 1, sig2


def _mp_pca_core(data, ps=2, overcomplete=True, mask=None):
    """Apply local MP-PCA denoising to 2D or 3D spatial data."""
    data = np.asarray(data, dtype=float)
    spatial_shape = data.shape[:-1]
    spatial_dims = len(spatial_shape)

    if spatial_dims not in (2, 3):
        raise ValueError("MP-PCA requires 2D or 3D spatial data with offsets on the last axis")

    if ps < 1:
        raise ValueError("ps must be >= 1")

    patch_width = 2 * ps + 1
    if any(size < patch_width for size in spatial_shape):
        return np.array(data, copy=True), np.zeros(spatial_shape), np.zeros(spatial_shape)

    n = data.shape[-1]
    patch_shape = (patch_width,) * spatial_dims
    patch_size = int(np.prod(patch_shape))

    if mask is None:
        valid_mask = np.ones(spatial_shape, dtype=bool)
    else:
        valid_mask = np.asarray(mask, dtype=bool)
        if valid_mask.shape != spatial_shape:
            raise ValueError("mask shape must match the spatial dimensions of data")

    den = np.zeros_like(data, dtype=float)
    ncomps = np.zeros(spatial_shape, dtype=float)
    sig2 = np.zeros(spatial_shape, dtype=float)
    processed = np.zeros(spatial_shape, dtype=bool)

    if overcomplete:
        wei = np.zeros_like(data, dtype=float)

    ranges = [range(ps, spatial_shape[axis] - ps) for axis in range(spatial_dims)]
    center_patch_index = (ps,) * spatial_dims

    for center in np.ndindex(*(len(axis_range) for axis_range in ranges)):
        center_coords = tuple(ranges[axis][center[axis]] for axis in range(spatial_dims))
        if not valid_mask[center_coords]:
            continue

        data_slices = tuple(slice(coord - ps, coord + ps + 1) for coord in center_coords)
        X = data[data_slices + (slice(None),)]
        X = X.reshape(patch_size, n)
        M = np.mean(X, axis=0)
        X = X - M
        L, W = np.linalg.eigh(np.dot(X.T, X) / patch_size)

        c, sig = pca_noise_classifier(L, patch_size)
        preserved_components = max(0, n - c)

        Y = X.dot(W[:, c:])
        X = Y.dot(W[:, c:].T)
        X = X + M
        X = X.reshape(patch_shape + (n,))

        if overcomplete:
            weight = 1.0 / (1.0 + preserved_components)
            wei[data_slices + (slice(None),)] += weight
            den[data_slices + (slice(None),)] += X * weight
            ncomps[data_slices] += preserved_components * weight
            sig2[data_slices] += sig * weight
            processed[data_slices] = True
        else:
            den[center_coords + (slice(None),)] = X[center_patch_index + (slice(None),)]
            ncomps[center_coords] = preserved_components
            sig2[center_coords] = sig
            processed[center_coords] = True

    result = np.array(data, copy=True)

    if overcomplete:
        valid_weights = wei > 0
        result[valid_weights] = den[valid_weights] / wei[valid_weights]

        valid_spatial = wei[..., 0] > 0
        ncomps_out = np.zeros(spatial_shape, dtype=float)
        sig2_out = np.zeros(spatial_shape, dtype=float)
        ncomps_out[valid_spatial] = ncomps[valid_spatial] / wei[..., 0][valid_spatial]
        sig2_out[valid_spatial] = sig2[valid_spatial] / wei[..., 0][valid_spatial]
        return result, np.sqrt(np.maximum(sig2_out, 0.0)), ncomps_out

    result[processed] = den[processed]
    return result, np.sqrt(np.maximum(sig2, 0.0)), ncomps


def pca_denoising(dwi, ps=2, overcomplete=True):
    """ Denoises DWI volumes using PCA analysis and Marchenko–Pastur
    probability theory

    Parameters
    ----------
    dwi : array ([X, Y, Z, g])
        Matrix containing the 4D DWI data.
    ps : int
        Number of neighbour voxels for the PCA analysis.
        Default: 2
    overcomplete : boolean
        If set to True, overcomplete local PCA is computed
        Default: False

    Returns
    -------
    den : array ([X, Y, Z, g])
        Matrix containing the denoised 4D DWI data.
    std : array ([X, Y, Z])
        Matrix containing the noise std estimated using
        Marchenko-Pastur probability theory.
    ncomps : array ([X, Y, Z])
        Number of eigenvalues preserved for the denoised
        4D data.
    """
    dwi = np.asarray(dwi, dtype=float)

    if dwi.ndim == 3:
        return _mp_pca_core(dwi, ps=ps, overcomplete=overcomplete)

    if dwi.ndim != 4:
        raise ValueError("pca_denoising expects data shaped as [X, Y, offsets] or [X, Y, Z, offsets]")

    if dwi.shape[2] >= (2 * ps + 1):
        return _mp_pca_core(dwi, ps=ps, overcomplete=overcomplete)

    den = np.array(dwi, copy=True)
    std = np.zeros(dwi.shape[:3], dtype=float)
    ncomps = np.zeros(dwi.shape[:3], dtype=float)

    for z in range(dwi.shape[2]):
        den[:, :, z, :], std[:, :, z], ncomps[:, :, z] = _mp_pca_core(
            dwi[:, :, z, :],
            ps=ps,
            overcomplete=overcomplete,
        )

    return den, std, ncomps


def localpca(DWI, psize, nep):
    # performes localpca given the number of elements to be preserved
    m = (2*psize + 1) ** 3
    n = DWI.shape[3]
    DWIden = np.zeros(DWI.shape)
    for k in range(psize, DWI.shape[2] - psize):
        for j in range(psize, DWI.shape[1] - psize):
            for i in range(psize, DWI.shape[0] - psize):
                X = DWI[i - psize: i + psize + 1, j - psize: j + psize + 1,
                        k - psize: k + psize + 1, :]
                X = X.reshape(m, n)
                M = np.mean(X, axis=0)
                X = X - M
                [L, W] = np.linalg.eigh(np.dot(X.T, X)/m)
                Y = X.dot(W[:, -nep:])
                X = Y.dot(W[:, -nep:].T)
                X = X + M
                X = X.reshape(2*psize + 1, 2*psize + 1, 2*psize + 1, n)
                DWIden[i, j, k, :] = X[psize, psize, psize]
    return DWIden

