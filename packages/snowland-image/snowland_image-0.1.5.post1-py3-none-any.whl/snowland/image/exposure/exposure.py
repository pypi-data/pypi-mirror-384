# -*- coding: utf-8 -*-

try:
    from collections import Counter
except ImportError:
    from collections.abc import Counter

import numpy as np
import cv2

npa = np.array


def histogram(image: np.ndarray):
    """
    像素直方图统计
    :param image:
    :return:
    """
    image: np.ndarray = npa(image)
    return Counter(image.flatten())


def equalize_hist(image: np.ndarray):
    """
    彩图按3通道进行直方图均衡化
    """
    result_image = np.zeros_like(image)
    result_image[:, :, 0] = cv2.equalizeHist(image[:, :, 0])
    result_image[:, :, 1] = cv2.equalizeHist(image[:, :, 1])
    result_image[:, :, 2] = cv2.equalizeHist(image[:, :, 2])
    return result_image
