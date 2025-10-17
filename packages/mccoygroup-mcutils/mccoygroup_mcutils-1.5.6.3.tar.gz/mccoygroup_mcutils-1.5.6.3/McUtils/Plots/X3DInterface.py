import abc
import uuid

import numpy as np

from ..Jupyter import JHTML, X3DHTML
from .. import Numputils as nput

__all__ = [
    "X3D",
    "X3DPrimitive",
    "X3DGeometryObject",
    "X3DGeometryGroup",
    "X3DGroup",
    "X3DScene",
    "X3DBackground",
    "X3DMaterial",
    "X3DLine",
    "X3DSphere",
    "X3DCone",
    "X3DCylinder",
    "X3DCappedCylinder",
    "X3DArrow",
    "X3DTorus",
    "X3DRectangle2D",
    "X3DDisk2D",
    "X3DCircle2D",
    "X3DPolyline2D",
    "X3DTriangleSet",
    "X3DIndexedTriangleSet",
    "X3DIndexedLineSet",
    "X3DSwitch",
    "X3DListAnimator"
]

class X3DObject(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def to_x3d(self):
        ...

class X3D(X3DObject):
    defaults = dict(
        width=500,
        height=500
    )
    def __init__(self, *children, id=None, dynamic_loading=True, **opts):
        if len(children) == 1 and isinstance(children[0], (tuple, list)):
            children = children[0]
        self.children = children
        self.opts = opts
        if id is None:
            id = "x3d-" + str(uuid.uuid4())[:6]
        self.id = id
        self.dynamic_loading = dynamic_loading

    X3DOM_JS = 'https://www.x3dom.org/download/1.8.3/x3dom-full.js'
    X3DOM_CSS = 'https://www.x3dom.org/download/x3dom.css'

    @classmethod
    def get_export_script(self, id):
        return f"""
(function(){{
  let link = document.createElement('a');
  let base_name = '{id}';
  link.download = base_name + '.png';
  link.href = document.getElementById('{id}').getElementsByTagName('canvas')[0].toDataURL()
  link.click();
}})()
       """

    @classmethod
    def get_record_screen_script(self, id, polling_rate=30, recording_duration=2, video_format='video/webm'):
            return f"""
    (function(){{
        let canvas = document.getElementById('{id}').getElementsByTagName('canvas')[0];
        
        let pollingRate = (typeof canvas.pollingRate === 'undefined') ? {polling_rate} : canvas.pollingRate;
        let videoFormat = (typeof canvas.videoFormat === 'undefined') ? "{video_format}" : canvas.videoFormat;
        let videoExtension = canvas.videoExtension;
        if (typeof canvas.videoExtension === 'undefined') {{
            videoExtension = ""
        }}
        let x3DRecordingStream = canvas.captureStream(pollingRate);
        let mediaRecorder = new MediaRecorder(x3DRecordingStream, {{mimeType: videoFormat}});
        
        mediaRecorder.frames = [];
        mediaRecorder.ondataavailable = function(e) {{
          mediaRecorder.frames.push(e.data);
        }};
        
        mediaRecorder.onstop = function(e) {{
          link = document.createElement('a');
          const base_name = '{id}';
          const blob = mediaRecorder.frames[0];
          link.download = base_name + videoExtension;
          console.log(blob);
          const blobURL = window.URL.createObjectURL(blob);
          link.href = blobURL;
          console.log(blobURL);
          mediaRecorder.frames = [];
          link.click();
        }};
        
        let duration = (typeof canvas.recordingDuration === 'undefined') ? {recording_duration} : canvas.recordingDuration;
        setTimeout(() => {{mediaRecorder.stop()}}, duration * 1000);
        mediaRecorder.start()
    }})()
           """
    @classmethod
    def set_animation_duration_script(self, id):
        return f"""
    (function(){{
        let canvas = document.getElementById('{id}').getElementsByTagName('canvas')[0];
        let input = document.getElementById('{id}-duration-input');
        
        canvas.recordingDuration = input.value;
    }})()
           """

    include_export_button = False
    include_record_button = False
    def to_widget(self, dynamic_loading=None, include_export_button=None, include_record_button=None):
        id = self.id
        x3d_embed = self.to_x3d()#.tostring()

        if dynamic_loading is None:
            dynamic_loading = self.dynamic_loading
        if include_export_button is None:
            include_export_button = self.include_export_button
        if include_record_button is None:
            include_record_button = self.include_record_button

        if not dynamic_loading:
            base_fig = JHTML.Div(
                JHTML.Link(rel='stylesheet', href=self.X3DOM_CSS),
                JHTML.Script(src=self.X3DOM_JS),
                x3d_embed,
                id=id
            )
        else:
            JHTML.Link(rel='stylesheet', href=self.X3DOM_CSS),
            load_script = JHTML.Script(src=self.X3DOM_JS).tostring()
            kill_id = "tmp-"+str(uuid.uuid4())[:10]
            base_fig = JHTML.Figure(
                # JHTML.Link(rel='stylesheet', href=self.X3DOM_CSS),
                x3d_embed,
                JHTML.Image(
                    src='data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7',
                    id=kill_id,
                    onload=f"""
                    (function() {{
                        document.getElementById("{kill_id}").remove();
                        const frag = document.createRange().createContextualFragment(`{load_script}`);
                        document.head.appendChild(frag);
                    }})()"""
                    ),
                id=id
            )

        elems = [base_fig]
        if include_export_button:
            elems.append(JHTML.Button("Save Figure", onclick=self.get_export_script(self.id)))
        if include_record_button:
            elems.extend([
                JHTML.Button("Record Animation", onclick=self.get_record_screen_script(self.id)),
                JHTML.Input(value="2", id=self.id+'-duration-input', oninput=self.set_animation_duration_script(self.id))
            ])

        if len(elems) > 1:
            return JHTML.Div(
                *elems
            )
        else:
            return elems[0]

    def to_html(self, *base_elems, header_elems=None,
                dynamic_loading=False,
                include_export_button=None,
                include_record_button=None,
                **header_info):
        id = self.id
        x3d_embed = self.to_widget(
            dynamic_loading=dynamic_loading,
            include_export_button=include_export_button,
            include_record_button=include_record_button
        )  # .tostring()

        return JHTML.Html(
            JHTML.Head(
                *(header_elems if header_elems is not None else []),
                JHTML.Link(rel='stylesheet', href=self.X3DOM_CSS),
                JHTML.Script(src=self.X3DOM_JS),
                **header_info
            ),
            JHTML.Body(
                *base_elems,
                x3d_embed
            ),
            id=id
        )

    def _ipython_display_(self):
        return self.to_widget()._ipython_display_()
    def get_mime_bundle(self):
        return self.to_widget().get_mime_bundle()
    def to_x3d(self):
        base_opts = dict(self.defaults, **self.opts)
        for k in ['width', 'height']:
            if k in base_opts:
                v = base_opts[k]
                if nput.is_numeric(v):
                    base_opts[k] = f'{v:.0f}px'
        return X3DHTML.X3D(
            JHTML.HTML.Head(),
            *[a.to_x3d() if hasattr(a, 'to_x3d') else a for a in self.children],
            **base_opts
        )
    def display(self):
        return self.to_widget().display()

    def show(self):
        from ..Jupyter.JHTML import JupyterAPIs
        dynamic_loading = JupyterAPIs().in_jupyter_environment()
        self.to_widget(dynamic_loading=dynamic_loading).display()

    def dump(self, file, write_html=True, **opts):
        if write_html:
            html = self.to_html()
        else:
            html = self.to_x3d()
        return html.write(file, **opts)

class X3DOptionsSet(X3DObject):
    __props__ = {}

    def __init__(self, **attrs):
        self.attrs = attrs

    conversion_map = {}
    @classmethod
    def prop_keys(cls):
        return (cls.__props__ | cls.conversion_map.keys())
    def prep_attrs(self, attrs:dict):
        attrs = {
            self.conversion_map.get(k, k):v
            for k,v in attrs.items()
        }
        excess_keys = attrs.keys() - self.__props__
        if len(excess_keys) > 0:
            cls = type(self).__name__
            raise ValueError(f"keys {excess_keys} are invalid keys for {cls}")
        return attrs

class X3DMaterial(X3DOptionsSet):
    __props__ = {
        "diffuseColor",
        "ambientIntensity",
        "emissiveColor",
        "specularColor",
        "shininess",
        "transparency",
        # "metadata"
    }
    conversion_map = {
        "brightness": "ambientIntensity",
        "glow": "emissiveColor",
        "color": "diffuseColor",
        "specularity": "specularColor"
    }
    def to_x3d(self):
        return X3DHTML.Material(**self.prep_attrs(self.attrs))

class X3DAppearance(X3DOptionsSet):
    __props__ = {
        "alphaClipThreshold",
        "blendMode",
        "colorMaskMode"
        "depthMode"
        "lineProperties"
        "material"
        "metadata"
        "pointProperties"
        "shaders",
        "sortKey",
        "sortType",
        "texture",
        "textureTransform"
    }
    def prep_attrs(self, attrs:dict):
        material_keys = attrs.keys() & X3DMaterial.prop_keys()
        line_keys = attrs.keys() & X3DLineProperties.prop_keys()
        point_keys = attrs.keys() & X3DPointProperties.prop_keys()

        rem_keys = attrs.keys() - (
            X3DMaterial.prop_keys()
            | X3DLineProperties.prop_keys()
            | X3DPointProperties.prop_keys()
        )
        base_attrs = {k:attrs[k] for k in rem_keys}

        if len(material_keys) > 0:
            base_attrs['material'] = {k:attrs[k] for k in material_keys}

        if len(line_keys) > 0:
            base_attrs['lineProperties'] = {k:attrs[k] for k in line_keys}

        if len(point_keys) > 0:
            base_attrs['pointProperties'] = {k:attrs[k] for k in point_keys}

        return base_attrs
    def to_x3d(self):
        base_attrs = self.prep_attrs(self.attrs)

        comps = []
        line_props = base_attrs.pop('lineProperties', None)
        if line_props is not None:
            if isinstance(line_props, dict):
                line_props = X3DLineProperties(**line_props)
            if isinstance(line_props, X3DLineProperties):
                line_props = line_props.to_x3d()
            comps.append(line_props)

        point_props = base_attrs.pop('pointProperties', None)
        if point_props is not None:
            if isinstance(point_props, dict):
                point_props = X3DPointProperties(**point_props)
            if isinstance(point_props, X3DPointProperties):
                point_props = point_props.to_x3d()
            comps.append(point_props)

        material_props = base_attrs.pop('material', None)
        if material_props is not None:
            if isinstance(material_props, dict):
                material_props = X3DMaterial(**material_props)
            if isinstance(material_props, X3DMaterial):
                material_props = material_props.to_x3d()
            comps.append(material_props)

        return X3DHTML.Appearance(*comps, **base_attrs)

class X3DLineProperties(X3DOptionsSet):
    __props__ = {
        "applied",
        "linetype",
        "linewidth",
        "linewidthScaleFactor"
    }
    conversion_map = {
        "line_style":"linetype",
        "line_thickness":"linewidth"
    }
    def prep_attrs(self, attrs:dict):
        attrs = super().prep_attrs(attrs)
        attrs['linewidthScaleFactor'] = attrs.get('linewidthScaleFactor', '1')
        attrs['containerField'] = attrs.get('containerField', 'lineProperties')
        return attrs
    def to_x3d(self):
        return X3DHTML.LineProperties(**self.prep_attrs(self.attrs))

class X3DPointProperties(X3DOptionsSet):
    __props__ = {
        "attenuation",
        "pointSizeMaxValue",
        "pointSizeMinValue",
        "pointSizeScaleFactor"
    }
    conversion_map = {
        "point_size":"pointSizeScaleFactor"
    }
    def prep_attrs(self, attrs:dict):
        attrs = super().prep_attrs(attrs)
        attrs['containerField'] = attrs.get('containerField', 'pointProperties')
        attrs['pointSizeMaxValue'] = str(
            max([
                float(attrs.get('pointSizeMaxValue', '0')),
                float(attrs.get('pointSizeMinValue', '0')),
                float(attrs.get('pointSizeScaleFactor', '0')),
            ])
        )
        return attrs
    def to_x3d(self):
        return X3DHTML.PointProperties(**self.prep_attrs(self.attrs))

class X3DPrimitive(X3DObject):
    wrapper_class = None
    tag_class = None
    def __init__(self, *children, **opts):
        if len(children) == 1 and isinstance(children[0], (tuple, list)):
            children = children[0]
        self.children = children
        self.opts = opts
    def split_opts(self, opts:dict):
        material_keys = opts.keys() & (
            X3DMaterial.prop_keys()
            | X3DAppearance.prop_keys()
            | X3DLineProperties.prop_keys()
            | X3DPointProperties.prop_keys()
        )
        rem_keys = opts.keys() - material_keys
        return {k:opts[k] for k in rem_keys}, {k:opts[k] for k in material_keys}
    def get_appearance(self, appearance_options):
        if len(appearance_options) > 0:
            return X3DAppearance(**appearance_options).to_x3d()
        else:
            return None
    def to_x3d(self):
        obj_opts, appearance_opts = self.split_opts(self.opts)
        kids = [k.to_x3d() if hasattr(k, 'to_x3d') else k for k in self.children]
        appearance = self.get_appearance(appearance_opts)
        if self.tag_class is None:
            if appearance is not None:
                kids = [appearance] + kids
            return self.wrapper_class(
                kids,
                **obj_opts
            )
        else:
            core = self.tag_class(kids, **obj_opts)
            appearance = self.get_appearance(appearance_opts)
            if appearance is not None:
                return self.wrapper_class(appearance, core)
            else:
                return core

class X3DScene(X3DPrimitive):
    wrapper_class = X3DHTML.Scene
    default_viewpoint = {'viewAll':True}
    children: list
    def __init__(self, *children:X3DPrimitive, background=None, viewpoint=None, **opts):
        if viewpoint is None:
            viewpoint = self.default_viewpoint
        elif viewpoint is False:
            viewpoint = {}
        super().__init__(*children, **opts)
        if background is not None:
            self.children = [X3DBackground(color=background)] + list(self.children)
        if len(viewpoint) > 0:
            viewpoint = self.get_view_settings(**viewpoint)
            self.children = [X3DHTML.Viewpoint(**viewpoint)] + list(self.children)

    default_up_vector = (0, 1, 0)
    default_right_vector = (1, 0, 0)
    default_view_vector = (0, 0, 1)
    default_view_distance = 10
    @classmethod
    def get_view_settings(cls,
                          up_vector=None, view_vector=None, right_vector=None,
                          view_distance=None, view_center=None, view_matrix=None, view_position=None, **etc):
        # CO = coords0[1] - coords0[0]
        # OH = coords0[5] - coords0[1]
        if view_matrix is None:
            if view_vector is None:
                if (
                    up_vector is not None and right_vector is not None
                ):
                    view_vector = nput.vec_crosses(up_vector, right_vector, normalize=True)
                elif right_vector is not None:
                    view_vector = nput.vec_crosses(cls.default_up_vector, right_vector, normalize=True)
                elif up_vector is not None:
                    view_vector = nput.vec_crosses(up_vector, cls.default_right_vector, normalize=True)

            if view_vector is not None:
                m = nput.rotation_matrix(
                    view_vector,
                    cls.default_view_vector
                )
            else:
                m = np.eye(3)

            if up_vector is None and right_vector is not None:
                if view_vector is None:
                    view_vector = cls.default_view_vector
                up_vector = nput.vec_normalize(
                    nput.vec_crosses(view_vector, right_vector)
                )
            if up_vector is not None:
                m = m @ nput.rotation_matrix(
                    m.T @ up_vector,
                    cls.default_up_vector
                )
            view_matrix = m

        ang, cross = nput.extract_rotation_angle_axis(view_matrix)
        if view_vector is None:
            view_vector = view_matrix[:, -1]
        if view_position is None:
            if view_distance is None:
                view_distance = cls.default_view_distance
            view_position = view_distance * nput.vec_normalize(np.asanyarray(view_vector))
            if view_center is not None:
                view_center = view_matrix @ np.asanyarray(view_center)
                view_position = view_distance * nput.vec_normalize(
                    view_position + view_center
                )
        else:
            view_position = view_matrix @ np.asanyarray(view_position)
        return dict(
            {
                'orientation': list(cross) + [ang],
                'position': view_position
            },
            **etc
        )

class X3DBackground(X3DOptionsSet):
    wrapper_class = X3DHTML.Background
    __props__ = {
        'skyColor',
        'skyAngle'
    }
    conversion_map = {
        "color": "skyColor"
    }
    def prep_attrs(self, attrs: dict):
        attrs = super().prep_attrs(attrs)
        color = attrs.get('skyColor', None)
        if color is not None:
            if isinstance(color, (list, tuple, np.ndarray)) and all(isinstance(c, str) for c in color):
                color = " ".join(color)
            if isinstance(color, str):
                try:
                    _ = [float(s) for s in color.split()]
                except ValueError:
                    from .Colors import ColorPalette

                    bits = []
                    for c in color.split():
                        if color.startswith('#'):
                            c = ColorPalette.parse_rgb_code(c)
                        else:
                            c = np.array(ColorPalette.parse_color_string(c))
                        bits.extend(np.array(c) / 255)
                    attrs['skyColor'] = bits
        return attrs

    def to_x3d(self):
        return X3DHTML.Background(**self.prep_attrs(self.attrs))

class X3DCoordinate(X3DPrimitive):
    wrapper_class = X3DHTML.Coordinate
    def __init__(self, points):
        super().__init__(point=self.prep_points(points))
    @classmethod
    def prep_points(cls, points):
        return " ".join(np.asanyarray(np.round(points, 4)).flatten().astype(str))

class X3DColor(X3DPrimitive):
    wrapper_class = X3DHTML.Color
    def __init__(self, colors):
        super().__init__(color_list=colors)
    def split_opts(self, opts:dict):
        base_opts, appearance_opts = super().split_opts(opts)
        base_opts['color'] = self.prep_color(base_opts.pop('color_list'))
        return base_opts, appearance_opts
    @classmethod
    def prep_color(cls, points):
        return " ".join(np.asanyarray(np.round(points, 4)).flatten().astype(str))

class X3DGroup(X3DPrimitive):
    wrapper_class = X3DHTML.Group

class X3DSwitch(X3DPrimitive):
    wrapper_class = X3DHTML.Switch

class X3DGeometryObject(X3DPrimitive):
    wrapper_class = X3DHTML.Shape
    def __init__(self, *args, **opts):
        geom_opts, self.material_opts = self.split_opts(opts)
        self.geometry_opts = self.prep_geometry_opts(*args, **geom_opts)
        super().__init__()
    @abc.abstractmethod
    def prep_geometry_opts(self, *args, **opts) -> dict:
        ...
    def create_tag_object(self, **core_opts):
        return self.tag_class(**core_opts)
    def create_object(self,
                      translation=None,
                      rotation=None,
                      scale=None,
                      normal=None,
                      up_vector=None,
                      bbox_center=None,
                      **core_opts):
        base_obj = self.create_tag_object(**core_opts)
        tf = {}
        if normal is not None:
            if up_vector is None:
                up_vector = [0, 0, 1]
            angs, crosses = nput.vec_angles(up_vector, normal, return_crosses=True, return_norms=False)
            if rotation is not None:
                if isinstance(rotation, str):
                    rotation = np.array(rotation.split()).astype(float)
                angs, crosses = nput.extract_rotation_angle_axis(
                    nput.rotation_matrix(crosses, angs)
                        @ nput.rotation_matrix(rotation[:3], rotation[3])
                )
            rotation = np.concatenate([crosses, [angs]])
        for k,v in [["translation",translation], ["rotation",rotation], ["scale", scale], ['bboxcenter', bbox_center]]:
            if v is not None:
                tf[k] = np.round(v, 4) if not isinstance(v, str) else v
        if len(tf) == 0:
            tf = None
        # base_obj = X3DHTML.Transform(base_obj, translation=translation, rotation=rotation, scale=scale)
        return base_obj, tf
    def get_rotation(self, axis, up_vector=None):
        if up_vector is None:
            up_vector = [0, 1, 0]
        angs, crosses, norms = nput.vec_angles(up_vector, axis, return_crosses=True, return_norms=True)
        if nput.is_numeric(angs):
            return np.concatenate([crosses, [angs]]), norms[1]
        else:
            return np.concatenate([crosses, angs[..., np.newaxis]], axis=-1), norms[1]
    def to_x3d(self):
        # obj_opts, material_opts = self.split_opts(self.opts)
        # kids = [k.to_x3d() for k in self.children]
        core, tf = self.create_object(**self.geometry_opts)
        appearance = self.get_appearance(self.material_opts)
        if appearance is not None:
            core = self.wrapper_class(appearance, core)
        if tf is not None:
            core = X3DHTML.Transform(core, **tf)
        return core

class X3DGeometryGroup(X3DGeometryObject):
    @abc.abstractmethod
    def prep_geometry_opts(self, *args, **opts) -> list[dict]:
        ...
    def prep_vecs(self, vecs, nstruct=None):
        if vecs is None:
            return [None] * nstruct
        else:
            vecs = np.asanyarray(vecs)
            if vecs.ndim == 1:
                vecs = vecs[np.newaxis]
            if nstruct is not None:
                vecs = np.broadcast_to(vecs, (nstruct, vecs.shape[-1]))
        return vecs
    def prep_mats(self, mats, nstruct=None):
        if mats is None:
            return [None] * nstruct
        else:
            mats = np.asanyarray(mats)
            if mats.ndim == 2:
                mats = mats[np.newaxis]
            if nstruct is not None:
                mats = np.broadcast_to(mats, (nstruct,) + mats.shape[-2:])
            return mats
    def prep_const(self, const, nstruct):
        if const is None:
            return [None] * nstruct
        else:
            const = np.asanyarray(const)
            if const.ndim == 0:
                const = const[np.newaxis]
            const = np.broadcast_to(const, (nstruct,))
            return const
    def to_x3d(self):
        kids = [self.create_object(**g) for g in self.geometry_opts]
        appearance = self.get_appearance(self.material_opts)
        objs = []
        for o,tf in kids:
            if appearance is not None:
                o = self.wrapper_class(appearance, o)
            if tf is not None:
                o = X3DHTML.Transform(o, **tf)
            objs.append(o)
        if len(objs) == 1:
            return objs[0]
        else:
            return X3DHTML.Group(objs)

class X3DSphere(X3DGeometryGroup):
    tag_class = X3DHTML.Sphere

    def prep_geometry_opts(self, centers, radius=1, **opts):
        centers = self.prep_vecs(centers)
        rads = self.prep_const(radius, centers.shape[0])
        return [{"translation":c, "radius":r} for c,r in zip(centers, rads)]

class X3DCylinder(X3DGeometryGroup):
    tag_class = X3DHTML.Cylinder

    def prep_geometry_opts(self, starts, ends, radius=1, **opts):
        starts = self.prep_vecs(starts)
        ends = self.prep_vecs(ends)
        radius = self.prep_const(radius, starts.shape[0])

        axes = ends - starts
        rots, norms = self.get_rotation(axes)

        return [
            {"translation":s, "rotation":a, "height":n, "radius":r}
            for s,a,n,r in zip((starts + ends) / 2, rots, norms, radius)
        ]

class X3DCone(X3DGeometryGroup):
    tag_class = X3DHTML.Cone

    def prep_geometry_opts(self, starts, ends, radius=1, top_radius=None, **opts):
        starts = self.prep_vecs(starts)
        ends = self.prep_vecs(ends)
        radius = self.prep_const(radius, starts.shape[0])
        top_radius = self.prep_const(top_radius, starts.shape[0])

        axes = ends - starts
        rots, norms = self.get_rotation(axes)

        return [
            {"translation":s, "rotation":a, "height":n, "bottomRadius":r, "topRadius":t}
            for s,a,n,r,t in zip((starts + ends) / 2, rots, norms, radius, top_radius)
        ]

class X3DArrow(X3DGroup):

    arrowhead_class = X3DCone
    cylinder_class = X3DCylinder

    def __init__(self,
                 starts, ends,
                 radius=1,
                 top_radius=None,
                 arrowhead_radius=2,
                 arrowhead_radius_mode='scaled',
                 arrowhead_offset=.3,
                 arrowhead_offset_mode='scaled',
                 cylinder_class=None,
                 arrowhead_class=None,
                 **opts):
        if arrowhead_class is None:
            arrowhead_class = self.arrowhead_class
        if cylinder_class is None:
            cylinder_class = self.cylinder_class

        ends = np.asanyarray(ends)
        starts = np.asanyarray(starts)
        arrow_vectors = ends - starts
        norms = nput.vec_norms(arrow_vectors)
        if arrowhead_offset_mode == 'scaled':
            arrowhead_offset = arrowhead_offset * norms
        disp_vectors = arrowhead_offset * nput.vec_normalize(arrow_vectors, norms=norms)
        arrow_starts = ends - disp_vectors
        if arrowhead_radius_mode == 'scaled':
            arrowhead_radius = arrowhead_radius * radius
        arrowheads = arrowhead_class(arrow_starts, ends,
                                     radius=arrowhead_radius,
                                     top_radius=top_radius,
                                     **opts)
        cylinders = cylinder_class(starts, arrow_starts, radius=radius, **opts)

        super().__init__(
            arrowheads, cylinders
        )

class X3DCappedCylinder(X3DGroup):

    cap_class = X3DSphere
    cylinder_class = X3DCylinder

    def __init__(self,
                 starts, ends,
                 radius=1,
                 cylinder_class=None,
                 cap_class=None,
                 cap_offset=0,
                 use_caps=(True, True),
                 **opts):
        if cap_class is None:
            cap_class = self.cap_class
        if cylinder_class is None:
            cylinder_class = self.cylinder_class

        if cap_offset != 0:
            raise NotImplementedError("cap offseting not supported yet")

        if use_caps is True: use_caps = [True, True]
        elif use_caps is False: use_caps = [False, False]

        cap_list = []
        if use_caps[0]:
            cap_list.append(cap_class(starts, radius=radius, **opts))
        if use_caps[1]:
            cap_list.append(cap_class(ends, radius=radius, **opts))
        cylinders = cylinder_class(starts, ends, radius=radius, **opts)

        super().__init__(
            *cap_list, cylinders
        )

class X3DText(X3DGeometryGroup):
    tag_class = X3DHTML.Text

    def __init__(self, *args, billboard=True, billboard_opts=None, **opts):
        if billboard:
            if billboard_opts is None:
                billboard_opts = {'axisOfRotation':'0 0 0'}
            self.wrapper_class = lambda *x,**y:X3DHTML.Billboard(X3DHTML.Shape(*x, **y), **billboard_opts)
        super().__init__(*args, **opts)
    def create_tag_object(self, font_style=None, **core_opts):
        body = []
        if font_style is not None:
            body.append(font_style)
        return self.tag_class(body, **core_opts)
    def prep_geometry_opts(self, centers, text, font_style=None, rotation=None, normal=None, **opts):
        centers = self.prep_vecs(centers)
        rotation = self.prep_vecs(rotation, len(centers))
        normal = self.prep_vecs(normal, len(centers))
        text = self.prep_const(text, len(centers))
        font_style = [
            X3DHTML.FontStyle(**fs)
                if fs is not None else
            None
            for fs in self.prep_const(font_style, len(centers))
        ]
        return [
            {"translation": c, 'string': t, 'length': len(t), 'font_style':fs, 'rotation':r, 'normal':n}
            for c, t, fs, r, n in zip(centers, text, font_style, rotation, normal)
        ]

class X3DTorus(X3DGeometryGroup):
    tag_class = X3DHTML.Torus

    def prep_geometry_opts(self, centers, radius=1, inner_radius=None,
                           normal=None, rotation=None, scale=None,
                           angle=None,
                           **opts):
        if angle is not None and angle < 0:
            if rotation is None:
                rotation = [0, 0, 1, 0]
            if isinstance(rotation, str):
                rotation = np.array(rotation.split()).astype(float)
            rotation = list(rotation[:3]) + [rotation[3] + angle]
            angle = abs(angle)
        centers = self.prep_vecs(centers)
        normal = self.prep_vecs(normal, centers.shape[0])
        rotation = self.prep_vecs(rotation, centers.shape[0])
        scale = self.prep_vecs(scale, centers.shape[0])
        radius = self.prep_const(radius, centers.shape[0])
        inner_radius = self.prep_const(inner_radius, centers.shape[0])
        angle = self.prep_const(angle, centers.shape[0])

        return [
            {
                "translation": s, "normal": n, "outerRadius": r,
                "innerRadius": i, 'rotation': rot, 'scale': sc,
                'angle': ang,
                **opts}
            for s, n, rot, sc, r, i, ang in zip(
                centers, normal,
                rotation, scale,
                radius, inner_radius, angle
            )
        ]

class X3DCoordinatesWrapper(X3DGeometryGroup):
    tag_class: X3DHTML.X3DElement
    def create_tag_object(self, *, point, color=None, **etc):
        body = [X3DCoordinate(point).to_x3d()]
        if color is not None:
            body.append(X3DColor(color).to_x3d())
        return self.tag_class(body, **etc)
    def prep_geometry_opts(self, point, **etc):
        return [
            dict({"translation":"0,0,0", "point":point}, **etc)
        ]

class X3DIndexedCoordinatesWrapper(X3DCoordinatesWrapper):
    def prep_geometry_opts(self, point, indices, vertex_colors=None, **etc):
        base_dict = dict(
                {
                    'index': " ".join(np.asanyarray(indices).flatten().astype(int).astype(str))
                },
                **super().prep_geometry_opts(point, **etc)[0]
            )
        if vertex_colors is not None:
            base_dict['colorPerVertex'] = True
            base_dict['color'] = vertex_colors
        return [base_dict]

class X3DGeometry2DGroup(X3DGeometryGroup):
    def prep_geometry_opts(self, center, **etc):
        # raise Exception(crosses)
        # a = np.concatenate([crosses, [angs]])
        # a, _ = self.get_rotation(crosses, up_vector=up_vector)
        return [
            {
                "translation":center,
                 **etc
            }
        ]

class X3DRectangle2D(X3DGeometry2DGroup):
    tag_class = X3DHTML.Rectangle2D
class X3DCircle2D(X3DGeometry2DGroup):
    tag_class = X3DHTML.Circle2D
    def prep_geometry_opts(self, centers, radius=1,
                           normal=None, rotation=None, scale=None,
                           angle=None,
                           **opts):
        centers = self.prep_vecs(centers)
        normal = self.prep_vecs(normal, centers.shape[0])
        if angle is not None and angle < 0:
            if rotation is None:
                rotation = [0, 0, 1, 0]
            if isinstance(rotation, str):
                rotation = np.array(rotation.split()).astype(float)
            rotation = list(rotation[:3]) + [rotation[3] + angle]
            angle = abs(angle)
        rotation = self.prep_vecs(rotation, centers.shape[0])
        scale = self.prep_vecs(scale, centers.shape[0])
        radius = self.prep_const(radius, centers.shape[0])
        angle = self.prep_const(angle, centers.shape[0])

        return [
            {
                "translation": s, "normal": n, "radius": r,
                'rotation': rot, 'scale': sc,
                'angle': ang,
                **opts}
            for s, n, rot, sc, r, ang in zip(
                centers, normal,
                rotation, scale,
                radius, angle
            )
        ]

class X3DDisk2D(X3DGeometry2DGroup):
    tag_class = X3DHTML.Disk2D

    def prep_geometry_opts(self, centers, radius=1, inner_radius=None,
                           normal=None, rotation=None, scale=None,
                           angle=None,
                           **opts):
        centers = self.prep_vecs(centers)
        normal = self.prep_vecs(normal, centers.shape[0])
        if angle is not None and angle < 0:
            if rotation is None:
                rotation = [0, 0, 1, 0]
            if isinstance(rotation, str):
                rotation = np.array(rotation.split()).astype(float)
            rotation = list(rotation[:3]) + [rotation[3] + angle]
            angle = abs(angle)
        rotation = self.prep_vecs(rotation, centers.shape[0])
        scale = self.prep_vecs(scale, centers.shape[0])
        radius = self.prep_const(radius, centers.shape[0])
        inner_radius = self.prep_const(inner_radius, centers.shape[0])
        angle = self.prep_const(angle, centers.shape[0])

        return [
            {
                "translation": s, "normal": n, "outerRadius": r,
                "innerRadius": i, 'rotation': rot, 'scale': sc,
                'angle': ang,
                **opts}
            for s, n, rot, sc, r, i, ang in zip(
                centers, normal,
                rotation, scale,
                radius, inner_radius, angle
            )
        ]
class X3DPolyline2D(X3DGeometry2DGroup):
    tag_class = X3DHTML.Polyline2D

class X3DPointSet(X3DCoordinatesWrapper):
    tag_class = X3DHTML.PointSet
class X3DLine(X3DCoordinatesWrapper):
    tag_class = X3DHTML.LineSet
class X3DTriangleSet(X3DCoordinatesWrapper):
    tag_class = X3DHTML.TriangleSet
class X3DIndexedTriangleSet(X3DIndexedCoordinatesWrapper):
    tag_class = X3DHTML.IndexedTriangleSet
class X3DIndexedLineSet(X3DIndexedCoordinatesWrapper):
    tag_class = X3DHTML.IndexedLineSet
    def prep_geometry_opts(self, point, indices, **etc):
        opts = super().prep_geometry_opts(point, indices, **etc)
        opts[0]['coordIndex'] = opts[0].pop('index')
        return opts
class X3DIndexedQuadSet(X3DIndexedCoordinatesWrapper):
    tag_class = X3DHTML.IndexedQuadSet
class X3DIndexedFaceSet(X3DIndexedCoordinatesWrapper):
    tag_class = X3DHTML.IndexedFaceSet

class X3DListAnimator(X3DGroup):
    def __init__(self, *frames, id=None, animation_duration=2, running=True, slider=False,
                 # allow_interpolation=True,
                 **opts):
        self.uuid = str(uuid.uuid4())
        if id is None:
            id = f"animation-{self.uuid}"
        self.id = id
        anim_frames = X3DSwitch(
                *frames,
                id=id,
                whichChoice="0"
            )
        nframes = len(anim_frames.children) - 1
        key_frames = np.linspace(0, 1, nframes)
        elements = []
        if slider:
            elements.append(
                JHTML.Input(type="range", value="0", min="0", max=f"{nframes}", step="1", cls="slider",
                            oninput=f"""document.getElementById("{id}").setAttribute("whichChoice", this.value)""")
            )
        elements.append(anim_frames)
        if running:
            elements.extend([
                X3DHTML.TimeSensor(id=f'animation-clock-{self.uuid}', cycleInterval=animation_duration, loop=True,
                                   enabled=running
                                   ),
                X3DHTML.IntegerSequencer(id=f'animation-indexer-{self.uuid}', key=key_frames,
                                         keyValue=np.arange(nframes)),
                X3DHTML.Route(
                    fromField='fraction_changed', fromNode=f'animation-clock-{self.uuid}',
                    toField='set_fraction', toNode=f'animation-indexer-{self.uuid}'
                ),
                X3DHTML.Route(
                    fromField='value_changed', fromNode=f'animation-indexer-{self.uuid}',
                    toField='whichChoice', toNode=self.id
                )
            ])

        super().__init__(elements, **opts)

