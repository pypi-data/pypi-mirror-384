import numpy as np

from ..JHTML import JHTML, HTML, HTMLWidgets
from ..Apps import WrapperComponent
import uuid

__all__ = [
    # "D3API",
    "D3"
]
__reload_hook__ = ["..JHTML", "..Apps"]

class D3API:
    _api_versions = {}
    @classmethod
    def load(cls, version='v5'):
        if version not in cls._api_versions:
            cls._api_versions[version] = JHTML.JavascriptAPI(
    d3_init="""
let model = this.model;
if (typeof(model) === 'undefined' || model === null){
    model = this;
}

if (typeof(model.d3) === 'undefined' || model.d3 === null) {
    return import("https://d3js.org/d3.""" + version + """.min.js")
      .then(() => (model.d3 = d3));
} else {
    return Promise.resolve();
}""",

    d3_call="""
let model = this.model;
if (typeof(model) === 'undefined' || model === null){
    model = this;
}

model.callHandler("d3_init").then(()=>{
    let d3 = model.d3;
    let methods = event.content['methods'];
    let args = event.content['args'];
    let debug = event.content['debug'];
    let el = this.el;
    if (typeof(el) === 'undefined' || el === null) {
        if (event.content.hasOwnProperty('id')) {
            el = "#" + event.content['id']
        }
    }

    if (typeof(el) === 'undefined' || el === null) {
        alert("no d3 object provided");
    } else {
        let svg = d3.select(el);
        if (debug) { console.log(el, svg); }
        return methods.reduce(
            (acc, method, index) => {
                if (method in svg) {
                    let fn = svg[method];
                    if (debug) { console.log(method, args[index], fn); }
                    let argl = [svg, ...args[index]];
                    svg = fn.call(...argl);
                    if (debug) { console.log(svg); }
                } else {
                    if (debug) { console.log("no attr", method); }
                }
            }, 
            []
        )
    }
})
""",
    d3_props="""
let model = this.model;
if (typeof(model) === 'undefined' || model === null){
    model = this;
}

model.callHandler("d3_init").then(()=>{
    let d3 = model.d3;
    let props = event.content['properties'];
    let debug = event.content['debug'];
    let el = this.el;
    if (typeof(el) === 'undefined' || el === null) {
        if (event.content.hasOwnProperty('id')) {
            el = "#" + event.content['id']
        }
    }

    if (typeof(el) === 'undefined' || el === null) {
        alert("no d3 object provided");
    } else {
        let svg = d3.select(el);
        if (debug) { console.log(el, svg); }
        let attrs = props.map(
            (prop) => svg.attr(prop)
        );
        this.send({type:"content", content:attrs});
    }
})
"""
)
        return cls._api_versions[version]

def short_uuid(len=6):
    return str(uuid.uuid4()).replace("-", "")[:len]

