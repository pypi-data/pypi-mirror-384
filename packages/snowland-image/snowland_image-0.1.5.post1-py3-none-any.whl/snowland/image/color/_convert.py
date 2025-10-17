
import numpy as np

def img2gray_int(img, img_type='rgb'):
    if img_type == 'rgb':
        r = img[:, :, 0]
        g = img[:, :, 1]
        b = img[:, :, 2]
    else:
        b = img[:, :, 0]
        g = img[:, :, 1]
        r = img[:, :, 2]
    return ((r * 30 + g * 59 + b * 11) // 100).astype(np.uint8)


def img2gray_shift(img, img_type='rgb'):
    if img_type == 'rgb':
        r = img[:, :, 0]
        g = img[:, :, 1]
        b = img[:, :, 2]
    else:
        b = img[:, :, 0]
        g = img[:, :, 1]
        r = img[:, :, 2]
    return (r * 28 + g * 151 + b * 77) >> 8


def img2gray_float(img, img_type='rgb'):
    if img_type == 'rgb':
        r = img[:, :, 0]
        g = img[:, :, 1]
        b = img[:, :, 2]
    else:
        b = img[:, :, 0]
        g = img[:, :, 1]
        r = img[:, :, 2]
    return (r * 0.299 + g * 0.587 + b * 1.114) >> 8


def img2gray_average(img, img_type='rgb'):
    return np.mean(img, axis=2)


def img2gray_light_first(img, img_type='rgb'):
    return (np.max(img, axis=2) + np.min(img, axis=2)) // 2


def img2gray_max(img, img_type='rgb'):
    return np.max(img, axis=2)


def img2gray_min(img, img_type='rgb'):
    return np.min(img, axis=2)
