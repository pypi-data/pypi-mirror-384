"""
For now, just a super simple Enum of supported backends
Maybe in the future we'll add better support so that the backends themselves can all support a common subset
of features, but I think we'll 90% of the time just want to use MPL or VTK so who knows...
If that happens, lots of the 'if backend == MPL' stuff will change to use a Backend object
"""

__all__ = [
    "GraphicsBackend"
]

import enum, abc, contextlib, numpy as np
import uuid

from .. import Numputils as nput
from .. import Devutils as dev

from . import VTKInterface as vtk
from ..ExternalPrograms import VPythonInterface as vpython
from . import X3DInterface as x3d
from .SceneJSON import SceneJSON as sceneJSON

DPI_SCALING = 72

class AxisManager:
    def __init__(self,
                 tick_getter,
                 tick_setter,
                 tick_locator,
                 minor_tick_locator,
                 tick_formatter,
                 minor_tick_formatter
                 ):
        self.get_ticks = tick_getter
        self.set_ticks = tick_setter
        self.set_major_locator = tick_locator
        self.set_minor_locator = minor_tick_locator
        self.set_major_formatter = tick_formatter
        self.set_minor_formatter = minor_tick_formatter


class XAxisManager(AxisManager):
    def get_xticks(self):
        return self.get_ticks()
    def set_xticks(self, ticks, **kwargs):
        return self.set_ticks(ticks, **kwargs)

class YAxisManager(AxisManager):
    def get_yticks(self):
        return self.get_ticks()
    def set_yticks(self, ticks, **kwargs):
        return self.set_ticks(ticks, **kwargs)

class ZAxisManager(AxisManager):
    def get_zticks(self):
        return self.get_ticks()
    def set_zticks(self, ticks, **kwargs):
        return self.set_ticks(ticks, **kwargs)

class GraphicsAxes(metaclass=abc.ABCMeta):
    """
    A wrapper to provide a canonical form for matplotlib.axes.Axes
    so that other backends can plug in cleanly
    """
    def __init__(self):
        self.xaxis = XAxisManager(
            self.get_xticks,
            self.set_xticks,
            None,
            None,
            None,
            None
        )
        self.yaxis = YAxisManager(
            self.get_yticks,
            self.set_yticks,
            None,
            None,
            None,
            None
        )

    @classmethod
    def canonicalize_opts(cls, opts):
        return opts
    @abc.abstractmethod
    def remove(self, *, backend):
        ...
    @abc.abstractmethod
    def clear(self, *, backend):
        ...

    @abc.abstractmethod
    def get_plotter(self, method):
        ...

    @abc.abstractmethod
    def get_plot_label(self):
        ...
    @abc.abstractmethod
    def set_plot_label(self, val, **style):
        ...

    @abc.abstractmethod
    def get_style_list(self):
        ...
    @abc.abstractmethod
    def set_style_list(self, props):
        ...

    @abc.abstractmethod
    def get_frame_visible(self):
        ...
    @abc.abstractmethod
    def set_frame_visible(self, frame_spec):
        ...
    @abc.abstractmethod
    def get_frame_style(self):
        ...
    @abc.abstractmethod
    def set_frame_style(self, frame_spec):
        ...
    @abc.abstractmethod
    def get_xlabel(self):
        ...
    @abc.abstractmethod
    def set_xlabel(self, val, **style):
        ...
    @abc.abstractmethod
    def get_ylabel(self):
        ...
    @abc.abstractmethod
    def set_ylabel(self, val, **style):
        ...
    @abc.abstractmethod
    def get_xlim(self):
        ...
    @abc.abstractmethod
    def set_xlim(self, val, **opts):
        ...
    @abc.abstractmethod
    def get_ylim(self):
        ...
    @abc.abstractmethod
    def set_ylim(self, val, **opts):
        ...
    @abc.abstractmethod
    def get_xticks(self):
        ...
    @abc.abstractmethod
    def set_xticks(self, val, **opts):
        ...
    @abc.abstractmethod
    def get_yticks(self):
        ...
    @abc.abstractmethod
    def set_yticks(self, val, **opts):
        ...
    @abc.abstractmethod
    def get_xtick_style(self):
        ...
    @abc.abstractmethod
    def set_xtick_style(self, **opts):
        ...
    @abc.abstractmethod
    def get_ytick_style(self):
        ...
    @abc.abstractmethod
    def set_ytick_style(self, **opts):
        ...
    @abc.abstractmethod
    def set_aspect_ratio(self, ar):
        ...
    @abc.abstractmethod
    def get_bbox(self):
        ...
    @abc.abstractmethod
    def set_bbox(self, bbox):
        ...
    @abc.abstractmethod
    def get_facecolor(self):
        ...
    @abc.abstractmethod
    def set_facecolor(self, fg):
        ...
    @abc.abstractmethod
    def get_padding(self):
        ...

    def legend(self, **opts):
        raise NotImplementedError("legend")

    def get_graphics_properties(self, obj, property=None):
        raise NotImplementedError("get_graphics_properties")
    def set_graphics_properties(self, obj, **props):
        raise NotImplementedError("set_graphics_properties")

    @abc.abstractmethod
    def draw_line(self, points, **styles):
        ...
    def draw_point(self, points, **styles):
        return self.draw_disk(points, **styles)
    @abc.abstractmethod
    def draw_disk(self, points, **styles):
        ...
    @abc.abstractmethod
    def draw_rect(self, points, **styles):
        ...
    def draw_triangle(self, points, **styles):
        return self.draw_poly(points, **styles)
    @abc.abstractmethod
    def draw_poly(self, points, **styles):
        ...
    @abc.abstractmethod
    def draw_arrow(self, points, **styles):
        ...
    @abc.abstractmethod
    def draw_text(self, points, vals, **styles):
        ...

class GraphicsAxes3D(GraphicsAxes):
    def __init__(self):
        super().__init__()
        self.zaxis = ZAxisManager(
            self.get_zticks,
            self.set_zticks,
            None,
            None,
            None,
            None
        )

    @abc.abstractmethod
    def get_zlim(self):
        ...
    @abc.abstractmethod
    def set_zlim(self, val, **opts):
        ...
    @abc.abstractmethod
    def get_zticks(self):
        ...
    @abc.abstractmethod
    def set_zticks(self, val, **opts):
        ...
    @abc.abstractmethod
    def get_ztick_style(self):
        ...
    @abc.abstractmethod
    def set_ztick_style(self, **opts):
        ...

    @abc.abstractmethod
    def get_view_settings(self):
        ...
    @abc.abstractmethod
    def set_view_settings(self, **ops):
        ...

    @abc.abstractmethod
    def draw_sphere(self, points, rads, **styles):
        ...

    @abc.abstractmethod
    def draw_cylinder(self, start, end, rad, circle_points=48, **opts):
        ...

class GraphicsFigure(metaclass=abc.ABCMeta):
    """
    A wrapper to provide a canonical form for matplotlib.figure.Figure
    so that other backends can plug in cleanly
    """
    Axes = None
    def __init__(self, axes=None):
        self.axes = axes
    @classmethod
    def construct(self, **kw) -> 'GraphicsFigure':
        raise NotImplementedError("needs an overload")
    @classmethod
    def canonicalize_opts(cls, opts):
        return opts
    @abc.abstractmethod
    def create_axes(self, rows, cols, spans, **kw) -> 'GraphicsAxes':
        ...
    @abc.abstractmethod
    def create_inset(self, bbox, **kw) -> 'GraphicsAxes':
        ...
    def create_colorbar(self, graphics, axes, norm=None, cmap=None, **kw):
        raise NotImplementedError("create_colorbar")
    def add_axes(self, ax) -> 'GraphicsAxes':
        if self.axes is None: self.axes = []
        if not isinstance(ax, self.Axes): ax = self.Axes(ax)
        self.axes.append(ax)
        return ax
    @abc.abstractmethod
    def clear(self, *, backend):
        ...
    @abc.abstractmethod
    def close(self, *, backend):
        ...

    def get_bboxes(self):
        return [
            a.get_bbox() for a in self.axes
        ]

    @abc.abstractmethod
    def get_size_inches(self):
        ...
    @abc.abstractmethod
    def set_size_inches(self, w, h):
        ...
    @abc.abstractmethod
    def set_extents(self, extents):
        ...

    @abc.abstractmethod
    def get_facecolor(self):
        ...
    @abc.abstractmethod
    def set_facecolor(self, fg):
        ...

    @abc.abstractmethod
    def savefig(self, file, **opts):
        ...

    @abc.abstractmethod
    def animate_frames(self, frames, **animation_opts):
        ...

    def to_html(self):
        ...
    def _repr_html_(self):
        return self.to_html()
    def tight_layout(self):
        ...


class GraphicsBackend(metaclass=abc.ABCMeta):
    Figure = GraphicsFigure
    @abc.abstractmethod
    def create_figure(self, *args, **kwargs) -> 'tuple[GraphicsFigure, tuple[GraphicsAxes]]':
        ...
    def create_axes(self, figure:'GraphicsFigure', *args, **kwargs):
        return figure.create_axes(*args, **kwargs, backend=self)
    def create_inset(self, figure, *args, **kw) -> 'GraphicsAxes':
        return figure.create_inset(*args, **kw)
    def close_figure(self, figure:'GraphicsFigure'):
        return figure.close(backend=self)
    def remove_axes(self, axes:'GraphicsAxes'):
        return axes.remove(backend=self)
    def clear_figure(self, figure:'GraphicsFigure'):
        return figure.clear(backend=self)
    def clear_axes(self, axes:'GraphicsAxes'):
        return axes.clear(backend=self)
    @abc.abstractmethod
    def get_interactive_status(self) -> 'bool':
        ...
    @abc.abstractmethod
    def disable_interactivity(self):
        ...
    @abc.abstractmethod
    def enable_interactivity(self):
        ...
    @abc.abstractmethod
    def show_figure(self, figure, reshow=None):
        ...

    @abc.abstractmethod
    def get_available_themes(self):
        ...
    class ThemeContextManager(metaclass=abc.ABCMeta):
        def __init__(self, theme_parents, theme_spec):
            self.spec = self.canonicalize_theme_opts(theme_parents, theme_spec)

        @classmethod
        @abc.abstractmethod
        def canonicalize_theme_opts(self, theme_parents, theme_spec):
            ...
        @abc.abstractmethod
        def __enter__(self):
            ...
        @abc.abstractmethod
        def __exit__(self, exc_type, exc_val, exc_tb):
            ...
    def theme_context(self, theme_parents, spec):
        return self.ThemeContextManager(theme_parents, spec)

    class DefaultBackends(enum.Enum):
        MPL = 'matplotlib'
        MPL3D = 'matplotlib3D'
        VTK = 'vtk'
        VPython = 'vpython'
        VPython2D = 'vpython2D'
        X3D = 'x3d'
        SceneJSON = 'json'

    registered_backends = {}
    @classmethod
    def get_default_backends(cls):
        return {
            cls.DefaultBackends.MPL.value: MPLBackend,
            cls.DefaultBackends.MPL3D.value: MPLBackend,
            cls.DefaultBackends.VTK.value: VTKBackend,
            cls.DefaultBackends.VPython2D.value: VPythonBackend,
            cls.DefaultBackends.VPython.value: VPythonBackend3D,
            cls.DefaultBackends.X3D.value: X3DBackend,
            cls.DefaultBackends.SceneJSON.value: SceneJSONBackend,
        }
    @classmethod
    def lookup(cls, backend, opts=None) -> 'GraphicsBackend':
        if opts is None: opts = {}
        if not isinstance(backend, GraphicsBackend):
            name = backend
            backend = cls.registered_backends.get(name, None)
            if backend is None:
                backend_key = cls.DefaultBackends(name).value
                backend = cls.get_default_backends().get(backend_key)
        return backend(**opts)

