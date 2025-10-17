
import abc, weakref, uuid, traceback as tb
import sys
import threading

from .types import *

from ...Misc import mixedmethod
from ..JHTML import JHTML, DefaultOutputWidget
from ..JHTML.WidgetTools import JupyterAPIs, frozendict

class JHTMLConversionError(Exception):
    """
    Represents an error in converting to JHTML
    """
    def __init__(self, widgets, cause, tb, message="failed to convert to JHTML:\n{}"):
        self.widgets = widgets
        self.base_cause = cause
        self.base_tb = tb
        self.message_template = message
        super().__init__(self.format_message())
    def format_message(self, limit=10):
        widget_chain = "\n".join(("  >> " if i > 0 else "") + repr(w) for i,w in enumerate(self.widgets))
        cause = "\n".join(tb.format_exception(None, self.base_cause, self.base_tb, limit=-limit))
        return self.message_template.format(widget_chain + "\n" + cause)

__all__ = [
    "WidgetInterface",
    "GenericDisplay",
    "DelayedResult",
    "Component",
    "WrapperComponent",
    "Container",
    "MenuComponent",
    "ListGroup",
    "Button",
    "LinkButton",
    "Spinner",
    "Progress",
    "ButtonGroup",
    "Navbar",
    "Carousel",
    "Pagination",
    "Sidebar",
    "Dropdown",
    "DropdownList",
    "Tabs",
    "TabPane",
    "TabList",
    "Accordion",
    "AccordionHeader",
    "AccordionBody",
    "Opener",
    "OpenerHeader",
    "OpenerBody",
    "CardOpener",
    "Modal",
    "ModalHeader",
    "ModalBody",
    "ModalFooter",
    "Offcanvas",
    "OffcanvasHeader",
    "OffcanvasBody",
    "Toast",
    "ToastBody",
    "ToastHeader",
    "ToastContainer",
    "Spacer",
    "Breadcrumb",
    "Card",
    "CardHeader",
    "CardBody",
    "CardFooter",
    "ModifierComponent",
    "Tooltip",
    "Popover",
    "Layout",
    "Grid",
    "Table",
    "Flex"
]
__reload_hook__ = ["..JHTML", "..WidgetTools"]

class WidgetInterface(metaclass=abc.ABCMeta):
    """
    Provides the absolute minimum necessary for hooking
    an interface that creates an `ipywidget` into the
    Jupyter display runtime
    """
    @abc.abstractmethod
    def to_widget(self):
        ...
    # @abc.abstractmethod
    def initialize(self):
        ...
    def _ipython_display_(self):
        JupyterAPIs.get_display_api().display(self.to_widget())
        self.initialize()

    _display_locks = set()
    def display(self):
        if self not in self._display_locks: # don't want to call this over and over...
            self._display_locks.add(self)
            try:
                self._ipython_display_()
            finally:
                self._display_locks.remove(self)
    def get_mime_bundle(self):
        return self.to_widget().get_mime_bundle()
    @mixedmethod
    def _ipython_pinfo_(self):
        from ...Docs import jdoc
        return jdoc(self)

class Component(WidgetInterface):
    """
    Provides an abstract base class for an interface element
    to allow for the easy construction of interesting interfaces
    """
    def __init__(self, dynamic=True, debug_pane=None, **attrs):
        super().__init__()
        self._parents = weakref.WeakSet()
        self._widget_cache = None
        attrs['dynamic'] = dynamic
        self._attrs = attrs
        self.debug_pane = DefaultOutputWidget.get_default() if debug_pane is None else debug_pane
    @property
    def attrs(self):
        return frozendict(self._attrs)
    @attrs.setter
    def attrs(self, value):
        self._attrs = value

    def get_attr(self, key):
        return self._attrs[key]
    def get_child(self, key):
        raise NotImplementedError("{} doesn't have children".format(
            type(self).__name__
        ))
    def __getitem__(self, item):
        if isinstance(item, str):
            return self.get_attr(item)
        else:
            return self.get_child(item)

    def set_attr(self, key, value):
        self._attrs[key] = value
    def update_widget_attr(self, key, value):
        self._widget_cache[key] = value
    def set_child(self, which, new):
        raise NotImplementedError("{} doesn't have children".format(
            type(self).__name__
        ))
    def update_widget_child(self, key, value):
        self._widget_cache[key] = value
    def __setitem__(self, key, value):
        if isinstance(key, str):
            self.set_attr(key, value)
            if self._widget_cache is not None:
                self.update_widget_attr(key, value)
        else:
            self.set_child(key, value)
            if self._widget_cache is not None:
                self.update_widget_child(key, value)

    def del_attr(self, key,):
        del self._attrs[key]
    def del_widget_attr(self, key):
        del self._widget_cache[key]
    def del_child(self, which):
        raise NotImplementedError("{} doesn't have children".format(
            type(self).__name__
        ))
    def del_widget_child(self, key):
        del self._widget_cache[key]
    def __delitem__(self, key):
        if isinstance(key, str):
            self.del_attr(key)
            if self._widget_cache is not None:
                self.del_widget_attr(key)
        else:
            self.del_child(key)
            if self._widget_cache is not None:
                self.del_widget_child(key)

    def insert(self, where, new):
        self.insert_child(where, new)
        if self._widget_cache is not None:
            self.insert_widget_child(where, new)
    def append(self, child):
        return self.insert(None, child)

    def insert_child(self, where, child):
        raise NotImplementedError("{} doesn't have children".format(
            type(self).__name__
        ))
    def insert_widget_child(self, where, child):
        self._widget_cache.insert(where, child)

    def add_class(self, *cls):
        self.add_component_class(*cls)
        if self._widget_cache is not None:
            self.add_widget_class(*cls)
    def add_component_class(self, *cls):
        if not 'cls' in self._attrs:
            self._attrs['cls'] = []
        new = self._attrs['cls'].copy()
        for c in cls:
            for y in JHTML.manage_class(c):
                if y not in new:
                    new.append(y)
        self._attrs['cls'] = new
    def add_widget_class(self, *cls):
        return self._widget_cache.add_class(*cls)
    def remove_class(self, *cls):
        self.remove_component_class(*cls)
        if self._widget_cache is not None:
            self.remove_widget_class(*cls)
    def remove_component_class(self, *cls):
        if not 'cls' in self._attrs:
            self._attrs['cls'] = []
        new = self._attrs['cls'].copy()
        for c in cls:
            for y in JHTML.manage_class(c):
                try:
                    new.remove(y)
                except ValueError:
                    pass
        self._attrs['cls'] = new
    def remove_widget_class(self, *cls):
        return self._widget_cache.remove_class(*cls)

    @abc.abstractmethod
    def to_jhtml(self, parent=None):
        ...
    def to_widget(self, parent=None):
        if parent is not None:
            self._parents.add(parent)
        if self._widget_cache is None:
            with DefaultOutputWidget(self.debug_pane):
                try:
                    self._widget_cache = self.to_jhtml()
                except JHTMLConversionError as e:
                    raise JHTMLConversionError(e.widgets + [self], e.base_cause, e.base_tb) from None
                except:
                    _, e, tb = sys.exc_info()
                    raise JHTMLConversionError([self], e, tb) from None
                self._widget_cache.component = self
            # self._widget_cache.to_widget.observe(self.set_value, )
        return self._widget_cache
    def mutate(self, fn):
        fn(self)
        self.invalidate_cache()
    def invalidate_cache(self):
        self._widget_cache = None
        for w in self._parents:
            w.invalidate_cache()
