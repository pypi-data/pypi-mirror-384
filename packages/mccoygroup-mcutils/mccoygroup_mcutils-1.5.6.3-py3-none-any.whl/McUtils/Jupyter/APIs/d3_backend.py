from .d3 import D3
from ..JHTML.WidgetTools import frozendict

__all__ = ["RendererD3", "FigureManagerD3", "FigureCanvasD3", "_BackendD3"]
__reload_hook__ = ["..JHTML", ".d3"]

import uuid, hashlib, itertools, io, base64, numpy as np
from PIL import Image

# from matplotlib import _api
# from matplotlib._pylab_helpers import Gcf
import matplotlib as mpl
from matplotlib import font_manager as fm
from matplotlib.backend_bases import (_Backend, FigureCanvasBase, FigureManagerBase, RendererBase)
from matplotlib.colors import rgb2hex
# from matplotlib.dates import UTC
from matplotlib.path import Path
from matplotlib import _path
from matplotlib.transforms import Affine2D, Affine2DBase

class RendererD3(RendererBase):
    """
    A modification of the base matplotlib SVG renderer to plug into the D3 library work we've done
    """

    _capstyle_d = {'projecting': 'square', 'butt': 'butt', 'round': 'round'}
    @staticmethod
    def _short_float_fmt(x):
        """
        Create a short string representation of a float, which is %f
        formatting with trailing zeros and the decimal point removed.
        """
        return f'{x:f}'.rstrip('0').rstrip('.')
    @staticmethod
    def _generate_transform(transform_list):
        parts = []
        for type, value in transform_list:
            if (type == 'scale' and (value == (1,) or value == (1, 1))
                    or type == 'translate' and value == (0, 0)
                    or type == 'rotate' and value == (0,)):
                continue
            if type == 'matrix' and isinstance(value, Affine2DBase):
                value = value.to_values()
            parts.append('{}({})'.format(type, ' '.join(RendererD3._short_float_fmt(x) for x in value)))
        return ' '.join(parts)

    def __init__(self, width, height, basename=None, image_dpi=72, *, metadata=None):
        self.width = width
        self.height = height
        self.image_dpi = image_dpi  # actual dpi at which we rasterize stuff

        if basename is None:
            basename = ""
        self.basename = basename

        self._tree = []
        self._elems = None
        self._toplevel = []
        self._defs = {'clips':{}, 'hatches':{}, 'glyphs':[], 'markers':[], 'paths':[]}
        self._groupd = {}
        self._image_counter = itertools.count()
        self._clipd = {}
        self._markers = {}
        self._path_collection_id = 0
        self._hatchd = {}
        # self._has_gouraud = False
        # self._n_gradients = 0

        super().__init__()
        self._glyph_map = dict()
        # str_height = _short_float_fmt(height)
        # str_width = _short_float_fmt(width)
        # svgwriter.write(svgProlog)
        # self._start_id = self.writer.start(
        #     'svg',
        #     width=f'{str_width}pt',
        #     height=f'{str_height}pt',
        #     viewBox=f'0 0 {str_width} {str_height}',
        #     xmlns="http://www.w3.org/2000/svg",
        #     version="1.1",
        #     attrib={'xmlns:xlink': "http://www.w3.org/1999/xlink"})
        # self._write_metadata(metadata)
        # self._write_default_style()

    def open_group(self, s, gid=None):
        # print(" "*len(self._tree), ">>", s)
        self._elems = []
        self._tree.append([s, gid, self._elems])
    def close_group(self, s):
        tag, gid, elems = self._tree.pop()
        # print(" "*len(self._tree), "<<", s)
        el = D3.Group(
            *elems,
            cls=tag.replace('.', '-'),
            id=gid
        )
        if len(self._tree) == 0:
            self._elems = None
            self._toplevel.append(el)
        else:
            self._elems = self._tree[-1][-1]
            self._elems.append(el)

    def write_defs(self):
        self._write_clips()
        self._write_hatches()
        # self.writer.close(self._start_id)
        # self.writer.flush()

    def _make_id(self, type, content):
        salt = mpl.rcParams['svg.hashsalt']
        if salt is None:
            salt = str(uuid.uuid4())
        m = hashlib.sha256()
        m.update(salt.encode('utf8'))
        m.update(str(content).encode('utf8'))
        return f'{type}{m.hexdigest()[:10]}'

    def _make_flip_transform(self, transform):
        return transform + Affine2D().scale(1, -1).translate(0, self.height)

    def _get_hatch(self, gc, rgbFace):
        """
        Create a new hatch pattern
        """
        if rgbFace is not None:
            rgbFace = tuple(rgbFace)
        edge = gc.get_hatch_color()
        if edge is not None:
            edge = tuple(edge)
        dictkey = (gc.get_hatch(), rgbFace, edge)
        oid = self._hatchd.get(dictkey)
        if oid is None:
            oid = self._make_id('h', dictkey)
            self._hatchd[dictkey] = ((gc.get_hatch_path(), rgbFace, edge), oid)
        else:
            _, oid = oid
        return oid

    def _write_hatches(self):
        if not len(self._hatchd):
            return
        hatch_data = []
        HATCH_SIZE = 72
        for hatch_key,(path, face, stroke), oid in self._hatchd.items():
            if hatch_key not in self._defs['hatches']:
                path_data = self._convert_path(
                    path,
                    Affine2D().scale(HATCH_SIZE).scale(1.0, -1.0).translate(0, HATCH_SIZE),
                    simplify=False
                )
                if face is None:
                    fill = 'none'
                else:
                    fill = rgb2hex(face)

                self._defs['hatches'][hatch_key] = D3.Pattern(
                        D3.Rect(x=0, y=0, width=HATCH_SIZE + 1, height=HATCH_SIZE + 1, fill=fill),
                        D3.Path(d=path_data, fill=rgb2hex(stroke), stroke=rgb2hex(stroke),
                                stroke_width=mpl.rcParams['hatch.linewidth'],
                                stroke_linecap='butt',
                                stroke_linejoin='miter'
                                ),
                        id=oid,
                        patternUnits="userSpaceOnUse",
                        x=0, y=0,
                        width=HATCH_SIZE,
                        height=HATCH_SIZE
                    )

    def _get_style_dict(self, gc, rgbFace):
        """Generate a style string from the GraphicsContext and rgbFace."""
        attrib = {}

        forced_alpha = gc.get_forced_alpha()

        if gc.get_hatch() is not None:
            attrib['fill'] = f"url(#{self._get_hatch(gc, rgbFace)})"
            if (rgbFace is not None and len(rgbFace) == 4 and rgbFace[3] != 1.0
                    and not forced_alpha):
                attrib['fill-opacity'] = rgbFace[3]
        else:
            if rgbFace is None:
                attrib['fill'] = 'none'
            else:
                if tuple(rgbFace[:3]) != (0, 0, 0):
                    attrib['fill'] = rgb2hex(rgbFace)
                if (len(rgbFace) == 4 and rgbFace[3] != 1.0
                        and not forced_alpha):
                    attrib['fill-opacity'] = rgbFace[3]

        if forced_alpha and gc.get_alpha() != 1.0:
            attrib['opacity'] = gc.get_alpha()

        offset, seq = gc.get_dashes()
        if seq is not None:
            attrib['stroke-dasharray'] = ','.join(val for val in seq)
            attrib['stroke-dashoffset'] = self._short_float_fmt(offset)

        linewidth = gc.get_linewidth()
        if linewidth:
            rgb = gc.get_rgb()
            attrib['stroke'] = rgb2hex(rgb)
            if not forced_alpha and rgb[3] != 1.0:
                attrib['stroke-opacity'] = rgb[3]
            if linewidth != 1.0:
                attrib['stroke-width'] = linewidth
            if gc.get_joinstyle() != 'round':
                attrib['stroke-linejoin'] = gc.get_joinstyle()
            if gc.get_capstyle() != 'butt':
                attrib['stroke-linecap'] = self._capstyle_d[gc.get_capstyle()]

        return attrib

    def _get_style(self, gc, rgbFace):
        return self._get_style_dict(gc, rgbFace)

    def _get_clip_attrs(self, gc):
        cliprect = gc.get_clip_rectangle()
        clippath, clippath_trans = gc.get_clip_path()
        if clippath is not None:
            clippath_trans = self._make_flip_transform(clippath_trans)
            dictkey = (id(clippath), str(clippath_trans))
        elif cliprect is not None:
            x, y, w, h = cliprect.bounds
            y = self.height-(y+h)
            dictkey = (x, y, w, h)
        else:
            return {}
        clip = self._clipd.get(dictkey)
        if clip is None:
            oid = self._make_id('p', dictkey)
            if clippath is not None:
                self._clipd[dictkey] = ((clippath, clippath_trans), oid)
            else:
                self._clipd[dictkey] = (dictkey, oid)
        else:
            clip, oid = clip
        return {'clip-path': f'url(#{oid})'}

    def _write_clips(self):
        if not len(self._clipd):
            return
        clip_paths = []
        for clip_key,(clip, oid) in self._clipd.items():
            if clip_key not in self._defs['clips']:
                if len(clip) == 2:
                    clippath, clippath_trans = clip
                    path_data = self._convert_path(clippath, clippath_trans, simplify=False)
                    clip_shape = D3.Path(d=path_data)
                else:
                    x, y, w, h = clip
                    clip_shape = D3.Rect(x=x, y=y, width=w, height=h)
                self._defs['clips'][clip_key] = D3.ClipPath(clip_shape, id=oid)

    def option_image_nocomposite(self):
        # docstring inherited
        return not mpl.rcParams['image.composite_image']

    def _convert_path(self, path, transform=None, clip=None, simplify=None, sketch=None):
        if clip:
            clip = (0.0, 0.0, self.width, self.height)
        else:
            clip = None
        return _path.convert_to_string(
            path, transform, clip, simplify, sketch, 6,
            [b'M', b'L', b'Q', b'C', b'z'], False).decode('ascii')

    def draw_path(self, gc, path, transform, rgbFace=None):
        # docstring inherited
        trans_and_flip = self._make_flip_transform(transform)
        clip = (rgbFace is None and gc.get_hatch_path() is None)
        simplify = path.should_simplify and clip
        path_data = self._convert_path(
            path, trans_and_flip, clip=clip, simplify=simplify,
            sketch=gc.get_sketch_params()
        )
        path = D3.Path(
            d=path_data,
            **self._get_clip_attrs(gc),
            style=self._get_style(gc, rgbFace)
        )
        if gc.get_url() is not None:
            path = D3.Link(
                path,
                **{'xlink:hred':gc.get_url()}
            )
        self._elems.append(path)

    def draw_markers(self, gc, marker_path, marker_trans, path, trans, rgbFace=None):
        if not len(path.vertices):
            return

        path_data = self._convert_path(
            marker_path,
            marker_trans + Affine2D().scale(1.0, -1.0),
            simplify=False)
        style = self._get_style_dict(gc, rgbFace)
        dictkey = (path_data, frozendict(style))
        oid = self._markers.get(dictkey)
        style = {k: v for k, v in style.items() if k.startswith('stroke')}

        if oid is None:
            oid = self._make_id('m', dictkey)
            self._defs['markers'].append(D3.Path(id=oid, d=path_data, style=style))
            self._markers[dictkey] = oid

        # writer.start('g', **self._get_clip_attrs(gc))
        trans_and_flip = self._make_flip_transform(trans)
        attrib = {'xlink:href': f'#{oid}'}
        clip = (0, 0, self.width*72, self.height*72)
        uses = []
        for vertices, code in path.iter_segments(trans_and_flip, clip=clip, simplify=False):
            if len(vertices):
                x, y = vertices[-2:]
                attrib['x'] = self._short_float_fmt(x)
                attrib['y'] = self._short_float_fmt(y)
                attrib['style'] = self._get_style(gc, rgbFace)
                uses.append(D3.Use(**attrib))
        self._elems.append(D3.Group(*uses, **self._get_clip_attrs(gc)))

    def draw_path_collection(self, gc, master_transform, paths, all_transforms,
                             offsets, offset_trans, facecolors, edgecolors,
                             linewidths, linestyles, antialiaseds, urls,
                             offset_position):
        # Is the optimization worth it? Rough calculation:
        # cost of emitting a path in-line is
        #    (len_path + 5) * uses_per_path
        # cost of definition+use is
        #    (len_path + 3) + 9 * uses_per_path
        len_path = len(paths[0].vertices) if len(paths) > 0 else 0
        uses_per_path = self._iter_collection_uses_per_path(
            paths, all_transforms, offsets, facecolors, edgecolors)
        should_do_optimization = len_path + 9 * uses_per_path + 3 < (len_path + 5) * uses_per_path
        if not should_do_optimization:
            return super().draw_path_collection(
                gc, master_transform, paths, all_transforms,
                offsets, offset_trans, facecolors, edgecolors,
                linewidths, linestyles, antialiaseds, urls,
                offset_position
            )

        path_codes = {}
        for i, (path, transform) in enumerate(
                self._iter_collection_raw_paths(master_transform, paths, all_transforms)
        ):
            transform = Affine2D(transform.get_matrix()).scale(1.0, -1.0)
            d = self._convert_path(path, transform, simplify=False)
            oid = 'C{:x}_{:x}_{}'.format(self._path_collection_id, i, self._make_id('', d))
            path_codes[oid] = D3.Path(id=oid, d=d)
        self._defs['paths'].extend(*path_codes.values())

        collections = []
        for xo, yo, path_id, gc0, rgbFace in self._iter_collection(
                gc, path_codes, offsets, offset_trans,
                facecolors, edgecolors, linewidths, linestyles,
                antialiaseds, urls, offset_position
        ):
            url = gc0.get_url()
            attrib = {
                'xlink:href': f'#{path_id}',
                'x': self._short_float_fmt(xo),
                'y': self._short_float_fmt(self.height - yo),
                'style': self._get_style(gc0, rgbFace)
                }
            elem = D3.Use(**attrib)
            clip_attrs = self._get_clip_attrs(gc0)
            if clip_attrs:
                elem = D3.Group(elem, **clip_attrs)
            if url is not None:
                elem = D3.Link(elem, **{'xlink:href': url})
            collections.append(elem)
        self._path_collection_id += 1
        self._elems.extend(collections)

    def option_scale_image(self):
        # docstring inherited
        return True

    def get_image_magnification(self):
        return self.image_dpi / 72.0

    def draw_image(self, gc, x, y, im, transform=None):

        h, w = im.shape[:2]

        if w == 0 or h == 0:
            return

        attrib = {}
        oid = gc.get_gid()
        # if mpl.rcParams['svg.image_inline']:
        buf = io.BytesIO()
        Image.fromarray(im).save(buf, format="png")
        oid = oid or self._make_id('image', buf.getvalue())
        attrib['xlink:href'] = (
            "data:image/png;base64,\n" +
            base64.b64encode(buf.getvalue()).decode('ascii')
        )
        # else:
        #     if self.basename is None:
        #         raise ValueError("Cannot save image data to filesystem when "
        #                          "writing SVG to an in-memory buffer")
        #     filename = f'{self.basename}.image{next(self._image_counter)}.png'
        #     # _log.info('Writing image file for inclusion: %s', filename)
        #     Image.fromarray(im).save(filename)
        #     oid = oid or 'Im_' + self._make_id('image', filename)
        #     attrib['xlink:href'] = filename
        attrib['id'] = oid

        if transform is None:
            w = 72.0 * w / self.image_dpi
            h = 72.0 * h / self.image_dpi

            elem = D3.Image(
                transform=self._generate_transform([('scale', (1, -1)), ('translate', (0, -h))]),
                x=x,
                y=-(self.height - y - h),
                width=w, height=h,
                **attrib
            )
        else:
            alpha = gc.get_alpha()
            if alpha != 1.0:
                attrib['opacity'] = alpha

            flipped = (
                Affine2D().scale(1.0 / w, 1.0 / h) +
                transform +
                Affine2D()
                .translate(x, y)
                .scale(1.0, -1.0)
                .translate(0.0, self.height)
            )

            attrib['transform'] = self._generate_transform([('matrix', flipped.frozen())])
            attrib['style'] = (
                'image-rendering:crisp-edges;'
                'image-rendering:pixelated')
            elem = D3.Image(width=w, height=h, **attrib)

        clip_attrs = self._get_clip_attrs(gc)
        if clip_attrs:
            # Can't apply clip-path directly to the image because the image has
            # a transformation, which would also be applied to the clip-path.
            elem = D3.Group(elem, **clip_attrs)

        url = gc.get_url()
        if url is not None:
            elem = D3.Link(elem, **{'xlink:href': url})

        self._elems.append(elem)

    def _update_glyph_map_defs(self, glyph_map_new):
        """
        Emit definitions for not-yet-defined glyphs, and record them as having
        been defined.
        """
        if glyph_map_new:
            new_glyphs = []
            for char_id, (vertices, codes) in glyph_map_new.items():
                char_id = self._adjust_char_id(char_id)
                # x64 to go back to FreeType's internal (integral) units.
                path_data = self._convert_path(
                    Path(vertices * 64, codes), simplify=False)
                new_glyphs.append(
                    D3.Path(
                        id=char_id,
                        d=path_data,
                        transform=self._generate_transform([('scale', (1 / 64,))])
                    )
                )
            self._defs['glyphs'].extend(new_glyphs)
            self._glyph_map.update(glyph_map_new)

    def _adjust_char_id(self, char_id):
        return char_id.replace("%20", "_")

    def _draw_text_as_path(self, gc, x, y, s, prop, angle, ismath, mtext=None):
        # docstring inherited

        # HTML.comment(s)

        glyph_map = self._glyph_map

        text2path = self._text2path
        color = rgb2hex(gc.get_rgb())
        fontsize = prop.get_size_in_points()

        style = {}
        if color != '#000000':
            style['fill'] = color
        alpha = gc.get_alpha() if gc.get_forced_alpha() else gc.get_rgb()[3]
        if alpha != 1:
            style['opacity'] = alpha
        font_scale = fontsize / text2path.FONT_SCALE
        text_group_attrib = {
            'style': style,
            'transform': self._generate_transform([
                ('translate', (x, y)),
                ('rotate', (-angle,)),
                ('scale', (font_scale, -font_scale))]),
        }

        paths = []
        if not ismath:
            font = text2path._get_font(prop)
            _glyphs = text2path.get_glyphs_with_font(
                font, s, glyph_map=glyph_map, return_new_glyphs_only=True)
            glyph_info, glyph_map_new, rects = _glyphs
            self._update_glyph_map_defs(glyph_map_new)

            for glyph_id, xposition, yposition, scale in glyph_info:
                attrib = {'xlink:href': f'#{glyph_id}'}
                if xposition != 0.0:
                    attrib['x'] = self._short_float_fmt(xposition)
                if yposition != 0.0:
                    attrib['y'] = self._short_float_fmt(yposition)
                paths.append(D3.Use(**attrib))

        else:
            if ismath == "TeX":
                _glyphs = text2path.get_glyphs_tex(
                    prop, s, glyph_map=glyph_map, return_new_glyphs_only=True)
            else:
                _glyphs = text2path.get_glyphs_mathtext(
                    prop, s, glyph_map=glyph_map, return_new_glyphs_only=True)
            glyph_info, glyph_map_new, rects = _glyphs
            self._update_glyph_map_defs(glyph_map_new)

            for char_id, xposition, yposition, scale in glyph_info:
                char_id = self._adjust_char_id(char_id)
                paths.append(
                    D3.Use(
                        transform=self._generate_transform([
                            ('translate', (xposition, yposition)),
                            ('scale', (scale,)),
                            ]),
                        **{'xlink:href': f'#{char_id}'}
                    )
                )

            for verts, codes in rects:
                path = Path(verts, codes)
                path_data = self._convert_path(path, simplify=False)
                paths.append(D3.Path(d=path_data))

        return D3.Group( # TODO: add comments
            *paths,
            **text_group_attrib
        )

    def _draw_text_as_text(self, gc, x, y, s, prop, angle, ismath, mtext=None):

        color = rgb2hex(gc.get_rgb())
        style = {}
        if color != '#000000':
            style['fill'] = color

        alpha = gc.get_alpha() if gc.get_forced_alpha() else gc.get_rgb()[3]
        if alpha != 1:
            style['opacity'] = alpha

        if not ismath:
            attrib = {}

            font_parts = []
            if prop.get_style() != 'normal':
                font_parts.append(prop.get_style())
            if prop.get_variant() != 'normal':
                font_parts.append(prop.get_variant())
            weight = fm.weight_dict[prop.get_weight()]
            if weight != 400:
                font_parts.append(f'{weight}')

            def _normalize_sans(name):
                return 'sans-serif' if name in ['sans', 'sans serif'] else name

            def _expand_family_entry(fn):
                fn = _normalize_sans(fn)
                # prepend generic font families with all configured font names
                if fn in fm.font_family_aliases:
                    # get all of the font names and fix spelling of sans-serif
                    # (we accept 3 ways CSS only supports 1)
                    for name in mpl.rcParams['font.' + fn]:
                        yield _normalize_sans(name)
                # whether a generic name or a family name, it must appear at
                # least once
                yield fn

            def _get_all_quoted_names(prop):
                # only quote specific names, not generic names
                return [name if name in fm.font_family_aliases else repr(name)
                        for entry in prop.get_family()
                        for name in _expand_family_entry(entry)]

            font_parts.extend([
                f'{self._short_float_fmt(prop.get_size())}px',
                # ensure expansion, quoting, and dedupe of font names
                ", ".join(dict.fromkeys(_get_all_quoted_names(prop)))
            ])
            style['font'] = ' '.join(font_parts)
            if prop.get_stretch() != 'normal':
                style['font-stretch'] = prop.get_stretch()
            attrib['style'] = style

            if mtext and (angle == 0 or mtext.get_rotation_mode() == "anchor"):
                # If text anchoring can be supported, get the original
                # coordinates and add alignment information.

                # Get anchor coordinates.
                transform = mtext.get_transform()
                ax, ay = transform.transform(mtext.get_unitless_position())
                ay = self.height - ay

                # Don't do vertical anchor alignment. Most applications do not
                # support 'alignment-baseline' yet. Apply the vertical layout
                # to the anchor point manually for now.
                angle_rad = np.deg2rad(angle)
                dir_vert = np.array([np.sin(angle_rad), np.cos(angle_rad)])
                v_offset = np.dot(dir_vert, [(x - ax), (y - ay)])
                ax = ax + v_offset * dir_vert[0]
                ay = ay + v_offset * dir_vert[1]

                ha_mpl_to_svg = {'left': 'start', 'right': 'end',
                                 'center': 'middle'}
                style['text-anchor'] = ha_mpl_to_svg[mtext.get_ha()]

                attrib['x'] = self._short_float_fmt(ax)
                attrib['y'] = self._short_float_fmt(ay)
                attrib['style'] = style
                attrib['transform'] = self._generate_transform([
                    ("rotate", (-angle, ax, ay))])

            else:
                attrib['transform'] = self._generate_transform([
                    ('translate', (x, y)),
                    ('rotate', (-angle,))])

            return D3.Text(s, **attrib)

        else:
            # writer.comment(s)

            width, height, descent, glyphs, rects = \
                self._text2path.mathtext_parser.parse(s, 72, prop)

            # Apply attributes to 'g', not 'text', because we likely have some
            # rectangles as well with the same style and transformation.
            group_attrs = dict(
                style=style,
                transform=self._generate_transform([
                    ('translate', (x, y)),
                    ('rotate', (-angle,))
                ]),
            )

            # Sort the characters by font, and output one tspan for each.
            spans = {}
            for font, fontsize, thetext, new_x, new_y in glyphs:
                entry = fm.ttfFontProperty(font)
                font_parts = []
                if entry.style != 'normal':
                    font_parts.append(entry.style)
                if entry.variant != 'normal':
                    font_parts.append(entry.variant)
                if entry.weight != 400:
                    font_parts.append(f'{entry.weight}')
                font_parts.extend([
                    f'{self._short_float_fmt(fontsize)}px',
                    f'{entry.name!r}',  # ensure quoting
                ])
                style = {'font': ' '.join(font_parts)}
                if entry.stretch != 'normal':
                    style['font-stretch'] = entry.stretch
                style = style
                if thetext == 32:
                    thetext = 0xa0  # non-breaking space
                spans.setdefault(style, []).append((new_x, -new_y, thetext))


            text_elems = []
            for style, chars in spans.items():
                chars.sort()

                if len({y for x, y, t in chars}) == 1:  # Are all y's the same?
                    ys = str(chars[0][1])
                else:
                    ys = ' '.join(str(c[1]) for c in chars)

                attrib = {
                    'style': style,
                    'x': ' '.join(self._short_float_fmt(c[0]) for c in chars),
                    'y': ys
                }

                text_elems.append(D3.TextSpan(
                    ''.join(chr(c[2]) for c in chars),
                    **attrib
                ))

            group_elems = [ D3.Text(*text_elems) ]
            for x, y, width, height in rects:
                group_elems.append(
                    D3.Rect(
                        x=x,
                        y=-y - 1,
                        width=width,
                        height=height
                    )
                )

            return D3.Group(
                *group_elems,
                **group_attrs
            )

    text_as_path = False
    def draw_text(self, gc, x, y, s, prop, angle, ismath=False, mtext=None):
        # docstring inherited

        if self.text_as_path:#mpl.rcParams['svg.fonttype'] == 'path':
            text_elem = self._draw_text_as_path(gc, x, y, s, prop, angle, ismath, mtext)
        else:
            text_elem = self._draw_text_as_text(gc, x, y, s, prop, angle, ismath, mtext)

        clip_attrs = self._get_clip_attrs(gc)
        if clip_attrs:
            # Cannot apply clip-path directly to the text, because
            # it has a transformation
            text_elem = D3.Group(text_elem, **clip_attrs)

        if gc.get_url() is not None:
            text_elem = D3.Link(text_elem, **{'xlink:href': gc.get_url()})

        self._elems.append(text_elem)

    def flipy(self):
        # docstring inherited
        return True

    def get_canvas_width_height(self):
        # docstring inherited
        return self.width, self.height

    def get_text_width_height_descent(self, s, prop, ismath):
        # docstring inherited
        return self._text2path.get_text_width_height_descent(s, prop, ismath)

    def get_toplevel(self):
        big_defs = []
        for def_list in self._defs.values():
            if isinstance(def_list, dict):
                big_defs.extend(def_list.values())
            else:
                big_defs.extend(def_list)
        elems = []
        if len(big_defs) > 0:
            elems.append(D3.Definitions(*big_defs))
        elems.extend(self._toplevel)

        return elems
    def insert_d3(self, root:'D3.Frame'):
        """
        width='%spt' % str_width,
        height='%spt' % str_height,
        viewBox='0 0 %s %s' % (str_width, str_height),
        xmlns="http://www.w3.org/2000/svg",
        version="1.1",
        attrib={'xmlns:xlink': "http://www.w3.org/1999/xlink"}
        :param root:
        :return:
        """
        elems = self.get_toplevel()
        root.svg.attrs = dict(
            width='{}pt'.format(self.width),
            height='{}pt'.format(self.height),
            viewBox='0 0 {w} {h}'.format(w=self.width, h=self.height),
            xmlns="http://www.w3.org/2000/svg",
            version="1.1"
            # attrib={'xmlns:xlink': "http://www.w3.org/1999/xlink"}
        )
        root.svg.elems = elems
        # for e in elems:
        #     root.append(e)

