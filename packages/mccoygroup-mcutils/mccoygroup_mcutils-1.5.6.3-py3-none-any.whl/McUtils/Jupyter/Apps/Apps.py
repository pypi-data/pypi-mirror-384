
__all__ = [
    "App",
    "SettingsPane",
    "Manipulator",
]

import types, typing

import numpy as np

from ..JHTML import JHTML, DefaultOutputWidget#, HTML, ActiveHTMLWrapper
from .Interfaces import *
from .Controls import Control, FunctionDisplay
from .Variables import WidgetControl, InterfaceVars, DefaultVars

# NonPrimitiveInterfaceType = typing.Union[
#     HTMLableType,
#     WidgetableType,
#     Component,
#     typing.Tuple[
#         typing.Union[
#             HTMLableType,
#             WidgetableType,
#             Component
#         ],
#         typing.Mapping
#     ]
# ]


__reload_hook__ = ['..JHTML', '.Interfaces', '.Controls', '.Variables']

# class FunctionDisplay:
#     def __init__(self, func, vars):
#         self.func = func
#         self.vars = vars
#         self.output = JupyterAPIs.get_widgets_api().Output()
#         self.update = self.update # a weird kluge to prevent a weakref issue...
#     def display(self):
#         self.output.clear_output()
#         with self.output:
#             res = self.func(**{x.name: x.value for x in self.vars})
#             if res is not None:
#                 JupyterAPIs.get_display_api().display(res)
#     def update(self, *ignored_settings):
#         return self.display()
#     def to_widget(self):
#         for v in self.vars:
#             v.callbacks.add(self.update)
#         return self.output
class Manipulator(Card):

    theme = Card.merge_themes(
        Card.theme,
        {
            'controls': {},
            'output': {}
        }
    )
    def __init__(self, func, *controls, debounce=None, autoclear=True, **etc):
        super().__init__(**etc)
        self.controls = [self.canonicalize_control(c) for c in controls]
        vars = [c.var for c in self.controls]
        self.output = FunctionDisplay(func, vars, debounce=debounce, autoclear=autoclear, **self.theme.get('output', {}))
        body = Flex(
            [
                self.output,
                Flex(self.controls, direction='column', **self.theme.get('controls', {}))
            ],
            direction='column'
        )
        self.component_args['body'] = (body,)
    @classmethod
    def canonicalize_control(cls, settings):
        if isinstance(settings, (WidgetControl, Control)):
            return settings
        else:
            var, settings = settings
            if not isinstance(settings, dict):
                if isinstance(settings, (list, tuple)) and isinstance(settings[0], (int, float, np.integer, np.floating)):
                    settings = {'range':settings}
                else:
                    settings = {'value':settings}
            # try:
            control = Control.construct(var, **settings)
            # except:
            #     control = WidgetControl(var, **settings)

            return control
    def initialize(self):
        self.output.update(None)