class WrapperComponent(Component):
    """
    Extends the base component interface to allow for the
    construction of interesting compound interfaces (using `JHTML.Compound`).
    Takes a `dict` of `wrappers` naming the successive levels of the interface
    along with a `theme` that provides style declarations for each level.

    Used primarily to create `Bootstrap`-based interfaces.
    """
    wrappers = dict(wrapper=JHTML.Div)
    theme = dict(wrapper={'cls': []})
    def __init__(self,
                 items: ElementType,
                 wrappers=None,
                 theme=None,
                 extend_base_theme=True,
                 **attrs):

        self.items, attrs = self.manage_items(items, attrs)

        if wrappers is None:
            wrappers = self.wrappers
        self.wrappers = wrappers

        wrappers = list(wrappers.items())

        self.theme = self.manage_theme(theme, extend_base_theme=extend_base_theme)
        self.theme[wrappers[0][0]] = self.merge_themes(self.theme.get(wrappers[0][0], {}), attrs)
        if len(wrappers) > 1:
            attrs = {'wrapper_attrs':self.theme}
            self.wrapper = JHTML.Compound(*[
                (key, wrapper)
                for i, (key, wrapper)
                in enumerate(wrappers)
            ])
        else:
            attrs = self.theme[wrappers[0][0]]
            self.wrapper = wrappers[0][1]
        super().__init__(**attrs) # need to delegate attr updates to the theme...

        # self.item_attrs = theme.get(item[0], {})
        # self.item = item[-1]
    def handle_variants(self, theme):
        if 'variant' in theme or 'base-cls' in theme:
            theme = theme.copy()
            cls = theme.get('cls', [])
            if isinstance(cls, str):
                cls = cls.split()
            theme['cls'] = list(cls) + [theme.get('base-cls', cls[0] if len(cls) > 0 else "")+"-"+theme.get('variant', '')]
            try:
                del theme['variant']
            except KeyError:
                pass
            try:
                del theme['base-cls']
            except KeyError:
                pass
        return theme
    def manage_theme(self, theme, extend_base_theme=True):
        if theme is None:
            theme = self.theme
        theme = theme.copy()
        if extend_base_theme:
            for k,v in self.theme.items():
                if k in theme:
                    theme[k] = self.merge_themes(v, theme[k])
                else:
                    theme[k] = self.theme[k].copy()
        return theme
    @classmethod
    def merge_themes(cls, theme: 'None|dict', attrs:dict, merge_keys=('cls',)):
        """
        Needs to handle cases where a `theme` is provided
        which includes things like `cls` declarations and then the
        `attrs` may also include `cls` declarations and the `attrs`
        declarations get appended to the theme
        """

        if theme is None:
            theme = {}
        theme = theme.copy()

        kinter = theme.keys() & attrs.keys()
        if merge_keys is not None:
            kinter = kinter & set(merge_keys)

        for k in attrs:
            if k in kinter:
                if isinstance(theme[k], str):
                    theme[k] = theme[k].split()
                if isinstance(attrs[k], str):
                    attrs[k] = attrs[k].split()
                if attrs[k] is None:
                    attrs[k] = []
                if isinstance(theme[k], dict):
                    theme[k] = cls.merge_themes(theme[k], attrs[k], merge_keys=None)
                else:
                    theme[k] = theme[k] + attrs[k]
            else:
                theme[k] = attrs[k]

        return theme

    @classmethod
    def manage_items(cls, items, attrs):
        if isinstance(items, dict):
            attrs = dict(attrs, **items)
            del attrs['body']
            items = items['body']
        elif (
                isinstance(items, tuple)
                and len(items) == 2
                and isinstance(items[1], dict)
        ):
            attrs = dict(attrs, **items[1])
            items = items[0]
        if (
                isinstance(items, (str, int, float, JupyterAPIs.get_widgets_api().Widget))
                or hasattr(items, 'to_tree')
                or hasattr(items, 'to_widget')
        ):
            items = [items]
        elif items is None:
            items = []
        else:
            items = list(items)
        return items, attrs
    def get_child(self, key):
        return self.items[key]
    def set_child(self, which, new):
        self.items[which] = new
    def insert_child(self, where, child):
        if where is None:
            where = len(self.items)
        self.items.insert(where, child)
    # def add_component_class(self, *cls):
    #     if 'cls' not in self.attrs:
    #         base_cls = None
    #     self.add
    #         self.attrs['cls'] =
    #     new = self.wrapper_classes.copy()
    #     for c in cls:
    #         for y in JHTML.manage_class(c):
    #             if y not in new:
    #                 new.append(y)
    #     self.wrapper_classes = new
    # def remove_component_class(self, *cls):
    #     new = self.wrapper_classes.copy()
    #     for c in cls:
    #         for y in JHTML.manage_class(c):
    #             try:
    #                 new.remove(y)
    #             except ValueError:
    #                 pass
    #     self.wrapper_classes = new

    def wrap_items(self, items):
        if isinstance(self.wrappers, JHTML.Compound):
            attrs = self.attrs.copy()
            wrapper_attrs = self.attrs.get('wrapper_attrs', {}).copy()
            for k,v in wrapper_attrs:
                wrapper_attrs[k] = self.handle_variants(v.copy())
            del attrs['wrapper_attrs']
            return self.wrapper(*items, wrapper_attrs=wrapper_attrs, **attrs)
        else:
            return self.wrapper(*items, **self.handle_variants(self.attrs))
    def to_jhtml(self, parent=None):
        return self.wrap_items(self.items)
class Container(WrapperComponent):
    """
    Extends the base `WrapperComponent` to include a final
    `items` spec for cases where there is a base wrapper and a set of items,
    e.g. a list group which has the `list-group` outer class and a set of `list-items` inside.
    """
    wrappers = dict(wrapper=JHTML.Div, item=JHTML.Span)
    theme = dict(wrapper={'cls':[]}, item={'cls':[]})
    def __init__(self,
                 items: ElementType,
                 wrappers: dict = None,
                 **attrs) -> None:

        if wrappers is None:
            wrappers = self.wrappers
        self.wrappers = wrappers

        wrappers = list(wrappers.items())
        if len(wrappers) == 1:
            wrappers.append([JHTML.Span, {}])
        item = wrappers[-1]
        wrappers = dict(wrappers[:-1])


        self._items = None
        items, attrs = self.manage_items(items, attrs)
        super().__init__(None, wrappers=wrappers, **attrs)
        self._items = items

        self.item_attrs = self.theme.get(item[0], {}).copy()
        self.item = item[-1]

        if isinstance(self.item, dict): # a way to specify a subtheme
            item_wrappers = list(self.item.items())
            item_theme = self.item_attrs
            if len(item_wrappers) > 1:
                self.item_attrs = {k[0]:item_theme.get(k[0], {}) for k in item_wrappers}
                self.item = JHTML.Compound(*[
                    (key, wrapper)
                    for i, (key, wrapper)
                    in enumerate(item_wrappers)
                ])
            else:
                self.item_attrs = item_theme.get(wrappers[0][1], {})
                self.item = item_wrappers[0][1]

    @property
    def items(self):
        return [self.create_item(i) for i in self._items]
    @items.setter
    def items(self, items):
        if self._items is not None:
            raise ValueError("can't set items")
    def _create_dict_item(self, body=None, **extra):
        if isinstance(self.item, JHTML.Compound):
            wrapper_attrs = self.item_attrs.copy()
            for k, v in wrapper_attrs.items():
                wrapper_attrs[k] = self.handle_variants(v)
            n, _ = self.item.destructure_wrapper(self.item.base) # get base name
            if n is not None:
                wrapper_attrs[n] = self.merge_themes(wrapper_attrs.get(n, {}), extra)
            return self.item(body, wrapper_attrs=wrapper_attrs)
        else:
            return self.item(body, **self.merge_themes(self.handle_variants(self.item_attrs), extra))
    def _create_base_item(self, body):
        if isinstance(self.item, JHTML.Compound):
            return self.item(body, wrapper_attrs=self.item_attrs)
        else:
            return self.item(body, **self.item_attrs)
    def create_item(self, i, **kw):
        if isinstance(i, dict):
            if 'raw' in i:
                return i['raw']
            if len(kw) > 0:
                return self._create_dict_item(**dict(i, **kw))
            else:
                return self._create_dict_item(**i)
        else:
            if len(kw) > 0:
                return self._create_dict_item(body=i, **kw)
            else:
               return self._create_base_item(i)

    def update_widget_child(self, key, value):
        super().update_widget_child(key, self.create_item(value))
    def insert_widget_child(self, where, child):
        super().insert_widget_child(where, self.create_item(child))
