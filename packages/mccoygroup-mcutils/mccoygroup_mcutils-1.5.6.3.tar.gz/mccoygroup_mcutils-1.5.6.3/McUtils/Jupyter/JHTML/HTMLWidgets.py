import os.path, pathlib
import sys
import weakref, io, asyncio, threading, time
from .HTML import CSS, HTML, HTMLManager
from .WidgetTools import JupyterAPIs, DefaultOutputWidget

__all__ = [
    "HTMLWidgets",
    "ActiveHTMLWrapper"
]

__reload_hook__ = [".HTML", ".WidgetTools"]

class ActiveHTMLWrapper:
    base=None
    _subwrappers = weakref.WeakKeyDictionary()
    # to keep anonymous wrappers alive until their elements go out of scope
    def __init__(self,
                 *elements,
                 tag=None,
                 cls=None,
                 id=None,
                 value=None,
                 style=None,
                 event_handlers=None,
                 javascript_handles=None,
                 onevents=None,
                 data=None,
                 debug_pane=None,
                 track_value=None,
                 continuous_update=None,
                 **attributes
                 ):
        HTMLElement = self.load_HTMLElement()
        self.HTMLElement = HTMLElement

        if len(elements) == 1 and isinstance(elements[0], (list, tuple)):
            elements = elements[0]

        #pre-prune
        attrs = {}
        if '_debugPrint' in attributes:
            attrs['_debugPrint'] = attributes['_debugPrint']
            del attributes['_debugPrint']
        if 'trackInput' in attributes:
            if track_value is None:
                track_value = attributes['trackInput']
            del attributes['trackInput']
        if track_value is not None:
            attrs['trackInput'] = track_value
        if 'continuousUpdate' in attributes:
            if continuous_update is None:
                continuous_update = attributes['continuousUpdate']
            del attributes['continuousUpdate']
        if continuous_update is not None:
            attrs['continuousUpdate'] = continuous_update

        self._handle_api = None
        if javascript_handles is not None:
            if hasattr(javascript_handles, 'javascript_handles'):
                self._handle_api = javascript_handles
                attrs['jsAPI'] = javascript_handles.elem
            else:
                if javascript_handles is not None and 'api' in javascript_handles:
                    javascript_handles = javascript_handles.copy()
                    self._handle_api = javascript_handles['api']
                    attrs['jsAPI'] = javascript_handles['api'].elem
                    del javascript_handles['api']
                attrs['jsHandlers'] = javascript_handles

        if self.base is not None:
            shadow_el = self.base(cls=cls, style=style, **attributes)
        else:
            shadow_el = None

        attributes = HTMLManager.manage_attrs(attributes)
        if tag is None and hasattr(shadow_el, 'tag'):
            tag = shadow_el.tag
        if tag is not None:
            attrs['tagName'] = tag

        if shadow_el is not None:
            if 'class' in shadow_el.attrs:
                cls = shadow_el['class']
        if cls is not None:
            classList = HTMLManager.manage_class(cls)
            attrs['classList'] = classList

        eventPropertiesDict = {}
        if event_handlers is not None:
            event_handlers = event_handlers.copy()
            for c, v in event_handlers.items():
                if isinstance(v, dict):
                    v = v.copy()
                    if 'callback' in v:
                        callback = v['callback']
                        del v['callback']
                        event_handlers[c] = callback
                        v['notify'] = True
                    else:
                        event_handlers[c] = None
                    eventPropertiesDict[c] = v
                elif isinstance(v, str):
                    eventPropertiesDict[c] = v
                    event_handlers[c] = None
                else:
                    eventPropertiesDict[c] = None
                    event_handlers[c] = v
        if len(eventPropertiesDict) > 0:
            attrs['eventPropertiesDict'] = eventPropertiesDict

        if onevents is not None:
            if event_handlers is None:
                event_handlers = {}
            for c,v in onevents.items():
                if isinstance(v, dict):
                    v = v.copy()
                    if 'callback' in v:
                        callback = v['callback']
                        del v['callback']
                        event_handlers[c] = callback
                        v['notify'] = True
                    else:
                        event_handlers[c] = None
                    onevents[c] = v
                elif isinstance(v, str):
                    onevents[c] = v
                    event_handlers[c] = None
                else:
                    onevents[c] = None
                    event_handlers[c] = v
            if len(onevents) > 0:
                attrs['onevents'] = onevents

        if not isinstance(elements, (list, tuple)):
            val = elements
            if isinstance(val, str):
                attrs['innerHTML'] = val
            elif isinstance(val, HTML.XMLElement):
                val.add_update_callback(
                    lambda w,*_,s=self:setattr(s, 'html', w) if hasattr(s, 'elem') else None
                )
                attrs['innerHTML'] = val.tostring()
            else:
                attrs['children'] = [self.canonicalize_widget(val)]
        elif len(elements) == 1:
            val = elements[0]
            if isinstance(val, str):
                attrs['innerHTML'] = val
            elif isinstance(val, HTML.XMLElement):
                val.add_update_callback(
                    lambda w,*_,s=self:setattr(s, 'html', w) if hasattr(s, 'elem') else None
                )
                attrs['innerHTML'] = val.tostring()
            else:
                attrs['children'] = [self.canonicalize_widget(val)]
        else:
            elements = [self.canonicalize_widget(x) for x in elements]
            attrs['children'] = elements
        if id is not None:
            attrs['id'] = id
        if value is not None:
            attrs['value'] = value

        extra_styles, attributes = HTMLManager.extract_styles(attributes)
        if shadow_el is not None:
            if 'style' in shadow_el.attrs:
                extra_styles = shadow_el['style']
            else:
                extra_styles = {}

        if style is None:
            style = extra_styles
        else:
            for k,v in extra_styles.items():
                if k in style and style[k] != v:
                    raise ValueError("style {} given twice".format(k))
                style[k] = v
        if len(style) > 0:
            style = HTMLManager.manage_styles(style).props
            # if isinstance(style, str):
            #     style = CSS.parse(style).props
            # elif isinstance(style, CSS):
            #     style = style.props
            attrs['styleDict'] = style

        if len(attributes) > 0:
            attrs['elementAttributes'] = attributes

        if data is not None:
            attrs['exportData'] = data

        self.elem = HTMLElement(**attrs)
        self.link(self.elem)
        self._html_cache = None

        if debug_pane is None:
            debug_pane = DefaultOutputWidget.get_default()
        self.debug_pane = debug_pane

        self._event_handlers = {} if event_handlers is None else event_handlers
        if len(eventPropertiesDict) > 0:
            self.elem.bind_callback(self.handle_event)
        # if eventPropertiesDict
        # for e in event_handlers:
        #     eventPropertiesDict[e] = None
    def __call__(self, *elems, **kwargs):
        return type(self)(
            self.elements + list(*elems),
            tag=self.tag,
            cls=self.class_list,
            style=self.style,
            event_handlers=self.event_handlers,
            onevents=self.onevents,
            javascript_handles=self.javascript_handles,
            value=self.value,
            id=self.id,
            debug_pane=self.debug_pane,
            track_value=self.track_value,
            continuous_update=self.continuous_update,
            **dict(self.attrs, **kwargs)
        )
    @classmethod
    def canonicalize_widget(cls, x):
        if isinstance(x, HTML.XMLElement.atomic_types):
            x = str(x)
        Widget = JupyterAPIs.get_widgets_api().Widget
        if isinstance(x, Widget):
            return x
        elif isinstance(x, ActiveHTMLWrapper):
            elem = x.elem
            cls._subwrappers[elem] = x
            return elem
        elif isinstance(x, str):
            return cls.canonicalize_widget(HTML.parse(x, strict=False))
        elif isinstance(x, HTML.XMLElement):
            subwrapper = ActiveHTMLWrapper.from_HTML(x)
            elem = subwrapper.elem
            cls._subwrappers[elem] = subwrapper
            return elem
        elif hasattr(x, 'to_widget'):
            return cls.canonicalize_widget(x.to_widget())
        else:
            raise NotImplementedError("don't know what to do with object {} of type {}".format(
                x, type(x)
            ))
    @classmethod
    def from_HTML(cls, x:HTML.XMLElement, event_handlers=None, debug_pane=None, **props):
        attrs = x.attrs
        props["event_handlers"] = event_handlers
        props["debug_pane"] = debug_pane
        for key, target in [("cls", "class")]:
            if target in attrs:
                props[key] = attrs[target]
                del attrs[target]
        props = dict(props, **attrs)
        body = []
        for y in x.elems:
            if hasattr(y, 'tostring'):
                # if hasattr(y, 'to_widget'):
                #     raise ValueError(y)
                # try:
                y = y.tostring()
                # except:
                #     raise Exception(y)
            body.append(y)

        new = cls(*body, tag=x.tag, **props)
        return new

    @classmethod
    def load_HTMLElement(cls):
        from .ActiveHTMLWidget import HTMLElement
        return HTMLElement
    @classmethod
    def convert_child(cls, c):
        HTMLElement = cls.load_HTMLElement()
        if isinstance(c, ActiveHTMLWrapper):
            return c.to_html()
        elif isinstance(c, HTMLElement):
            if hasattr(c, 'wrappers'):
                w = next(iter(c.wrappers))
                return w.to_html()
            else:
                try:
                    wrapper_cls = HTMLWidgets.get_class_map()[c.tagName]
                except KeyError:
                    wrapper_cls = lambda *elems, tag=c.tagName, **attrs: cls(*elems, tag=tag, **attrs)

                body = []
                if c.innerHTML != "":
                    body.append(c.innerHTML)
                elif c.textContent != "":
                    body.append(c.textContent)
                else:
                    body = [cls.convert_child(x) for x in c.children]
                attrs = c.elementAttributes.copy()
                if c.value != "":
                    attrs['value'] = c.value
                if c.id != "":
                    attrs["id"] = c.id
                if len(c.classList) > 0:
                    attrs["cls"] = c.classList
                if len(c.styleDict) > 0:
                    attrs["style"] = c.styleDict

                new_el = wrapper_cls(*body, **attrs)
                return new_el.to_html()
        elif isinstance(c, JupyterAPIs.get_widgets_api().Widget):
            html = HTML.XMLElement("jwidget", id=c.model_id)
            html.mirror = c
            return html
        elif isinstance(c, HTML.XMLElement):
            return c
        else:
            raise ValueError("don't know how to convert {} {}".format(type(c), HTMLElement))
    def to_html(self):
        try:
            wrapper_cls = HTML.get_class_map()[self.tag]
        except KeyError:
            wrapper_cls = lambda *elems, **attrs: HTML.XMLElement(self.tag, *elems, **attrs)

        # raise Exception(wrapper_cls, self.tag)
        attrs = self.attrs.copy()
        if self.value is not None:
            attrs['value'] = self.value
        if self.id is not None:
            attrs["id"] = self.id
        if len(self.class_list) > 0:
            attrs["class"] = self.class_list
        if len(self.style) > 0:
            attrs["style"] = self.style

        if self.html is not None:
            html = wrapper_cls(self.html, **attrs)
        elif self.text is not None:
            html = wrapper_cls(self.text, **attrs)
        else:
            html = wrapper_cls(
                *(self.convert_child(x) for x in self.children),
                **attrs
            )
        html.mirror = self
        return html

    def find(self, path, find_mirror=True):
        base = self.to_html().find(path)
        if find_mirror and base is not None:
            base = base.mirror
        return base
    def findall(self, path, find_mirror=True):
        base = self.to_html().findall(path)
        if find_mirror and base is not None:
            base = [b.mirror for b in base]
        return base
    def iterfind(self, path, find_mirror=True):
        bases = self.base.iterfind(path)
        for b in bases:
            if find_mirror and b is not None:
                b = b.mirror
            yield b
    def find_by_id(self, id, mode='first', parent=None, find_mirror=True):
        base = self.to_html().find_by_id(id, mode=mode, parent=parent)
        if find_mirror and base is not None:
            base = base.mirror
        return base

    # def to_tree(self, root=None, parent=None):
    #     if parent is not None:
    #         self._parents.add(parent)
    #     if self._tree_cache is None:
    #         ...
    #         if root is None:
    #             root = ElementTree.Element('root')
    #         attrs = self.construct_etree_attrs(self.attrs)
    #         my_el = ElementTree.SubElement(root, self.tag, attrs)
    #         if all(isinstance(e, str) for e in self.elems):
    #             my_el.text = "\n".join(self.elems)
    #         else:
    #             for elem in self.elems:
    #                 self.construct_etree_element(elem, my_el, parent=self)
    #         self._tree_cache = my_el
    #     elif root is not None:
    #         if self._tree_cache not in root:
    #             root.append(self._tree_cache)
    #     return self._tree_cache
    def to_widget(self, parent=None):
        return self.elem
    def __repr__(self):
        body = (
            self.children if len(self.children) > 0
            else self.html_string if self.html_string is not None
            else self.text if self.text is not None
            else ""
        )
        return "{}({}, {!r}, cls={}, style={}, id={})".format(
            type(self).__name__,
            self.tag,
            body,
            self.class_list,
            self.style,
            self.id
        )
    def display(self):
        wrapper = HTMLWidgets.Div(self, cls='jhtml')
        return JupyterAPIs.get_display_api().display(wrapper.elem)
    def _ipython_display_(self):
        return self.display()
    def get_mime_bundle(self):
        w = HTMLWidgets.Div(self, cls='jhtml').elem
        plaintext = repr(self)
        if len(plaintext) > 110:
            plaintext = plaintext[:110] + '…'
        data = {
            'text/plain': plaintext,
        }
        if w._view_name is not None:
            # The 'application/vnd.jupyter.widget-view+json' mimetype has not been registered yet.
            # See the registration process and naming convention at
            # http://tools.ietf.org/html/rfc6838
            # and the currently registered mimetypes at
            # http://www.iana.org/assignments/media-types/media-types.xhtml.
            data['application/vnd.jupyter.widget-view+json'] = {
                'version_major': 2,
                'version_minor': 0,
                'model_id': w._model_id
            }
        return data

    @staticmethod
    def _handle_event(e, event_handlers, self):
        try:
            handler = event_handlers[e['type']]
        except KeyError:
            pass
        else:
            handler(e, self)
    def handle_event(self, e):
        with self.debug_pane:
            return self._handle_event(e, self.event_handlers, self)

    def link(self, elem):
        if not hasattr(elem, 'wrappers'):
            elem.wrappers = weakref.WeakSet()
        elem.wrappers.add(self)
        def wrapper():
            return next(iter(elem.wrappers))
        elem.wrapper = wrapper

    # add an API to make the elem look more like regular HTML
    @property
    def tag(self):
        return 'div' if self.elem.tagName == '' else self.elem.tagName
    @property
    def id(self):
        eid = self.elem.id
        return None if eid == "" else eid
    @id.setter
    def id(self, val):
        if val is None:
            val = ""
        self.elem.id = val
    @property
    def text(self):
        eid = self.elem.textContent
        return None if eid == "" else eid
    @text.setter
    def text(self, val):
        self.elem.children = []
        self.html_string = ""
        self.elem.textContent = val
        self.elem.send_state('children')
    @property
    def value(self):
        eid = self.elem.value
        return None if eid == "" else eid
    @value.setter
    def value(self, val):
        if val is None:
            val = ""
        self.elem.value = val
    @property
    def attrs(self):
        return self.elem.elementAttributes
    @attrs.setter
    def attrs(self, val):
        if "id" in val:
            self.elem.id = val['id']
            del val['id']
        if "value" in val:
            self.elem.value = val['value']
            del val['value']
        if "javascript_handles" in val:
            self.javascript_handles = val
            del val['javascript_handles']
        val = HTMLManager.manage_attrs(val)
        if "class" in val:
            self.elem.classList = HTMLManager.manage_class(val['class'])
            self.elem.send_state('classList')
            del val['class']
        if "style" in val:
            self.elem.styleDict = HTMLManager.manage_styles(val["style"]).props
            del val['style']
            self.elem.send_state('styleDict')
        self.elem.elementAttributes = val

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.get_attribute(item)
        else:
            return self.get_child(item)
    def __setitem__(self, item, value):
        if isinstance(item, str):
            self.set_attribute(item, value)
        else:
            self.set_child(item, value)
    def __delitem__(self, item):
        if isinstance(item, str):
            self.del_attribute(item)
        else:
            self.del_child(item)
    def get_attribute(self, key):
        if key == "id":
            return self.id
        elif key == "value":
            return self.value
        elif key == "style":
            return self.style
        elif key == "javascript_handles":
            return self.javascript_handles
        elif key == "event_handlers":
            return self.event_handlers
        elif key == "onevents":
            return self.onevents
        else:
            key = HTMLManager.clean_key(key)
            if key == "class":
                return self.class_list
            if key in CSS.known_properties:
                return self.elem.styleDict[key]
            else:
                return self.elem.elementAttributes[key]
    def set_attribute(self, key, value):
        if key == "id":
            self.id = value
        elif key == "value":
            self.value = value
        elif key == "javascript_handles":
            self.javascript_handles = value
        elif key == "event_handlers":
            self.event_handlers = value
        elif key == "onevents":
            self.onevents = value
        elif key == "style":
            self.elem.styleDict = HTMLManager.manage_styles(value)
            self.elem.send_state('styleDict')
        else:
            key = HTMLManager.clean_key(key)
            if key == "class":
                self.class_list = value
            elif key in CSS.known_properties:
                self.elem.styleDict[key] = value
                self.elem.send_state('styleDict')
            else:
                attrs = self.elem.elementAttributes
                attrs[key] = value
                self.elem.elementAttributes = attrs
                self.elem.send_state('elementAttributes')
    def del_attribute(self, key):
        if key == "id":
            self.id = None
        elif key == "value":
            self.value = None
        elif key == "style":
            self.elem.styleDict = {}
            self.elem.send_state('styleDict')
        elif key == "javascript_handles":
            self.javascript_handles = None
        elif key == "event_handlers":
            self.event_handlers = None
        elif key == "onevents":
            self.onevents = None
        else:
            key = HTMLManager.clean_key(key)
            if key == "class":
                self.elem.classList = []
                self.elem.send_state('classList')
            elif key in CSS.known_properties:
                del self.elem.styleDict[key]
                self.elem.send_state('styleDict')
            else:
                del self.elem.elementAttributes[key]
                self.elem.send_state('elementAttributes')
    def get_child(self, position, wrapper=False):
        kids = self.elem.children
        if len(kids) == 0:
            body = self.html
            if body is None:
                raise IndexError("element {} has no body to index".format(self))
            val = body[position]
        else:
            val = kids[position]
        if wrapper and hasattr(val, 'wrappers'):
            return next(iter(val.wrappers))
        else:
            return val
    def set_child(self, position, value):
        kids = self.elem.children
        if len(kids) == 0:
            body = self.html
            if body is None:
                raise IndexError("element {} has no body to index".format(self))
            body[position] = value
        else:
            kids[position] = self.canonicalize_widget(value)
            self.children = kids
            # self.elem.children = kids
            # self.elem.send_state('children')
    def insert(self, where, child):
        kids = self.elem.children
        if len(kids) == 0:
            body = self.html
            if body is None:
                kids = list(kids)
                kids.insert(0, self.canonicalize_widget(child))
                self.children = tuple(kids)
            elif isinstance(child, (str, HTML.XMLElement)):
                body.insert(where, child)
            else:
                self.activate_body()
                self.insert(where, child)
        else:
            kids = list(kids)
            if where is None:
                where = len(kids)
            kids.insert(where, self.canonicalize_widget(child))
            self.children = tuple(kids)
    def append(self, child):
        self.insert(None, child)
    def del_child(self, position):
        kids = self.elem.children
        if len(kids) == 0:
            body = self.html
            if body is None:
                raise IndexError("element {} has no body to index".format(self))
            del body[position]
        else:
            del kids[position]
            self.children = kids
            # self.elem.children = kids
            # self.elem.send_state('children')
    def activate_body(self):
        html = self.html
        self.html_string = ""
        self.children = [self.canonicalize_widget(html)]
    @property
    def elements(self):
        kids = self.elem.children
        if len(kids) == 0:
            kids = []
            if self.text is not None:
                kids.append(self.text)
            elif self.html_string is not None:
                kids.append(self.html_string)
        return kids
    @property
    def children(self):
        return self.elem.children
    @children.setter
    def children(self, kids):
        self.elem.children = kids
        self.elem.send_state('children')
    @property
    def html_string(self):
        eid = self.elem.innerHTML
        return None if eid == "" else eid
    @html_string.setter
    def html_string(self, val):
        if len(self.elem.children) > 0:
            self.elem.children = []
        self.elem.innerHTML = val
        self._html_cache = None
    @property
    def html(self):
        if self._html_cache is None:
            self._html_cache = self.load_HTML()
        return self._html_cache
    @html.setter
    def html(self, html):
        self._html_cache = html
        self.html_string = html.tostring()
        self._html_cache = html
    def _track_html_change(self, *_):
        html = self._html_cache
        self.html_string = html.tostring()
        self._html_cache = html
    def load_HTML(self):
        html_base = self.html_string
        if html_base is not None:
            html_base = HTML.parse(html_base, strict=False)
            html_base.on_update = self._track_html_change
        return html_base

    @property
    def javascript_handles(self):
        if self._handle_api is None:
            return self.elem.jsHandlers
        else:
            return self._handle_api
    @javascript_handles.setter
    def javascript_handles(self, js):
        if hasattr(js, 'javascript_handles'):
            self._handle_api = js
            self.elem.jsAPI = js.elem
            self.elem.send_state('jsAPI')
        else:
            if js is not None and 'api' in js:
                js = js.copy()
                self._handle_api = js['api']
                self.elem.jsAPI = js['api'].elem
                self.elem.send_state('jsAPI')
                del js['api']
            else:
                self._handle_api = None
            self.elem.jsHandlers = js
            self.elem.send_state('jsHandlers')
    @property
    def class_list(self):
        return self.elem.classList
    @class_list.setter
    def class_list(self, cls):
        self.elem.classList = HTMLManager.manage_class(cls)
        self.elem.send_state('classList')
    def add_class(self, *cls):
        cl = self.elem.classList
        cur_len = len(cl)
        proper_classes = []
        for c in cls:
            proper_classes.extend(HTMLManager.manage_class(c))
        for c in proper_classes:
            if c not in cl:
                cl.append(c)
        if len(cl) > cur_len:
            self.elem.classList = cl
            self.elem.send_state('classList')
        return self
    def remove_class(self, *cls):
        cl = self.elem.classList
        cur_len = len(cl)
        proper_classes = []
        for c in cls:
            proper_classes.extend(HTMLManager.manage_class(c))
        for c in proper_classes:
            if c in cl:
                cl.remove(c)
        if len(cl) < cur_len:
            self.elem.classList = cl
            self.elem.send_state('classList')
        return self

    @property
    def style(self):
        return self.elem.styleDict
    @style.setter
    def style(self, style):
        self.elem.classList = HTMLManager.manage_styles(style).props
        self.elem.send_state('styleDict')
    def add_styles(self, **sty):
        sd = self.elem.styleDict
        for c,v in sty.items():
            sd[c] = v
        self.elem.styleDict = sd
        self.elem.send_state('styleDict')
    def remove_styles(self, *sty):
        sd = self.elem.styleDict
        for c in sty:
            if c in sd:
                del sd[c]
        self.elem.styleDict = sd
        self.elem.send_state('styleDict')

    @property
    def data(self):
        return self.elem.exportData
    @data.setter
    def data(self, d:dict):
        self.elem.exportData = d

    @property
    def event_handlers(self):
        return {
            k: self._event_handlers[k] if self._event_handlers[k] is not None else v
            for k, v in self.elem.eventPropertiesDict.items()
        }
    @event_handlers.setter
    def event_handlers(self, event_handlers):
        self.update_events(event_handlers)
    def update_events(self, events):
        self.add_event(**events, send=False)
        self.remove_event(*(k for k in self.elem.eventPropertiesDict if k not in events))
    def add_event(self, send=True, **events):
        ed = self.elem.eventPropertiesDict
        for c,v in events.items():
            if isinstance(v, dict):
                v = v.copy()
                if 'callback' in v:
                    callback = v['callback']
                    del v['callback']
                    self._event_handlers[c] = callback
                    v['notify'] = True
                else:
                    self._event_handlers[c] = None
                if len(v) > 0:
                    ed[c] = v
                else:
                    ed[c] = None
            elif isinstance(v, str):
                ed[c] = v
                self._event_handlers[c] = None
            else:
                ed[c] = None
                self._event_handlers[c] = v
        self.elem.eventPropertiesDict = ed
        if send:
            self.elem.send_state('eventPropertiesDict')
        if len(self.elem.eventPropertiesDict) > 0:
            self.elem.bind_callback(self.handle_event)
        return self
    def remove_event(self, *events, send=True):
        ed = self.elem.eventPropertiesDict
        for c in events:
            if c in ed:
                del ed[c]
            if c in self._event_handlers:
                del self._event_handlers[c]
        self.elem.eventPropertiesDict = ed
        if send:
            self.elem.send_state('eventPropertiesDict')
        if len(self.elem.eventPropertiesDict) == 0:
            self.elem.reset_callbacks()

    _message_waiting_semaphores = {}
    @staticmethod
    def _on_msg(msg, callback, current_event):
        def on_msg(e, self, msg=msg, callback=callback, current_event=current_event):
            res = None
            if callback is not None:
                res = callback(e, self)
            if current_event is not None:
                current_event()
            self._message_waiting_semaphores[msg] = [False, res]
        return on_msg
    async def _wait_for_message(self, msg, poll_interval=.05):
        # self._message_waiting_semaphores[msg] = [False, list(self.elem._callbacks.callbacks)]
        while self._message_waiting_semaphores.get(msg, [True, None])[0]:
            await asyncio.sleep(poll_interval)
    async def wait_for_message(self, msg, callback, suppress_others=False, timeout=1, poll_interval=.05):
        self._message_waiting_semaphores[msg] = [True, None]
        og_listener = self.event_handlers.get(msg, None)
        current_event = og_listener if not suppress_others else callback
        if not suppress_others:
            if isinstance(current_event, str):
                current_event = {'method':current_event}
            elif not isinstance(current_event, dict):
                current_event = {'callback':current_event}
            else:
                current_event = current_event.copy()
            current_event['callback'] = self._on_msg(msg, callback, current_event['callback'])
        self.add_event(
            **{msg:current_event}
        )
        # print(self._event_handlers)
        try:
            await asyncio.wait_for(asyncio.create_task(self._wait_for_message(msg, poll_interval=poll_interval)), timeout=timeout)
            res = self._message_waiting_semaphores[msg][1]
        finally:
            self._message_waiting_semaphores[msg][1] = None
            if og_listener is None:
                self.remove_event(msg)
            else:
                self.add_event(**{msg: og_listener})
        # del self._message_waiting_semaphores[msg]
        return res
    def call(self, method, buffers=None, return_message=None, callback=None, timeout=1, poll_interval=0.05, suppress_others=False, **content):
        if return_message is not None:
            fut = asyncio.ensure_future(
                self.wait_for_message(return_message, callback, timeout=timeout, poll_interval=poll_interval, suppress_others=suppress_others)
            )
        base = self.elem.call(method, content=content, buffers=buffers)
        if return_message is not None:
            return fut
        return base
    def _setup_thread_listener(self, msg, callback, suppress_others=False):
        self._message_waiting_semaphores[msg] = [True, None]
        og_listener = self.event_handlers.get(msg, None)
        current_event = og_listener if not suppress_others else callback
        if not suppress_others:
            if isinstance(current_event, str):
                current_event = {'method': current_event}
            elif not isinstance(current_event, dict):
                current_event = {'callback': current_event}
            else:
                current_event = current_event.copy()
            current_event['callback'] = self._on_msg(msg, callback, current_event['callback'])
        self.add_event(
            **{msg: current_event}
        )
    def _wait_for_thread_message(self, msg, poll_interval=.05):
        while self._message_waiting_semaphores.get(msg, [True, None])[0]:
            time.sleep(poll_interval)
    def _wait_for_result(self, msg, og_listener, timeout=1, poll_interval=.05):
        try:
            # just here to allow the coroutines to work while the thread thinks...
            t = threading.Thread(target=self._wait_for_thread_message, args=(msg,), kwargs=dict(poll_interval=poll_interval))
            t.start()
            t.join(timeout)
            if t.is_alive():
                self._message_waiting_semaphores[msg][0] = False
                raise TimeoutError("didn't get a result")
            res = self._message_waiting_semaphores[msg][1]
        finally:
            self._message_waiting_semaphores[msg][1] = None
            if og_listener is None:
                self.remove_event(msg)
            else:
                self.add_event(**{msg: og_listener})
        # del self._message_waiting_semaphores[msg]
        return res
    def _thread_call(self, method, buffers=None, return_message=None, callback=None, timeout=1, poll_interval=0.05, suppress_others=False, **content):
        if return_message is not None:
            og_listener = self._setup_thread_listener(return_message, callback, suppress_others=suppress_others)
        base = self.elem.call(method, content=content, buffers=buffers)
        if return_message is not None:
            return self._wait_for_result(return_message, og_listener, timeout=timeout, poll_interval=poll_interval)
        return base
    def add_javascript(self, **methods):
        ed = self.javascript_handles
        if isinstance(ed, ActiveHTMLWrapper):
            ed.add_javascript(**methods)
        else:
            ed.update(methods)
            self.javascript_handles = ed
        return self
    def remove_javascript(self, *methods):
        ed = self.javascript_handles
        if isinstance(ed, ActiveHTMLWrapper):
            ed.remove_javascript(*methods)
        else:
            for c in methods:
                if c in ed:
                    del ed[c]
            self.javascript_handles = ed
        return self

    def trigger(self, method, buffers=None, **content):
        return self.elem.trigger(method, content=content, buffers=buffers)
    @property
    def onevents(self):
        return {
            k:self._event_handlers[k] if self._event_handlers[k] is not None else v
            for k,v in self.elem.onevents.items()
        }
    @onevents.setter
    def onevents(self, onevents):
        self.update_onevents(onevents)
    def update_onevents(self, events):
        self.on(**events, send=False)
        self.off(*(k for k in self.elem.onevents if k not in events))
    def on(self, send=True, **events):
        ed = self.elem.onevents
        for c,v in events.items():
            if isinstance(v, dict):
                v = v.copy()
                if 'callback' in v:
                    callback = v['callback']
                    del v['callback']
                    self._event_handlers[c] = callback
                    v['notify'] = True
                else:
                    self._event_handlers[c] = None
                if len(v) > 0:
                    ed[c] = v
                else:
                    ed[c] = None
            elif isinstance(v, str):
                ed[c] = v
                self._event_handlers[c] = None
            else:
                ed[c] = None
                self._event_handlers[c] = v
        self.elem.onevents = ed
        if send:
            self.elem.send_state('onevents')
        if len(self.elem.onevents) > 0:
            self.elem.bind_callback(self.handle_event)
        return self
    def off(self, *events, send=True):
        ed = self.elem.onevents
        for c in events:
            if c in ed:
                del ed[c]
            if c in self._event_handlers:
                del self._event_handlers[c]
        self.elem.onevents = ed
        if send:
            self.elem.send_state('onevents')
        if len(self.elem.eventPropertiesDict) == 0:
            self.elem.reset_callbacks()

    @property
    def track_value(self):
        return self.elem.trackInput
    @track_value.setter
    def track_value(self, v):
        self.elem.trackInput = v
    @property
    def continuous_update(self):
        return self.elem.continuousUpdate
    @continuous_update.setter
    def continuous_update(self, v):
        self.elem.continuousUpdate = v

    class LazyLoader:
        def __init__(self, base_cls, args, kwargs):
            self.base = base_cls
            self.args = args
            self.kwargs = kwargs
            self._obj = None
        def load(self):
            if self._obj is None:
                self._obj = self.base(*self.args, **self.kwargs)
            return self._obj
    @classmethod
    def loader(cls, *args, **kwargs):
        return cls.LazyLoader(cls, args, kwargs)

