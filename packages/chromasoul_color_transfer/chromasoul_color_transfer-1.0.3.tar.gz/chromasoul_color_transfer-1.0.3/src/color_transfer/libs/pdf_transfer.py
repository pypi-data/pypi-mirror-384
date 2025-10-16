#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List, Optional
import numpy as np
import cv2
from color_transfer.libs.base_transfer import BaseTransfer


class PDFTransfer(BaseTransfer):
    """Transfer reference image's color distribution to input image using PDF matching with regrain.

    This implementation uses optimal rotation matrices for 3-channel images and performs
    probability density function transfer in multiple color spaces, with optional texture preservation.
    """

    def __init__(
        self,
        regrain: bool = False,
        smoothness: float = 1.0,
        nbits: List[int] = None,
    ):
        """Initialize PDF transfer with parameters.

        Args:
            regrain: Whether to apply texture preservation.
            smoothness: Smoothness parameter for regrain.
            n_bits: Pyramid levels.
        """
        super().__init__()
        self.regrain = regrain

        # Default nbits values for pyramid levels
        if nbits is None:
            nbits = [4, 16, 32, 64, 64, 64]

        self.rotation_matrices = self._get_optimal_rotations()
        self.ref_cdfs: Optional[List[np.ndarray]] = None

        # Initialize regrain processor if needed
        if self.regrain:
            self.regrain_processor = _Regrain(smoothness=smoothness, nbits=nbits)

    def extract(self, img_ref: np.ndarray):
        """Extract reference image's color distribution information.

        Args:
            img_ref: BGR numpy array of reference image, shape (h, w, 3).
        """
        # Convert to float and normalize to [0, 1]
        img_ref_float = img_ref.astype(np.float32) / 255.0

        # Reshape to (c, h*w)
        _, _, c = img_ref_float.shape
        reshape_ref = img_ref_float.reshape(-1, c).transpose()

        # Calculate CDFs for each rotation
        self.ref_cdfs = []

        for rotation_matrix in self.rotation_matrices:
            # Rotate reference image
            rot_ref = np.matmul(rotation_matrix, reshape_ref)
            self.ref_cdfs.append(rot_ref)

    def transfer(self, img: np.ndarray) -> np.ndarray:
        """Transfer reference color distribution to input image.
        Args:
            img: BGR numpy array of input image, shape (h, w, c).
        Returns:
            img_out: BGR numpy array of transferred image, shape (h, w, c).
        """
        # Convert to float and normalize to [0, 1]
        img_float = img.astype(np.float32) / 255.0

        # Reshape to (c, h*w)
        h, w, c = img_float.shape
        reshape_img = img_float.reshape(-1, c).transpose()

        # Apply PDF transfer
        img_out_float = self._pdf_transfer_nd(reshape_img)

        # Convert to uint8
        img_out_float = np.clip(img_out_float, 0, 1)
        # Reshape back to original shape
        img_out_float = (img_out_float * 255).astype(np.uint8)
        img_out_float = img_out_float.transpose().reshape(h, w, c)

        # Apply regrain if enabled
        if self.regrain:
            img_out_float = self.regrain_processor.regrain(img_float, img_out_float)

        # Clip values to valid range [0, 255]
        img_tgt = np.array(np.clip(img_out_float, 0, 255), dtype=np.uint8)

        return img_tgt

    def _pdf_transfer_nd(self, img: np.ndarray, step_size: int = 1) -> np.ndarray:
        """Apply n-dim probability density function transfer.
        Args:
            img: shape=(c, n).
            step_size: arr = arr + step_size * delta_arr.
        Returns:
            img_out: shape=(c, n).
        """
        # n times of 1d-pdf-transfer
        img_out = np.array(img)
        for index in range(len(self.rotation_matrices)):
            rotation_matrix: np.ndarray = self.rotation_matrices[index]
            rot_arr_ref = self.ref_cdfs[index]

            rot_arr_in: np.ndarray = np.matmul(rotation_matrix, img_out)
            rot_arr_out = np.zeros(rot_arr_in.shape)
            for i in range(rot_arr_out.shape[0]):
                rot_arr_out[i] = self._pdf_transfer_1d(rot_arr_in[i], rot_arr_ref[i])
            rot_delta_arr = rot_arr_out - rot_arr_in
            delta_arr = np.matmul(rotation_matrix.transpose(), rot_delta_arr)
            img_out = step_size * delta_arr + img_out
        return img_out

    def _pdf_transfer_1d(self, arr_in=None, arr_ref=None, n=300):
        """Apply 1-dim probability density function transfer.
        Args:
            arr_in: 1d numpy input array.
            arr_ref: 1d numpy reference array.
            n: discretization num of distribution of image's pixels.
        Returns:
            arr_out: transfered input array.
        """

        arr: np.ndarray = np.concatenate((arr_in, arr_ref))
        # discretization as histogram
        min_v = arr.min() - self.eps
        max_v = arr.max() + self.eps
        xs = np.array([min_v + (max_v - min_v) * i / n for i in range(n + 1)])
        hist_in, _ = np.histogram(arr_in, xs)
        hist_ref, _ = np.histogram(arr_ref, xs)
        xs = xs[:-1]
        # compute probability distribution
        cum_in = np.cumsum(hist_in)
        cum_ref = np.cumsum(hist_ref)
        d_in = cum_in / cum_in[-1]
        d_ref = cum_ref / cum_ref[-1]
        # transfer
        t_d_in = np.interp(d_in, d_ref, xs)
        t_d_in[d_in <= d_ref[0]] = min_v
        t_d_in[d_in >= d_ref[-1]] = max_v
        arr_out = np.interp(arr_in, xs, t_d_in)
        return arr_out

    def _get_optimal_rotations(self) -> List[np.ndarray]:
        """Get optimal rotation matrices for 3-channel color transfer.

        Returns:
            List of 3x3 optimal rotation matrices.
        """
        # Optimal rotations for 3-channel color transfer
        rotations = [
            np.eye(3),  # Identity
            np.array(
                [
                    [0.3333, 0.6667, 0.6667],
                    [0.6667, 0.3333, -0.6667],
                    [-0.6667, 0.6667, -0.3333],
                ]
            ),
            np.array(
                [
                    [0.5774, 0.5774, 0.5774],
                    [0.5774, 0.2113, -0.7887],
                    [-0.5774, 0.7887, -0.2113],
                ]
            ),
            np.array(
                [
                    [0.5774, 0.4082, 0.7071],
                    [0.5774, 0.4082, -0.7071],
                    [-0.5774, 0.8165, 0.0],
                ]
            ),
            np.array(
                [
                    [0.3326, 0.1978, 0.9220],
                    [0.6652, 0.6753, -0.3170],
                    [-0.6652, 0.7104, 0.2206],
                ]
            ),
            np.array(
                [
                    [0.4685, 0.8616, 0.1954],
                    [0.4685, -0.4253, -0.7746],
                    [-0.7491, 0.2766, -0.6015],
                ]
            ),
        ]
        return rotations


