#!/usr/bin/env python
# -*- coding: utf-8 -*-

from color_transfer.libs.base_transfer import BaseTransfer
import numpy as np


class MeanStdTransfer(BaseTransfer):
    """Transfer reference image's mean, std to input image's mean, std.
    img_tgt = (img - mean(img)) / std(img) * std(img_ref) + mean(img_ref).
    """

    def extract(self, img_ref: np.ndarray):
        """Extract reference mean, std.

        Args:
            img_ref: bgr numpy array of reference image.
        """
        # Calculate mean and std using NumPy
        try:
            self.mean_ref = np.mean(img_ref, axis=(0, 1), keepdims=True)
            self.std_ref = np.std(img_ref, axis=(0, 1), keepdims=True)
        except Exception as e:
            raise e

    def transfer(self, img: np.ndarray) -> np.ndarray:
        """Transfer the target image's color.

        Args:
            img: bgr numpy array of input image.
        Returns:
            img_tgt: bgr numpy array of target image.
        """
        # Calculate mean and std using NumPy
        mean = np.mean(img, axis=(0, 1), keepdims=True)
        std = np.std(img, axis=(0, 1), keepdims=True)
        # Apply color transfer formula
        img_tgt = (img - mean) / (std + self.eps) * self.std_ref + self.mean_ref

        # Clip values to valid range [0, 255]
        img_tgt = np.array(np.clip(img_tgt, 0, 255), dtype=np.uint8)
        return img_tgt