class ComponentContainer(WrapperComponent):
    components = {}
    def __init__(self, component_args:dict=None, component_kwargs:dict=None,components=None, **attrs):
        super().__init__([], **attrs)
        if components is None:
            components = {}
        self.components = dict(self.components, **components)
        self.component_args = component_args if component_args is not None else {}
        self.component_kwargs = component_kwargs if component_kwargs is not None else {}
    def create_components(self):
        return {
            k:c(
                *self.component_args.get(k, []),
                theme=self.theme.get(k, {}),
                **self.component_kwargs.get(k, {})
            )
            for k,c in self.components.items()
            if not (len(self.component_args.get(k, [])) == 1 and len(self.component_kwargs.get(k, [])) == 0 and self.component_args.get(k, [])[0] is None) # components to ignore
        }
    def handle_variants(self, theme):
        return theme
    def wrap_items(self, items):
        items = list(self.create_components().values())
        return super().wrap_items(items)
class ModifierComponent(Component):
    modifiers = None
    def __init__(self, base=None, **modifiers):
        base_mods = self.modifiers
        if base_mods is None:
            base_mods = {}
        modifiers = dict(base_mods, **modifiers)
        super().__init__(**modifiers)
        self.base = base
    def __call__(self, base):
        if self.base is None:
            self.base = base
        else:
            raise ValueError("{} already has a base object".format(
                self
            ))
        return self
    blacklist = {'dynamic'}
    def to_jhtml(self):
        base = self.base
        if hasattr(base, 'to_jhtml'):
            base = base.to_jhtml()
        for k,v in self.attrs.items():
            if k not in self.blacklist:
                base[k] = v
        return base

class Button(WrapperComponent):
    wrappers = dict(button=JHTML.Bootstrap.Button)
    theme = dict(button={'cls':['btn'], 'variant':'primary'})
    def __init__(self, body, action=None, event_handlers=None, **kwargs):
        if event_handlers is None:
            event_handlers = {}
        self._action = action
        if isinstance(action, (str, dict, list)):
            event_handlers['click'] = action
        else:
            event_handlers['click'] = self._eval
        self._eval_lock = None
        super().__init__(
            body,
            event_handlers=event_handlers,
            **kwargs
        )
    @property
    def action(self):
        return self._action
    @action.setter
    def action(self, a):
        self._action = a
        if isinstance(a, (str, dict, list)):
            self._attrs['event_handlers'] = {'click':a}
            if self._widget_cache is not None:
                self._widget_cache.add_event(click=a)
        else:
            self._attrs['event_handlers'] = {'click':self._eval}
            if self._widget_cache is not None:
                self._widget_cache.add_event(click=self._eval)
    def _eval(self, *args):
        if self.action is not None and self._eval_lock is None:
            self._eval_lock = True
            w = self.to_widget()
            try:
                pane = w.debug_pane
            except AttributeError:
                pane = None
            try:
                if pane is None:
                    self.action(*args)
                else:
                    with pane:
                        self.action(*args)
            finally:
                self._eval_lock = None
class LinkButton(Button):
    wrappers = dict(button=JHTML.Anchor)
    theme = dict(button={'cls':[]})

class Spinner(WrapperComponent):
    wrappers = {'spinner':JHTML.Div}
    theme = {'spinner':{'cls':[], 'base-cls':'spinner', 'variant':'border'}}
    def __init__(self, body=None, role='status', **attrs):
        """
        :param variant:
        :type variant:
        :param attrs:
        :type attrs:
        """
        if body is None:
            body = JHTML.Span("Loading...", cls="visually-hidden")
        super().__init__(body, role=role, **attrs)

class Progress(WrapperComponent):
    wrappers = {'wrapper':JHTML.Div, 'bar':None}
    theme = {'wrapper':{'cls':['progress']}, 'bar':{'cls':['progress-bar']}}
    def __init__(self, value=0, label=None, wrappers=None, **attrs):
        items = []
        if label is True:
            label = str(value) + "%"
        elif not label:
            label = None
        if label is not None:
            items.append(label)
        if wrappers is None:
            wrappers = self.wrappers.copy()
        if 'bar' not in wrappers:
            wrappers['bar'] = None
        if wrappers['bar'] is None:
            wrappers['bar'] = JHTML.Styled(JHTML.Div, width=str(value)+"%", dynamic=True)
        super().__init__(
            items,
            wrappers=wrappers,
            **attrs
        )
    @property
    def container(self):
        return self.to_widget().compound_wrapper_data["container"]
    @property
    def bar(self):
        return self.to_widget().compound_wrapper_data["bar"]
    def update_widget_attr(self, attr, val):
        self.container[attr] = val

#region Menus
class MenuComponent(Container):
    def __init__(self, items:ElementType, **attrs):
        super().__init__(items, **attrs)
        self._item_map = {}
    def create_item(self, item, **kw):
        item = super().create_item(item, **kw)
        if hasattr(item, 'id'):
            self._item_map[item.id] = item
        elif 'id' in item.attrs:
            self._item_map[item.attrs['id']] = item
        return item
class ListGroup(MenuComponent):
    theme = {
        'wrapper':{'cls':['list-group', 'list-group-flush']},
        'item':{'cls':['list-group-item', 'list-group-item-action']}
    }
class ButtonGroup(MenuComponent):
    wrappers = {
        'wrapper':JHTML.Div,
        'item':Button
    }
    theme = {
        'wrapper':{'cls':['btn-group']}
    }
class DropdownList(MenuComponent):
    wrappers = {
        'wrapper': JHTML.Ul,
        'item': {'list-item':JHTML.Li, 'link':JHTML.Anchor}
    }
    theme = {
        'wrapper': {'cls': ['dropdown-menu']},
        'item': {'list-item':{}, 'link':{'cls': ['dropdown-item']}},
    }
    def create_item(self, item, **kw):
        if isinstance(item, dict) and 'action' in item:
            item = item.copy()
            item['event_handlers'] = {'click':item['action']}
            del item['action']
        item = super().create_item(item, **kw)
        return item
class Dropdown(ComponentContainer):
    components = {
        'toggle':Button,
        'list':DropdownList
    }
    theme = {
        'wrapper':{'cls':['dropdown']},
        'toggle':{'button':{'cls':['dropdown-toggle'], 'data-bs-toggle':'dropdown'}}
    }
    def __init__(self, header:ElementType, actions:ElementType, **attrs):
        super().__init__(
            {
                'toggle':(header,),
                'list':(self.prep_actions(actions),)
            },
            **attrs
        )
    def prep_actions(self, actions):
        if isinstance(actions, dict):
            acts = []
            for k,v in actions.items():
                if isinstance(v, tuple) and len(v) == 2 and isinstance(v[1], dict):
                    v, opts = v
                else:
                    opts = {}
                acts.append(dict(opts, body=k, action=v))
            actions = acts
        return actions

class Navbar(MenuComponent):
    wrappers = {
        'wrapper':JHTML.Nav,
        'container':JHTML.Div,
        'nav':JHTML.Div,
        'item':JHTML.Anchor
    }
    theme = {
        'wrapper': {'cls':['navbar', 'navbar-expand']},
        'container': {'cls':['container-fluid']},
        'nav': {'cls':['navbar-nav']},
        'item': {'cls':['nav-link']}
    }
class Sidebar(MenuComponent):
    wrappers = {
        'wrapper': JHTML.Nav,
        'item': {'list-item':JHTML.Li, 'link':JHTML.Anchor}
    }
    theme = {
        'wrapper': {'cls': ['nav', 'flex-column']},
        'item': {
            'list-item': {'cls': ['nav-item']},
            'link': {'cls': ['nav-link']}
        }
    }

class Pagination(MenuComponent):
    wrappers = {
        'wrapper': JHTML.Nav,
        'container': JHTML.Ul,
        'item': {'page-item': JHTML.Li, 'link': JHTML.Anchor}
    }
    theme = {
        'wrapper': {'cls': []},
        'container': {'cls': ['pagination']},
        'item': {
            'page-item': {'cls': ['page-item']},
            'link': {'cls': ['page-link']}
        }
    }


