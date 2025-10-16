#!/usr/bin/env python
# -*- coding: utf-8 -*-

from color_transfer.libs.base_transfer import BaseTransfer
import numpy as np
from typing import Optional


class PCCMTransfer(BaseTransfer):
    """Transfers colors from a reference image to content images using Principal Component Color Matching.

    This method matches the color distribution by performing PCA on both images
    and transforming the content image to match the reference image's principal component space.
    """

    def __init__(self):
        super().__init__()
        self.mean_ref: Optional[np.ndarray] = None
        self.eigvec_ref: Optional[np.ndarray] = None
        self.eigval_ref: Optional[np.ndarray] = None

    def extract(self, img_ref: np.ndarray) -> None:
        """Extract reference image statistics for color transfer.
        Computes and stores the mean vector, eigenvalues and eigenvectors
        of the reference image's covariance matrix for later use in transfer operations.
        Args:
            img_ref: BGR numpy array of reference image with shape (H, W, 3)
        """
        # Convert HxWxC image to (H*W)xC matrix
        _, _, c = img_ref.shape
        img_ref = img_ref[:, :, ::-1]
        img_ref_flat = img_ref.reshape(-1, c).astype(np.float64)

        # Compute reference statistics
        self.mean_ref = np.mean(img_ref_flat, axis=0)
        cov_ref = np.cov(img_ref_flat, rowvar=False)

        # Perform eigenvalue decomposition
        eigval_ref, eigvec_ref = np.linalg.eig(cov_ref)

        # Store eigenvalues and eigenvectors
        self.eigval_ref = eigval_ref
        self.eigvec_ref = eigvec_ref

    def transfer(self, img: np.ndarray) -> np.ndarray:
        """Transfer reference color characteristics to input image using PCA transformation.
        Applies principal component transformation to match the color distribution
        of the input image to the reference image's distribution in PCA space.
        Args:
            img: BGR numpy array of input image with shape (H, W, 3)
        Returns:
            img_tgt: BGR numpy array of color-transferred image with shape (H, W, 3)
        """
        # Store original shape and convert to 2D array
        original_shape = img.shape
        _, _, c = original_shape
        img = img[:, :, ::-1]
        img_flat = img.reshape(-1, c).astype(np.float64)

        # Compute content image statistics
        mean_content = np.mean(img_flat, axis=0)
        cov_content = np.cov(img_flat, rowvar=False)

        # Perform eigenvalue decomposition for content image
        eigval_content, eigvec_content = np.linalg.eig(cov_content)

        # Add small epsilon to eigenvalues for numerical stability
        epsilon = self.eps
        eigval_content_safe = eigval_content + epsilon
        eigval_ref_safe = self.eigval_ref + epsilon

        # Create scaling matrix
        scaling = np.diag(np.sqrt(eigval_ref_safe / eigval_content_safe))

        # Build transformation matrix
        # transform = eigvec_ref × scaling × eigvec_content^T
        transform: np.ndarray = self.eigvec_ref.dot(scaling)
        transform = transform.dot(eigvec_content.T)

        # Apply transformation
        # result = (content - mean_content) × transform^T + mean_ref
        centered_content: np.ndarray = img_flat - mean_content
        result: np.ndarray = centered_content.dot(transform.T) + self.mean_ref

        # Reshape to original dimensions and clip to valid range
        img_tgt = result.reshape(original_shape)
        img_tgt = img_tgt[:, :, ::-1]
        img_tgt = np.clip(img_tgt, 0, 255).astype(np.uint8)

        return img_tgt