class MPLManager:
    _plt = None
    _patch = None
    _coll = None
    _mpl = None
    _colors = None
    _jlab = None
    _widg = None
    _anim = None

    @classmethod
    def plt_api(cls):
        if cls._plt is None:
            import matplotlib.pyplot as plt
            cls._plt = plt
        return cls._plt
    @classmethod
    def mpl_api(cls):
        if cls._mpl is None:
            import matplotlib as mpl
            cls._mpl = mpl
        return cls._mpl
    @classmethod
    def color_api(cls):
        if cls._colors is None:
            import matplotlib.colors as colors
            cls._colors = colors
        return cls._colors

    @classmethod
    def patch_api(cls):
        if cls._patch is None:
            import matplotlib.patches as patch
            cls._patch = patch
        return cls._patch
    @classmethod
    def collections_api(cls):
        if cls._coll is None:
            import matplotlib.collections as coll
            cls._coll = coll
        return cls._coll
    @classmethod
    def widgets_api(cls):
        if cls._widg is None:
            import matplotlib.widgets as widg
            cls._widg = widg
        return cls._widg
    @classmethod
    def animations_api(cls):
        if cls._anim is None:
            import matplotlib.animation as anim
            cls._anim = anim
        return cls._anim
    @classmethod
    def draw_if_interactive(self, *args, **kwargs):
        pass
    @classmethod
    def magic_backend(self, backend):
        try:
            from IPython.core.getipython import get_ipython
        except ImportError:
            pass
        else:
            shell = get_ipython()
            ip_name = type(shell).__name__
            in_nb = ip_name == 'ZMQInteractiveShell'
            if in_nb:
                try:
                    from IPython.core.magics import PylabMagics
                except ImportError:
                    pass
                else:
                    set_jupyter_backend = PylabMagics(shell).matplotlib
                    set_jupyter_backend(backend)

    # This flag will be reset by draw_if_interactive when called
    _draw_called = False
    # list of figures to draw when flush_figures is called
    _to_draw = []
    settings_stack = []
    @contextlib.contextmanager
    @classmethod
    def figure_settings(cls, figure):
        old_backend = None
        was_interactive = None
        drawer = None
        draw_all = None
        old_magic_backend = None
        old_show = None

        mpl = cls.mpl_api()
        plt = cls.plt_api()

        if figure.mpl_backend is not None:
            old_backend = mpl.get_backend()
        was_interactive = plt.isinteractive()

        cls.settings_stack.append((
            old_backend,
            was_interactive,
            drawer,
            draw_all,
            old_magic_backend,
            old_show
        ))
        try:
            if not figure.managed:
                # import matplotlib.pyplot as plt
                # plt.ioff
                # if 'inline' in self.mpl.get_backend():
                #     backend = self.plt._backend_mod
                #     self.plt.show = ...
                #     self._old_show = backend.show
                #     backend.show = self.jupyter_show
                if not figure.interactive:
                    plt.ioff()
                    # manager.canvas.mpl_disconnect(manager._cidgcf)
                    # self._drawer = self.plt.draw_if_interactive
                    # self._draw_all = self.plt.draw_all
                    # self.plt.draw_if_interactive = self.draw_if_interactive
                    # self.plt.draw_all = self.draw_if_interactive
                    # if self.fig.mpl_backend is None:
                    #     self._old_magic_backend = self.mpl.get_backend()
                    #     self.magic_backend('Agg')
                else:
                    plt.ion()
                    # if self.fig.mpl_backend is None:
                    #     self._old_magic_backend = self.mpl.get_backend()
                    #     if 'inline' not in self._old_magic_backend:
                    #         self.magic_backend('inline')

            yield None
        finally:
            (
                old_backend,
                was_interactive,
                drawer,
                draw_all,
                old_magic_backend,
                old_show
            ) = cls.settings_stack.pop()

            if old_backend is not None:
                mpl.use(old_backend)
            if drawer is not None:
                plt.draw_if_interactive = drawer
            if draw_all is not None:
                plt.draw_all = draw_all
            if old_show is not None:
                plt._backend_mod.show = old_show

            if old_magic_backend is not None:
                if 'inline' in old_magic_backend:
                    cls.magic_backend('inline')
                else:
                    mpl.use(old_magic_backend)
            if was_interactive and not plt.isinteractive():
                plt.ion()

    @classmethod
    def mpl_disconnect(cls, graphics):
        # this is a hack that might need to be updated in the future
        if 'inline' in cls.mpl_api().get_backend():
            try:
                from matplotlib._pylab_helpers import Gcf
                canvas = graphics.figure.canvas
                num = canvas.manager.num
                if all(hasattr(num, attr) for attr in ["num", "_cidgcf", "destroy"]):
                    manager = num
                    if Gcf.figs.get(manager.num) is manager:
                        Gcf.figs.pop(manager.num)
                    else:
                        return
                else:
                    try:
                        manager = Gcf.figs.pop(num)
                    except KeyError:
                        return
                # manager.canvas.mpl_disconnect(manager._cidgcf)
                # self.fig.figure.canvas.mpl_disconnect(
                #     self.fig.figure.canvas.manager._cidgcf
                # )
            except:
                pass

    @classmethod
    def mpl_connect(cls, graphics):
        if 'inline' in cls.mpl_api().get_backend():
            # try:
            from matplotlib._pylab_helpers import Gcf
            canvas = graphics.figure.canvas
            manager = canvas.manager
            num = canvas.manager.num
            Gcf.figs[num] = manager
            manager._cidgcf = canvas.mpl_connect(
                "button_press_event", lambda event: Gcf.set_active(manager)
            )
            # manager.canvas.mpl_disconnect(manager._cidgcf)
            # self.fig.figure.canvas.mpl_disconnect(
            #     self.fig.figure.canvas.manager._cidgcf
            # )
            # except:
            #     pass

    @classmethod
    def jupyter_show(cls, close=None, block=None):
        """Show all figures as SVG/PNG payloads sent to the IPython clients.
        Parameters
        ----------
        close : bool, optional
            If true, a ``plt.close('all')`` call is automatically issued after
            sending all the figures. If this is set, the figures will entirely
            removed from the internal list of figures.
        block : Not used.
            The `block` parameter is a Matplotlib experimental parameter.
            We accept it in the function signature for compatibility with other
            backends.
        """

        from matplotlib._pylab_helpers import Gcf
        from IPython.core.display import display
        plt = cls.plt_api()
        mpl_inline = plt._backend_mod

        if close is None:
            close = mpl_inline.InlineBackend.instance().close_figures
        try:
            for figure_manager in [Gcf.get_active()]:
                display(
                    figure_manager.canvas.figure,
                    metadata=mpl_inline._fetch_figure_metadata(figure_manager.canvas.figure)
                )
        finally:
            cls._to_draw = []
            # only call close('all') if any to close
            # close triggers gc.collect, which can be slow
            if close and Gcf.get_all_fig_managers():
                plt.close('all')