def short_uuid(len=6):
    return str(uuid.uuid4()).replace("-", "")[:len]

class Carousel(MenuComponent):
    wrappers = {
        'wrapper': JHTML.Div,
        'inner': JHTML.Div,
        'item': JHTML.Div
    }
    theme = {
        'wrapper': {'cls': ['carousel']},
        'inner': {'cls': ['carousel-inner']},
        'item': {'cls': ['carousel-item']}
    }
    def __init__(self, items, include_controls=True, data_bs_ride='carousel', interval=None, **attrs):
        self.include_controls = include_controls
        self._active_made = False
        self.base_name = 'carousel-' + short_uuid()
        self.interval = interval
        super().__init__(items, id=self.base_name, data_bs_ride=data_bs_ride, **attrs)
    def create_item(self, item, cls=None, data_bs_interval=None, **kw):
        cls = JHTML.manage_class(cls)
        if not self._active_made:
            cls = cls + ['active']
            self._active_made = True
        if data_bs_interval is None:
            data_bs_interval = str(self.interval) if self.interval is not None else "10000000000"
        return super().create_item(item, cls=cls, data_bs_interval=data_bs_interval, **kw)
    def next_button(self, body=None, cls='carousel-control-next', **kwargs):
        return JHTML.Button(
                    JHTML.Span(cls='carousel-control-next-icon') if body is None else body,
                    **self.merge_themes(dict(cls=cls, data_bs_target='#'+self.base_name, data_bs_slide='next'), kwargs)
                )
    def prev_button(self, body=None, cls='carousel-control-prev', **kwargs):
        return JHTML.Button(
            JHTML.Span(cls='carousel-control-prev-icon') if body is None else body,
            **self.merge_themes(
                dict(cls=cls, data_bs_target='#' + self.base_name, data_bs_slide='prev'),
                kwargs
            )
        )
    def wrap_items(self, items):
        base = super().wrap_items(items)
        if self.include_controls:
            base.append(self.prev_button())
            base.append(self.next_button())
        return base


class TabList(MenuComponent):
    wrappers = {
        'wrapper': JHTML.Ul,
        'item': {'list-item':JHTML.Li, 'tab-button':JHTML.Button}
    }
    theme = {
        'wrapper': {'cls':['nav'], 'variant':'tabs'},
        'item': {'list-item': {'cls':['nav-item']}, 'tab-button': {'cls':['nav-link']}}
    }
    def __init__(self, *args, base_name=None, role="tablist", **kwargs):
        if base_name is None:
            base_name = 'tabs-' + str(uuid.uuid1()).replace("-", "")[:5]
        self.base_name = base_name
        self._active = None
        super().__init__(*args, role=role, **kwargs)
    def create_item(self, item, cls=None, **kw):
        # cls = JHTML.manage_class(cls)
        # if not self._active_made:
        #     cls = cls + ['active']
        #     self._active_made = True
        # if data_bs_interval is None:
        #     data_bs_interval = str(self.interval) if self.interval is not None else "10000000000"
        # return super().create_item(item, cls=cls, data_bs_interval=data_bs_interval, **kw)
        cls = JHTML.manage_class(cls)
        item, _ = item
        item_id = self.base_name+"-"+item.replace(' ', '')
        if self._active is None:
            cls = cls + ['active']
            self._active = item_id
        return super().create_item(item, id=item_id+'-tab', cls=cls, data_bs_target='#'+item_id, data_bs_toggle='tab', **kw)
class TabPane(MenuComponent):
    wrappers = {
        'wrapper': JHTML.Div,
        'item': JHTML.Div
    }
    theme = {
        'wrapper': {'cls': ['tab-content']},
        'item': {'cls': ['tab-pane']}
    }
    def __init__(self, *args, base_name=None, **kwargs):
        if base_name is None:
            base_name = 'tabs-' + short_uuid()
        self.base_name = base_name
        self._active = None
        super().__init__(*args, **kwargs)
    def create_item(self, item, cls=None, **kw):
        key, item = item
        item_id = self.base_name+"-"+key.replace(' ', '')
        cls = JHTML.manage_class(cls)
        if self._active is None:
            cls = cls + ['active']
            self._active = item_id
        item = super().create_item(item, id=item_id, role='tabpanel', cls=cls, **kw)
        return item
class Tabs(ComponentContainer):
    components = {
        'list':TabList,
        'pane':TabPane
    }
    theme = {
        'pane':{},
        'list': {}
    }
    def __init__(self, tabs, base_name=None, **attrs):
        if base_name is None:
            base_name = 'tabs-' + str(uuid.uuid1()).replace("-", "")[:5]
        if isinstance(tabs, dict):
            tabs = tabs.items()
        super().__init__(
            {
                'list': (tabs,),
                'pane': (tabs,)
            },
            {
                'list':dict(id=base_name, base_name=base_name),
                'pane':dict(id=base_name, base_name=base_name)
            },
            **attrs
        )

class AccordionHeader(Container):
    wrapper_classes = ['accordion-header']
    item = JHTML.Button
    item_classes = ['accordion-button']
    def __init__(self, key, base_name=None, **kw):
        self.base_name = base_name
        super().__init__([key], id=self.base_name+'-heading', **kw)
    def create_item(self, i, **kw):
        return super().create_item(i, type='button', data_bs_toggle='collapse', data_bs_target='#'+self.base_name+'-collapse')
class AccordionBody(Container):
    wrapper_classes = ['accordion-collapse', 'collapse']
    item = JHTML.Div
    item_classes = ['accordion-body']
    def __init__(self, key, parent_name=None, base_name=None, **kw):
        self.base_name = base_name
        super().__init__([key], id=self.base_name+'-collapse', data_bs_parent='#'+parent_name, **kw)
class Accordion(MenuComponent):
    wrapper_classes = ['accordion']
    item = JHTML.Div
    item_classes = ['accordion-item']
    header_classes = ['h2']
    def __init__(self, items, base_name=None, header_classes=None, **attrs):
        if base_name is None:
            base_name = 'accordion-' + short_uuid()
        self.base_name = base_name
        if isinstance(items, dict):
            items = items.items()
        self._active = None
        if header_classes is not None:
            self.header_classes = JHTML.manage_class(header_classes)
        super().__init__(items, id=self.base_name, **attrs)
    def create_item(self, item, cls=None, **kw):
        key, item = item
        item_id = self.base_name + "-" + short_uuid(3)
        cls = JHTML.manage_class(cls)
        if self._active is None:
            cls = cls + ['show']
            self._active = item_id
            header_cls = None
        else:
            header_cls = ['collapsed']

        header = AccordionHeader(key, base_name=item_id, item_attrs={'cls':header_cls}, wrapper_classes=self.header_classes)
        body = AccordionBody(item, parent_name=self.base_name, base_name=item_id, cls=cls, **kw)
        return super().create_item([header, body])

class OpenerHeader(Container):
    wrappers = {
        'wrapper':JHTML.Div,
        'item':Button
    }
    theme = {
        'wrapper':{'cls':['collapse-header']},
        'item':{'cls':['accordion-button']},
    }
    def __init__(self, key, base_name=None, **kw):
        self.base_name = base_name
        super().__init__([key], id=self.base_name+'-heading', **kw)
    def create_item(self, i, **kw):
        return super().create_item(i, type='button', data_bs_toggle='collapse', data_bs_target='#'+self.base_name+'-collapse')
class OpenerBody(Container):
    wrappers = {
        'wrapper': JHTML.Div,
        'item': JHTML.Div
    }
    theme = {
        'wrapper': {'cls': ['collapse']},
        'item': {'cls': ['collapse-body']},
    }
    def __init__(self, key, base_name=None, **kw):
        self.base_name = base_name
        super().__init__([key], id=self.base_name+'-collapse', **kw)#, data_bs_parent='#'+parent_name, **kw)