class App(Component):
    """
    Provides a framework for making Jupyter Apps with the
    elements built out in the Interfaces package
    """
    _app_stack=[]
    themes = {
        'primary':{
            'header':{
                'wrapper': {'cls': ['navbar-dark', 'bg-secondary', 'border-bottom']}
            },
            'toolbar':{'cls':['form-check', 'bg-light', 'border-bottom']},
            'sidebar':{
                'classes':['bg-light', 'border-end', 'h-100'],
                'styles':{},
                'opener':{
                    'header':{
                        'cls':['pt-0', 'bg-light'],
                        'border_top':'1px solid rgb(240, 240, 240)'
                    },
                    'body': {
                        'cls':['ps-0', 'pe-0']
                    }
                },
                'body':{
                    'wrapper':{'cls':['bg-light', 'border-end', 'h-100']}
                }
            },
            'footer':{
                 'wrapper': {'cls': ['navbar-light', 'bg-light', 'border-top']}
            }
        }
    }
    @classmethod
    def merge_themes(cls, theme_1, theme_2):
        new = theme_1.copy()
        for k in theme_2:
            if k in new and isinstance(new[k], dict):
                new[k] = cls.merge_themes(new[k], theme_2[k])
            else:
                new[k] = theme_2[k]
        return new


    def __init__(self,
                 body=None,
                 header=None,
                 footer=None,
                 sidebar=None,
                 toolbar=None,
                 theme='primary',
                 layout='grid',
                 cls='app border',
                 output=None,
                 capture_output=None,
                 vars=None,
                 **attrs
                 ):
        self._parent = None if len(self._app_stack) == 0 else self._app_stack[-1]
        super().__init__()
        self.vars = DefaultVars.resolve() if vars is None else vars
        self.output = JHTML.OutputArea(autoclear=True) if output is None else output
        self.capture_output = self._parent is None if capture_output is None else capture_output
        self.theme = self.themes[theme] if isinstance(theme, str) else self.merge_themes(self.themes['primary'], theme)
        self._body = [None, body]
        self._header = [None, header]
        self._footer = [None, footer]
        self._sidebar = [None, sidebar]
        self._toolbar = [None, toolbar]
        self.layout = layout
        self.cls = cls
        self.attrs = attrs
        self._out = None
        self._vv = None
        self._stack_depth = 0
    def __enter__(self):
        if self._stack_depth == 0:
            self._vv = DefaultVars(self.vars)
            self._vv.__enter__()
            self._out = DefaultOutputWidget(self.output)
            self._out.__enter__()
            self._app_stack.append(self)
        self._stack_depth += 1
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stack_depth -= max(0, self._stack_depth - 1)
        if self._stack_depth == 0:
            self._vv.__exit__(exc_type, exc_val, exc_tb)
            self._vv = None
            self._out.__exit__(exc_type, exc_val, exc_tb)
            self._out = None
            self._app_stack.remove(self)
    @property
    def body(self):
        if self._body[1] is not None:
            if self._body[0] is None:
                with self:
                    self._body[0] = self.construct_body(self._body[1])
        return self._body[0]
    @body.setter
    def body(self, b):
        self._body = [None, b]
    @property
    def header(self):
        if self._header[1] is not None:
            if self._header[0] is None:
                with self:
                    self._header[0] = self.construct_header(self._header[1])
        return self._header[0]
    @header.setter
    def header(self, h):
        self._header = [None, h]
    @property
    def sidebar(self):
        if self._sidebar[1] is not None:
            if self._sidebar[0] is None:
                with self:
                    self._sidebar[0] = self.construct_sidebar(self._sidebar[1])
        return self._sidebar[0]
    @sidebar.setter
    def sidebar(self, s):
        self._sidebar = [None, s]
    @property
    def toolbar(self):
        if self._toolbar[1] is not None:
            if self._toolbar[0] is None:
                with self:
                    self._toolbar[0] = self.construct_toolbar(self._toolbar[1])
        return self._toolbar[0]
    @toolbar.setter
    def toolbar(self, t):
        self._toolbar = [None, t]
    @property
    def footer(self):
        if self._footer[1] is not None:
            if self._footer[0] is None:
                with self:
                    self._footer[0] = self.construct_footer(self._footer[1])
        return self._footer[0]
    @footer.setter
    def footer(self, f):
        self._footer = [None, f]
    @classmethod
    def prep_head_item(cls, item):
        if (
                isinstance(item, (tuple, list))
                and len(item) == 2
                and isinstance(item[1], (types.FunctionType, types.MethodType))
        ):
            item = Button(*item)
        return item
    @classmethod
    def construct_navbar_item(cls, item):
        if isinstance(item, dict) and len(item) == 1 and 'body' not in item:
            for item in item.items():
                item = tuple(item)
        if isinstance(item, (tuple, list)) and len(item) == 2:
            k,v = item
            if isinstance(v, (tuple, list, dict)):
                v = tuple(cls.prep_head_item(i) for i in v)
                item = {'raw':Dropdown(k, v)}
            elif isinstance(v, (types.FunctionType, types.MethodType)):
                item = Button(k, v)
        return item
    def construct_header(self, header, **opts):
        if isinstance(header, tuple) and len(header) == 2 and isinstance(header[1], dict):
            opts = dict(header[1], **opts)
            header = header[0]
        elif isinstance(header, dict):
            header = header.copy()
            sb = header['items']
            del header['items']
            opts = dict(header, **opts)
            header = sb
        elif not (isinstance(header, (list, tuple, Component)) or hasattr(header, 'to_widget') or hasattr(header, 'to_tree')):
            header = [header]
        if isinstance(header, (list, tuple)):
            header = Navbar(
                [self.construct_navbar_item(h) for h in header],
                **dict({'theme':self.theme['header']}, **opts)
            )
        # elif isinstance(header, str):
        #     header = ...
        # elif isinstance(header, (HTML.XMLElement, ActiveHTMLWrapper)):
        #     ...
        return header
    def construct_footer(self, footer, **opts):
        if isinstance(footer, tuple) and len(footer) == 2 and isinstance(footer[1], dict):
            opts = dict(footer[1], **opts)
            footer = footer[0]
        elif isinstance(footer, dict):
            footer = footer.copy()
            sb = footer['items']
            del footer['items']
            opts = dict(footer, **opts)
            footer = sb
        elif not (isinstance(footer, (list, tuple, Component)) or hasattr(footer, 'to_widget') or hasattr(footer, 'to_tree')):
            footer = [footer]
        if isinstance(footer, (list, tuple)):
            footer = Navbar(
                footer,
                **dict({'theme':self.theme['footer']}, **opts)
            )
        return footer
    def construct_sidebar_item(self, item):
        if isinstance(item, tuple):
            if isinstance(item[0], tuple) and len(item[0]) == 2:
                items = []
                for k,v in item:
                    if isinstance(v, tuple):
                        v = Sidebar([self.construct_sidebar_item(h) for h in v])
                    items.append((k, v))
                item = dict(body=Opener(items, theme=self.theme['sidebar']['opener']['header']), theme=self.theme['sidebar']['opener']['body'])
            else:
                k,v = item
                if isinstance(v, tuple):
                    v = Sidebar([self.construct_sidebar_item(h) for h in v])
                item = dict(body=Opener(((k, v),), theme=self.theme['sidebar']['opener']['header']), theme=self.theme['sidebar']['opener']['body'])
        return item
    def construct_sidebar(self, sidebar, **opts):
        if isinstance(sidebar, tuple) and len(sidebar) == 2 and isinstance(sidebar[1], dict):
            opts = dict(sidebar[1], **opts)
            sidebar = sidebar[0]
        elif isinstance(sidebar, dict):
            sidebar = sidebar.copy()
            sb = sidebar['items']
            del sidebar['items']
            opts = dict(sidebar, **opts)
            sidebar = sb
        elif not (isinstance(sidebar, (list, tuple, Component)) or hasattr(sidebar, 'to_widget') or hasattr(sidebar, 'to_tree')):
            sidebar = [sidebar]
        if isinstance(sidebar, (list, tuple)):
            sidebar = Sidebar(
                [self.construct_sidebar_item(h) for h in sidebar],
                **dict({'theme':self.theme['sidebar']['body']}, **opts)
            )
        return sidebar

    def construct_toolbar_item(self, item):
        if isinstance(item, dict):
            item = item.copy()
            var = item['var']
            del item['var']
            item = Control.construct(var, **item)
        return item
    def construct_toolbar(self, toolbar, **opts):
        if not (isinstance(toolbar, (list, tuple, Component)) or hasattr(toolbar, 'to_widget') or hasattr(toolbar, 'to_tree')):
            toolbar = [toolbar]
        if isinstance(toolbar, (list, tuple)):
            if isinstance(toolbar[0], (list, tuple)):
                toolbar = Grid(
                    [[self.construct_toolbar_item(h) for h in row] for row in toolbar],
                    **dict(self.theme['toolbar'], **opts)
                )
            else:
                toolbar = JHTML.Div(
                    [self.construct_toolbar_item(h) for h in toolbar],
                    **dict(self.theme['toolbar'], **opts)
                )
        return toolbar

    def wrap_body(self, fn, **styles):
        # @functools.wraps(fn)
        # def wrapper(event=None, pane=None, **vars):
        #     return fn(event=event, pane=pane, **vars)
        return FunctionDisplay(fn, self.vars, **styles)
    def construct_body_item(self, item):
        if isinstance(item, (types.MethodType, types.FunctionType, types.LambdaType)):
            item = self.wrap_body(item)
        elif not isinstance(item, (str, Component, JHTML.Styled)) and not (hasattr(item, 'to_string') or hasattr(item, 'to_jhtml')):
            try:
                item, styles = item
            except (ValueError, TypeError):
                pass
            else:
                if isinstance(item, (types.MethodType, types.FunctionType, types.LambdaType)):
                    item = self.wrap_body(item, **styles)
                else:
                    item = JHTML.Span(item, **styles)
        return item
    def construct_body(self, body):
        if isinstance(body, dict):
            body = Tabs({k:self.construct_body_item(b) for k,b in body.items()})
        elif isinstance(body, (list, tuple)):
            body = [self.construct_body(b) for b in body]
        else:
            body = self.construct_body_item(body)
        return body

    def construct_layout(self):
        with self:
            if self.layout == 'grid':
                elements = []
                nrows = 0
                ncols = 0

                # if self.header is not None:
                #     nrows += 1
                if self.sidebar is not None:
                    ncols += 1
                if self.toolbar is not None:
                    nrows += 1
                    ncols += 1
                if self.capture_output:
                    nrows += 1
                if self.body is not None:
                    nrows += 1 if not isinstance(self.body, list) else len(self.body)
                    ncols = min(ncols+1, 2)
                # if self.footer is not None:
                #     nrows += 1

                column_width = []
                row_height = []
                if self.header is not None:
                    header = []
                    header.append(Grid.Item(self.header, col_span=ncols))
                    elements.append(header)
                    row_height.append('auto')

                body = []
                if self.sidebar is not None:
                    body.append(Grid.Item(self.sidebar, row_span=nrows))
                    column_width.append('auto')
                if self.toolbar is not None:
                    body.append(self.toolbar)
                    elements.append(body)
                    if self.sidebar is not None:
                        body = [None]
                    else:
                        body = []
                    row_height.append('auto')
                if isinstance(self.body, (list, tuple)):
                    for i,b in enumerate(self.body):
                        body.append(b)
                        if i == 0:
                            row_height.append('1fr')
                            column_width.append('1fr')
                        else:
                            row_height.append('auto')
                        elements.append(body)
                        if self.sidebar is not None:
                            body = [None]
                        else:
                            body = []
                else:
                    body.append(self.body)
                    row_height.append('1fr')
                    column_width.append('1fr')
                    elements.append(body)

                if self.capture_output:
                    output_list = []
                    if self.sidebar is not None:
                        output_list.append(None)
                    output_list.append(Grid.Item(self.output))
                    elements.append(output_list)
                    row_height.append('auto')

                if self.footer is not None:
                    footer = []
                    footer.append(Grid.Item(self.footer, col_span=ncols))
                    elements.append(footer)
                    row_height.append('auto')

                layout = Grid(
                    elements,
                    column_width=column_width,
                    row_height=row_height,
                    cls=self.cls,
                    **self.attrs
                )
            else:
                raise NotImplementedError("ugh")
        return layout

    def to_jhtml(self):
        return self.construct_layout().to_jhtml()
class SettingsPane(App):
    themes = {
        'primary': App.merge_themes(
            App.themes['primary'],
            {'toolbar': dict(cls=['form-check'])}
        )
    }
    def __init__(self, settings, cls=None, **opts):
        super().__init__(
            toolbar=settings,
            cls=cls,
            **opts
        )