class FigureManagerD3(FigureManagerBase):
    """
    Manages a set of D3 canvases by providing a
    """

    def __init__(self, canvas:'FigureCanvasD3', num):
        # _log.debug("%s - __init__()", type(self))
        self.frame = D3.Frame()
        super().__init__(canvas, num)
        canvas.manager = self

    # @classmethod
    # def create_with_canvas(cls, canvas_class, figure, num):
    #     # docstring inherited
    #     frame = D3.Frame()
    #     return cls(canvas_class(figure=figure), frame, num)
    #     # return manager

    # @classmethod
    # def start_main_loop(cls):
    #     # no action needed, managed via Jupyter widgets
    #     ...

    def show(self):
        if not hasattr(self.canvas.figure, '_called_show') or self.canvas.figure._called_show:
            # self.frame.append(self.canvas.root)
            self.canvas.draw()
            self.frame.invalidate_cache()
            self.frame.display()

    # def destroy(self, *args):
    #     # no action needed, managed via Jupyter widgets
    #     ...

    def full_screen_toggle(self):
        raise NotImplementedError("can't make full screen...")
    def get_window_title(self):
        ...
        # # docstring inherited
        # return self.window.GetTitle()

    def set_window_title(self, title):
        ...
        # docstring inherited
        # self.window.SetTitle(title)

    def resize(self, width, height):
        dpi = self.canvas.figure.dpi
        self.frame.attr(height=height*dpi, width=width*dpi)