class Opener(MenuComponent):
    wrappers = {
        'wrapper':JHTML.Div,
        'item':JHTML.Div
    }
    theme = {
        'wrapper':{'cls':['opener']},
        'item':{'cls':['opener-item']},
        'header':{},
        'body':{}
    }
    def __init__(self, items, base_name=None, open=False, **attrs):
        if base_name is None:
            base_name = 'opener-' + short_uuid()
        self.base_name = base_name
        self.default_open=open
        if isinstance(items, dict):
            items = items.items()
        super().__init__(items, id=self.base_name, **attrs)
    def create_item(self, item, open=None, **kw):
        key, item = item
        item_id = self.base_name + "-" + short_uuid(3)
        if open is None:
            open = self.default_open

        ht = self.theme.get('header', {}).copy()
        ht['wrapper'] = self.merge_themes(
            ht.get('wrapper', {}),
            {'cls':['collapsed'] if not open else []}
        )
        ht['item'] = self.merge_themes(
            ht.get('item', {}),
            {'cls': ['collapsed'] if not open else []}
        )

        bt = self.theme.get('body', {}).copy()
        bt['wrapper'] = self.merge_themes(
            bt.get('wrapper', {}),
            {'cls': [] if not open else ['show']}
        )

        header = OpenerHeader(key, base_name=item_id, theme=ht)
        body = OpenerBody(item, base_name=item_id, theme=bt, **kw)
        return super().create_item([header, body])
class CardOpener(Opener):
    theme = {
        'wrapper': {'cls': ['opener', 'card', 'border-top-0']},
        'item': {'cls': ['opener-item']},
        "header": {
            'wrapper': {'cls': ['card-header', 'p-0', 'border-bottom-0', 'border-top']},
            'item': {'cls': ['text-dark', 'bg-transparent']}
        },
        "body": {'wrapper': {'cls': ['card-body']}}
    }

class Breadcrumb(MenuComponent):
    wrappers = {
        'wrapper':JHTML.Nav,
        'list':JHTML.Ol,
        'item':JHTML.Li
    }
    theme = {
        'wrapper': {'cls':[]},
        'list': {'cls':['breadcrumb']},
        'item': {'cls':['breadcrumb-item']}
    }

class CardBody(WrapperComponent):
    wrappers = {'wrapper':JHTML.Bootstrap.CardBody}
class CardHeader(WrapperComponent):
    wrappers = {'wrapper':JHTML.Bootstrap.CardHeader}
class CardFooter(WrapperComponent):
    wrappers = {'wrapper':JHTML.Bootstrap.CardFooter}
class Card(ComponentContainer):
    wrappers = {'wrapper':JHTML.Bootstrap.Card}
    components = {
        'header':CardHeader,
        'body':CardBody,
        'footer':CardFooter,
    }
    def __init__(self,
                 *args,
                 header=None,
                 body=None,
                 footer=None,
                 **attrs
                 ):
        if len(args) == 3:
            header, body, footer = args
        elif len(args) == 2:
            header, body = args
        elif len(args) == 1:
            body, = args
        elif len(args) > 0:
            raise NotImplementedError("too many body args")
        super().__init__(
            {
                'header':(header,),
                'body':(body,),
                'footer':(footer,)
            },
            **attrs
        )

class Modal(Container):
    wrapper_classes = ['modal', 'fade']
    subwrappers = [JHTML.Div, JHTML.Div]
    subwrapper_classes = [['modal-dialog', 'modal-dialog-centered'], ['modal-content']]
    def __init__(self,
                 header=None,
                 body=None,
                 footer=None,
                 id=None,
                 tabindex=-1,
                 **attrs
                 ):

        raise NotImplementedError("needs ComponentContainer update")
        items = []
        if header is not None:
            header = ModalHeader(header)
            items.append(header)
        self.header = header
        if body is not None:
            body = ModalBody(body)
            items.append(body)
        self.body = body
        if footer is not None:
            footer = ModalFooter(footer)
            items.append(footer)
        self.footer = footer
        if id is None:
            id = 'modal-'+short_uuid(6)
        self._id = id
        super().__init__(items, id=id, tabindex=tabindex, **attrs)

    trigger_class = JHTML.Bootstrap.Button
    def get_trigger(self, *items, trigger_class=None, data_bs_toggle='modal', data_bs_target=None, **attrs):
        if trigger_class is None:
            trigger_class = self.trigger_class
        if data_bs_target is None:
            data_bs_target = "#"+self._id
        return trigger_class(items, data_bs_toggle=data_bs_toggle, data_bs_target=data_bs_target, **attrs)
    @classmethod
    def close_button(self):
        return JHTML.Button(cls='btn-close', data_bs_dismiss='modal')
class ModalHeader(WrapperComponent):
    wrappers = {'wrapper':JHTML.Div}
    theme = {'wrapper':{'cls':['modal-header']}}
    def __init__(self, items, **attrs):
        items, attrs = self.manage_items(items, attrs)
        items.append(Modal.close_button())
        super().__init__(items, **attrs)
class ModalFooter(WrapperComponent):
    wrappers = {'wrapper':JHTML.Div}
    theme = {'wrapper':{'cls':['modal-footer']}}
class ModalBody(WrapperComponent):
    wrappers = {'wrapper':JHTML.Div}
    theme = {'wrapper':{'cls':['modal-body']}}

class Offcanvas(Container):
    wrapper_classes = ['offcanvas', 'ps-4', 'pt-5', 'pb-5']
    def __init__(self,
                 header=None,
                 body=None,
                 id=None,
                 tabindex=-1,
                 cls=None,
                 placement='start',
                 **attrs
                 ):
        raise NotImplementedError("needs ComponentContainer update")
        items = []
        if header is not None:
            header = OffcanvasHeader(header)
            items.append(header)
        self.header = header
        if body is not None:
            body = OffcanvasBody(body)
            items.append(body)
        self.body = body
        if id is None:
            id = 'offcanvas-'+short_uuid(6)
        self._id = id
        cls = JHTML.manage_class(cls) + ['offcanvas-' + placement]
        super().__init__(items, id=id, tabindex=tabindex, cls=cls, **attrs)

    trigger_class = JHTML.Bootstrap.Button
    def get_trigger(self, *items, trigger_class=None, data_bs_toggle='offcanvas', data_bs_target=None, **attrs):
        if trigger_class is None:
            trigger_class = self.trigger_class
        if data_bs_target is None:
            data_bs_target = "#"+self._id
        return trigger_class(items, data_bs_toggle=data_bs_toggle, data_bs_target=data_bs_target, **attrs)
    @classmethod
    def close_button(self):
        return JHTML.Button(cls='btn-close', data_bs_dismiss='offcanvas')
class OffcanvasHeader(WrapperComponent):
    wrappers = {'wrapper':JHTML.Div}
    theme = {'wrapper':{'cls':['offcanvas-header', 'm-2', 'border-bottom']}}
    def __init__(self, items, **attrs):
        items, attrs = self.manage_items(items, attrs)
        items.append(Offcanvas.close_button())
        super().__init__(items, **attrs)
class OffcanvasBody(WrapperComponent):
    wrappers = {'wrapper':JHTML.Div}
    theme = {'wrapper':{'cls':['offcanvas-body']}}

class Spacer(WrapperComponent):
    wrappers = {'wrapper':JHTML.Span}
    theme = {'wrapper':{'cls':['me-auto']}}
    def __init__(self, items=None, **kwargs):
        if items is None:
            items = []
        super().__init__(items, **kwargs)

ToastAPI = JHTML.JavascriptAPI.loader(
    init="""widget.el.toast = new context.bootstrap.Toast(widget.el)""",
    showToast="""
let id = widget.getAttribute("data-bs-target");
let el = document.querySelector(id);
el.toast.show();
"""
)
class ToastBody(WrapperComponent):
    wrappers = {
        'wrapper':JHTML.Div
    }
    theme = {
        'wrapper': {'cls':['toast-body']}
    }
    def __init__(self, items, include_controls=False, cls=None, **attrs):
        if include_controls:
            cls = JHTML.manage_class(cls) + ['d-flex']
            items, attrs = self.manage_items(items, attrs)
            items.extend([Spacer(), Toast.close_button()])
        super().__init__(items, cls=cls, **attrs)
