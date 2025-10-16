#!/usr/bin/env python
# -*- coding: utf-8 -*-

from color_transfer.libs.base_transfer import BaseTransfer
import numpy as np
from typing import Optional
import ot


class EMDTransfer(BaseTransfer):
    """Transfer reference image's color space to input image's color space using EMD Transport."""

    def __init__(self):
        super().__init__()
        # training samples
        self.samples_num = 500
        self.samples_ref: Optional[np.ndarray] = None

    def extract(self, img_ref: np.ndarray):
        """Extract reference data from reference image.

        Args:
            img_ref: bgr numpy array of reference image.
        """
        try:
            img_ref = img_ref[:, :, ::-1]
            img_ref = img_ref.astype(np.float64)
            normal_ref = np.clip(img_ref / 255.0, 0.0, 1.0)

            h, w, c = normal_ref.shape
            mat_ref = normal_ref.reshape(h * w, c)

            idx_ref = np.random.randint(mat_ref.shape[0], size=(self.samples_num,))

            self.samples_ref = mat_ref[idx_ref, :]
        except Exception as e:
            raise e

    def transfer(self, img: np.ndarray) -> np.ndarray:
        """Transfer the target image's color.
        Args:
            img: bgr numpy array of input image.
        Returns:
            img_tgt: bgr numpy array of target image.
        """
        img = img[:, :, ::-1]
        img = img.astype(np.float64)
        normal = np.clip(img / 255.0, 0.0, 1.0)

        h, w, c = normal.shape
        mat = normal.reshape(h * w, c)
        idx = np.random.randint(mat.shape[0], size=(self.samples_num,))

        samples = mat[idx, :]

        # EMDTransport
        # need to fit every image
        ot_emd = ot.da.EMDTransport()
        ot_emd.fit(Xs=samples, Xt=self.samples_ref)

        emd_tgt: np.ndarray = ot_emd.transform(Xs=mat)

        img_out_float = np.clip(emd_tgt.reshape(normal.shape), 0, 1)

        # Reshape back to original shape
        img_out_float = (img_out_float * 255).astype(np.uint8)

        img_tgt = np.array(np.clip(img_out_float, 0, 255), dtype=np.uint8)
        img_tgt = img_tgt[:, :, ::-1]

        return img_tgt
