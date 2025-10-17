# -*- coding: utf-8 -*-
from typing import List, Union

import matplotlib.pyplot as plt
import numpy as np

from skimage.data import checkerboard

npa = np.array


def get_left_up_start_pt(bin_img):
    """
    获取左上角边界点， 从左上角查找开始
    :param bin_img:
    :return:
    """
    h = bin_img.shape[0]
    find, start_i, start_j = False, 0, 0

    for i in range(h):
        xi, = np.where(bin_img[i] == 0)
        if len(xi):
            find, start_i, start_j = True, i, xi[0]
            break
    return find, start_i, start_j


def trace_contour(bin_img, find, start_i, start_j):
    h, w = bin_img.shape
    Direct = [(-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0)]
    BeginDirect = 0
    findstart = 0
    cur_i, cur_j = start_i, start_j
    li = [(cur_i, cur_j)]
    while findstart == 0:
        findpoint = 0
        while findpoint == 0:
            i, j = cur_i + Direct[BeginDirect][1], cur_j + Direct[BeginDirect][0]
            if not (0 <= i < h and 0 <= j < w):
                BeginDirect = (BeginDirect + 1) % 8
                break
            pixel = bin_img[i][j]
            if pixel == 0:
                findpoint = 1
                cur_i, cur_j = i, j
                if cur_i == start_i and cur_j == start_j:
                    findstart = 1
                else:
                    li.append((i, j))

                BeginDirect = (BeginDirect - 2) % 8
            else:
                BeginDirect = (BeginDirect + 1) % 8
    return li


def trace_contour_with_mask(bin_img, find, start_i, start_j):
    h, w = bin_img.shape
    contour_img = np.ones_like(bin_img, dtype=np.uint8) * 255

    if find:
        contour_img[start_i][start_j] = 0

    Direct = [(-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0)]
    BeginDirect = 0
    findstart = 0
    cur_i = start_i
    cur_j = start_j
    li = [(cur_i, cur_j)]
    while findstart == 0:
        findpoint = 0
        while findpoint == 0:
            i = cur_i + Direct[BeginDirect][1]
            j = cur_j + Direct[BeginDirect][0]
            if not (0 <= i < h and 0 <= j < w):
                BeginDirect = (BeginDirect + 1) % 8
                break
            pixel = bin_img[i][j]
            if pixel == 0:
                findpoint = 1
                cur_i = i
                cur_j = j
                if cur_i == start_i and cur_j == start_j:
                    findstart = 1
                else:
                    li.append((i, j))

                contour_img[cur_i][cur_j] = 0

                BeginDirect -= 1
                if BeginDirect == -1:
                    BeginDirect = 7
                BeginDirect -= 1
                if BeginDirect == -1:
                    BeginDirect = 7
            else:
                BeginDirect += 1
                if BeginDirect == 8:
                    BeginDirect = 0

    return contour_img, li


def inner_boundary_tracking(points: Union[List, np.ndarray]):
    """
    内边界跟踪算法
    :param points:
    :return:
    """
    points = npa(points)
    set_points = set(((p[0], p[1]) for p in points))
    start = min(set_points)
    Direct = npa([(-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0)])
    BeginDirect = 0
    cur = start
    li = [cur]
    while True:
        p = cur + Direct[BeginDirect]
        if (p[0], p[1]) in set_points:
            if np.allclose(p, start):
                break
            else:
                li.append(p)
                cur = p
            BeginDirect = (BeginDirect - 2) % 8
        else:
            BeginDirect = (BeginDirect + 1) % 8
    return li


# 调用
if __name__ == '__main__':
    bin_img = checkerboard()
    find, start_i, start_j = get_left_up_start_pt(bin_img)
    contour_img, li = trace_contour_with_mask(bin_img, find, start_i, start_j)
    points_x, points_y = np.where(bin_img == 0)
    points = list(zip(points_x, points_y))
    li2 = inner_boundary_tracking(points)
    print(len(li), len(li2))
    plt.imshow(contour_img, cmap='gray')
    plt.show()
    print(li)