class ToastHeader(WrapperComponent):
    wrappers = {
        'wrapper':JHTML.Div
    }
    theme = {
        'wrapper': {'cls':['toast-header']}
    }
    def __init__(self, items, include_controls=True, **attrs):
        if include_controls:
            items, attrs = self.manage_items(items, attrs)
            items.extend([Spacer(), Toast.close_button()])
        super().__init__(items, **attrs)
class Toast(WrapperComponent):
    wrappers = {
        'wrapper':JHTML.Div
    }
    theme = {
        'wrapper': {'cls':['toast']}
    }
    def __init__(self,
                 header=None,
                 body=None,
                 role='alert',
                 hidden=True,
                 cls=None,
                 id=None,
                 javascript_handles=None,
                 onevents=None,
                 **attrs
                 ):
        raise NotImplementedError("needs update")
        attrs['role'] = role
        items = []
        only_body = header is not None and body is None
        if only_body:
            body = header
            header = None
        if header is not None:
            items.append(ToastHeader(header))
        if body is not None:
            items.append(ToastBody(body, include_controls=only_body))
        if id is None:
            id = 'toast-'+short_uuid(6)
        self._id = id
        if not hidden:
            cls = JHTML.manage_class(cls) + ['show']
        if javascript_handles is None:
            javascript_handles = ToastAPI.load()
        if onevents is None:
            onevents = {'initialize':'init'}
        super().__init__(items, cls=cls, javascript_handles=javascript_handles, onevents=onevents, id=id, **attrs)

    trigger_class = JHTML.Bootstrap.Button
    def get_trigger(self, *items, trigger_class=None, data_bs_toggle='toast', data_bs_target=None, **attrs):
        if trigger_class is None:
            trigger_class = self.trigger_class
        if data_bs_target is None:
            data_bs_target = "#" + self._id
        return trigger_class(items,
                             data_bs_toggle=data_bs_toggle,
                             data_bs_target=data_bs_target,
                             javascript_handles=self.to_widget().javascript_handles,
                             event_handlers={"click":"showToast"},
                             **attrs
                             )
    @classmethod
    def close_button(self):
        return JHTML.Button(cls='btn-close', data_bs_dismiss='toast')
    def show(self):
        self.add_class('show')
        self.remove_class('hide')
    def hide(self):
        self.remove_class('show')
        self.add_class('hide')
class ToastContainer(WrapperComponent):
    wrappers = {
        'wrapper':JHTML.Div
    }
    theme = {
        'wrapper': {'cls':['toast-container']}
    }
    def __init__(self, items=None, **kwargs):
        if items is None:
            items = []
        super().__init__(items, **kwargs)
    def create_toast(self, header=None, body=None, hidden=False, **kwargs):
        toast = Toast(header=header, body=body, hidden=hidden, **kwargs)
        self.append(toast)
        return toast


#endregion

#region Misc

class Tooltip(ModifierComponent):
    modifiers = dict(
        data_bs_toggle="tooltip",
        data_bs_placement='top',
        javascript_handles={
        "update": """
if (widget.tooltip !== null && widget.tooltip !== undefined) {
    let title = widget.getAttribute('title');
    if (!(title && typeof title === 'object') || title !== this.tooltipTitle) {
        this.callHandler("init", event);
    } else {
        this.tooltip.update();
        this.el.setAttribute("title", "");
    }
}
                """,
        "init": """
let shown=false;
if (widget.tooltip !== null && widget.tooltip !== undefined) {
    if (widget.tooltip.tip !== null) {
        widget.tooltipTitle = null;
        let tip = widget.tooltip.tip;
        shown = tip && tip.classList.contains("show");
        widget.tooltip.dispose();
    }
}
widget.tooltip = new context.bootstrap.Tooltip(widget.el);
widget.tooltip._setContent = widget.tooltip.setContent;
function wrapperSetContent(tip) {
    widget.tooltip._setContent(tip);
    let title = widget.getAttribute('title');
    if (title && typeof title === 'object') {
        if (!(widget.tooltip.tip && title == widget.tooltipTitle)) {
            widget.tooltipTitle = title;
            let bwrap = tip.querySelector('.tooltip-inner');
            if (bwrap) {
                widget.create_child_view(title).then(
                  (view)=>{
                        while (bwrap.lastChild) {
                            bwrap.removeChild(bwrap.lastChild);
                        };
                        bwrap.appendChild(view.el)
                    }
                );
            }
        }
    }
    tip.classList.add('jhtml');
    return tip;
}
widget.tooltip.setContent = wrapperSetContent;
if (shown) {
    let trigger = widget.el.getAttribute("data-bs-trigger");
    if (trigger && trigger.split(' ').includes('click')) {
        widget.el.click();
    } else {
        widget.tooltip.show()
    }
};
""",
        "destroy": """
    if (widget.tooltip !== null && widget.tooltip !== undefined) {
        if (widget.tooltip.tip !== null) {
            widget.tooltip.dispose();
        }
    }"""
        },
        onevents={
            'initialize': "init",
            'view-change:data-bs-trigger': 'init',
            'view-change:data-bs-placement': 'init',
            'view-change:title': 'update',
            'remove': "destroy"
        }
    )
    def __init__(self, base=None, title="tooltip", data_bs_html=None, **kwargs):
        if not isinstance(title, str):
            if hasattr(title, 'tostring'):
                title = title.tostring()
                if data_bs_html is None:
                    data_bs_html = True
            elif hasattr(title, 'to_widget'):
                title = title.to_widget()
                if hasattr(title, 'elem'):
                    title = title.elem
                kwargs['onevents'] = dict(self.modifiers['onevents'], change='init')
                if data_bs_html is None:
                    data_bs_html = True
            elif isinstance(title, JupyterAPIs.get_widgets_api().Widget):
                if data_bs_html is None:
                    data_bs_html = True
            elif hasattr(title, 'to_tree'):
                title = title.to_tree().tostring()
                if data_bs_html is None:
                    data_bs_html = True
            else:
                raise TypeError('tooltip title must be a string')
        if data_bs_html is not None:
            kwargs['data_bs_html'] = data_bs_html
        super().__init__(base, title=title, **kwargs)