class MPLAxes(GraphicsAxes):
    def __init__(self, mpl_axes_object, **opts):
        self.obj = mpl_axes_object
        self.opts = self.canonicalize_opts(opts)
        super().__init__()
        self.xaxis = self.obj.xaxis
        self.yaxis = self.obj.yaxis
    def clear(self, *, backend=None):
        ax = self.obj
        all_things = ax.artists + ax.patches
        for a in all_things:
            a.remove()
    def remove(self, *, backend):
        self.obj.remove()

    def get_plotter(self, method):
        plot_method = getattr(self.obj, method)
        def plot(*data, **styles):
            return plot_method(*data, **styles)
        return plot


    def get_plot_label(self):
        return self.obj.set_title()
    def set_plot_label(self, val, **style):
        self.obj.set_title(val, **style)

    def get_style_list(self):
        raise NotImplementedError("style list cyclers not supported")
    def set_style_list(self, props):
        self.obj.set_prop_cycle(**props)

    def get_frame_visible(self):
        return (
            (
                self.obj.spines['left'].get_visible(),
                self.obj.spines['right'].get_visible()
            ),
            (
                self.obj.spines['bottom'].get_visible(),
                self.obj.spines['top'].get_visible()
            ),
        )
    def set_frame_visible(self, frame_spec):
        if frame_spec is True or frame_spec is False:
            self.obj.set_frame_on(frame_spec)
        else:
            lr, bt = frame_spec
            if lr is None:
                l = r = None
            elif lr is True or lr is False:
                l = r = lr
            else:
                l,r = lr
            if bt is True or bt is False:
                b = t = bt
            else:
                b,t = bt
            for k,v in [
                ['left', l],
                ['right', r],
                ['bottom', b],
                ['top', t]
            ]:
                if v is not None: self.obj.spines[k].set_visible(v)

    def get_frame_style(self):
        return (
            (
                self.obj.spines['left'].get(),
                self.obj.spines['right'].get()
            ),
            (
                self.obj.spines['bottom'].get(),
                self.obj.spines['top'].get()
            ),
        )
    def set_frame_style(self, frame_spec):
        if isinstance(frame_spec, dict):
            l, r, b, t = frame_spec
        else:
            lr, bt = frame_spec
            if lr is None:
                l = r = None
            elif lr is True or lr is False:
                l = r = lr
            else:
                l,r = lr
            if bt is True or bt is False:
                b = t = bt
            else:
                b,t = bt
        for k,v in [
            ['left', l],
            ['right', r],
            ['bottom', b],
            ['top', t]
        ]:
            if v is not None: self.obj.spines[k].set(**v)

    def get_xlabel(self):
        return self.obj.get_xlabel()
    def set_xlabel(self, val, **style):
        self.obj.set_xlabel(val, **style)
    def get_ylabel(self):
        return self.obj.get_ylabel()
    def set_ylabel(self, val, **style):
        self.obj.set_ylabel(val, **style)

    def get_xlim(self):
        return self.obj.get_xlim()
    def set_xlim(self, val, **opts):
        self.obj.set_xlim(val, **opts)
    def get_ylim(self):
        return self.obj.get_ylim()
    def set_ylim(self, val, **opts):
        self.obj.set_ylim(val, **opts)

    def get_xticks(self):
        return self.obj.get_xticks()
    def set_xticks(self, val, **opts):
        self.obj.set_xticks(val, **opts)

    def get_yticks(self):
        return self.obj.get_yticks()
    def set_yticks(self, val, **opts):
        self.obj.set_yticks(val, **opts)

    def get_xtick_style(self):
        return self.obj.tick_params(axis='x')
    def set_xtick_style(self, **opts):
        return self.obj.tick_params(axis='x', **opts)
    def get_ytick_style(self):
        return self.obj.tick_params(axis='y')
    def set_ytick_style(self, **opts):
        return self.obj.tick_params(axis='y', **opts)

    def set_aspect_ratio(self, ar):
        self.obj.set_aspect(ar)

    def get_bbox(self):
        bbox = self.obj.get_position()
        if hasattr(bbox, 'get_points'):
            bbox = bbox.get_points()
        bbox = [
            [b*DPI_SCALING for b in bb]
            for bb in bbox
        ]

        return bbox
    def set_bbox(self, bbox):
        if hasattr(bbox, 'get_points'):
            bbox = bbox.get_points()
        else:
            bbox = [
                [b / DPI_SCALING for b in bb]
                for bb in bbox
            ]
        ((lx, by), (rx, ty)) = bbox
        self.obj.set_position([lx, by, rx-lx, ty-by])

    def get_facecolor(self):
        return self.obj.get_facecolor()
    def set_facecolor(self, fg):
        return self.obj.set_facecolor(fg)

    def get_padding(self):
        padding = [
            ['left', 'right'],
            ['bottom', 'top']
        ]
        xlab_padding = None
        ylab_padding = None
        for i, l in enumerate(padding):
            for j, key in enumerate(l):
                spine = self.obj.spines[key]
                viz = spine.get_visible()
                if viz:
                    ((l, b), (r, t)) = bbox = spine.get_window_extent().get_points()
                    if i == 0:
                        base_pad = r - l
                        if xlab_padding is None:
                            xlabs = self.obj.get_xticklabels()
                            if len(xlabs) > 0:
                                min_x = 1e10
                                max_x = -1e10
                                for lab in xlabs:
                                    ((l, b), (r, t)) = lab.get_window_extent().get_points()
                                    min_x = min(l, min_x)
                                    max_x = max(r, max_x)
                                xlab_padding = max_x - min_x
                            else:
                                xlab_padding = 0
                        padding[i][j] = base_pad + xlab_padding
                    else:
                        base_pad = t - b
                        if ylab_padding is None:
                            ylabs = self.obj.get_yticklabels()
                            if len(ylabs) > 0:
                                min_y = 1e10
                                max_y = -1e10
                                for lab in ylabs:
                                    ((l, b), (r, t)) = lab.get_window_extent().get_points()
                                    min_y = min(b, min_y)
                                    max_y = max(t, max_y)
                                ylab_padding = max_y - min_y
                            else:
                                ylab_padding = 0
                        padding[i][j] = base_pad + ylab_padding
                else:
                    padding[i][j] = 0
        return padding

    def legend(self, **opts):
        return self.get_plotter('legend')(**opts)

    def get_graphics_properties(self, obj, property=None):
        from matplotlib.artist import getp

        return getp(obj, property=property)
    def set_graphics_properties(self, obj, **props):
        from matplotlib.artist import setp

        return setp(obj, **props)

    def draw_line(self, points, **styles):
        points = np.asanyarray(points)
        if points.ndim == 2:
            points = points[np.newaxis]
        return self.get_plotter('plot')(
            points[:, 0],
            points[:, 1],
            **styles
        )

    def draw_disk(self, points, **styles):
        points = np.asanyarray(points)
        if points.ndim == 1:
            points = points[np.newaxis]
        return self.get_plotter('scatter')(
            points[:, 0],
            points[:, 1],
            **styles
        )

    def draw_rect(self, points, **styles):
        patches = MPLManager.patch_api()
        coll = MPLManager.collections_api()
        points = np.asanyarray(points)
        if points.ndim == 2:
            points = points[np.newaxis]

        anchors = points[:, 0]
        widths = points[:, 1, 0] - points[:, 0, 0]
        heights = points[:, 1, 1] - points[:, 0, 1]

        rects = coll.PatchCollection([
            patches.Rectangle(a, w, h, **styles)
            for a,w,h in zip(anchors, widths, heights)
        ])

        self.obj.add_patch(rects)

    def draw_poly(self, points, **styles):
        patches = MPLManager.patch_api()
        coll = MPLManager.collections_api()
        points = np.asanyarray(points)
        if points.ndim == 2:
            points = points[np.newaxis]

        polys = coll.PatchCollection([
            patches.Polygon(pt, **styles) for pt in points
        ])

        self.obj.add_patch(polys)

    def draw_arrow(self, points, **styles):
        points = np.asanyarray(points)
        if points.ndim == 2:
            points = points[np.newaxis]
        return self.get_plotter('arrow')(
            *points[0],
            *(points[1] - points[0]),
            **styles
        )

    def draw_text(self, points, vals, **styles):
        points = np.asanyarray(points)
        if points.ndim == 1:
            points = points[np.newaxis]
        if isinstance(vals, str):
            vals = [vals]

        text_plotter = self.get_plotter('text')
        text = [
             text_plotter(*pt, txt, **styles)
             for pt, txt in zip(points, vals)
        ]

        return text

class MPLAxes3D(MPLAxes):
    def __init__(self, mpl_axes_object, **opts):
        super().__init__(mpl_axes_object, **opts)
        self.zaxis = self.obj.zaxis

    def get_view_settings(self):
        return {'elev': self.obj.elev, 'azim':self.obj.azim,
                'roll':self.obj.roll, 'vertical_axis':self.obj.vertical_axis}
    def set_view_settings(self, **values):
        # if isinstance(value, dict):
        #     if 'elev' not in value:
        #         value['elev'] = self.obj.elev
        #     if 'azim' not in value:
        #         value['azim'] = self.obj.azim
        #     if 'roll' not in value:
        #         value['roll'] = self.obj.arollzim
        #     if 'vertical_axis' not in value:
        #         value['vertical_axis'] = self.obj.vertical_axis
        # else:
        #     value = dict(zip(['elev', 'azim', 'roll', 'vertical_axis'], value))
        self.obj.view_init(**values)

    def draw_sphere(self, center, radius, sphere_points=48, **opts):
        surface = self.get_plotter('plot_surface')

        u = np.linspace(0, 2 * np.pi, sphere_points)
        v = np.linspace(0, np.pi, sphere_points)
        x = radius * np.outer(np.cos(u), np.sin(v))
        y = radius * np.outer(np.sin(u), np.sin(v))
        z = radius * np.outer(np.ones(np.size(u)), np.cos(v))

        return surface(x + center[0], y + center[1], z + center[2], **opts)

    def draw_cylinder(self, start, end, rad, circle_points=48, **opts):
        surface = self.get_plotter('plot_surface')

        u = np.linspace(0, 2 * np.pi, circle_points)
        v = np.linspace(0, np.pi, circle_points)

        # pulled from SO: https://stackoverflow.com/a/32383775/5720002

        # vector in direction of axis
        v = end - start
        # find magnitude of vector
        mag = np.linalg.norm(v)
        # unit vector in direction of axis
        v = v / mag
        # make some vector not in the same direction as v
        not_v = np.array([1, 0, 0])
        if (v == not_v).all():
            not_v = np.array([0, 1, 0])
        # make vector perpendicular to v
        n1 = np.cross(v, not_v)
        # normalize n1
        n1 /= np.linalg.norm(n1)
        # make unit vector perpendicular to v and n1
        n2 = np.cross(v, n1)
        # surface ranges over t from 0 to length of axis and 0 to 2*pi
        t = np.linspace(0, mag, circle_points)
        theta = np.linspace(0, 2 * np.pi, circle_points)
        # use meshgrid to make 2d arrays
        t, theta = np.meshgrid(t, theta)
        # generate coordinates for surface
        X, Y, Z = [start[i] + v[i] * t + rad * np.sin(theta) * n1[i] + rad * np.cos(theta) * n2[i] for i
                   in [0, 1, 2]]

        return surface(X, Y, Z, **opts)

