import unittest

from scipy.spatial.distance import euclidean
import numpy as np

from matplotlib import pyplot as plt

from snowland.graphics.core import CutDirection
from snowland.graphics.utils import get_point_by_rate_index, move_distance_by_point, cut_to_length, alignment_with_cut

npa = np.array
npl = np.linalg


class TestCutToLength(unittest.TestCase):
    def test_start_2p9(self):
        line = npa([[0, 0], [0, 1], [1, 1], [1, 0]])
        dist = 2.9
        new_line = cut_to_length(line, dist, CutDirection.Start)
        new_line_truth = npa([[0, 0.1], [0, 1], [1, 1], [1, 0]])
        # print(new_line_truth)
        # print(new_line)
        # plt.plot(new_line_truth[:, 0], new_line_truth[:, 1], 'b')
        # plt.plot(new_line[:, 0], new_line[:, 1], 'r--')
        # plt.show()
        assert np.allclose(new_line, new_line_truth)

    def test_start_0p1(self):
        line = npa([[0, 0], [0, 1], [1, 1], [1, 0]])
        dist = 0.1
        new_line = cut_to_length(line, dist, CutDirection.Start)
        new_line_truth = npa([[1, 0.1], [1, 0]])
        # print(new_line_truth)
        # print(new_line)
        # plt.plot(new_line_truth[:, 0], new_line_truth[:, 1], 'b')
        # plt.plot(new_line[:, 0], new_line[:, 1], 'r--')
        # plt.show()
        assert np.allclose(new_line, new_line_truth)

    def test_end_2p9(self):
        line = npa([[0, 0], [0, 1], [1, 1], [1, 0]])
        dist = 2.9
        new_line = cut_to_length(line, dist, CutDirection.End)
        new_line_truth = npa([[0, 0], [0, 1], [1, 1], [1, 0.1]])
        # print(new_line_truth)
        # print(new_line)
        # plt.plot(new_line_truth[:, 0], new_line_truth[:, 1], 'b')
        # plt.plot(new_line[:, 0], new_line[:, 1], 'r--')
        # plt.show()
        assert np.allclose(new_line, new_line_truth)

    def test_end_0p1(self):
        line = npa([[0, 0], [0, 1], [1, 1], [1, 0]])
        dist = 0.1
        new_line = cut_to_length(line, dist, CutDirection.End)
        new_line_truth = npa([[0., 0.], [0., 0.1]])
        # print(new_line_truth)
        # print(new_line)
        # plt.plot(new_line_truth[:, 0], new_line_truth[:, 1], 'b')
        # plt.plot(new_line[:, 0], new_line[:, 1], 'r--')
        # plt.show()
        assert np.allclose(new_line, new_line_truth)

    def test_end_3p1(self):
        line = npa([[0, 0], [0, 1], [1, 1], [1, 0]])
        dist = 3.1
        new_line = cut_to_length(line, dist, CutDirection.End)
        new_line_truth = npa([[0, 0], [0, 1], [1, 1], [1, 0], [1, -0.1]])
        print(new_line_truth)
        print(new_line)
        # plt.plot(new_line_truth[:, 0], new_line_truth[:, 1], 'b')
        # plt.plot(new_line[:, 0], new_line[:, 1], 'r--')
        # plt.show()
        assert np.allclose(new_line, new_line_truth)

    def test_start_3p1(self):
        line = npa([[0, 0], [0, 1], [1, 1], [1, 0]])
        dist = 3.1
        new_line = cut_to_length(line, dist, CutDirection.Start)
        new_line_truth = npa([[0, -0.1], [0, 0], [0, 1], [1, 1], [1, 0]])
        print(new_line_truth)
        print(new_line)
        # plt.plot(new_line_truth[:, 0], new_line_truth[:, 1], 'b')
        # plt.plot(new_line[:, 0], new_line[:, 1], 'r--')
        # plt.show()
        assert np.allclose(new_line, new_line_truth)

    def test_start_0p1_3d(self):
        line = npa([[0, 0, 0], [0, 1, 1], [1, 1, 2], [1, 0, 3]])
        dist = 0.1
        new_line = cut_to_length(line, dist, CutDirection.End)
        new_line_truth = npa([[0., 0., 0], [0., 0.1, 0.1]])

        plt.plot(new_line_truth[:, 0], new_line_truth[:, 1], 'b')
        plt.plot(new_line[:, 0], new_line[:, 1], 'r--')
        plt.show()
        assert np.allclose(new_line, new_line_truth)


class TestAlignmentWithCut(unittest.TestCase):
    def test_case_1(self):
        line1 = npa([[0.0, 0], [1, 1], [3, 1], [4, 2]])
        line2 = npa([[0.2, 0.2], [1.2, 1.2], [3.2, 1.2], [4.2, 2.2]])
        new_line1, new_line2, _, _ = alignment_with_cut(line1, line2, eps=0.01)

        print(line1, new_line1)
        print(line2, new_line2)
        plt.figure(1)
        plt.grid("on")
        plt.plot(line1[:, 0], line1[:, 1], 'b-', label='line1')
        plt.plot(line2[:, 0], line2[:, 1], 'r-', label='line2')
        plt.legend(loc=0)
        plt.figure(2)
        plt.grid("on")
        plt.plot(new_line1[:, 0], new_line1[:, 1], 'b.--', label='line1')
        plt.plot(new_line2[:, 0], new_line2[:, 1], 'r.--', label='line2')
        plt.legend(loc=0)
        plt.show()