class FigureCanvasD3(FigureCanvasBase):
    """
    The canvas the figure renders into.  Calls the draw and print fig
    methods, creates the renderers, etc.

    Note: GUI templates will want to connect events for button presses,
    mouse movements and key presses to functions that call the base
    class methods button_press_event, button_release_event,
    motion_notify_event, key_press_event, and key_release_event.  See the
    implementations of the interactive backends for examples.

    Attributes
    ----------
    figure : `~matplotlib.figure.Figure`
        A high-level Figure instance
    """

    # The instantiated manager class.  For further customization,
    # ``FigureManager.create_with_canvas`` can also be overridden; see the
    # wx-based backends for an example.
    manager_class = FigureManagerD3

    def __init__(self, figure=None, manager=None):
        super().__init__(figure=figure)
        # self.root = D3.SVG()
        self.manager = manager

    def draw(self, clear=False):
        """
        Draw the figure using the renderer.

        It is important that this method actually walk the artist tree
        even if not output is produced because this will trigger
        deferred work (like computing limits auto-limits and tick
        values) that users may want access to before saving to disk.
        """
        wi, hi = self.figure.get_size_inches()
        dpi = self.figure.dpi
        renderer = RendererD3(wi*dpi, hi*dpi, image_dpi=self.figure.dpi)
        # print(self.figure.get_children()[1].get_children())
        self.figure.draw(renderer)
        # if clear:
        #     self.root.clear()
        renderer.insert_d3(self.manager.frame)

    @classmethod
    def render_objects(cls, figure, obj):
        wi, hi = figure.get_size_inches()
        dpi = figure.dpi
        renderer = RendererD3(wi * dpi, hi * dpi, image_dpi=figure.dpi)
        # print(self.figure.get_children()[1].get_children())
        if hasattr(obj, 'draw'):
            obj = [obj]
        for o in obj:
            o.draw(renderer)
        # if clear:
        #     self.root.clear()
        return renderer.get_toplevel()


########################################################################
#
# Now just provide the standard names that backend.__init__ is expecting
#
########################################################################

@_Backend.export
class _BackendD3(_Backend):
    FigureCanvas = FigureCanvasD3
    FigureManager = FigureManagerD3