class MPLFigure(GraphicsFigure):
    Axes = MPLAxes

    _refs = set()
    def __init__(self, mpl_figure_object, **opts):
        if mpl_figure_object in self._refs: raise ValueError(...)
        self._refs.add(mpl_figure_object)
        self.obj = mpl_figure_object
        super().__init__(**self.canonicalize_opts(opts))
    def __hash__(self): # we need weakref to behave right
        return hash(self.obj)
    def create_axes(self, rows, cols, spans, **kw):
        return self.add_axes(
            self.obj.add_subplot((rows, cols, spans), **kw)
        )
    def create_inset(self, bbox, **kw) -> 'GraphicsAxes':
        ((x, y), (X, Y)) = bbox
        return self.add_axes(
            self.obj.add_axes([x, y, X-x, Y-y], **kw)
        )
    def clear(self, *, backend):
        raise NotImplementedError(...)
    def close(self, *, backend):
        return backend.plt.close(self.obj)

    _cb_opts = ("orientation", "extendfrac", "extendrect", "drawedges", "boundaries", "spacing")
    def create_colorbar(self, graphics, axes, norm=None, cmap=None, **kw):
        if graphics is None:
            import matplotlib.cm as cm
            graphics = cm.ScalarMappable(norm=norm, cmap=cmap)
        cb_opts, fig_opts = dev.OptionsSet(kw).split(None, self._cb_opts)
        self.obj.colorbar(graphics, cax=axes.obj, **cb_opts)
        if len(fig_opts) > 0:
            from .Graphics import Graphics
            Graphics(
                # parent=self,
                figure=self,
                axes=axes
            ).set_options(**fig_opts)
        return axes
    def get_figure_label(self):
        return self.obj.suptitle()
    def set_figure_label(self, val, **style):
        self.obj.suptitle(val, **style)

    def get_size_inches(self):
        return self.obj.get_size_inches()
    def set_size_inches(self, w, h):
        self.obj.set_size_inches(w, h)

    def set_extents(self, extents):
        if isinstance(extents, (list, tuple)):
            lr, bt = extents
            if isinstance(lr, (list, tuple)):
                l,r = lr
            else:
                l = r = lr
            if isinstance(bt, (list, tuple)):
                b,t = bt
            else:
                b = t = bt
        else:
            l = r = b = t = extents
        self.obj.subplots_adjust(
            left=l,
            right=r,
            bottom=b,
            top=t
        )  # , hspace=0, wspace=0)

    def set_figure_spacings(self, spacing):
        if isinstance(spacing, (list, tuple)):
            w,h = spacing
        else:
            w = h = spacing
        self.obj.subplots_adjust(wspace=w, hspace=h)

    def get_facecolor(self):
        return self.obj.get_facecolor()
    def set_facecolor(self, fg):
        return self.obj.set_facecolor(fg)

    def savefig(self, file, **opts):
        return self.obj.savefig(file, **opts)

    def animate_frames(self, frames, export_html=True, **animation_opts):
        fig = self.obj
        frames = [
            [f] if hasattr(f, 'axes') else f
            for f in frames
        ]
        frames = [
            [
                f.graphics if hasattr(f, 'graphics') else f
                for f in frame_list
            ]
            for frame_list in frames
        ]
        animation = MPLManager.animations_api().ArtistAnimation(
            fig,
            frames,
            **animation_opts
        )
        if export_html:
            from ..Jupyter import JHTML
            display = JHTML.APIs.get_display_api()
            animation = display.HTML(animation.to_jshtml())
        return animation
    def to_html(self):
        return self.obj._repr_html_()
    def tight_layout(self):
        self.obj.tight_layout()

class MPLBackend(GraphicsBackend):
    Figure = MPLFigure
    @property
    def plt(self):
        return MPLManager.plt_api()
    @property
    def mpl(self):
        return MPLManager.mpl_api()
    def create_figure(self, *args, **kwargs):
        Axes = self.Figure.Axes
        figure, axes = MPLManager.plt_api().subplots(*args, **kwargs)
        if isinstance(axes, (np.ndarray, list, tuple)):
            if isinstance(axes[0], (np.ndarray, list, tuple)):
                axes = tuple(tuple(Axes(b) for b in a) for a in axes)
            else:
                axes = tuple(Axes(a) for a in axes)
        else:
            axes = Axes(axes)
        return self.Figure(figure), axes
    def show_all(self):
        self.plt.show()

    class ThemeContextManager(GraphicsBackend.ThemeContextManager):
        def __init__(self, theme_parents, theme_spec):
            super().__init__(theme_parents, theme_spec)
            self.context = MPLManager.plt_api().style.context(self.spec)

        @classmethod
        def canonicalize_theme_opts(self, theme_parents, theme_opts) -> 'tuple[list[str], dict]':
            from matplotlib import cycler

            theme_dict = {}
            for k,v in theme_opts.items():
                if isinstance(v, dict):
                    for sk,sv in v.items():
                        if isinstance(sv, dict):
                            sv = cycler(**sv)
                        theme_dict[k+'.'+sk] = sv
                # else:
                #     theme_dict[k] = v
            return theme_parents + [theme_dict]

        def __enter__(self):
            return self.context.__enter__()
        def __exit__(self, exc_type, exc_val, exc_tb):
            return self.context.__exit__(exc_type, exc_val, exc_tb)

    def show_figure(self, graphics, reshow=None):
        self.plt.show()
        # return graphics.show_mpl(self, reshow=reshow)

    def get_interactive_status(self) -> 'bool':
        return self.plt.isinteractive()
    def disable_interactivity(self):
        return self.plt.ioff()
    def enable_interactivity(self):
        return self.plt.ion()
    def get_available_themes(self):
        import matplotlib.style as sty
        theme_names = sty.available
        return theme_names

class MPLFigure3D(MPLFigure):
    Axes = MPLAxes3D
    def create_axes(self, rows, cols, spans, projection='3d', **kw):
        return super().create_axes(rows, cols, spans, projection=projection, **kw)
class MPLBackend3D(MPLBackend):
    Figure = MPLFigure3D
    def create_figure(self, *args, subplot_kw=None, **kwargs):
        from mpl_toolkits.mplot3d import Axes3D
        subplot_kw = dict({"projection": '3d'}, **({} if subplot_kw is None else subplot_kw))
        return super().create_axes(*args, subplot_kw=subplot_kw, **kwargs)

class GraphicsRegionAxes(GraphicsAxes):
    def __init__(self, figure_region):
        self.region = figure_region

    @staticmethod
    def renormalize(pos, og_reg, final_reg=None):
        o_min, o_max = og_reg
        pos = (pos - o_min) / (o_max - o_min)
        if final_reg is not None:
            F_min, F_max = final_reg
            pos = pos * (F_max - F_min) + F_min
        return pos

    def normalize_positions(self, pos):
        ndim = pos.shape[-1]

        x = self.renormalize(pos[..., 0], self.get_xlim(), self.region[0])
        y = self.renormalize(pos[..., 1], self.get_ylim(), self.region[1])
        if ndim == 2:
            z = self.renormalize(pos[..., 2], self.get_zlim(), self.region[2])
            crds = [x, y, z]
        else:
            crds = [x, y]
        return np.moveaxis(np.array(crds), 0, -1)

class VTKAxes(GraphicsRegionAxes):

    def __init__(self, figure_region, figure: vtk.VTKWindow):
        self.obj = figure
        self.objs = []
        self._plot_label = None
        super().__init__(figure_region)

    @classmethod
    def canonicalize_opts(cls, opts):
        return opts

    def remove(self, *, backend):
        self.obj.close()

    def clear(self, *, backend):
        for o in self.objs:
            self.obj.remove_object(o)

    def get_plotter(self, method):
        raise NotImplementedError(f"plotter for {method} not implemented")

    def get_plot_label(self):
        return self.obj.get_title()
        # return self._plot_label

    def set_plot_label(self, val, **style):
        return self.obj.set_title(val)
        # x_min, x_max = self.region[0]
        # y_min, y_max = self.region[1]
        # pos = self.renormalize(np.array([(x_max+x_min)/2, (y_max+y_min)/2, 0]))
        # self.obj.draw_text(val, )

    def get_style_list(self):
        raise NotImplementedError("style list cyclers not supported")
    def set_style_list(self, props):
        raise NotImplementedError("style list cyclers not supported")

    def get_frame_visible(self):
        raise NotImplementedError("get_frame_visible")

    def set_frame_visible(self, frame_spec):
        raise NotImplementedError("set_frame_visible")

    def get_frame_style(self):
        raise NotImplementedError("get_frame_style")

    def set_frame_style(self, frame_spec):
        raise NotImplementedError("set_frame_style")

    def get_xlabel(self):
        raise NotImplementedError("get_xlabel")

    def set_xlabel(self, val, **style):
        raise NotImplementedError("set_xlabel")

    def get_ylabel(self):
        raise NotImplementedError("get_xlabel")

    def set_ylabel(self, val, **style):
        raise NotImplementedError("set_ylabel")

    def get_xlim(self):
        return self.obj.get_xlim()
    def set_xlim(self, val, **opts):
        return self.obj.set_xlim(val)

    def get_ylim(self):
        return self.obj.get_ylim()
    def set_ylim(self, val, **opts):
        return self.obj.set_ylim(val)

    def get_zlim(self):
        return self.obj.get_zlim()
    def set_zlim(self, val, **opts):
        return self.obj.set_zlim(val)

    def get_xticks(self):
        raise NotImplementedError("get_xticks")
    def set_xticks(self, val, **opts):
        raise NotImplementedError("set_xticks")

    def get_yticks(self):
        raise NotImplementedError("get_yticks")
    def set_yticks(self, val, **opts):
        raise NotImplementedError("set_yticks")

    def get_xtick_style(self):
        raise NotImplementedError("get_xtick_style")
    def set_xtick_style(self, **opts):
        raise NotImplementedError("set_xtick_style")

    def get_ytick_style(self):
        raise NotImplementedError("get_ytick_style")
    def set_ytick_style(self, **opts):
        raise NotImplementedError("set_ytick_style")

    def set_aspect_ratio(self, ar):
        raise NotImplementedError("set_aspect_ratio")

    def get_bbox(self):
        raise NotImplementedError("get_bbox")
        return [self.obj.get_xlim(), self.obj.get_ylim(), self.obj.get_zlim()]
    def set_bbox(self, bbox):
        raise NotImplementedError("set_bbox")

    def get_facecolor(self):
        return self.obj.get_facecolor()
    def set_facecolor(self, fg):
        return self.obj.set_facecolor(fg)

    def get_padding(self):
        raise NotImplementedError("get_padding")

    @abc.abstractmethod
    def draw_line(self, points, **styles):
        ...

    @abc.abstractmethod
    def draw_disk(self, points, **styles):
        ...

    @abc.abstractmethod
    def draw_rect(self, points, **styles):
        ...

    @abc.abstractmethod
    def draw_poly(self, points, **styles):
        ...

    @abc.abstractmethod
    def draw_arrow(self, points, **styles):
        ...

    @abc.abstractmethod
    def draw_text(self, points, vals, **styles):
        ...

    @abc.abstractmethod
    def draw_sphere(self, points, rads, **styles):
        ...

    @abc.abstractmethod
    def animate_frames(self, frames, **animation_opts):
        ...

class VTKFigure(GraphicsFigure):
    Axes = VTKAxes

    def __init__(self, vtk_window: vtk.VTKWindow, **opts):
        self.obj = vtk_window
        super().__init__(**self.canonicalize_opts(opts))

    def create_axes(self, rows, cols, spans, **kw) -> 'GraphicsAxes':
        return self.add_axes(
            self.obj.add_subplot((rows, cols, spans), **kw)
        )

    @abc.abstractmethod
    def create_inset(self, bbox, **kw) -> 'GraphicsAxes':
        raise NotImplementedError(...)

    @abc.abstractmethod
    def clear(self, *, backend):
        self.obj.clear()
        # for obj in ...:


    @abc.abstractmethod
    def close(self, *, backend):
        ...

    def get_bboxes(self):
        return [
            a.get_bbox() for a in self.axes
        ]

    @abc.abstractmethod
    def get_size_inches(self):
        ...

    @abc.abstractmethod
    def set_size_inches(self, w, h):
        ...

    @abc.abstractmethod
    def savefig(self, file, **opts):
        ...

