"""
Graphics primitives module
Provides stuff like Disk, Sphere, etc. and lets them figure out how to plot themselves
"""

__all__ = [
    "GraphicsPrimitive",
    "Sphere",
    "Cylinder",
    "Disk",
    "Line",
    "Text",
    "Arrow",
    "Inset",
    "Point",
    "Triangle",
    "Polygon"
]

import abc, numpy as np
from .VTKInterface import *

class GraphicsPrimitive(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def plot(self, axes, *args, graphics=None, **kwargs):
        """The one method that needs to be implemented, which takes the graphics and actually puts stuff on its axes

        :param axes:
        :type axes:
        :param args:
        :type args:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        pass

    @abc.abstractmethod
    def get_bbox(self):
        ...

class Disk(GraphicsPrimitive):
    def __init__(self, position=(0, 0), radius=1, **opts):
        self.pos = position
        self.rad = radius
        self.opts = opts
        self.prim = None

    def get_bbox(self):
        return [(self.pos[0]-self.rad, self.pos[1]-self.rad), (self.pos[0]+self.rad, self.pos[1]+self.rad)]

    def plot(self, axes, *args, graphics=None, zdir=None, **kwargs):
        if hasattr(axes, 'axes'):
            axes = axes.axes

        return axes.draw_disk(self.pos, radius=self.rad, **dict(self.opts, **kwargs))
class Line(GraphicsPrimitive):
    def __init__(self, points, radius=.1, **opts):
        self.pos = points
        # self.pos2 = pos2
        # self.rest = rest
        self.rad = 72*radius # this can't be configured nearly as cleanly as the circle stuff...
        self.opts = opts
    @property
    def points(self):
        return self.pos
    def get_bbox(self):
        pos = np.array(self.points).T
        return [(np.min(pos[0]), np.min(pos[1])), (np.max(pos[0]), np.max(pos[1]))]
    def plot(self, axes, *args, graphics=None, **kwargs):
        if hasattr(axes, 'axes'):
            axes = axes.axes

        kw = dict(edgecolors=[[0.]*3+[.3]])
        kw = dict(kw, **self.opts)
        kw = dict(kw, s=[(10*self.rad)**2], **kwargs)
        return axes.draw_line(self.pos, **kw)

class Text(GraphicsPrimitive):
    def __init__(self, txt, pos, bbox=((1, 1), (1, 1)), **opts):
        self.txt = txt
        self.pos = pos
        self.bbox = bbox
        self.opts = opts
    def get_bbox(self):
        return [
            (self.pos[0]-self.bbox[0][0], self.pos[1]-self.bbox[1][0]),
            (self.pos[0]+self.bbox[0][1], self.pos[1]+self.bbox[1][1])
        ]
    def plot(self, axes, *args, graphics=None, **kwargs):
        if hasattr(axes, 'axes'):
            axes = axes.axes
        return axes.draw_text(self.pos, self.txt, **self.opts)

class Arrow(GraphicsPrimitive):
    def __init__(self, pos1, pos2, **opts):
        self.pos1 = pos1
        self.pos2 = pos2
        self.opts = opts
    def get_bbox(self):
        pos = np.array([self.pos1, self.pos2]).T
        return [(np.min(pos[0]), np.min(pos[1])), (np.max(pos[0]), np.max(pos[1]))]
    def plot(self, axes, *args, graphics=None, **kwargs):
        if hasattr(axes, 'axes'):
            axes = axes.axes
        return axes.draw_arrow([self.pos1, self.pos2], **self.opts)

class Sphere(GraphicsPrimitive):
    def __init__(self, position=(0, 0, 0), radius=1, sphere_points=48, **opts):
        self.pos = position
        self.rad = radius
        self.opts = dict(opts, sphere_points=sphere_points)

    def get_bbox(self):
        raise NotImplementedError("...")

    def plot(self, axes, *args, sphere_points=None, graphics=None, **kwargs):
        if hasattr(axes, 'axes'):
            axes = axes.axes
        return axes.draw_sphere(self.pos, self.rad, **self.opts)

class Cylinder(GraphicsPrimitive):
    def __init__(self, p1, p2, radius, circle_points = 32, **opts):
        self.pos1 = p1
        self.pos2 = p2
        self.rad = radius
        self.opts = opts
        self.circle_points = circle_points

    def get_bbox(self):
        raise NotImplementedError("...")

    def plot(self, axes, *args, circle_points=None, graphics=None, **kwargs):
        if isinstance(axes.figure, VTKWindow):
            self.prim = VTKCylinder(self.pos1, self.pos2, self.rad, **self.opts)
            s = self.prim
            return s.plot(axes.figure)
        else:
            if hasattr(axes, 'axes'):
                axes = axes.axes
            return axes.draw_cylinder(self.pos1, self.pos2, self.rad, **self.opts)

class Point(GraphicsPrimitive):
    def __init__(self, pts, **opts):
        self.pos = pts
        self.opts = dict(opts)

    def get_bbox(self):
        raise NotImplementedError("...")

    def plot(self, axes, *args, graphics=None, **kwargs):
        if hasattr(axes, 'axes'):
            axes = axes.axes
        return axes.draw_point(self.pos, **self.opts)

class Triangle(GraphicsPrimitive):
    def __init__(self, pts, **opts):
        self.pos = pts
        self.opts = dict(opts)

    def get_bbox(self):
        raise NotImplementedError("...")

    def plot(self, axes, *args, sphere_points=None, graphics=None, **kwargs):
        if hasattr(axes, 'axes'):
            axes = axes.axes
        return axes.draw_triangle(self.pos, **self.opts)

class Polygon(GraphicsPrimitive):
    def __init__(self, points, **opts):
        self.pos = points
        self.opts = dict(opts)

    def get_bbox(self):
        raise NotImplementedError("...")

    def plot(self, axes, *args, sphere_points=None, graphics=None, **kwargs):
        if hasattr(axes, 'axes'):
            axes = axes.axes
        return axes.draw_poly(self.pos, **self.opts)


class Inset(GraphicsPrimitive):
    def __init__(self, prims, position, offset=(.5, .5), dimensions=None, plot_range=None, **opts):
        self.prims = prims
        self.pos = position
        self.opts = opts
        self._plot_range = plot_range
        self._dimensions = dimensions
        self.offset = offset
        self._prim_cache = {}

    @property
    def plot_range(self):
        if self._plot_range is None:
            return self.get_plot_range()
        else:
            return self._plot_range
    @plot_range.setter
    def plot_range(self, pr):
        ((_, _), (_, _)) = pr
        self.plot_range = pr
    def get_plot_range(self):
        if len(self.prims) == 0:
            return [[0, 1], [0, 1]]
        [(plx, prx), (pby, pty)] = [[np.inf, -np.inf], [np.inf, -np.inf]]
        for g in self.prims:
            ((lx, by), (rx, ty)) = g.get_bbox()
            plx = min(lx, plx)
            prx = max(rx, prx)
            pby = min(by, pby)
            pty = max(ty,pty)
        return [(plx, prx), (pby, pty)]

    @property
    def dimensions(self):
        if self._dimensions is None:
            ((lx, rx), (by, ty)) = self.plot_range
            return (rx - lx, ty - by)
        else:
            dims = self._dimensions
            if dims[0] is None:
                ((lx, rx), (by, ty)) = self.plot_range
                w = (rx - lx)/(ty - by)*dims[1]
                dims = (w, dims[1])
            elif dims[1] is None:
                ((lx, rx), (by, ty)) = self.plot_range
                h = (ty - by)/(rx - lx)*dims[0]
                dims = (dims[0], h)
            return dims
    def get_bbox(self, graphics=None, preserve_aspect=None):
        w, h = self.dimensions
        if preserve_aspect is None and self._dimensions is not None:
            preserve_aspect = self._dimensions[0] is None or self._dimensions[1] is None
        if preserve_aspect and graphics is not None:
            ((lx, rx), (by, ty)) = graphics.plot_range
            gw = (rx - lx)
            gh = (ty - by)
            ar = graphics.aspect_ratio
            ((slx, srx), (sby, sty)) = self.plot_range
            sar = (sty - sby) / (srx - slx)
            if isinstance(ar, str) and ar == 'auto':
                w1, h1 = graphics.image_size
                ar = h1 / w1
            art = (gh/gw) / ar # the ratio of plot_range aspect to true aspect
            if self._dimensions[1] is None:
                h = w * (sar * art)
            else:
                w = h / (sar * art)

        ox, oy = self.offset
        x, y = self.pos
        bbox = [
            [x - ox * w, y - oy * h],
            [x + (1 - ox) * w, y + (1 - oy) * h],
        ]
        return bbox

    def get_axes(self, graphics, bbox=None, **opts):
        if bbox is None:
            bbox = self.get_bbox()
        if graphics.figure in self._prim_cache:
            self._prim_cache[graphics.figure].close()
        self._prim_cache[graphics.figure] = graphics.create_inset(bbox, **opts)
        return self._prim_cache[graphics.figure]

    def plot(self, axes, *args, graphics=None, **kwargs):
        if isinstance(axes.figure, VTKWindow):
            raise NotImplemented
        else:
            if graphics is None:
                graphics = axes
            bbox = self.get_bbox(graphics=graphics)
            g = self.get_axes(graphics, bbox, **self.opts)
            prims = [p.change_figure(g) if hasattr(p, 'change_figure') else p.plot(g) for p in self.prims]
            return prims

    # def __del__(self):
    #     if self._prim is not None:
    #         self._prim.remove()