class Popover(ModifierComponent):
    modifiers = dict(
        data_bs_toggle="popover",
        data_bs_placement='top',
        data_bs_container='body',
        tabindex="0",
        javascript_handles={
            "update":"""
if (widget.popover !== null && widget.popover !== undefined) {
    let body = widget.getAttribute('data-bs-content');
    if (!(body && typeof body === 'object') || body !== this.popoverBody) {
        this.callHandler("init", event);
    } else {
        let title = widget.getAttribute('title');
        if (!(title && typeof title === 'object') || title !== this.popoverTitle) {
            this.callHandler("init", event);
        } else {
            this.popover.update();
            this.el.setAttribute("title", "")
        }
    }
}
            """,
            "init":"""
let shown=false;
if (widget.popover !== null && widget.popover !== undefined) {
    if (widget.popover.tip !== null) {
        widget.popoverBody = null;
        widget.popoverTitle = null;
        let tip = widget.popover.tip;
        shown = tip && tip.classList.contains("show");
        widget.popover.dispose();
    }
}
widget.popover = new context.bootstrap.Popover(widget.el);
widget.popover._oldGetTipElement = widget.popover.getTipElement;
function wrapperGetElement() {
    let tip = widget.popover._oldGetTipElement();
    let body = widget.getAttribute('data-bs-content');
    if (body && typeof body === 'object') {
        if (body !== widget.popoverBody) {
            widget.popoverBody = body;
            let bwrap = widget.popover.tip.querySelector('.popover-body');
            if (bwrap) {
                widget.create_child_view(body).then(
                  (view)=>{
                        while (bwrap.lastChild) {
                            bwrap.removeChild(bwrap.lastChild);
                        };
                        bwrap.appendChild(view.el)
                    }
                );
            }
        }
    }
    let title = widget.getAttribute('title');
    if (title && typeof title === 'object') {
        if (title !== widget.popoverTitle) {
            widget.popoverTitle = title;
            let bwrap = widget.popover.tip.querySelector('.popover-header');
            if (bwrap) {
                widget.create_child_view(title).then(
                  (view)=>{
                        while (bwrap.lastChild) {
                            bwrap.removeChild(bwrap.lastChild);
                        };
                        bwrap.appendChild(view.el)
                    }
                );
            }
        }
    }
    tip.classList.add('jhtml');
    return tip;
}
widget.popover.getTipElement = wrapperGetElement;
if (shown) {
    const triggers = widget.el.getAttribute("data-bs-trigger").split(' ');
    if (triggers.includes('click')) {
        widget.el.click();
    } else {
        widget.popover.show()
    }
};
""",
                            "destroy":"""
if (widget.popover !== null && widget.popover !== undefined) {
    if (widget.popover.tip !== null) {
        widget.popover.dispose();
    }
}"""},
        onevents={
            'initialize':"init",
            'view-change:data-bs-trigger':'init',
            'view-change:data-bs-placement':'init',
            'view-change:title': 'update',
            'view-change:data-bs-content':'update',
            'remove':"destroy"
        }
    )
    def __init__(self, base=None, body="", data_bs_trigger="hover focus", data_bs_html=None, title=None, **kwargs):
        if title is not None:
            if not isinstance(title, str):
                if hasattr(title, 'tostring'):
                    title = title.tostring()
                    if data_bs_html is None:
                        data_bs_html = True
                elif hasattr(title, 'to_tree'):
                    title = title.to_tree().tostring()
                    if data_bs_html is None:
                        data_bs_html = True
                elif isinstance(title, JupyterAPIs.get_widgets_api().Widget):
                    if data_bs_html is None:
                        data_bs_html = True
                elif hasattr(title, 'to_widget'):
                    title = title.to_widget()
                    if hasattr(title, 'elem'):
                        title = title.elem
                    if data_bs_html is None:
                        data_bs_html = True
                else:
                    raise TypeError('popover title must be a string')
            kwargs['title'] = title
        if not isinstance(body, str):
            if hasattr(body, 'tostring'):
                body = body.tostring()
                if data_bs_html is None:
                    data_bs_html = True
            elif hasattr(body, 'to_tree'):
                body = body.to_tree().tostring()
                if data_bs_html is None:
                    data_bs_html = True
            elif isinstance(body, JupyterAPIs.get_widgets_api().Widget):
                if data_bs_html is None:
                    data_bs_html = True
            elif hasattr(body, 'to_widget'):
                body = body.to_widget()
                if hasattr(body, 'elem'):
                    body = body.elem
                if data_bs_html is None:
                    data_bs_html = True
            else:
                raise TypeError('popover body must be a string')
        if data_bs_trigger is not None:
            kwargs['data_bs_trigger'] = data_bs_trigger
        if data_bs_html is not None:
            kwargs['data_bs_html'] = data_bs_html
        super().__init__(base, data_bs_content=body, **kwargs)

#endregion

#region Layouts

class LayoutItem(Component):
    wrapper = JHTML.Div
    properties = []
    def __init__(self, item, **attrs):
        super().__init__()
        self.item = item
        self.attrs = attrs
    @abc.abstractmethod
    def get_layout_styles(self, **kwargs):
        raise NotImplementedError("LayoutItem is an abstract class")
    def to_jhtml(self):
        attrs = self.attrs
        style = self.get_layout_styles()
        if 'style' in self.attrs:
            style = dict(attrs['style'], **style)
            attrs = attrs.copy()
            del attrs['style']
        wat = self.wrapper(
            self.item,
            style=style,
            **attrs
        )
        return wat
class Layout(Component):
    wrapper = JHTML.Div
    Item = LayoutItem
    def __init__(self, elements, wrapper=None, item_attrs=None, style=None, **attrs):
        super().__init__()
        if item_attrs is None:
            item_attrs = {}
        self.layout_settings, self.elements = self.setup_layout(elements, item_attrs)
        self._style = {} if style is None else style
        self.attrs = attrs
        if wrapper is None:
            wrapper = self.wrapper
        self.wrapper = wrapper
    def wrap_item(self, e, attrs):
        return self.Item(e, **attrs)
    def setup_layout(self, elements, item_attrs):
        return None, [self.wrap_item(e, item_attrs) for e in elements]
    @abc.abstractmethod
    def get_layout_styles(self, **kwargs):
        raise NotImplementedError("Layout is an abstract class")
    @property
    def styles(self):
        return dict(self._style, **self.get_layout_styles())
    def to_jhtml(self):
        return self.wrapper(
            *self.elements,
            style=self.styles,
            **self.attrs
        )

class GridItem(LayoutItem):
    def __init__(self, item,
                 row=None, col=None,
                 row_span=None, col_span=None,
                 alignment=None, justification=None,
                 **attrs
                 ):
        super().__init__(item, **attrs)
        self.row = row
        self.col = col
        self.row_span = row_span
        self.col_span = col_span
        self.alignment = alignment
        self.justification = justification
        self.attrs = attrs
    @classmethod
    def get_grid_styles(cls,
                           row=None, row_span=None,
                           col=None, col_span=None,
                           alignment=None, justification=None
                           ):
        settings = {}
        if row is not None:
            settings['grid-row-start'] = row
            if row_span is not None:
                settings['grid-row-end'] = 'span ' + str(row_span)
        if col is not None:
            settings['grid-column-start'] = col
            if col_span is not None:
                settings['grid-column-end'] = 'span ' + str(col_span)
        if alignment is not None:
            settings['align-self'] = alignment
        if justification is not None:
            settings['justify-self'] = justification
        return settings
    def get_layout_styles(self):
        return self.get_grid_styles(
            row=self.row, row_span=self.row_span,
            col=self.col, col_span=self.col_span,
            alignment=self.alignment, justification=self.justification,
        )
class Grid(Layout):
    Item = GridItem
    def __init__(self, elements,
                 rows=None, cols=None,
                 alignment=None, justification=None,
                 row_spacing=None, col_spacing=None,
                 item_attrs=None,
                 row_height='auto',
                 column_width='1fr',
                 **attrs
                 ):
        super().__init__(elements, item_attrs=item_attrs, **attrs)
        if rows is None:
            rows = self.layout_settings['rows']
        if cols is None:
            cols = self.layout_settings['cols']
        self.rows = rows
        self.cols = cols
        self.alignment = alignment
        self.justification = justification
        self.row_gaps = row_spacing
        self.col_gaps = col_spacing
        self.row_height = row_height
        self.col_width = column_width
    def setup_layout(self, grid, attrs):
        elements = []
        nrows = 0
        ncols = 0
        for i, row in enumerate(grid):
            for j, el in enumerate(row):
                if el is None:
                    continue
                elem = self.wrap_item(el, dict(attrs, row=i+1, col=j+1))
                n = elem.row
                if elem.row_span is not None:
                    n += elem.row_span
                if n > nrows:
                    nrows = n
                m = elem.col
                if elem.col_span is not None:
                    m += elem.col_span
                if m > ncols:
                    ncols = m
                elements.append(elem)
        return {'rows':nrows, 'cols':ncols}, elements
    def wrap_item(self, e, attrs):
        if not isinstance(e, self.Item):
            e = self.Item(e, **attrs)
        elif hasattr(e, 'items'):
            body = e['body']
            e = dict(e)
            del e['body']
            e = self.Item(body, **dict(attrs, **e))
        else:
            if e.row is None:
                e.row = attrs['row']
            if e.col is None:
                e.col = attrs['col']
        return e
    @classmethod
    def get_grid_styles(cls,
                        rows=None,  cols=None,
                        alignment=None, justification=None,
                        row_gap=None, col_gap=None,
                        row_height='1fr', col_width='1fr'
                        ):
        settings = {'display':'grid'}
        if rows is not None:
            if isinstance(row_height, str) and ' ' not in row_height:
                settings['grid-template-rows'] = 'repeat({rows}, {height})'.format(rows=rows, height=row_height) if isinstance(rows, int) else rows
            elif isinstance(row_height, str):
                settings['grid-template-rows'] = row_height
            else:
                settings['grid-template-rows'] = " ".join(row_height)

        if cols is not None:
            if isinstance(col_width, str) and ' ' not in col_width:
                settings['grid-template-columns'] = 'repeat({cols}, {width})'.format(cols=cols, width=col_width) if isinstance(cols, int) else cols
            elif isinstance(col_width, str):
                settings['grid-template-columns'] = col_width
            else:
                settings['grid-template-columns'] = " ".join(col_width)
        if alignment is not None:
            settings['align-items'] = alignment
        if justification is not None:
            settings['justify-items'] = justification
        if row_gap is not None:
            settings['row-gap'] = row_gap
        if col_gap is not None:
            settings['column-gap'] = col_gap
        return settings
    def get_layout_styles(self):
        return self.get_grid_styles(
            rows=self.rows, cols=self.cols,
            alignment=self.alignment, justification=self.justification,
            row_gap=self.row_gaps, col_gap=self.col_gaps,
            row_height=self.row_height, col_width=self.col_width
        )

