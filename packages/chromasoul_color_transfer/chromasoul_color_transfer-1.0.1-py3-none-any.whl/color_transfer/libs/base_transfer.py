#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np


class BaseTransfer:
    """The Base Transfer Class for Color Transfer."""

    def __init__(self):
        self.eps = 1e-6  # avoid the divide zero error

    def extract(self, img_ref: np.ndarray):
        print(img_ref)

    def transfer(self, img: np.ndarray) -> np.ndarray:
        img_tgt = img
        return img_tgt
