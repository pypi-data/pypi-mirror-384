#!/usr/bin/env python
# -*- coding: utf-8 -*-

from color_transfer.libs.base_transfer import BaseTransfer
import numpy as np
from typing import Optional


class LHMTransfer(BaseTransfer):
    """Transfers colors from a reference image to content images using Linear Histogram Matching.

    This method matches the color distribution by considering both per-channel statistics
    and cross-channel correlations through covariance matrix transformation.
    """

    def __init__(self):
        super().__init__()
        self.mean_ref: Optional[np.ndarray] = None
        self.cov_ref_sqrt: Optional[np.ndarray] = None

    def _matrix_sqrt(self, X: np.ndarray) -> np.ndarray:
        """Compute the matrix square root using eigenvalue decomposition.
        Args:
            X: Input square matrix
        Returns:
            Matrix square root of X
        """
        eig_val, eig_vec = np.linalg.eig(X)
        # Add small epsilon for numerical stability
        sqrt_matrix: np.ndarray = eig_vec.dot(np.diag(np.sqrt(eig_val + 1e-8)))
        sqrt_matrix = sqrt_matrix.dot(eig_vec.T)
        return sqrt_matrix

    def extract(self, img_ref: np.ndarray) -> None:
        """Extract reference image statistics for color transfer.
        Computes and stores the mean vector and covariance matrix square root
        of the reference image for later use in transfer operations.
        Args:
            img_ref: BGR numpy array of reference image with shape (H, W, 3)
        """
        # Convert HxWxC image to (H*W)xC matrix
        _, _, c = img_ref.shape
        img_ref_flat = img_ref.reshape(-1, c).astype(np.float64)

        # Compute reference statistics
        self.mean_ref = np.mean(img_ref_flat, axis=0)
        cov_ref = np.cov(img_ref_flat, rowvar=False)
        self.cov_ref_sqrt = self._matrix_sqrt(cov_ref)

    def transfer(self, img: np.ndarray) -> np.ndarray:
        """Transfer reference color characteristics to input image.
        Applies linear transformation to match the color distribution
        of the input image to the reference image's distribution.
        Args:
            img: BGR numpy array of input image with shape (H, W, 3)
        Returns:
            img_tgt: BGR numpy array of color-transferred image with shape (H, W, 3)
        """
        # Store original shape and convert to 2D array
        original_shape = img.shape
        _, _, c = original_shape
        img_flat = img.reshape(-1, c).astype(np.float64)

        # Compute content image statistics
        mean_content: np.ndarray = np.mean(img_flat, axis=0)
        cov_content = np.cov(img_flat, rowvar=False)
        cov_content_sqrt = self._matrix_sqrt(cov_content)

        try:
            # Compute inverse of content covariance square root
            inv_cov_content_sqrt = np.linalg.inv(cov_content_sqrt)
        except np.linalg.LinAlgError:
            # Fallback to pseudo-inverse if matrix is singular
            inv_cov_content_sqrt = np.linalg.pinv(cov_content_sqrt)

        # Apply linear histogram matching transformation
        # result = cov_ref_sqrt × inv(cov_content_sqrt) × (img - mean_content) + mean_ref
        transform_matrix: np.ndarray = self.cov_ref_sqrt.dot(inv_cov_content_sqrt)
        centered_content: np.ndarray = (img_flat - mean_content).T
        result: np.ndarray = transform_matrix.dot(centered_content)
        result = result.T + self.mean_ref

        # Reshape to original dimensions and clip to valid range
        img_tgt = result.reshape(original_shape)
        img_tgt = np.clip(img_tgt, 0, 255).astype(np.uint8)

        return img_tgt
