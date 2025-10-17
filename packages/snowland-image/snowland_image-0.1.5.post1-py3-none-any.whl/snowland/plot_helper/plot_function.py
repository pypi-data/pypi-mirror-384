# -*- coding: utf-8 -*-
from typing import List, Tuple

import numpy as np
from astartool.error import ParameterError, ParameterValueError
from matplotlib import pylab as plt
from mpl_toolkits import mplot3d
from snowland.graphics.core.analytic_geometry_2d import Line2D, FunctionLine2D
from snowland.graphics.core.analytic_geometry_3d import FunctionSurface, FunctionLine3D
from snowland.graphics.core.analytic_geometry_base import Function
from astar_math.functions import DiscreteBaseIntervals, ContinuousBaseIntervals, BaseIntervals, Intervals, IntervalType, ListIntervals

npa = np.array


def plot_line2d_geometry(line: Line2D, x=None, y=None, *args, handle=plt, **kwargs):
    """
    绘制线数据line_2d
    :param line: Line2D
    :param x: np.ndarray or list, 可选, x范围
    :param y: np.ndarray or list, 可选, y范围
    :param args:
    :param handle: 绘图句柄
    :param kwargs:
    :return:
    """
    if x is not None:
        y = line.get(x=x)
        ax = handle.plot(x, y, *args, **kwargs)
    elif y is not None:
        x = line.get(y=y)
        ax = handle.plot(x, y, *args, **kwargs)
    else:
        raise ParameterError("错误的输入数据")
    return ax


def plot_function_2d(function: FunctionLine2D,
                     interval: (BaseIntervals, Intervals, List, np.ndarray, Tuple) = None,
                     points=10, *args, handle=plt, **kwargs):
    """
    绘制函数
    :param function: 多项式对象
    :param interval: 绘制的区间（左右均为闭区间）
    :param points: 绘制的点数
    :param args: matplotlib参数
    :param handle: 绘图句柄
    :param kwargs: matplotlib参数
    :return:
    """
    if interval is None:
        if isinstance(function, FunctionLine2D):
            interval = function.domain_of_definition
        else:
            interval = ListIntervals(ContinuousBaseIntervals((-10, 10), open_or_closed=[IntervalType.Closed, IntervalType.Closed]))
    else:
        if isinstance(interval, BaseIntervals):
            interval = ListIntervals(interval)
        elif isinstance(interval, Intervals):
            pass
        else:
            assert len(interval) == 2
            interval = ListIntervals(ContinuousBaseIntervals(interval, open_or_closed=[IntervalType.Closed, IntervalType.Closed]))

    if not isinstance(function, FunctionLine2D):
        function = FunctionLine2D(function)
    if interval.is_empty():
        raise ParameterValueError("interval error")
    for base_interval in interval.intervals:
        if isinstance(base_interval, DiscreteBaseIntervals):
            if interval.use_values:
                res = handle.scatter(interval.values, function(interval.values))
            else:
                boundary = base_interval.boundary
                f1 = np.isinf(boundary[0])
                f2 = np.isinf(boundary[1])
                if f1 and f2:
                    boundary = [-10, 10]
                elif f1:
                    boundary = [boundary[1] - 20, boundary[1]]
                elif f2:
                    boundary = [boundary[0], 20 + boundary[1]]

                x = np.linspace(boundary[0], boundary[1], points)
                y = function(x)
                res = handle.scatter(x, y, *args, **kwargs)
        else:
            boundary = base_interval.boundary
            f1 = np.isinf(boundary[0])
            f2 = np.isinf(boundary[1])
            if f1 and f2:
                boundary = [-10, 10]
            elif f1:
                boundary = [boundary[1] - 20, boundary[1]]
            elif f2:
                boundary = [boundary[0], 20 + boundary[1]]

            x = np.linspace(boundary[0], boundary[1], points)
            y = function(x)
            res = handle.plot(x, y, *args, **kwargs)

    return res


def plot_function_surface_3d(function: FunctionSurface, interval, points=10, *args, handle=plt, **kwargs):
    """
    绘制多项式
    :param function: 多项式对象
    :param interval: 绘制的区间（左右均为闭区间）
    :param points: 绘制的点数
    :param args: matplotlib参数
    :param handle: 绘图句柄
    :param kwargs: matplotlib参数
    :return:
    """
    if handle == plt:
        handle = plt.axes(projection='3d')
    if isinstance(points, int):
        p1, p2 = points, points
    else:
        p1, p2 = points[:2]
    xi = np.linspace(interval[0][0], interval[0][1], p1)
    yi = np.linspace(interval[1][0], interval[1][1], p2)
    XI, YI = np.meshgrid(xi, yi)
    function = FunctionSurface(function)
    res = handle.plot_surface(XI, YI, function([XI, YI]), *args, **kwargs)
    return res


def plot_function_line_3d(function: FunctionSurface, interval, points=10, *args, handle=plt, **kwargs):
    """
    绘制多项式
    :param function: 多项式对象
    :param interval: 绘制的区间（左右均为闭区间）
    :param points: 绘制的点数
    :param args: matplotlib参数
    :param handle: 绘图句柄
    :param kwargs: matplotlib参数
    :return:
    """
    if handle == plt:
        handle = plt.axes(projection='3d')
    if isinstance(points, int):
        p1, p2 = points, points
    else:
        p1, p2 = points[:2]
    xi = np.linspace(interval[0][0], interval[0][1], p1)
    yi = np.linspace(interval[1][0], interval[1][1], p2)
    function = FunctionSurface(function)
    res = handle.plot3D(xi, yi, function([xi, yi]), *args, **kwargs)
    return res


def plot_function(function: Function, interval, points=10, *args, handle=plt, **kwargs):
    """
    绘制函数
    :param function:
    :param interval:
    :param points:
    :param args:
    :param handle:
    :param kwargs:
    :return:
    """
    if isinstance(function, FunctionLine2D):
        return plot_function_2d(function, interval, points=points, *args, handle=handle, **kwargs)
    elif isinstance(function, FunctionSurface):
        if handle == plt:
            handle = plt.axes(projection='3d')
        return plot_function_surface_3d(function, interval, points=points, *args, handle=handle, **kwargs)
    elif isinstance(function, FunctionLine3D):
        if handle == plt:
            handle = plt.axes(projection='3d')
        return plot_function_line_3d(function, interval, points=points, *args, handle=handle, **kwargs)
    else:
        return plot_function_2d(function, interval, points=points, *args, handle=handle, **kwargs)