class VTKBackend(GraphicsBackend):
    ...

class VPythonWrapper:
    _vec = None
    @classmethod
    def vpythonify(cls, arg):
        if cls._vec is None:
            cls._vec = vpython.method('vector')
        if isinstance(arg, (list, tuple, np.ndarray)):
            arg = cls._vec(*arg)
        return arg
    @classmethod
    def vpython_color(cls, color):
        if isinstance(color, str):
            color = MPLManager.color_api().to_rgb(color)
        return cls.vpythonify(color)

class VPythonCanvasWrapper(VPythonWrapper):

    def __init__(self, canvas):
        self.canvas = canvas

    def remove(self, *, backend=None):
        self.canvas.delete()
    def clear(self, *, backend=None):
        for obj in self.canvas.objects:
            obj.visible = False

    @property
    def width(self):
        return self.canvas.width
    @width.setter
    def width(self, width):
        self.canvas.width = width

    @property
    def height(self):
        return self.canvas.height
    @height.setter
    def height(self, height):
        self.canvas.height = height

    @property
    def title(self):
        return self.canvas.title
    @title.setter
    def title(self, title):
        self.canvas.title = title

    @property
    def axis(self):
        return self.canvas.axis
    @axis.setter
    def axis(self, axis):
        self.canvas.axis = axis

    @property
    def up(self):
        return self.canvas.up
    @up.setter
    def up(self, up):
        self.canvas.up = up

    @property
    def background(self):
        return self.canvas.background
    @background.setter
    def background(self, background):
        self.canvas.background = self.vpython_color(background)

    def primitive(self, name, *args, color=None, **opts):
        args = [
            self.vpythonify(arg) for arg in args
        ]
        opts = {
            k:self.vpythonify(arg) for k,arg in opts.items()
        }
        opts['color'] = self.vpython_color(color)
        opts = {
            k:o for k,o in opts.items()
            if o is not None
        }
        return vpython.method(name)(*args, canvas=self.canvas, **opts)

    def box(self, left_corner, right_corner, **styles):
        return self.primitive('box',
                              pos=left_corner,
                              length=right_corner[0] - left_corner[0],
                              height=right_corner[1] - left_corner[1],
                              width=right_corner[2] - left_corner[2], **styles)

    def curve(self, points, **styles):
        return self.primitive('curve', points, **styles)

    def cylinder(self, start, end, rad, **styles):
        start = np.asanyarray(start)
        end = np.asanyarray(end)
        v = end - start
        n = np.linalg.norm(v)
        v = v / n

        return self.primitive('cylinder',
                              start,
                              rad=rad,
                              axis=v,
                              length=n,
                              **styles)

    def arrow(self, points, **styles):
        return self.primitive('arrow', points, **styles)

    def label(self, pos, text, **styles):
        return self.primitive('label', pos, text **styles)

    def sphere(self, points, rads, **styles):
        return self.primitive('sphere', pos=points, rad=rads, **styles)

class VPythonGraphWrapper(VPythonWrapper):

    def __init__(self, graph):
        self.graph = graph
        self.objs = []

    @property
    def title(self):
        return self.graph.title
    @title.setter
    def title(self, title):
        self.graph.title = title

    @property
    def xtitle(self):
        return self.graph.xtitle
    @xtitle.setter
    def xtitle(self, xtitle):
        self.graph.xtitle = xtitle

    @property
    def ytitle(self):
        return self.graph.ytitle
    @ytitle.setter
    def ytitle(self, ytitle):
        self.graph.ytitle = ytitle

    @property
    def background(self):
        return self.graph.background
    @background.setter
    def background(self, background):
        self.graph.background = self.vpython_color(background)

    @property
    def foreground(self):
        return self.graph.foreground
    @foreground.setter
    def foreground(self, foreground):
        self.graph.foreground = self.vpython_color(foreground)

    @property
    def xmin(self):
        return self.graph.xmin
    @xmin.setter
    def xmin(self, xmin):
        self.graph.xmin = xmin

    @property
    def xmax(self):
        return self.graph.xmax
    @xmax.setter
    def xmax(self, xmax):
        self.graph.xmax = xmax

    @property
    def ymin(self):
        return self.graph.ymin
    @ymin.setter
    def ymin(self, ymin):
        self.graph.ymin = ymin

    @property
    def ymax(self):
        return self.graph.ymax
    @ymax.setter
    def ymax(self, ymax):
        self.graph.ymax = ymax

    @property
    def width(self):
        return self.graph.width
    @width.setter
    def width(self, width):
        self.graph.width = width

    @property
    def height(self):
        return self.graph.height
    @height.setter
    def height(self, height):
        self.graph.height = height

    def remove(self, *, backend=None):
        self.graph.delete()
    def clear(self, *, backend=None):
        for obj in self.graph.objects:
            obj.visible = False

    def plot(self, x, y, color=None, marker_color=None, dot_color=None, **styles):
        curve = vpython.gcurve(
            color=self.vpython_color(color),
            marker_color=self.vpython_color(marker_color),
            dot_color=self.vpython_color(dot_color),
            graph=self.graph,
            **styles
        )
        curve.plot(np.array([x, y]).T)
        self.objs.append(curve)
        return curve

    def scatter(self, x, y, color=None, marker_color=None, dot_color=None, **styles):
        curve = vpython.gdots(
            color=self.vpython_color(color),
            marker_color=self.vpython_color(marker_color),
            dot_color=self.vpython_color(dot_color),
            graph=self.graph,
            **styles
        )
        curve.plot(np.array([x, y]).T)
        self.objs.append(curve)
        return curve

    def vbars(self, x, y, color=None, marker_color=None, dot_color=None, **styles):
        curve = vpython.gvbars(
            color=self.vpython_color(color),
            marker_color=self.vpython_color(marker_color),
            dot_color=self.vpython_color(dot_color),
            graph=self.graph,
            **styles
        )
        curve.plot(np.array([x, y]).T)
        self.objs.append(curve)
        return curve

    def hbars(self, x, y, color=None, marker_color=None, dot_color=None, **styles):
        curve = vpython.ghbars(
            color=self.vpython_color(color),
            marker_color=self.vpython_color(marker_color),
            dot_color=self.vpython_color(dot_color),
            graph=self.graph,
            **styles
        )
        curve.plot(np.array([x, y]).T)
        self.objs.append(curve)
        return curve

class VPythonAxes(GraphicsAxes):
    def __init__(self, graph:VPythonGraphWrapper):
        super().__init__()
        self.graph = graph

    def remove(self, *, backend):
        self.graph.remove(backend=backend)
    def clear(self, *, backend):
        self.graph.clear(backend=backend)

    def get_plotter(self, method):
        raise NotImplementedError(...)

    def get_plot_label(self):
        return self.graph.title
    def set_plot_label(self, val, **style):
        self.graph.title = val

    def get_style_list(self):
        raise NotImplementedError("style list cyclers not supported")
    def set_style_list(self, props):
        raise NotImplementedError("style list cyclers not supported")

    def get_frame_visible(self):
        raise NotImplementedError(...)
    def set_frame_visible(self, frame_spec):
        raise NotImplementedError(...)

    def get_frame_style(self):
        raise NotImplementedError(...)
    def set_frame_style(self, frame_spec):
        raise NotImplementedError(...)

    def get_xlabel(self):
        return self.graph.xtitle
    def set_xlabel(self, val, **style):
        self.graph.xtitle = val

    def get_ylabel(self):
        return self.graph.ytitle
    def set_ylabel(self, val, **style):
        self.graph.ytitle = val

    def get_xlim(self):
        return [self.graph.xmin, self.graph.xmax]
    def set_xlim(self, val, **opts):
        self.graph.xmin, self.graph.xmax = val

    def get_ylim(self):
        return [self.graph.ymin, self.graph.ymax]
    def set_ylim(self, val, **opts):
        self.graph.ymin, self.graph.ymax = val

    def get_xticks(self):
        raise NotImplementedError(...)
    def set_xticks(self, val, **opts):
        raise NotImplementedError(...)

    def get_yticks(self):
        raise NotImplementedError(...)
    def set_yticks(self, val, **opts):
        raise NotImplementedError(...)

    def get_xtick_style(self):
        raise NotImplementedError(...)
    def set_xtick_style(self, **opts):
        raise NotImplementedError(...)

    def get_ytick_style(self):
        raise NotImplementedError(...)
    def set_ytick_style(self, **opts):
        raise NotImplementedError(...)

    def set_aspect_ratio(self, ar):
        raise NotImplementedError(...)

    def get_bbox(self):
        raise NotImplementedError(...)
    def set_bbox(self, bbox):
        raise NotImplementedError(...)

    def get_facecolor(self):
        return self.graph.background
    def set_facecolor(self, fg):
        self.graph.background = fg

    def get_padding(self):
        raise NotImplementedError(...)

    def draw_line(self, points, **styles):
        return self.graph.plot(*np.asanyarray(points).T, **styles)

    def draw_disk(self, points, color=None, edge_color=None, radius=1,
                  edgecolors=None,
                  s=None, **styles):
        if edgecolors is None:
            if edge_color is not None:
                edgecolors = edge_color
            else:
                edgecolors=[[0.] * 3 + [.3]]
        if s is None:
            s = (10 * radius) ** 2
        return self.graph.scatter(*np.asanyarray(points).T, s=s, edgecolors=edgecolors, **styles)

    def draw_rect(self, points, **styles):
        raise NotImplementedError("too annoying")

    def draw_poly(self, points, **styles):
        raise NotImplementedError("too annoying")

    def draw_arrow(self, points, color=None, **styles):
        raise NotImplementedError("too annoying")

    def draw_text(self, points, vals, color=None, **styles):
        raise NotImplementedError("too annoying")
        # pts = np.asanyarray(points)
        # if pts.ndim == 1:
        #     return vpython.label(pts, vals, color=self.vpython_color(color), canvas=self.canvas, **styles)
        # else:
        #     return [
        #         vpython.label(pt, t, color=self.vpython_color(color), canvas=self.canvas, **styles)
        #         for pt, t in zip(pts, vals)
        #     ]

    def draw_sphere(self, points, rads, color=None, **styles):
        raise NotImplementedError("too annoying")
        # return vpython.sphere(points, rads, color=self.vpython_color(color), canvas=self.canvas, **styles)

    def animate_frames(self, frames, **animation_opts):
        raise NotImplementedError("not sure how to animate vpython")