class TableItem(GridItem):
    def __init__(self, item,
                 row=None, col=None,
                 row_span=None, col_span=None,
                 alignment=None, justification=None,
                 header=False,
                 **attrs
                 ):
        super().__init__(
            item,
            row=row, col=col,
            row_span=row_span, col_span=col_span,
            alignment=alignment, justification=justification,
            **attrs
        )
        self.header = header
    def wrapper(self, item, **kwargs):
        if self.header:
            return JHTML.TableHeading(item, **kwargs)
        else:
            return JHTML.TableItem(item,  **kwargs)
class Table(Grid):
    Item = TableItem
    def __init__(
            self,
            elements,
            rows=None, cols=None,
            alignment=None, justification=None,
            row_spacing=None, col_spacing=None,
            item_attrs=None,
            row_height='1fr',
            column_width='1fr',
            table_headings=None,
            striped=True,
            **attrs
    ):
        self.headings = table_headings
        self.striped = striped
        super().__init__(
            elements,
            rows=rows, cols=cols,
            alignment=alignment, justification=justification,
            row_spacing=row_spacing, col_spacing=col_spacing,
            item_attrs=item_attrs,
            row_height=row_height,
            column_width=column_width,
            **attrs
        )
    def wrapper(self, *elems, cls=None, **attrs):
        if self.striped:
            cls = ['table', 'table-striped'] + JHTML.manage_class(cls)
        else:
            cls = ['table'] + JHTML.manage_class(cls)
        if self.headings is not None:
            elems = [
                JHTML.TableHeader(elems[0], display='contents'),
                JHTML.TableBody(*elems[1:], display='contents')
            ]
        else:
            elems = [JHTML.TableBody(*elems, display='contents')]
        return JHTML.Table(
            *elems,
            cls=cls,
            **attrs
        )

    def setup_layout(self, grid, attrs):
        rows = []
        nrows = 0
        ncols = 0
        has_header = self.headings is not None
        if has_header:
            header = JHTML.TableRow(*[
                self.wrap_item(el, dict(attrs, row=0, col=j+1, header=True))
                for j,el in enumerate(self.headings)
                ],
                display='contents'
            )
            rows.append(header)
            nrows = 1
        for i, row in enumerate(grid):
            tr = []
            if has_header:
                i += 1
            for j, el in enumerate(row):
                if el is None:
                    continue
                elem = self.wrap_item(el, dict(attrs, row=i+1, col=j+1))
                n = elem.row
                if elem.row_span is not None:
                    n += elem.row_span
                if n > nrows:
                    nrows = n
                m = elem.col
                if elem.col_span is not None:
                    m += elem.col_span
                if m > ncols:
                    ncols = m
                tr.append(elem)
            rows.append(JHTML.TableRow(*tr, display='contents'))
        return {'rows':nrows, 'cols':ncols}, rows


class FlexItem(LayoutItem):
    def __init__(self,
                 item,
                 order=None, grow=None,
                 shrink=None, basis=None,
                 alignment=None,
                 **attrs
                 ):
        super().__init__(item, **attrs)
        self.order = order
        self.grow = grow
        self.shrink = shrink
        self.basis = basis
        self.alignment = alignment
    @classmethod
    def get_flex_styles(cls,
                        order=None, grow=None,
                        shrink=None, basis=None,
                        alignment=None
                        ):
        settings = {}
        if order is not None:
            settings['flex-order'] = order
        if grow is not None:
            settings['flex-grow'] = grow
        if shrink is not None:
            settings['flex-shrink'] = shrink
        if basis is not None:
            settings['flex-basis'] = basis
        if alignment is not None:
            settings['align-self'] = alignment
        return settings
    def get_layout_styles(self):
        return self.get_flex_styles(
            order=self.order, grow=self.grow,
            shrink=self.shrink, basis=self.basis,
            alignment=self.alignment
        )
class Flex(Layout):
    Item = FlexItem
    def __init__(self,
                 elements,
                 direction=None, wrap=None,
                 alignment=None, justification=None,
                 content_alignment=None,
                 **attrs
                 ):
        super().__init__(elements, **attrs)
        self.direction = direction
        self.wrap = wrap
        self.content_alignment = content_alignment
        self.alignment = alignment
        self.justification = justification
    @classmethod
    def get_flex_styles(cls,
                        direction=None, wrap=None,
                        alignment=None, justification=None,
                        content_alignment=None
                        ):
        settings = {'display': 'flex'}
        if direction is not None:
            settings['flex-direction'] = direction
        if wrap is not None:
            settings['flex-wrap'] = wrap
        if alignment is not None:
            settings['align-items'] = alignment
        if justification is not None:
            settings['justify-content'] = justification
        if content_alignment is not None:
            settings['align-content'] = content_alignment
        return settings
    def get_layout_styles(self):
        return self.get_flex_styles(
            direction=self.direction, wrap=self.wrap,
            alignment=self.alignment, justification=self.justification,
            content_alignment=self.content_alignment
        )

#endregion


class GenericDisplay(WidgetInterface):
    def __init__(self, obj):
        self.obj = obj
    def to_widget(self):
        if hasattr(self.obj, 'to_widget'):
            res = self.obj.to_widget()
        else:
            res = JHTML.OutputArea(autoclear=True)
            res.show_buffered(self.obj)
            # with res:
            # res.show_buffered(self.obj)
            # with res:
            #     if hasattr(self.obj, '_ipython_display_'):
            #         self.obj._ipython_display_()
            #     else:
            #         JupyterAPIs.get_display_api().display(self.obj)
        return res

class ResultTypes:
    NoResult = "NoResult"
class DelayedResult(WidgetInterface):

    NoResult = ResultTypes.NoResult

    def __init__(self, func, *args,
                 output=None,
                 callback=None,
                 parent=None,
                 **kwargs
                 ):
        self.output = self.get_output_area(output)
        self.caller = (func, args, kwargs)
        self._thread = None
        self.result = self.NoResult
        self.error = None
        self.callback = callback
        self.parent = parent

    def get_output_area(self, output=None):
        if output is None:
            output = JHTML.OutputArea()
        return output

    def __enter__(self):
        self.output.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.output.__exit__()

    def _run(self):
        # with self.output:
        try:
            res = self.caller[0](*self.caller[1], **self.caller[2], runner=self)
        except Exception as e:
            self.error = e
            with self.output:
                raise
        else:
            self.result = res
            # with self.output:
            try:
                if hasattr(res, 'to_widget'):
                    res = res.to_widget()
                self.output.show_buffered(res)
                # with self.output:
                #     if hasattr(res, '_ipython_display_'):
                #         res._ipython_display_()
                #     else:
                #         JupyterAPIs.get_display_api().display(res)
            except:
                with self.output:
                    raise

        if self.callback is not None:
            self.callback(self.result, self.error, self)

    def start_process(self):
        if self._thread is None:
            self._thread = threading.Thread(target=self._run)
            self._thread.start()
        return self._thread

    def to_widget(self):
        self.start_process()
        return self.output