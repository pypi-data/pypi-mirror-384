
__all__ = [
    "JupyterAPIs",
    "DefaultOutputWidget"
]

class JupyterAPIs:
    """
    Provides access to the various Jupyter APIs
    """

    _apis = None
    @classmethod
    def load_api(cls):
        try:
            import IPython as base
        except ImportError:
            base = None

        try:
            import IPython.core.interactiveshell as shell
        except ImportError:
            shell = None
        try:
            import IPython.core.display as display
        except ImportError:
            display = None
        try:
            import ipywidgets as widgets
            widgets.Output
        except ImportError:
            widgets = None
        try:
            import ipyevents as events
        except ImportError:
            events = None

        cls._apis = (
            display,
            widgets,
            events,
            shell,
            base
        )

    @classmethod
    def get_shell_api(cls):
        if cls._apis is None:
            cls.load_api()
        return cls._apis[3]
    @classmethod
    def get_shell_instance(cls):
        return cls.get_shell_api().InteractiveShell.instance()

    @classmethod
    def get_base_api(cls):
        if cls._apis is None:
            cls.load_api()
        return cls._apis[4]
    @classmethod
    def in_jupyter_environment(cls):
        base = cls.get_base_api()
        if base is None:
            return False
        else:
            shell = base.get_ipython().__class__.__name__
            return 'zmq' in shell.lower()

    @classmethod
    def get_display_api(cls):
        if cls._apis is None:
            cls.load_api()
        return cls._apis[0]

    @property
    def display_api(self):
        return self.get_display_api()

    @classmethod
    def get_widgets_api(self):
        if self._apis is None:
            self.load_api()
        return self._apis[1]

    @property
    def widgets_api(self):
        return self.get_widgets_api()

    @classmethod
    def get_events_api(self):
        if self._apis is None:
            self.load_api()
        return self._apis[2]

    @property
    def events_api(self):
        return self.get_events_api()

    # @classmethod
    # def raw_html(cls, html):
    #     return cls.get_widgets_api().HTML(html)
    # @classmethod
    # def raw_markdown(cls, markdown):
    #     out = cls.get_widgets_api().Output()
    #     out.append_display_data(cls.get_display_api().Markdown(markdown))
    #     return out

class DefaultOutputWidget:
    _output_area_stack = []
    def __init__(self, obj=None):
        self.obj = JupyterAPIs.get_widgets_api().Output() if obj is None else obj
    @classmethod
    def get_default(cls):
        if len(cls._output_area_stack) == 0:
            return JupyterAPIs.get_widgets_api().Output()
        else:
            return cls._output_area_stack[-1]
    def __enter__(self):
        new = self.obj
        self._output_area_stack.append(new)
        return new
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._output_area_stack.pop()
    def __call__(self, *args, **kwargs):
        return self.get_default()

class frozendict(dict):
    def __hash__(self):
        return hash(tuple(self.values())) + hash(tuple(self.keys()))
    def __setitem__(self, key, value):
        raise TypeError("`frozendict` is immutable")