#!/usr/bin/env python
# -*- coding: utf-8 -*-

from color_transfer.libs.base_transfer import BaseTransfer
import numpy as np


class LabTransfer(BaseTransfer):
    """Transfer reference image's mean, std to input image's mean, std in LAB color space."""

    def _bgr2lab(self, bgr_img: np.ndarray) -> np.ndarray:
        """Convert BGR image to LAB color space using NumPy."""
        # Normalize to [0, 1]
        bgr_normalized = bgr_img.astype(np.float32) / 255.0

        # Convert BGR to RGB
        rgb_normalized = bgr_normalized[..., [2, 1, 0]]

        # Apply gamma correction to linear RGB
        rgb_linear = np.where(
            rgb_normalized > 0.04045,
            ((rgb_normalized + 0.055) / 1.055) ** 2.4,
            rgb_normalized / 12.92,
        )

        # Convert to XYZ color space
        xyz = self._rgb2xyz(rgb_linear)

        # Convert XYZ to LAB
        lab = self._xyz2lab(xyz)

        # Scale LAB values to standard ranges
        lab[..., 0] = lab[..., 0] * 255.0 / 100.0  # L: [0, 100] -> [0, 255]
        lab[..., 1] = lab[..., 1] + 128.0  # a: [-128, 127] -> [0, 255]
        lab[..., 2] = lab[..., 2] + 128.0  # b: [-128, 127] -> [0, 255]

        return np.clip(lab, 0, 255).astype(np.uint8)

    def _lab2bgr(self, lab_img: np.ndarray) -> np.ndarray:
        """Convert LAB image to BGR color space using NumPy."""
        lab = lab_img.astype(np.float32)

        # Scale LAB values back to standard ranges
        lab[..., 0] = lab[..., 0] * 100.0 / 255.0  # L: [0, 255] -> [0, 100]
        lab[..., 1] = lab[..., 1] - 128.0  # a: [0, 255] -> [-128, 127]
        lab[..., 2] = lab[..., 2] - 128.0  # b: [0, 255] -> [-128, 127]

        # Convert LAB to XYZ
        xyz = self._lab2xyz(lab)

        # Convert XYZ to linear RGB
        rgb_linear = self._xyz2rgb(xyz)

        # Apply inverse gamma correction
        rgb_normalized = np.where(
            rgb_linear > 0.0031308,
            1.055 * (rgb_linear ** (1.0 / 2.4)) - 0.055,
            12.92 * rgb_linear,
        )

        # Convert RGB to BGR and scale back to [0, 255]
        bgr_normalized = rgb_normalized[..., [2, 1, 0]]
        bgr = np.clip(bgr_normalized * 255.0, 0, 255)

        return bgr.astype(np.uint8)

    def _rgb2xyz(self, rgb: np.ndarray) -> np.ndarray:
        """Convert linear RGB to XYZ color space."""
        # Transformation matrix from RGB to XYZ
        transform = np.array(
            [
                [0.4124564, 0.3575761, 0.1804375],
                [0.2126729, 0.7151522, 0.0721750],
                [0.0193339, 0.1191920, 0.9503041],
            ]
        )

        # Apply transformation
        xyz = np.dot(rgb, transform.T)
        return xyz

    def _xyz2rgb(self, xyz: np.ndarray) -> np.ndarray:
        """Convert XYZ to linear RGB color space."""
        # Inverse transformation matrix from XYZ to RGB
        transform = np.array(
            [
                [3.2404542, -1.5371385, -0.4985314],
                [-0.9692660, 1.8760108, 0.0415560],
                [0.0556434, -0.2040259, 1.0572252],
            ]
        )

        # Apply transformation
        rgb = np.dot(xyz, transform.T)
        return np.clip(rgb, 0, 1)

    def _xyz2lab(self, xyz: np.ndarray) -> np.ndarray:
        """Convert XYZ to LAB color space."""
        # Reference white (D65)
        ref_white = np.array([0.95047, 1.0, 1.08883])

        # Normalize by reference white
        xyz_normalized = xyz / ref_white

        # Apply nonlinear transformation
        xyz_f = np.where(
            xyz_normalized > 0.008856,
            xyz_normalized ** (1.0 / 3.0),
            7.787 * xyz_normalized + 16.0 / 116.0,
        )

        # Calculate LAB components
        L = np.where(
            xyz_normalized[..., 1] > 0.008856,
            116.0 * xyz_f[..., 1] - 16.0,
            903.3 * xyz_normalized[..., 1],
        )

        a = 500.0 * (xyz_f[..., 0] - xyz_f[..., 1])
        b = 200.0 * (xyz_f[..., 1] - xyz_f[..., 2])

        lab = np.stack([L, a, b], axis=-1)
        return lab

    def _lab2xyz(self, lab: np.ndarray) -> np.ndarray:
        """Convert LAB to XYZ color space."""
        L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]

        # Reference white (D65)
        ref_white = np.array([0.95047, 1.0, 1.08883])

        # Calculate intermediate values
        fy = (L + 16.0) / 116.0
        fx = a / 500.0 + fy
        fz = fy - b / 200.0

        # Calculate XYZ components
        xyz = np.zeros_like(lab)

        xyz_cubed = fx**3
        xyz[..., 0] = np.where(
            xyz_cubed > 0.008856, xyz_cubed, (fx - 16.0 / 116.0) / 7.787
        )

        y_cubed = fy**3
        xyz[..., 1] = np.where(L > 7.9996, y_cubed, L / 903.3)

        z_cubed = fz**3
        xyz[..., 2] = np.where(z_cubed > 0.008856, z_cubed, (fz - 16.0 / 116.0) / 7.787)

        # Denormalize by reference white
        xyz = xyz * ref_white
        return xyz

    def extract(self, img_ref: np.ndarray):
        """Extract reference mean, std in lab space.

        Args:
            img_ref: bgr numpy array of reference image.
        """
        # Calculate mean and std using NumPy
        try:
            # Convert BGR to LAB using NumPy
            lab_ref = self._bgr2lab(img_ref)
            self.mean_ref = np.mean(lab_ref, axis=(0, 1), keepdims=True)
            self.std_ref = np.std(lab_ref, axis=(0, 1), keepdims=True)
        except Exception as e:
            raise e

    def transfer(self, img: np.ndarray) -> np.ndarray:
        """Transfer the target image's color in lab space.

        Args:
            img: bgr numpy array of input image.
        Returns:
            img_tgt: bgr numpy array of target image.
        """
        # Convert BGR to LAB using NumPy
        lab = self._bgr2lab(img)
        # Calculate mean and std using NumPy
        mean = np.mean(lab, axis=(0, 1), keepdims=True)
        std = np.std(lab, axis=(0, 1), keepdims=True)
        # Apply color transfer formula
        lab_tgt = (lab - mean) / (std + self.eps) * self.std_ref + self.mean_ref

        # Clip values to valid range [0, 255]
        lab_tgt = np.array(np.clip(lab_tgt, 0, 255), dtype=np.uint8)

        # Convert LAB to BGR using NumPy
        img_tgt = self._lab2bgr(lab_tgt)
        return img_tgt
