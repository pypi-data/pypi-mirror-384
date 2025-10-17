# -*- coding: utf-8 -*-


import unittest

import numpy as np
from astartool.project import std_logging
from snowland.graphics.core.analytic_geometry_3d import *

npa = np.array


class TestLine3D(unittest.TestCase):
    @classmethod
    @std_logging()
    def setup_class(cls):
        pass

    @classmethod
    @std_logging()
    def teardown_class(cls):
        print('teardown_class()')

    @std_logging()
    def setup_method(self, method):
        pass

    @std_logging()
    def teardown_method(self, method):
        pass


class TestPlane3D(unittest.TestCase):
    @classmethod
    @std_logging()
    def setup_class(cls):
        pass

    @classmethod
    @std_logging()
    def teardown_class(cls):
        print('teardown_class()')

    @std_logging()
    def setup_method(self, method):
        pass

    @std_logging()
    def teardown_method(self, method):
        pass

    def test_xoy(self):
        xoy = Plane3D(v=(0, 0, 1), p0=(0, 0, 0))
        yoz = Plane3D(a=1, b=0, c=0, d=0)
        # zox = Plane3D(p1=(0, 0, 0), p2=(1, 0, 0), p3=(0, 0, 1))

        zox = Plane3D(p1=(1, 2, 3), p2=(1, 7, 0), p3=(0, 0, 1))
        self.assertTrue(xoy.is_vector_vertical(yoz.normal_vector()))

    def test_abc(self):
        npa = np.array
        from astar_math.linear_algebra.matrix import solve_mat
        mat = npa([[0, 5, -3], [-1, -7, 1]])
        result = npa([[0],[0]])
        # x = np.linalg.pinv(mat)
        # print(x)
        # print(x @ result)

        xx = solve_mat(mat, result)
        print(xx)
