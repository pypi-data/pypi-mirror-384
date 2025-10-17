import numpy as np

from snowland.graphics.utils import get_rotate_angle_degree
from matplotlib import pyplot as plt

npa = np.array


def format_point(p, eps=10):
    format = f"%.{eps}f"
    return format % p[0], format % p[1]


def get_points_by_circle_index(ps, start, end):
    if start < end:
        return ps[start:end]
    else:
        return np.vstack((ps[start:], ps[:end]))


def unoin_geometry(polygon1, polygon2, format_eps=10):
    """
    两个面求并
    :param polygon1:
    :param polygon2:
    :return:
    """
    str_points_p1 = [format_point(p, format_eps) for p in polygon1]
    str_points_p2 = [format_point(p, format_eps) for p in polygon2]
    set_ij = set(str_points_p1).intersection(str_points_p2)
    index_1 = []
    index_2 = []
    current_list = []
    li = []
    length_set = len(set_ij)
    if length_set:
        for x in set_ij:
            pi_ind = str_points_p1.index(x)
            pj_ind = str_points_p2.index(x)
            v1 = polygon1[(pi_ind + 1) % len(polygon1), :2] - polygon1[pi_ind, :2]
            v2 = polygon2[(pj_ind + 1) % len(polygon2), :2] - polygon1[pi_ind, :2]
            index_1.append(pi_ind)
            index_2.append(pj_ind)
            if np.cross(v1, v2) < 0:
                current_list.append(0)
            else:
                current_list.append(1)

        index_list = [index_1, index_2]
        polygon_list = [polygon1, polygon2]
        current = int(not current_list[0])
        start_point_index = index_list[current][0]
        first_point = (current, start_point_index)
        for i, _ in enumerate(set_ij):
            ind_min = min([ind for ind in range(length_set) if current_list[ind] == current],
                          key=lambda ind: (index_list[current][ind] - start_point_index - 1) % len
                          (polygon_list[current]) + 1)
            end_point_index = index_list[current][ind_min]
            li.append \
                (get_points_by_circle_index(polygon_list[current], start_point_index, end_point_index))
            current = int(not current)
            start_point_index = index_list[current][ind_min]
        # li.append(get_points_by_circle_index(polygon_list[current], start_point_index, first_point[1]))
        return np.vstack(li)
    else:
        return np.empty((4, 0))


if __name__ == '__main__':
    # polygon1 = npa([[116.71875, 40.19414314,  25.9, 0.],
    #                 [116.71875357, 40.19414132, 25.9, 0.],
    #                 [116.71879443, 40.19412048, 25.9, 0.],
    #                 [116.71883017, 40.19410225, 25.9, 0.],
    #                 [116.71885472, 40.19414854, 25.91, 0.],
    #                 [116.71889754, 40.19424178, 25.93, 0.],
    #                 [116.7188608, 40.19425966, 25.93, 0.],
    #                 [116.71882071, 40.19427916, 25.93, 0.],
    #                 [116.7187733, 40.19430516, 25.93, 0.],
    #                 [116.71875, 40.19425788, 25.93, 0.]])
    #
    # polygon2 = npa([[116.71875, 40.19414314,  25.9, 0.],
    #                 [116.71875357, 40.19414132, 25.9, 0.]])
    #                 [116.71879443, 40.19412048, 25.9, 0.],
    #                 [116.71883017, 40.19410225, 25.9, 0.],
    #                 [116.71885472, 40.19414854, 25.91, 0.],
    #                 [116.71889754, 40.19424178, 25.93, 0.],
    #                 [116.7188608, 40.19425966, 25.93, 0.],
    #                 [116.71882071, 40.19427916, 25.93, 0.],
    #                 [116.7187733, 40.19430516, 25.93, 0.],
    #                 [116.71875, 40.19425788, 25.93, 0.]])
    polygon1 = np.load("D:\\a.npy")
    polygon2 = np.load("D:\\b.npy")

    plt.plot(polygon1[:, 0], polygon1[:, 1], 'r')
    for i, p in enumerate(polygon1):
        plt.text(p[0], p[1], str(i))
    plt.plot(polygon2[:, 0], polygon2[:, 1], 'b')
    for i, p in enumerate(polygon2):
        plt.text(p[0], p[1], str(i))

    ps = unoin_geometry(polygon1, polygon2, 10)
    print(ps)
    plt.plot(ps[:, 0], ps[:, 1], 'g--')
    for i, p in enumerate(ps):
        plt.text(p[0], p[1], str(i))
    plt.show()