class HTMLWidgets:

    @classmethod
    def get_exec_prefix(cls):
        import subprocess
        ext_call = subprocess.run(["jupyter", "labextension", "list"], capture_output=True)
        path_list = ext_call.stdout.decode() + "\n" + ext_call.stderr.decode()
        end_path = ("share", "jupyter", "labextensions")
        for p in path_list.split():
            if os.path.isdir(p):
                p, p3 = os.path.split(p)
                p, p2 = os.path.split(p)
                root, p1 = os.path.split(p)
                if (p1, p2, p3) == end_path: # TODO: be a bit more careful?
                    return root
        else:
            return sys.exec_prefix


    @classmethod
    def load(cls, exec_prefix=None, overwrite=False):
        from .ActiveHTMLWidget import HTMLElement
        if exec_prefix is None:
            exec_prefix = cls.get_exec_prefix()

        nb = HTMLElement.jupyternb_install(exec_prefix=exec_prefix, overwrite=overwrite)
        lab = HTMLElement.jupyterlab_install(exec_prefix=exec_prefix, overwrite=overwrite)
        res = []
        if nb is not None:
            res.append(nb)
        if lab is not None:
            res.append(lab)
        if len(res) > 0:
            from IPython.core.display import display
            display(*res)

    _cls_map = None
    @classmethod
    def get_class_map(cls):
        if cls._cls_map is None:
            cls._cls_map = {}
            for v in cls.__dict__.values():
                if isinstance(v, type) and hasattr(v, 'base') and hasattr(v.base, 'tag'):
                    cls._cls_map[v.base.tag] = v
        return cls._cls_map
    @classmethod
    def from_HTML(cls, html:HTML.XMLElement, event_handlers=None, debug_pane=None, **props):
        tag = html.tag
        map = cls.get_class_map()
        try:
            tag_class = map[tag]
        except KeyError:
            tag_class = ActiveHTMLWrapper#lambda *es,**ats:HTML.XMLElement(tag, *es, **ats)
        return tag_class.from_HTML(html, event_handlers=event_handlers, debug_pane=debug_pane, **props)

    class JavascriptAPI(ActiveHTMLWrapper):
        def __init__(self, safety_wrap=True, _debugPrint=False, disable_caching=True, **javascript_handles):
            if safety_wrap:
                javascript_handles = {
                    k:self.safety_wrap(v) if k not in {"api", "src"} else v
                    for k,v in javascript_handles.items()
                }
                if 'src' in javascript_handles and os.path.isfile(javascript_handles['src']): # need to relink to Jupyter path
                    absfile = os.path.abspath(javascript_handles['src'])
                    javascript_handles['src'] = "/files"+"/".join(pathlib.Path(absfile).parts)
            if disable_caching and 'src' in javascript_handles:
                import urllib.parse as parse
                scheme, netloc, path, params, query, fragment = parse.urlparse(javascript_handles['src'])
                query+="cachetime="+str(time.time())
                javascript_handles['src'] = parse.urlunparse((scheme, netloc, path, params, query, fragment))
            self._api_src=None
            super().__init__(javascript_handles=javascript_handles, _debugPrint=_debugPrint)
        safety_template="try{{\n{body}\n}} catch(error) {{ console.log(error); alert('An error occurred: ' + error.toString() + '; check console for details') }}"
        def safety_wrap(self, v):
            return self.safety_template.format(body=v)
    class WrappedHTMLElement(ActiveHTMLWrapper):
        def __repr__(self):
            body = (
                self.children if len(self.children) > 0
                else self.html_string if self.html_string is not None
                else self.text if self.text is not None
                else ""
            )
            return "{}Element({!r}, cls={}, style={}, id={})".format(
                type(self).__name__,
                body,
                self.class_list,
                self.style,
                self.id
            )
    class Abbr(WrappedHTMLElement): base=HTML.Abbr
    class Address(WrappedHTMLElement): base=HTML.Address
    class Anchor(WrappedHTMLElement): base=HTML.Anchor
    A = Anchor
    class Area(WrappedHTMLElement): base=HTML.Area
    class Article(WrappedHTMLElement): base=HTML.Article
    class Aside(WrappedHTMLElement): base=HTML.Aside
    class Audio(WrappedHTMLElement): base=HTML.Audio
    class B(WrappedHTMLElement): base=HTML.B
    class Base(WrappedHTMLElement): base=HTML.Base
    class BaseList(WrappedHTMLElement): base=HTML.BaseList
    class Bdi(WrappedHTMLElement): base=HTML.Bdi
    class Bdo(WrappedHTMLElement): base=HTML.Bdo
    class Blockquote(WrappedHTMLElement): base=HTML.Blockquote
    class Body(WrappedHTMLElement): base=HTML.Body
    class Bold(WrappedHTMLElement): base=HTML.Bold
    class Br(WrappedHTMLElement): base=HTML.Br
    class Button(WrappedHTMLElement): base=HTML.Button
    class Canvas(WrappedHTMLElement): base=HTML.Canvas
    class Caption(WrappedHTMLElement): base=HTML.Caption
    class Cite(WrappedHTMLElement): base=HTML.Cite
    # class ClassAdder(WrappedHTMLElement): base=HTMLManager.ClassAdder
    # class ClassRemover(WrappedHTMLElement): base=HTMLManager.ClassRemover
    class Code(WrappedHTMLElement): base=HTML.Code
    class Col(WrappedHTMLElement): base=HTML.Col
    class Colgroup(WrappedHTMLElement): base=HTML.Colgroup
    class Data(WrappedHTMLElement): base=HTML.Data
    class Datalist(WrappedHTMLElement): base=HTML.Datalist
    class Dd(WrappedHTMLElement): base=HTML.Dd
    class Del(WrappedHTMLElement): base=HTML.Del
    class Details(WrappedHTMLElement): base=HTML.Details
    class Dfn(WrappedHTMLElement): base=HTML.Dfn
    class Dialog(WrappedHTMLElement): base=HTML.Dialog
    class Div(WrappedHTMLElement): base=HTML.Div
    class Dl(WrappedHTMLElement): base=HTML.Dl
    class Dt(WrappedHTMLElement): base=HTML.Dt
    # class ElementModifier(WrappedHTMLElement): base=HTML.ElementModifier
    class Em(WrappedHTMLElement): base=HTML.Em
    class Embed(WrappedHTMLElement): base=HTML.Embed
    class Fieldset(WrappedHTMLElement): base=HTML.Fieldset
    class Figcaption(WrappedHTMLElement): base=HTML.Figcaption
    class Figure(WrappedHTMLElement): base=HTML.Figure
    class Footer(WrappedHTMLElement): base=HTML.Footer
    class Form(WrappedHTMLElement): base=HTML.Form
    class Head(WrappedHTMLElement): base=HTML.Head
    class Header(WrappedHTMLElement): base=HTML.Header
    class Heading(WrappedHTMLElement): base=HTML.Heading
    class Hr(WrappedHTMLElement): base=HTML.Hr
    class Html(WrappedHTMLElement): base=HTML.Html
    class Iframe(WrappedHTMLElement): base=HTML.Iframe
    class Image(WrappedHTMLElement): base=HTML.Image
    class Img(WrappedHTMLElement): base=HTML.Img
    class Input(WrappedHTMLElement): base=HTML.Input
    class Ins(WrappedHTMLElement): base=HTML.Ins
    class Italic(WrappedHTMLElement): base=HTML.Italic
    class Kbd(WrappedHTMLElement): base=HTML.Kbd
    class Label(WrappedHTMLElement): base=HTML.Label
    class Legend(WrappedHTMLElement): base=HTML.Legend
    class Li(WrappedHTMLElement): base=HTML.Li
    class Link(WrappedHTMLElement): base=HTML.Link
    class List(WrappedHTMLElement): base=HTML.List
    class ListItem(WrappedHTMLElement): base=HTML.ListItem
    class Main(WrappedHTMLElement): base=HTML.Main
    class Map(WrappedHTMLElement): base=HTML.Map
    class Mark(WrappedHTMLElement): base=HTML.Mark
    class Meta(WrappedHTMLElement): base=HTML.Meta
    class Meter(WrappedHTMLElement): base=HTML.Meter
    class Nav(WrappedHTMLElement): base=HTML.Nav
    class Noscript(WrappedHTMLElement): base=HTML.Noscript
    class NumberedList(WrappedHTMLElement): base=HTML.NumberedList
    class Object(WrappedHTMLElement): base=HTML.Object
    class Ol(WrappedHTMLElement): base=HTML.Ol
    class Optgroup(WrappedHTMLElement): base=HTML.Optgroup
    class Option(WrappedHTMLElement): base=HTML.Option
    class Output(WrappedHTMLElement): base=HTML.Output
    class P(WrappedHTMLElement): base=HTML.P
    class Param(WrappedHTMLElement): base=HTML.Param
    class Picture(WrappedHTMLElement): base=HTML.Picture
    class Pre(WrappedHTMLElement): base=HTML.Pre
    class Progress(WrappedHTMLElement): base=HTML.Progress
    class Q(WrappedHTMLElement): base=HTML.Q
    class Rp(WrappedHTMLElement): base=HTML.Rp
    class Rt(WrappedHTMLElement): base=HTML.Rt
    class Ruby(WrappedHTMLElement): base=HTML.Ruby
    class S(WrappedHTMLElement): base=HTML.S
    class Samp(WrappedHTMLElement): base=HTML.Samp
    class Script(WrappedHTMLElement): base=HTML.Script
    class Section(WrappedHTMLElement): base=HTML.Section
    class Select(WrappedHTMLElement): base=HTML.Select
    class Small(WrappedHTMLElement): base=HTML.Small
    class Source(WrappedHTMLElement): base=HTML.Source
    class Span(WrappedHTMLElement): base=HTML.Span
    class Strong(WrappedHTMLElement): base=HTML.Strong
    class Style(WrappedHTMLElement): base=HTML.Style
    # class StyleAdder(WrappedHTMLElement): base=HTML.StyleAdder
    class Sub(WrappedHTMLElement): base=HTML.Sub
    class SubHeading(WrappedHTMLElement): base=HTML.SubHeading
    class SubsubHeading(WrappedHTMLElement): base=HTML.SubsubHeading
    class SubsubsubHeading(WrappedHTMLElement): base=HTML.SubsubsubHeading
    class SubHeading5(WrappedHTMLElement): base=HTML.SubHeading5
    class SubHeading6(WrappedHTMLElement): base=HTML.SubHeading6
    class Summary(WrappedHTMLElement): base=HTML.Summary
    class Sup(WrappedHTMLElement): base=HTML.Sup
    class Svg(WrappedHTMLElement): base=HTML.Svg
    class Table(WrappedHTMLElement): base=HTML.Table
    class TableHeader(WrappedHTMLElement): base=HTML.TableHeader
    class TableBody(WrappedHTMLElement): base=HTML.TableBody
    class TableHeading(WrappedHTMLElement): base=HTML.TableHeading
    class TableItem(WrappedHTMLElement): base=HTML.TableItem
    class TableRow(WrappedHTMLElement): base=HTML.TableRow
    class TagElement(WrappedHTMLElement): base=HTML.TagElement
    class Tbody(WrappedHTMLElement): base=HTML.Tbody
    class Td(WrappedHTMLElement): base=HTML.Td
    class Template(WrappedHTMLElement): base=HTML.Template
    class Text(WrappedHTMLElement): base=HTML.Text
    class Textarea(WrappedHTMLElement): base=HTML.Textarea
    class Tfoot(WrappedHTMLElement): base=HTML.Tfoot
    class Th(WrappedHTMLElement): base=HTML.Th
    class Thead(WrappedHTMLElement): base=HTML.Thead
    class Time(WrappedHTMLElement): base=HTML.Time
    class Title(WrappedHTMLElement): base=HTML.Title
    class Tr(WrappedHTMLElement): base=HTML.Tr
    class Track(WrappedHTMLElement): base=HTML.Track
    class U(WrappedHTMLElement): base=HTML.U
    class Ul(WrappedHTMLElement): base=HTML.Ul
    class Var(WrappedHTMLElement): base=HTML.Var
    class Video(WrappedHTMLElement): base=HTML.Video
    class Wbr(WrappedHTMLElement): base=HTML.Wbr

    class OutputArea(ActiveHTMLWrapper):
        def __init__(self, *elements, max_messages=None, autoclear=False, event_handlers=None, cls=None, **styles):
            if len(elements) == 1 and isinstance(elements, (list, tuple)):
                elements = elements[0]
            self._call_depth = 0
            self.autoclear = autoclear
            self.max_messages = max_messages
            self.output = JupyterAPIs.get_widgets_api().Output()
            elements = list(elements) + [self.output]
            super().__init__(*elements, event_handlers=event_handlers, cls=cls, **styles)
        def print(self, *args, **kwargs):
            with self:
                print(*args, **kwargs)
        def show_output(self, *args, **kwargs):
            with self:
                return JupyterAPIs().display_api.display(*args, **kwargs)

        def _get_display_data(self, args):
            outs = []
            for output in args:
                # Jupyter Widgets is broken so we need to patch...
                if hasattr(output, 'savefig'):
                    buf = io.BytesIO()
                    output.savefig(buf, format='png')
                    output = JupyterAPIs.get_display_api().Image(buf.getvalue())
                if output is not None:
                    if hasattr(output, 'get_mime_bundle'):
                        outs.append({
                            'output_type': 'display_data',
                            'data': output.get_mime_bundle(),
                            'metadata': {}
                        })
                    else:
                        if isinstance(output, str):
                            outs.append({
                                'output_type': 'display_data',
                                'data': {'text/plain':output},
                                'metadata': {}
                            })
                        else:
                            fmt = JupyterAPIs.get_shell_instance().display_formatter.format
                            data, metadata = fmt(output)
                            outs.append({
                                'output_type': 'display_data',
                                'data': data,
                                'metadata': metadata
                            })
            return outs

        def append_stdout(self, arg):
            self.output.append_stdout(arg)
        def append_stderr(self, arg):
            self.output.append_stderr(arg)
        def show_buffered(self, *args):
            self.output.outputs += tuple(self._get_display_data(args))
        def set_output(self, *args):
            # with self.output:
            self.output.outputs = tuple(self._get_display_data(args))
        def show_raw(self, *args):
            with self:
                api = JupyterAPIs().display_api
                api.publish_display_data(*({'text/plain': t} if isinstance(t, str) else t for t in args))
                # api.display(*(api.TextDisplayObject(t) for t in args))
        def clear(self, wait=False):
            self.output.clear_output(wait=wait)
            self.output.outputs = ()
        def __enter__(self):
            if self._call_depth < 1 and self.autoclear:
                self.clear(wait=True)
            self._call_depth += 1
            self.output.__enter__()
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            self._call_depth = max(self._call_depth-1, 0)
            if self.max_messages is not None:
                n = self.max_messages
                if len(self.output.outputs) > n:
                    self.output.outputs = self.output.outputs[-n:]
                elif len(self.output.outputs) == 1:  # and isinstance(self.output.outputs[0], str):
                    out_dict = self.output.outputs[0].copy()
                    msg = out_dict['text']
                    if msg.count('\n') > n:
                        msg = "\n".join(msg.splitlines()[-n:]) + "\n"
                        out_dict['text'] = msg
                    with self.output:
                        self.output.outputs = (out_dict,)
                        self.output._flush()
            return self.output.__exit__(exc_type, exc_val, exc_tb)