class VPythonFigure(GraphicsFigure):
    Axes = VPythonAxes

    _refs = set()
    def __init__(self, vpython_graph:VPythonGraphWrapper, **opts):
        if vpython_graph in self._refs: raise ValueError(...)
        self._refs.add(vpython_graph)
        self.graph = vpython_graph
        super().__init__(**self.canonicalize_opts(opts))
    @classmethod
    def construct(cls, **kw) -> 'VPythonFigure':
        return cls(vpython.graph(**kw))
    def create_axes(self, rows=1, cols=1, spans=1, **kw) -> 'GraphicsAxes':
        if (rows, cols, spans) != (1, 1, 1):
            raise NotImplementedError("can't create subcanvases")
        return self.add_axes(self.graph)
    def create_inset(self, bbox, **kw) -> 'GraphicsAxes':
        raise NotImplementedError(...)
    def clear(self, *, backend):
        self.graph.clear()
    def close(self, *, backend):
        self.graph.remove()

    def get_size_inches(self):
        return [self.graph.width//72, self.graph.height//72]
    def set_size_inches(self, w, h):
        self.graph.width, self.graph.height = w*72, h*72

    def get_facecolor(self):
        return self.graph.background
    def set_facecolor(self, fg):
        self.graph.background = fg

    def savefig(self, file, **opts):
        raise NotImplementedError("too annoying")

class VPythonBackend(GraphicsBackend):
    Figure = VPythonFigure
    def create_figure(self, *args, **kwargs):
        figure = self.Figure.construct(**kwargs)
        axes = self.Figure.create_axes()
        return figure, axes

    class ThemeContextManager(GraphicsBackend.ThemeContextManager):
        theme_stack = []

        @classmethod
        def canonicalize_theme_opts(self, theme_parents, theme_spec):
            return []
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            ...

    def show_figure(self, graphics, reshow=None):
        ...

    def get_interactive_status(self) -> 'bool':
        return True
    def disable_interactivity(self):
        raise NotImplementedError("not possible")
    def enable_interactivity(self):
        ...
    def get_available_themes(self):
        return []

class VPythonAxes3D(GraphicsAxes3D):
    def __init__(self, canvas:VPythonCanvasWrapper):
        super().__init__()
        self.canvas = canvas

    def remove(self, *, backend):
        self.canvas.remove(backend=backend)
    def clear(self, *, backend):
        self.canvas.clear(backend=backend)

    def get_plotter(self, method):
        raise NotImplementedError(...)

    def get_plot_label(self):
        return self.canvas.title
    def set_plot_label(self, val, **style):
        self.canvas.title = val

    def get_style_list(self):
        raise NotImplementedError("style list cyclers not supported")
    def set_style_list(self, props):
        raise NotImplementedError("style list cyclers not supported")

    def get_frame_visible(self):
        raise NotImplementedError(...)
    def set_frame_visible(self, frame_spec):
        ...
        # raise NotImplementedError(...)

    def get_frame_style(self):
        raise NotImplementedError(...)
    def set_frame_style(self, frame_spec):
        ...
        # raise NotImplementedError(...)

    def get_xlabel(self):
        raise NotImplementedError(...)
    def set_xlabel(self, val, **style):
        ...
        # raise NotImplementedError(...)

    def get_ylabel(self):
        raise NotImplementedError(...)
    def set_ylabel(self, val, **style):
        ...
        # raise NotImplementedError(...)

    def get_xlim(self):
        raise NotImplementedError(...)
    def set_xlim(self, val, **opts):
        ...
        # raise NotImplementedError(...)

    def get_ylim(self):
        raise NotImplementedError(...)
    def set_ylim(self, val, **opts):
        ...
        # raise NotImplementedError(...)

    def get_zlim(self):
        raise NotImplementedError(...)
    def set_zlim(self, val, **opts):
        ...
        # raise NotImplementedError(...)

    def get_xticks(self):
        return []
    def set_xticks(self, val, **opts):
        ...
        # raise NotImplementedError(...)

    def get_yticks(self):
        return []
    def set_yticks(self, val, **opts):
        ...
        # raise NotImplementedError(...)

    def get_zticks(self):
        return []
    def set_zticks(self, val, **opts):
        ...
        # raise NotImplementedError(...)

    def get_xtick_style(self):
        return {}
    def set_xtick_style(self, **opts):
        ...
        # raise NotImplementedError(...)

    def get_ytick_style(self):
        return {}
    def set_ytick_style(self, **opts):
        ...
        # raise NotImplementedError(...)

    def get_ztick_style(self):
        return {}
    def set_ztick_style(self, **opts):
        ...
        # raise NotImplementedError(...)

    def set_aspect_ratio(self, ar):
        ...
        # raise NotImplementedError(...)

    def get_bbox(self):
        raise NotImplementedError(...)
    def set_bbox(self, bbox):
        raise NotImplementedError(...)

    def get_facecolor(self):
        return self.canvas.background
    def set_facecolor(self, fg):
        self.canvas.background = fg

    def get_padding(self):
        raise NotImplementedError(...)

    def draw_line(self, points, **styles):
        return self.canvas.curve(points, **styles)

    def draw_disk(self, points, **styles):
        raise NotImplementedError("2D")

    def draw_rect(self, points, **styles):
        raise NotImplementedError("2D")

    def draw_poly(self, points, **styles):
        raise NotImplementedError("2D")

    def draw_arrow(self, points, **styles):
        return self.canvas.arrow(points, **styles)

    def draw_text(self, points, vals, **styles):
        pts = np.asanyarray(points)
        if pts.ndim == 1:
            return self.canvas.label(pts, vals, **styles)
        else:
            return [
                self.canvas.label(pt, t, **styles)
                for pt, t in zip(pts, vals)
            ]

    def draw_sphere(self, points, rads, **styles):
        return self.canvas.sphere(points, rads, **styles)

    def draw_cylinder(self, start, end, rad, **styles):
        return self.canvas.cylinder(start, end, rad, **styles)

    def draw_primitive(self, name, *args, **kwargs):
        return self.canvas.primitive(name, *args, **kwargs)

class VPythonFigure3D(GraphicsFigure):
    Axes = VPythonAxes3D

    _refs = set()
    def __init__(self, vpython_canvas:VPythonCanvasWrapper, **opts):
        if isinstance(vpython_canvas, VPythonCanvasWrapper):
            vpython_canvas = vpython_canvas.canvas
        if vpython_canvas in self._refs: raise ValueError(...)
        self._refs.add(vpython_canvas)
        self.canvas = VPythonCanvasWrapper(vpython_canvas)
        super().__init__(**self.canonicalize_opts(opts))
    @classmethod
    def construct(cls, **kw) -> 'GraphicsFigure':
        return cls(vpython.method('canvas')(**kw))
    def create_axes(self, rows=1, cols=1, spans=1, **kw) -> 'GraphicsAxes':
        if (rows, cols, spans) != (1, 1, 1):
            raise NotImplementedError("can't create subcanvases")
        return self.add_axes(self.canvas)
    def create_inset(self, bbox, **kw) -> 'GraphicsAxes':
        raise NotImplementedError(...)
    def clear(self, *, backend):
        self.canvas.clear()
    def close(self, *, backend):
        self.canvas.remove()
    def get_size_inches(self):
        return [self.canvas.width//72, self.canvas.height//72]
    def set_size_inches(self, w, h):
        self.canvas.width, self.canvas.height = w*72, h*72
    def set_extents(self, extents):
        ...
    def get_facecolor(self):
        return self.canvas.background
    def set_facecolor(self, fg):
        self.canvas.background = fg
    def savefig(self, file, **opts):
        raise NotImplementedError("too annoying")

class VPythonBackend3D(GraphicsBackend):
    Figure = VPythonFigure3D
    def create_figure(self, *args, **kwargs):
        figure = self.Figure.construct(**kwargs)
        axes = figure.create_axes()
        return figure, axes

    class ThemeContextManager(VPythonBackend.ThemeContextManager):
        ...

    def show_figure(self, graphics, reshow=None):
        ...

    def get_interactive_status(self) -> 'bool':
        return True
    def disable_interactivity(self):
        ...
    def enable_interactivity(self):
        ...
    def get_available_themes(self):
        return []

class X3DAxes(GraphicsAxes3D):
    def __init__(self, *children, title=None, background=None, **opts):
        super().__init__()
        self.children = list(children)
        self.title = title
        self.background = background
        self.opts = opts

    @classmethod
    def canonicalize_opts(cls, opts):
        return opts

    def remove(self, *, backend):
        self.children = []
        self.title = ""
        self.background = "white"

    def clear(self, *, backend):
        self.children = []
        self.title = ""
        self.background = "white"

    def get_plotter(self, method):
        ...

    def get_plot_label(self):
        return self.title
    def set_plot_label(self, val, **style):
        self.title = val

    def get_style_list(self):
        raise NotImplementedError("style list cyclers not supported")
    def set_style_list(self, props):
        raise NotImplementedError("style list cyclers not supported")

    def get_frame_visible(self):
        raise NotImplementedError(...)
    def set_frame_visible(self, frame_spec):
        ...
        # raise NotImplementedError(...)

    def get_frame_style(self):
        raise NotImplementedError(...)
    def set_frame_style(self, frame_spec):
        ...
        # raise NotImplementedError(...)

    def get_xlabel(self):
        raise NotImplementedError(...)
    def set_xlabel(self, val, **style):
        ...

    def get_ylabel(self):
        raise NotImplementedError(...)
    def set_ylabel(self, val, **style):
        ...

    def get_xlim(self):
        raise NotImplementedError(...)
    def set_xlim(self, val, **opts):
        ...

    def get_ylim(self):
        raise NotImplementedError(...)
    def set_ylim(self, val, **opts):
        ...

    def get_zlim(self):
        raise NotImplementedError(...)
    def set_zlim(self, val, **opts):
        ...

    def get_xticks(self):
        return []
    def set_xticks(self, val, **opts):
        ...

    def get_yticks(self):
        return []
    def set_yticks(self, val, **opts):
        ...

    def get_zticks(self):
        return []
    def set_zticks(self, val, **opts):
        ...

    def get_xtick_style(self):
        return {}
    def set_xtick_style(self, **opts):
        ...

    def get_ytick_style(self):
        return {}
    def set_ytick_style(self, **opts):
        ...

    def get_ztick_style(self):
        return {}
    def set_ztick_style(self, **opts):
        ...

    def set_aspect_ratio(self, ar):
        ...

    def get_bbox(self):
        raise NotImplementedError(...)
    def set_bbox(self, bbox):
        raise NotImplementedError(...)

    def get_facecolor(self):
        return self.background
    def set_facecolor(self, fg):
        self.background = fg

    def get_padding(self):
        raise NotImplementedError(...)

    def get_view_settings(self):
        return self.opts.get('viewpoint', {})
    def set_view_settings(self, **values):
        new_opts = {
            k:v for k,v in dict(self.opts.get('viewpoint', {}), **values).items()
            if v is not None
        }
        if len(new_opts) == 0 and 'viewpoint' in self.opts:
            del self.opts['viewpoint']
        else:
            self.opts['viewpoint'] = new_opts

    def draw_line(self, points, indices=None, s=None, riffle=True, line_thickness=None,
                  edgecolors=None, color=None, glow=None, **styles):
        if color is None: color = edgecolors
        if color is None: color = 'black'
        # if line_thickness is None and s is not None:
        #     if not nput.is_numeric(s): s = s[0]
        #     line_thickness = s / 1000
        points = np.asanyarray(points)
        if riffle:
            if indices is not None:
                indices = np.asanyarray(indices)
                if indices.ndim > 1 and indices.shape[-1] > 2:
                    riff_start = np.arange(indices.shape[-1])
                    riff_end = np.roll(riff_start, -1)
                    indices = np.concatenate([
                        indices[..., riff_start, np.newaxis],
                        indices[..., riff_end, np.newaxis]
                    ], axis=-1).reshape(-1, 2)
                    indices = np.concatenate([indices, np.full((indices.shape[0], 1), -1)], axis=-1)
            elif points.ndim > 2 and points.shape[-2] > 2:
                riff_start = np.arange(points.shape[-2])
                riff_end = np.roll(riff_start, 1)
                points = np.concatenate([
                    points[..., riff_start, np.newaxis, :],
                    points[..., riff_end, np.newaxis, :]
                ], axis=-2).reshape((-1, 2, 3))

        if line_thickness is not None:
            if indices is not None:
                raise NotImplementedError(indices)
            else:
                # line_set = x3d.X3DGroup([
                #     x3d.X3DCylinder(p1, p2, line_thickness=line_thickness, color=glow, **styles)
                #     for p1, p2 in zip(points[:-1], points[1:])
                # ])
                line_set = x3d.X3DCylinder(points[:-1], points[1:], radius=line_thickness,
                                           glow=glow,
                                           color=color,
                                           **styles)
        else:
            if glow is None:
                glow = color
            if indices is not None:
                line_set = x3d.X3DIndexedLineSet(points, indices, line_thickness=line_thickness, glow=glow, **styles)
            else:
                line_set = x3d.X3DLine(points, line_thickness=line_thickness, glow=glow, **styles)
        self.children.append(line_set)

        return line_set

    def draw_disk(self,
                  points,
                  radius=None,
                  color=None,
                  line_color=None,
                  edgecolors=None,
                  s=None,
                  normal=None,
                  line_thickness=None,
                  innerRadius=None,
                  outerRadius=None,
                  uv_axes=None,
                  uv_sign=None,
                  angle=None,
                  rotation=None,
                  solid=None,
                  **styles):
        if radius is None and s is not None:
            radius = s / 100
        if line_color is None:
            line_color = edgecolors

        if uv_axes is not None:
            u, v = uv_axes
            base_ang, base_norm = nput.vec_angles(u, v, return_crosses=True)
            base_norm = nput.vec_normalize(base_norm)
            if normal is None:
                normal = base_norm
            angs, crosses = nput.vec_angles([0, 0, 1], normal, return_crosses=True, return_norms=False)
            embedding_axes = nput.rotation_matrix(crosses, angs).T
            local_x, local_y, local_z = embedding_axes
            emb_angle, ax2 = nput.vec_angles(local_x, v)
            if uv_sign is None:
                # print(np.dot(local_x, v))
                # print(np.dot(local_y, v))
                # print(np.dot(local_x, u))
                # print(np.dot(local_y, u))
                uv_sign = np.sign(np.dot(local_y, v))
            emb_angle = uv_sign * emb_angle
            if rotation is None:
                rotation = [0, 0, 1, emb_angle]
            if angle is None:
                angle = base_ang

        objects = []
        if line_color is not None:
            if line_thickness is None:
                disk_set = x3d.X3DCircle2D(points,
                                           normal=normal,
                                           radius=radius,
                                           glow=line_color,
                                           rotation=rotation,
                                           solid=False if solid is None else solid,
                                           angle=angle,
                                           **styles
                                           )
            else:
                if color is None:
                    if innerRadius is None:
                        innerRadius = line_thickness
                    if outerRadius is None:
                        outerRadius = radius
                disk_set = x3d.X3DTorus(points,
                                        normal=normal,
                                        inner_radius=innerRadius if color is None else line_thickness,
                                        radius=outerRadius if color is None else radius,
                                        color=line_color,
                                        solid=solid,
                                        rotation=rotation,
                                        angle=angle,
                                        **styles
                                        )
            objects.append(disk_set)

        if color is None and line_color is None:
            color = 'black'
        if color is not None:
            if outerRadius is None:
                outerRadius = radius
            disk_set = x3d.X3DDisk2D(points,
                                     normal=normal,
                                     inner_radius=innerRadius,
                                     radius=outerRadius,
                                     color=color,
                                     rotation=rotation,
                                     solid=False if solid is None else solid,
                                     angle=angle,
                                     **styles
                                     )
            objects.append(disk_set)

        self.children.extend(objects)
        return objects

    def draw_arrow(self, points, **styles):
        points = np.asanyarray(points)
        arrows = x3d.X3DArrow(points[..., 0, :], points[..., 1, :], **styles)
        self.children.append(arrows)
        return arrows

    def draw_text(self, points, vals, **styles):
        text = x3d.X3DText(points, text=vals, **styles)
        self.children.append(text)
        return text

    def draw_rect(self, points, **styles):
        points = np.asanyarray(points)
        rects = x3d.X3DRectangle2D(points[..., 0, :], points[..., 1, :], **styles)
        self.children.append(rects)

        return rects
    def draw_point(self, points, color=None, glow=None, **styles):
        points = np.asanyarray(points)
        if glow is None: glow = color
        rects = x3d.X3DPointSet(points, glow=glow, **styles)
        self.children.append(rects)

        return rects
    def draw_triangle(self, points, indices=None, **styles):
        if indices is None:
            points = np.asanyarray(points)
            rects = x3d.X3DTriangleSet(points, **styles)
        else:
            points = np.asanyarray(points)
            indices = np.asanyarray(indices)
            rects = x3d.X3DIndexedTriangleSet(points, indices, **styles)
        self.children.append(rects)

        return rects
    def draw_poly(self, points, **styles):
        raise NotImplementedError("2D")

    def draw_sphere(self, centers, rads, **styles):
        spheres = x3d.X3DSphere(centers, radius=rads, **styles)
        self.children.append(spheres)

        return spheres

    def draw_cylinder(self, starts, ends, rads, capped=False, **styles):
        if capped:
            cyls = x3d.X3DCappedCylinder(starts, ends, radius=rads, **styles)
        else:
            cyls = x3d.X3DCylinder(starts, ends, radius=rads, **styles)
        self.children.append(cyls)

        return cyls

    def to_x3d(self):
        opts = dict(
            self.opts,
            background=self.background,
            title=self.title
        )
        return x3d.X3DScene(
            self.children,
            **opts
        )

class X3DFigure(GraphicsFigure):
    Axes = X3DAxes

    def __init__(self, width=640, height=500,
                 background='white', figsize=None, profile='Immersive', version='3.3',
                 id=None,
                 **opts):
        if id is None:
            id = f"x3d-{uuid.uuid4()}"
        self.id = id
        self.profile = profile
        self.version = version
        self.opts = dict(opts)
        self.width = width
        self.height = height
        if figsize is not None:
            self.set_size_inches(*figsize)
        self.background = background
        self.shown = False
        super().__init__()

    def __setitem__(self, key, value):
        self.opts[key] = value
    def __getitem__(self, item):
        return self.opts[item]

    def clear(self, *, backend):
        self.axes = []

    def close(self, *, backend):
        self.clear(backend=backend)

    def create_inset(self, bbox, **kw) -> 'GraphicsAxes':
        raise NotImplementedError("not possible")

    def create_axes(self, rows=1, cols=1, spans=1, **kw) -> 'GraphicsAxes':
        if (rows, cols, spans) != (1, 1, 1):
            raise NotImplementedError("can't create subcanvases")
        return self.add_axes(self.Axes(**kw))

    @classmethod
    def construct(cls, **kw) -> 'GraphicsFigure':
        return cls(**kw)

    def get_size_inches(self):
        return [self.width/DPI_SCALING, self.height/DPI_SCALING]
    def set_size_inches(self, w, h):
        self.width, self.height = w*DPI_SCALING, h*DPI_SCALING
    def set_extents(self, extents):
        ...
    def get_facecolor(self):
        return self.background
    def set_facecolor(self, fg):
        self.background = fg
    def savefig(self, file, format=None, **opts):
        return self.to_x3d(**opts).dump(file)
    def to_x3d(self, **opts):
        opts = dict(
            self.opts,
            profile=self.profile,
            version=self.version,
            width=self.width,
            height=self.height,
            id=self.id,
            **opts
        )
        return x3d.X3D(
            *[a.to_x3d() for a in self.axes],
            **opts
        )

    def animate_frames(self, frames: list['X3DAxes'], **animation_opts):
        animator = X3DAxes(
            x3d.X3DListAnimator(
                [
                    x3d.X3DGroup(f.children if hasattr(f, 'children') else f)
                    for f in frames
                ],
                **animation_opts
            ),
            **self.axes[0].opts
        )
        opts = dict(
            self.opts,
            profile=self.profile,
            version=self.version,
            width=self.width,
            height=self.height
        )
        return x3d.X3D(animator.to_x3d(), **opts)

class X3DBackend(GraphicsBackend):
    Figure = X3DFigure
    def create_figure(self, *args, **kwargs):
        figure = self.Figure.construct(**kwargs)
        axes = figure.create_axes()
        return figure, axes

    class ThemeContextManager(GraphicsBackend.ThemeContextManager):
        theme_stack = []

        @classmethod
        def canonicalize_theme_opts(self, theme_parents, theme_spec):
            return []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            ...

    def show_figure(self, graphics:X3DFigure, reshow=None):
        if not graphics.shown:
            from ..Jupyter.JHTML import JupyterAPIs
            dynamic_loading = JupyterAPIs().in_jupyter_environment()
            graphics.shown = True
            graphics.to_x3d().to_widget(dynamic_loading=dynamic_loading).display()

            # from ..Jupyter.JHTML.WidgetTools import JupyterAPIs
            #
            # display = JupyterAPIs.get_display_api()
            # html = graphics.to_x3d().to_widget().tostring()
            # return display.display(display.HTML(html))

    def get_interactive_status(self) -> 'bool':
        return True
    def disable_interactivity(self):
        ...
    def enable_interactivity(self):
        ...
    def get_available_themes(self):
        return []

class SceneJSONAxes(GraphicsAxes3D):
    def __init__(self, *children, title=None, background=None, **opts):
        super().__init__()
        self.children = list(children)
        self.title = title
        self.background = background
        self.opts = opts
        self.mode = None
        for c in children:
            mode = c.attrs.get('mode')
            if mode is not None:
                self.mode = mode
                break

    @classmethod
    def canonicalize_opts(cls, opts):
        return opts

    def remove(self, *, backend):
        self.children = []
        self.title = ""
        self.background = "white"

    def clear(self, *, backend):
        self.children = []
        self.title = ""
        self.background = "white"

    def get_plotter(self, method):
        ...

    def get_plot_label(self):
        return self.title
    def set_plot_label(self, val, **style):
        self.title = val

    def get_style_list(self):
        raise NotImplementedError("style list cyclers not supported")
    def set_style_list(self, props):
        raise NotImplementedError("style list cyclers not supported")

    def get_frame_visible(self):
        raise NotImplementedError(...)
    def set_frame_visible(self, frame_spec):
        ...
        # raise NotImplementedError(...)

    def get_frame_style(self):
        raise NotImplementedError(...)
    def set_frame_style(self, frame_spec):
        ...
        # raise NotImplementedError(...)

    def get_xlabel(self):
        raise NotImplementedError(...)
    def set_xlabel(self, val, **style):
        ...

    def get_ylabel(self):
        raise NotImplementedError(...)
    def set_ylabel(self, val, **style):
        ...

    def get_xlim(self):
        raise NotImplementedError(...)
    def set_xlim(self, val, **opts):
        ...

    def get_ylim(self):
        raise NotImplementedError(...)
    def set_ylim(self, val, **opts):
        ...

    def get_zlim(self):
        raise NotImplementedError(...)
    def set_zlim(self, val, **opts):
        ...

    def get_xticks(self):
        return []
    def set_xticks(self, val, **opts):
        ...

    def get_yticks(self):
        return []
    def set_yticks(self, val, **opts):
        ...

    def get_zticks(self):
        return []
    def set_zticks(self, val, **opts):
        ...

    def get_xtick_style(self):
        return {}
    def set_xtick_style(self, **opts):
        ...

    def get_ytick_style(self):
        return {}
    def set_ytick_style(self, **opts):
        ...

    def get_ztick_style(self):
        return {}
    def set_ztick_style(self, **opts):
        ...

    def set_aspect_ratio(self, ar):
        ...

    def get_bbox(self):
        raise NotImplementedError(...)
    def set_bbox(self, bbox):
        raise NotImplementedError(...)

    def get_facecolor(self):
        return self.background
    def set_facecolor(self, fg):
        self.background = fg

    def get_padding(self):
        raise NotImplementedError(...)

    def get_view_settings(self):
        return self.opts.get('viewpoint', {})
    def set_view_settings(self, **values):
        new_opts = {
            k:v for k,v in dict(self.opts.get('viewpoint', {}), **values).items()
            if v is not None
        }
        if len(new_opts) == 0 and 'viewpoint' in self.opts:
            del self.opts['viewpoint']
        else:
            self.opts['viewpoint'] = new_opts

    def draw_line(self, points, **styles):
        points = np.asanyarray(points)
        if points.shape[-1] == 3:
            self.mode = '3d'
        else:
            self.mode = '2d'
        line_set = sceneJSON.Line(points=points.tolist(), mode=self.mode, **styles)
        self.children.append(line_set)

        return line_set

    def draw_disk(self, points, rads=1, **styles):
        points = np.asanyarray(points)
        if points.shape[-1] == 3:
            self.mode = '3d'
        else:
            self.mode = '2d'
        rads = np.asanyarray(rads).tolist()
        disk_set = sceneJSON.Disk(center=points.tolist(), radius=rads, mode=self.mode, **styles)
        self.children.append(disk_set)

        return disk_set

    def draw_arrow(self, points, radius=.1, **styles):
        points = np.asanyarray(points)
        if points.shape[-1] == 3:
            self.mode = '3d'
        else:
            self.mode = '2d'
        arrows = sceneJSON.Arrow(points=points.tolist(), radius=radius, mode=self.mode, **styles)
        self.children.append(arrows)
        return arrows

    def draw_text(self, points, vals, **styles):
        points = np.asanyarray(points)
        if points.shape[-1] == 3:
            self.mode = '3d'
        else:
            self.mode = '2d'
        text = sceneJSON.Text(centers=points.tolist(), text=vals, mode=self.mode, **styles)
        self.children.append(text)
        return text

    def draw_rect(self, points, **styles):
        points = np.asanyarray(points)
        if points.shape[-1] == 3:
            self.mode = '3d'
        else:
            self.mode = '2d'
        rects = sceneJSON.Rectangle(points=points.tolist(), mode=self.mode, **styles)
        self.children.append(rects)

        return rects

    def draw_poly(self, points, **styles):
        points = np.asanyarray(points)
        if points.shape[-1] == 3:
            self.mode = '3d'
        else:
            self.mode = '2d'
        rects = sceneJSON.Polygon(points=points.tolist(), mode=self.mode, **styles)
        self.children.append(rects)

        return rects

    def draw_sphere(self, centers, rads, **styles):
        centers = np.asanyarray(centers)
        if centers.shape[-1] == 3:
            self.mode = '3d'
        else:
            self.mode = '2d'
        spheres = sceneJSON.Sphere(center=centers.tolist(), radius=rads, mode=self.mode, **styles)
        self.children.append(spheres)

        return spheres

    def draw_cylinder(self, starts, ends, rads, **styles):
        starts = np.asanyarray(starts)
        if starts.shape[-1] == 3:
            self.mode = '3d'
        else:
            self.mode = '2d'
        ends = np.asanyarray(ends).tolist()
        rads = np.asanyarray(rads).tolist()
        cyls = sceneJSON.Cylinder(start=starts.tolist(), end=ends, radius=rads, mode=self.mode, **styles)
        self.children.append(cyls)

        return cyls

    def to_json(self):
        opts = dict(
            self.opts,
            background=self.background,
            title=self.title
        )
        return sceneJSON.Scene(
            self.children,
            **opts
        )

class SceneJSONFigure(GraphicsFigure):
    Axes = SceneJSONAxes

    def __init__(self, width=640, height=500,
                 background='white', figsize=None, profile='Immersive', version='3.3',
                 id=None,
                 **opts):
        if id is None:
            id = f"scene-{uuid.uuid4()}"
        self.id = id
        self.profile = profile
        self.version = version
        self.opts = dict(opts)
        self.width = width
        self.height = height
        if figsize is not None:
            self.set_size_inches(*figsize)
        self.background = background
        self.shown = False
        super().__init__()

    def __setitem__(self, key, value):
        self.opts[key] = value
    def __getitem__(self, item):
        return self.opts[item]

    def clear(self, *, backend):
        self.axes = []

    def close(self, *, backend):
        self.clear(backend=backend)

    def create_inset(self, bbox, **kw) -> 'GraphicsAxes':
        raise NotImplementedError("not possible")

    def create_axes(self, rows=1, cols=1, spans=1, **kw) -> 'GraphicsAxes':
        if (rows, cols, spans) != (1, 1, 1):
            raise NotImplementedError("can't create subcanvases")
        return self.add_axes(self.Axes(**kw))

    @classmethod
    def construct(cls, **kw) -> 'GraphicsFigure':
        return cls(**kw)

    def get_size_inches(self):
        return [self.width/DPI_SCALING, self.height/DPI_SCALING]
    def set_size_inches(self, w, h):
        self.width, self.height = w*DPI_SCALING, h*DPI_SCALING
    def set_extents(self, extents):
        ...
    def get_facecolor(self):
        return self.background
    def set_facecolor(self, fg):
        self.background = fg
    def savefig(self, file, format=None, **opts):
        return self.to_json(**opts).dump(file)
    def to_json(self, **opts):
        opts = dict(
            self.opts,
            profile=self.profile,
            version=self.version,
            width=self.width,
            height=self.height,
            id=self.id,
            **opts
        )
        mode = '2d'
        for a in self.axes:
            if a.mode == '3d': mode = '3d'
        if mode == '3d':
            wrapper = sceneJSON.Graphics3D
        else:
            wrapper = sceneJSON.Graphics

        return wrapper(
            *[a.to_json() for a in self.axes],
            **opts
        )

    def animate_frames(self, frames: list['SceneJSONAxes'], **animation_opts):
        frames = [
            SceneJSONAxes(*f) if not isinstance(f, SceneJSONAxes) else f
            for f in frames
        ]
        wrapper = sceneJSON.Graphics if frames[0].mode == '2d' else sceneJSON.Graphics3D
        return sceneJSON.Animation(
            [wrapper(f.to_json()) for f in frames],
            **animation_opts
        )
        # animator = X3DAxes(
        #     x3d.X3DListAnimator(
        #         [
        #             x3d.X3DGroup(f.children if hasattr(f, 'children') else f)
        #             for f in frames
        #         ],
        #         **animation_opts
        #     ),
        #     **self.axes[0].opts
        # )
        # opts = dict(
        #     self.opts,
        #     profile=self.profile,
        #     version=self.version,
        #     width=self.width,
        #     height=self.height
        # )
        # return x3d.X3D(animator.to_x3d(), **opts).to_widget()

class SceneJSONBackend(GraphicsBackend):
    Figure = SceneJSONFigure
    def create_figure(self, *args, **kwargs):
        figure = self.Figure.construct(**kwargs)
        axes = figure.create_axes()
        return figure, axes

    class ThemeContextManager(GraphicsBackend.ThemeContextManager):
        theme_stack = []

        @classmethod
        def canonicalize_theme_opts(self, theme_parents, theme_spec):
            return []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            ...

    def show_figure(self, graphics:SceneJSONFigure, reshow=None):
        if not graphics.shown:
            graphics.shown = True

            from ..Jupyter import JHTML
            #
            # display = JupyterAPIs.get_display_api()
            return JHTML.Pre(graphics.to_json().tostring(indent=2)).display()
            # return html.display()

    def get_interactive_status(self) -> 'bool':
        return True
    def disable_interactivity(self):
        ...
    def enable_interactivity(self):
        ...
    def get_available_themes(self):
        return []