class D3:
    """
    Provides a namespace for encapsultating various D3 object types
    """

    class Frame(WrapperComponent):
        """
        Provides a frame in which to run D3 commands + access to the D3 handles
        """

        wrappers = dict(wrapper=JHTML.Div)
        theme = dict(wrapper={'cls': []}, item={'cls': []})

        def __init__(self, *elems, version='v5', id=None, javascript_handles=None, dynamic=None, **attrs):
            if javascript_handles is not None:
                raise ValueError(...)
            self._api = D3API.load(version)
            if id is None:
                id = "d3-frame-" + short_uuid()
            self.id = id
            elems = [self.canonicalize_element(e) for e in elems]
            self.svg = D3.SVG(*elems, frame=self, id=self.id, **attrs)
            self.handles = {e['id'] for e in elems}
            super().__init__(
                self.svg,
                javascript_handles=self._api,
                dynamic=dynamic
            )

        def canonicalize_element(self, e):
            if isinstance(e, (HTML.XMLElement, HTMLWidgets.WrappedHTMLElement)):
                try:
                    id = e['id']
                except KeyError:
                    id = None
                if id is None:
                    e['id'] = self.id + "-" + short_uuid(3)
            else:
                raise NotImplementedError("not sure how I should canonicalize to HTML yet...")
            return e

        def call(self, commands, id=None, debug=False, **call_kwargs):
            methods = [c[0] for c in commands]
            args = [c[1:] for c in commands]
            w = self.to_widget()
            return w.call(
                'd3_call',
                id=self.id if id is None else id,
                methods=methods,
                args=args,
                debug=debug,
                **call_kwargs
            )

        def props(self, props, id=None):
            w = self.to_widget()
            return w.call(
                'd3_props',
                id=self.id if id is None else id,
                properties=props,
                return_message="content",
                timeout=1,
                callback=lambda *_, **__: [_, __],
                poll_interval=.1
            )

        def select(self, id):
            return self.Selection(self, id)

        def attr(self, execute=True, id=None, **attrs):
            calls = [
                        ['attr', k, v]
                        for k, v in attrs.items() if k != "style"
                    ] + [
                        ['style', k, v]
                        for k, v in attrs.get('style', {}).items()
                    ]
            if execute:
                self.call(calls, id=id)
            else:
                return self.CallChain(self, calls, id=id)

        def set_id(self, id, parent_id=None):
            if parent_id is not None:
                self.handles.remove(parent_id)
                self.handles.add(id)
            return self.call([['attr', 'id', id]], id=parent_id)

        def append(self, shape, id=None, parent_id=None, debug=False, **attrs):
            if isinstance(shape, D3.D3Element):
                shape.frame = self
                shape.initialize()
                return shape
            elif isinstance(shape, str):
                if id is None:
                    id = self.id + "-" + short_uuid(3)
                self.handles.add(id)
                self.call(
                    [
                        ['append', shape],
                        ['attr', 'id', id],
                    ] + [
                        ['attr', k, v]
                        for k, v in attrs.items() if k != "style"
                    ] + [
                        ['style', k, v]
                        for k, v in attrs.get('style', {}).items()
                    ],
                    id=parent_id
                )
                return self.Selection(self, id)
            else:
                raise ValueError("can't append {}".format(shape))
        def insert(self, before_id, shape, id=None, parent_id=None, debug=False, **attrs):
            if before_id is None:
                return self.append(shape, id=id, parent_id=parent_id, debug=debug, **attrs)
            if isinstance(shape, D3.D3Element):
                shape.frame = self
                shape.insert_in_frame(where)
                return shape
            else:
                if id is None:
                    id = self.id + "-" + short_uuid(3)
                self.handles.add(id)
                self.call(
                    [
                        ['insert', shape, "#"+before_id],
                        ['attr', 'id', id],
                    ] + [
                        ['attr', k, v]
                        for k, v in attrs.items() if k != "style"
                    ] + [
                        ['style', k, v]
                        for k, v in attrs.get('style', {}).items()
                    ],
                    id=parent_id,
                    debug=debug
                )
                return self.Selection(self, id)
        def remove(self, id=None):
            if id is None:
                id = self.id
            if id in self.handles:
                self.handles.remove(id)
            self.call(
                [
                    ['remove']
                ],
                id=id
            )
        def transition(self, id=None):
            return self.CallChain(self, [['transition']], id=id)

        class CallChain:
            def __init__(self, frame, commands, id=None):
                self.frame = frame
                self.commands = commands
                self.id = id

            def __getattr__(self, command):
                return self.call(self, command)

            class call:
                def __init__(self, parent, command):
                    self.parent = parent
                    self.command = command

                def __call__(self, *args):
                    return type(self.parent)(
                        self.parent.frame,
                        self.parent.commands + [[self.command] + list(args)],
                        id=self.parent.id
                    )

            def execute(self):
                self.frame.call(
                    self.commands,
                    id=self.id
                )

        class Selection:
            def __init__(self, frame, handle):
                self.frame = frame
                self.handle = handle

            def call(self, commands):
                return self.frame.call(commands)

            def props(self, properties):
                return self.frame.props(properties, id=self.handle)

            def transition(self):
                return self.frame.transition(id=self.handle)

    _cls_map = None
    @classmethod
    def get_class_map(cls):
        if cls._cls_map is None:
            cls._cls_map = {}
            for v in cls.__dict__.values():
                if isinstance(v, type) and hasattr(v, 'tag'):
                    cls._cls_map[v.tag] = v
        return cls._cls_map

    class D3Element(HTML.XMLElement):
        """
        Provides a hook into the XMLElement API to provide a model
        that can talk with `d3` through a `D3.Frame`
        """

        def __init__(self, tag, *elems, frame:'D3.Frame'=None, id=None, on_update=None, style=None, activator=None, **attrs):
            self._frame = frame
            self._had_id = id is not None
            if id is None and self.frame is not None:
                id = self.frame.id + "-" + short_uuid(3)
            # self._id = id
            if on_update is None:
                on_update = self._on_update
            super().__init__(tag, id=id, on_update=on_update, style=style, **attrs)
            self._elems = [self._wrap_d3(e) for e in elems]
        def __repr__(self):
            return "{}<{}>".format(type(self).__name__, self.id)

        @property
        def frame(self):
            return self._frame
        @frame.setter
        def frame(self, frame):
            self.set_frame(frame)
        def set_frame(self, frame, parent_id=None):
            if frame is not self._frame:
                self._frame = frame
                if not self._had_id:
                    if frame is None:
                        self._attrs['id'] = None
                    elif parent_id is None:
                        self._attrs['id'] = frame.id + "-" + short_uuid(3)
                    else:
                        self._attrs['id'] = parent_id + "-" + short_uuid(3)
                for e in self.elems:
                    if not isinstance(e, (str, int, float, bool)):
                        e.set_frame(frame, parent_id=self.id)
        @property
        def id(self):
            return self._attrs.get('id', None)
        def set_id(self, parent_id, overwrite=False):
            if overwrite or not self._had_id:
                new_id = parent_id + "-" + short_uuid(3)
                if self.frame is None:
                    self._attrs["id"] = new_id # doesn't need to call
                else:
                    self['id'] = new_id # do call an update
            for k in self.elems:
                if not isinstance(k, (str, int, float, bool)):
                    k.set_id(self.id, overwrite=overwrite)

        def initialize(self, parent_id=None):
            tag, attrs = self.to_d3()
            self.frame.append(
                tag,
                **attrs,
                parent_id=parent_id
            )
            self.initialize_children()
        def initialize_children(self):
            for k in self.elems:
                if not isinstance(k, (str, int, float, bool)):
                    k.initialize(parent_id=self.id)

        def to_d3(self):
            style = self.style
            if style is None:
                style = {}
            return [self.tag, dict(self.attrs, id=self.id, style=style)]
        def __setitem__(self, item, value):
            if isinstance(value, (D3.D3Element, HTML.XMLElement)):
                value = self._wrap_d3(value)
            super().__setitem__(item, value)
        def insert(self, where, child):
            if isinstance(child, (D3.D3Element, HTML.XMLElement)):
                child = self._wrap_d3(child)
            super().insert(where, child)
        def set_elems(self, elems):
            super().set_elems([self._wrap_d3(e) for e in elems])
        @staticmethod
        def _on_update(element:'D3.D3Element', key, value, old_value, caller, subkey=None):
            if element.frame is not None:
                element.frame.invalidate_cache()
            if key == 'attributes':
                element.reset_attributes(value, old_value)
            elif key == 'elements':
                element.reset_children(value, old_value)
            elif key == 'attribute':
                element.set_attribute(subkey, value, old_value)
            elif key == 'element':
                if value is None:
                    element.remove_child(subkey)
                elif old_value is None:
                    element.insert_child(subkey, value)
                else:
                    element.replace_child(subkey, old_value, value)
            else:
                raise NotImplementedError("haven't implemented change {}".format(key))
        def reset_attributes(self, new_attrs, old_attrs):
            removed_attrs = old_attrs - new_attrs.keys()
            settable_attrs = dict(new_attrs, **{k:None for k in removed_attrs})
            if 'id' in settable_attrs:
                del settable_attrs['id']
            self.frame.attr(id=self.id, **settable_attrs)
        def set_attribute(self, attr, new_value, old_value):
            self.frame.attr(id=self.id, **{attr:new_value})
        def insert_child(self, where, new_value:'D3.D3Element'):
            tag, attrs = new_value.to_d3()
            if where is None or where >= len(self.elems):
                before_id = None
            else:
                before_id = self.elems[where].id
            if before_id is not None and before_id == new_value.id:
                # insert_child usually happens after insert is called on base data
                if where < len(self.elems) - 1:
                    before_id = self.elems[where] + 1
                else:
                    before_id = None
            self.frame.insert(
                before_id,
                tag,
                **attrs,
                parent_id=self.id
            )
            new_value.initialize_children()
        def replace_child(self, where, old, new:'D3.D3Element'):
            self.frame.remove(old.id)
            self.insert_child(where, new)
        def reset_children(self, new_children:'Iterable[D3.D3Element]', old_children:'Iterable[D3.D3Element]'):
            for k in old_children:
                self.frame.remove(k.id)
            for n in new_children:
                tag, attrs = n.to_d3()
                self.frame.append(
                    tag,
                    parent_id=self.id,
                    **attrs
                )

        def _wrap_d3(self, e)->'D3.D3Element':
            if isinstance(e, D3.D3Element):
                if e.id is None:
                    if self.id is not None:
                        e.set_id(self.id)
                    #     e._id = self.id + "-" + short_uuid(3)
                    #     print("-->", e._id)
                    # else:
                    #     print(e, self)
                e.frame = self.frame
            elif isinstance(e, HTML.XMLElement):
                cls = D3.get_class_map().get(e.tag, None)
                id = e.attrs.get('id', None)
                if id is None and self.id is not None:
                    id = self.id + "-" + short_uuid(3)
                if cls is None:
                    e = D3.D3Element(e.tag, *e.elems, id=id, frame=self.frame, on_update=e.on_update, **{k:v for k in e.attrs.items() if k!='id'})
                else:
                    e = cls(*e.elems, id=id, frame=self.frame, on_update=e.on_update, **{k:v for k in e.attrs.items() if k!='id'})
            elif isinstance(e, (str, int, float)):
                pass
            else:
                raise NotImplementedError("don't know how to handle {}".format(e))
            return e

    class TagElement(D3Element):
        tag = None
        def __init__(self, *elems, frame=None, **attrs):
            super().__init__(self.tag, *elems, frame=frame, **attrs)
        def __call__(self, *elems, **kwargs):
            return type(self)(
                self._elems + list(elems),
                frame=self.frame,
                activator=self.activator,
                on_update=self.on_update,
                **dict(self.attrs, **kwargs)
            )

    class A(TagElement): tag="a"
    Link = A
    class Animate(TagElement): tag="animate"
    class AnimateMotion(TagElement): tag="animateMotion"
    class AnimateTransform(TagElement): tag="animateTransform"
    class Circle(TagElement): tag="circle"
    class ClipPath(TagElement): tag="clipPath"
    class Defs(TagElement): tag="defs"
    Definitions = Defs
    class Desc(TagElement): tag="desc"
    Description = Desc
    class Ellipse(TagElement): tag="ellipse"
    class FeBlend(TagElement): tag="feBlend"
    FilterBlend = FeBlend
    class FeColorMatrix(TagElement): tag="feColorMatrix"
    FilterColorMatrix = FeColorMatrix
    class FeComponentTransfer(TagElement): tag="feComponentTransfer"
    FilterComponentTransfer = FeComponentTransfer
    class FeComposite(TagElement): tag="feComposite"
    FilterComposite = FeComposite
    class FeConvolveMatrix(TagElement): tag="feConvolveMatrix"
    FilterConvolveMatrix = FeConvolveMatrix
    class FeDiffuseLighting(TagElement): tag="feDiffuseLighting"
    FilterDiffuseLighting = FeDiffuseLighting
    class FeDisplacementMap(TagElement): tag="feDisplacementMap"
    FilterDisplacementMap = FeDisplacementMap
    class FeDistantLight(TagElement): tag="feDistantLight"
    FilterDistantLight = FeDistantLight
    class FeDropShadow(TagElement): tag="feDropShadow"
    FilterDropShadow = FeDropShadow
    class FeFlood(TagElement): tag="feFlood"
    FilterFlood = FeFlood
    class FeFuncA(TagElement): tag="feFuncA"
    FilterAlphaChannelFunction = FeFuncA
    class FeFuncB(TagElement): tag="feFuncB"
    FilterBlueChannelFunction = FeFuncB
    class FeFuncG(TagElement): tag="feFuncG"
    FilterGreenChannelFunction = FeFuncG
    class FeFuncR(TagElement): tag="feFuncR"
    FilterRedChannelFunction = FeFuncR
    class FeGaussianBlur(TagElement): tag="feGaussianBlur"
    FilterGaussianBlur = FeGaussianBlur
    class FeImage(TagElement): tag="feImage"
    FilterImage = FeImage
    class FeMerge(TagElement): tag="feMerge"
    FilterMerge = FeMerge
    class FeMergeNode(TagElement): tag="feMergeNode"
    FilterMergeNode = FeMergeNode
    class FeMorphology(TagElement): tag="feMorphology"
    FilterMorphology = FeMorphology
    class FeOffset(TagElement): tag="feOffset"
    FilterOffset = FeOffset
    class FePointLight(TagElement): tag="fePointLight"
    FilterPointLight = FePointLight
    class FeSpecularLighting(TagElement): tag="feSpecularLighting"
    FilterSpecularLighting = FeSpecularLighting
    class FeSpotLight(TagElement): tag="feSpotLight"
    FilterSpotLight = FeSpotLight
    class FeTile(TagElement): tag="feTile"
    FilterTile = FeTile
    class FeTurbulence(TagElement): tag="feTurbulence"
    FilterTurbulence = FeTurbulence
    class Filter(TagElement): tag="filter"
    class ForeignObject(TagElement): tag="foreignObject"
    class G(TagElement): tag="g"
    Group = G
    class Hatch(TagElement): tag="hatch"
    class HatchPath(TagElement): tag="hatchpath"
    class Image(TagElement): tag="image"
    class Line(TagElement): tag="line"
    class LinearGradient(TagElement): tag="linearGradient"
    class Marker(TagElement): tag="marker"
    class Mask(TagElement): tag="mask"
    class Metadata(TagElement): tag="metadata"
    class MPath(TagElement): tag="mpath"
    MotionPath = MPath
    class Path(TagElement): tag="path"
    class Pattern(TagElement): tag="pattern"
    class Polygon(TagElement): tag="polygon"
    class Polyline(TagElement): tag="polyline"
    class RadialGradient(TagElement): tag="radialGradient"
    class Rect(TagElement): tag="rect"
    class Script(TagElement): tag="script"
    class Set(TagElement): tag="set"
    class SolidColor(TagElement): tag="solidcolor"
    class Stop(TagElement): tag="stop"
    class Style(TagElement): tag="style"
    class SVG(TagElement): tag="svg"
    class Switch(TagElement): tag="switch"
    class Symbol(TagElement): tag="symbol"
    class Text(TagElement): tag="text"
    class TextPath(TagElement): tag="textPath"
    class Title(TagElement): tag="title"
    class Tspan(TagElement): tag="tspan"
    TextSpan = Tspan
    class Use(TagElement): tag="use"
    class View(TagElement): tag="view"

    class Plots:
        """
        Helper namespace for wrapping matplotlib plots
        """

        @classmethod
        def use_as_backend(cls):
            import matplotlib
            return matplotlib.use('module://' + cls.__module__ + '_backend')

        #TODO: encapsulate all of this in some sort of wrapper object
        @classmethod
        def get_plot_object(cls, figure):
            if hasattr(figure, 'figure'):
                figure = figure.figure
            return figure.canvas.manager.frame.svg

        @classmethod
        def render_mpl(cls, figure, mpl_objs):
            from .d3_backend import FigureCanvasD3
            return FigureCanvasD3.render_objects(figure, mpl_objs)

        @classmethod
        def get_mpl_plot_bounds(cls, figure):
            import McUtils.Parsers as parse

            svg = cls.get_plot_object(figure)
            # w, h = [float(x) for x in parse.Number.findall(svg.attrs['width'] + ' ' + svg.attrs['height'])]
            # [vmx, vmy, vMX, vMY] = [float(x) for x in parse.Number.findall(svg.attrs['viewBox'])]

            patch = svg.find(
                svg.build_selector(
                    dict(node_type='g', cls='axes'),
                    dict(node_type='g', cls='patch')
                )
            ).elems[0]

            mx, my, _, _, Mx, My, _, _ = [float(x) for x in parse.Number.findall(patch.attrs['d'])]
            return figure.plot_range, [[mx, my], [Mx, My]]

        @classmethod
        def to_plot_coords(cls, figure, data_points):
            ((dmx, dMx), (dmy, dMy)), ((mx, my), (Mx, My)) = cls.get_mpl_plot_bounds(figure)
            drx = dMx - dmx
            dry = dMy - dmy
            rx = Mx - mx
            ry = My - my
            data_points = np.asanyarray(data_points)
            smol = data_points.ndim == 1
            if smol:
                data_points = data_points[np.newaxis]
            scaled_x = (data_points[:, 0] - dmx) * rx / drx
            scaled_y = (data_points[:, 1] - dmy) * ry / dry

            data = np.array([scaled_x + mx, scaled_y + my]).T
            if smol:
                data = data[0]
            return data






        # class Wrapper:
        #     def __init__(self, figure):