class _Regrain:
    """Internal class for texture preservation (regrain) after color transfer.

    This implementation preserves the texture of the original image while applying
    the color characteristics of the transferred image.
    """

    def __init__(self, smoothness: float = 1.0, nbits: List[int] = None):
        """Initialize regrain processor.

        Args:
            smoothness: Controls the smoothness of the regrain process.
            nbits: Number of iterations at each pyramid level.
        """
        self.smoothness = smoothness
        self.nbits = nbits if nbits is not None else [4, 16, 32, 64, 64, 64]
        self.level = 0

    def regrain(self, img_arr_in: np.ndarray, img_arr_col: np.ndarray) -> np.ndarray:
        """Preserve texture of original image while applying transferred colors.

        Args:
            img_arr_in: Original input image (normalized to [0, 1]).
            img_arr_col: Color-transferred image (normalized to [0, 1]).

        Returns:
            img_arr_out: Result image with preserved texture and transferred colors.
        """
        img_arr_out = np.array(img_arr_in)
        img_arr_out = self._regrain_recursive(
            img_arr_out, img_arr_in, img_arr_col, self.nbits, self.level
        )
        return img_arr_out

    def _regrain_recursive(
        self,
        img_arr_out: np.ndarray,
        img_arr_in: np.ndarray,
        img_arr_col: np.ndarray,
        nbits: List[int],
        level: int,
    ) -> np.ndarray:
        """Recursive implementation of multi-resolution regrain.

        Args:
            img_arr_out: Current output image.
            img_arr_in: Original input image.
            img_arr_col: Color-transferred image.
            nbits: Number of iterations at each pyramid level.
            level: Current pyramid level.

        Returns:
            img_arr_out: Processed image at current level.
        """
        h, w, _ = img_arr_in.shape
        h2 = (h + 1) // 2
        w2 = (w + 1) // 2

        # Process at lower resolution if possible
        if len(nbits) > 1 and h2 > 20 and w2 > 20:
            # Resize images to lower resolution
            resize_arr_in = cv2.resize(
                img_arr_in, (w2, h2), interpolation=cv2.INTER_LINEAR
            )
            resize_arr_col = cv2.resize(
                img_arr_col, (w2, h2), interpolation=cv2.INTER_LINEAR
            )
            resize_arr_out = cv2.resize(
                img_arr_out, (w2, h2), interpolation=cv2.INTER_LINEAR
            )

            # Recursive call at lower resolution
            resize_arr_out = self._regrain_recursive(
                resize_arr_out, resize_arr_in, resize_arr_col, nbits[1:], level + 1
            )

            # Resize back to original resolution
            img_arr_out = cv2.resize(
                resize_arr_out, (w, h), interpolation=cv2.INTER_LINEAR
            )

        # Solve at current resolution
        img_arr_out = self._solve(img_arr_out, img_arr_in, img_arr_col, nbits[0], level)
        return img_arr_out

    def _solve(
        self,
        img_arr_out: np.ndarray,
        img_arr_in: np.ndarray,
        img_arr_col: np.ndarray,
        nbit: int,
        level: int,
        eps: float = 1e-6,
    ) -> np.ndarray:
        """Solve the optimization problem for texture preservation.

        Args:
            img_arr_out: Current output image.
            img_arr_in: Original input image.
            img_arr_col: Color-transferred image.
            nbit: Number of iterations.
            level: Current pyramid level.
            eps: Small value to prevent division by zero.

        Returns:
            img_arr_out: Optimized output image.
        """
        h, w, c = img_arr_in.shape

        # Helper functions for padding
        def first_pad_0(arr: np.ndarray) -> np.ndarray:
            return np.concatenate((arr[:1, :], arr[:-1, :]), axis=0)

        def first_pad_1(arr: np.ndarray) -> np.ndarray:
            return np.concatenate((arr[:, :1], arr[:, :-1]), axis=1)

        def last_pad_0(arr: np.ndarray) -> np.ndarray:
            return np.concatenate((arr[1:, :], arr[-1:, :]), axis=0)

        def last_pad_1(arr: np.ndarray) -> np.ndarray:
            return np.concatenate((arr[:, 1:], arr[:, -1:]), axis=1)

        # Calculate gradients
        delta_x = last_pad_1(img_arr_in) - first_pad_1(img_arr_in)
        delta_y = last_pad_0(img_arr_in) - first_pad_0(img_arr_in)
        delta = np.sqrt((delta_x**2 + delta_y**2).sum(axis=2, keepdims=True))

        # Calculate weights
        psi = 256 * delta / 5
        psi[psi > 1] = 1
        phi = 30 * 2 ** (-level) / (1 + 10 * delta / self.smoothness)

        # Calculate directional weights
        phi1 = (last_pad_1(phi) + phi) / 2
        phi2 = (last_pad_0(phi) + phi) / 2
        phi3 = (first_pad_1(phi) + phi) / 2
        phi4 = (first_pad_0(phi) + phi) / 2

        # Iterative optimization
        rho = 1 / 5.0
        for i in range(nbit):
            den = psi + phi1 + phi2 + phi3 + phi4
            num = (
                np.tile(psi, [1, 1, c]) * img_arr_col
                + np.tile(phi1, [1, 1, c])
                * (last_pad_1(img_arr_out) - last_pad_1(img_arr_in) + img_arr_in)
                + np.tile(phi2, [1, 1, c])
                * (last_pad_0(img_arr_out) - last_pad_0(img_arr_in) + img_arr_in)
                + np.tile(phi3, [1, 1, c])
                * (first_pad_1(img_arr_out) - first_pad_1(img_arr_in) + img_arr_in)
                + np.tile(phi4, [1, 1, c])
                * (first_pad_0(img_arr_out) - first_pad_0(img_arr_in) + img_arr_in)
            )

            img_arr_out = (
                num / np.tile(den + eps, [1, 1, c]) * (1 - rho) + rho * img_arr_out
            )

        return img_arr_out
