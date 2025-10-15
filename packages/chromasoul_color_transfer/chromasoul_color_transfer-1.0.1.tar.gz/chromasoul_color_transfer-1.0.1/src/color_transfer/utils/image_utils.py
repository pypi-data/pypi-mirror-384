#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
import cv2
import os


class ImageUtils:

    @staticmethod
    def load_img(path: str) -> np.ndarray:
        """
        load image from the path and convert to BGR numpy ndarray.
        Args:
            path: the path to the image.
        Returns:
            img: bgr numpy array of the image.
        """
        # use OpenCV to read the image
        # use cv2.IMREAD_COLOR to make sure the shape is (H, W, 3)
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"The path {path} does not exist.")

            img = cv2.imread(path, cv2.IMREAD_COLOR)

            if img is None:
                raise Exception(f"The image may be broken.")
            return img
        except Exception as e:
            raise e

    @staticmethod
    def save_img(img: np.ndarray, path: str):
        """
        Save the BGR format numpy ndarry to image file.
        Args:
            img: bgr numpy array of the image.
            path: the path to save the image.
        """
        if img is None:
            raise ValueError("The image cannot be None.")

        if not isinstance(img, np.ndarray):
            raise ValueError("The image must be numpy ndarray.")

        try:
            # make sure the target dir exists.
            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            # save the image use cv2
            cv2.imwrite(path, img)
        except Exception as e:
            raise e
