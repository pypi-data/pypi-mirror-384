import os
import re
import json
from .. import Devutils as dev
from .JHTML import JHTML
from ..ExternalPrograms import PILInterface

__all__ = [
    "NotebookReader"
]

class NotebookReader:
    def __init__(self, json_or_fp):
        self._name = None
        self._nb_json = None
        self._init_data = json_or_fp

    class NotebookCell:
        def __init__(self, nb:'NotebookReader', cell_data):
            self.nb = nb
            self.data = cell_data
            self._attachments = None
        @property
        def cell_type(self):
            return self.data['cell_type']
        @property
        def cell_index(self):
            return self.data.get('cell_index', None)
        def __repr__(self):
            cls = type(self)
            return f"{cls.__name__}(<{self.cell_index}>, '{self.cell_type}')"
        @property
        def attachments(self):
            return self.prep_attachments(self.nb, self.data.get('attachments', {}))
        def get_images(self):
            return {
                k:PILInterface.from_url(v.attrs['src'])
                for k,v in self.attachments.items()
                if k.startswith('image/')
            }
        @property
        def source(self):
            return self.data["source"]
        @property
        def text(self):
            if isinstance(self.data['source'], str):
                return self.data['source']
            else:
                return ''.join(self.data['source'])

        @classmethod
        def get_cell_header(cls, data):
            src = data['source']
            if len(src) == 0: return None

            if not isinstance(src, str):
                src = src[0]
            if src.strip().startswith("#"):
                return src.splitlines()[0].strip("#").strip()
            else:
                return None
        @property
        def cell_header(self):
            return self.get_cell_header(self.data)
        @property
        def html(self):
            return self.nb.get_mime_type_loader("text/html")(self.text)
        @classmethod
        def prep_attachments(cls, nb, attachment_data):
            attachments = {}
            for file_name,attachment_data in attachment_data.items():
                return {
                    mime_type: nb.get_mime_type_loader(mime_type)(value)
                    for mime_type, value in attachment_data.items()
                }
            return attachments

    def cell(self, data):
        return self.NotebookCell(self, data)
    def get_mime_image_loader(self, img_type):
        def load(data):
            return JHTML.Image(src=f"data:{img_type};base64,{data}")
        return load
    def get_mime_type_loader(self, mime_type):
        if mime_type.split("/")[0] == "image":
            return self.get_mime_image_loader(mime_type)
        else:
            return JHTML.Pre

    class CellList:
        def __init__(self, nb:'NotebookReader', cell_list):
            self.nb = nb
            self.cell_list = cell_list

        def __repr__(self):
            cls = type(self)
            return f"{cls.__name__}(<{len(self.cell_list)}>)"
        def __len__(self):
            return len(self.cell_list)
        def __iter__(self):
            for c in self.cell_list:
                yield self.nb.cell(c)
        def __getitem__(self, item):
            return self.nb.cell(self.cell_list[item])

        def modify(self, cells=None, *, nb=None):
            if nb is None:
                nb = self.nb
            return type(self)(nb, cells)
        def filter_cells(self, filter):
            return self.modify(
                [
                    dict(c, cell_index=i)
                        if 'cell_index' not in c
                    else c
                    for i, c in enumerate(self.cell_list)
                    if filter(c)
                ]
            )
        def find_cells_by_type(self, pattern):
            pattern = self.prep_regex(pattern)
            return self.filter_cells(
                lambda c: re.match(pattern, c['cell_type'])
            )
        def _match_header(self, pattern, data):
            header = self.nb.NotebookCell.get_cell_header(data)
            if header is None:
                return False
            else:
                return re.match(pattern, header)
        def find_cells_by_header(self, pattern):
            pattern = self.prep_regex(pattern)
            return self.filter_cells(
                lambda c: self._match_header(pattern, c)
            )
        def find_cells_with_attachments(self, pattern=None):
            if pattern is None:
                pattern = ".+"
            pattern = self.prep_regex(pattern)
            return self.filter_cells(
                lambda c: any(
                    any(re.match(pattern, mime) for mime in a_dat.keys())
                    for a_dat in c.get('attachments', {}).values()
                )
            )

        @classmethod
        def prep_regex(self, pattern, flags=None):
            if isinstance(pattern, tuple):
                pattern = "|".join(pattern)
            if isinstance(pattern, str):
                if flags is None:
                    pattern = re.compile(pattern)
                else:
                    pattern = re.compile(pattern, flags=flags)
            return pattern

    def cell_list(self, cells=None):
        if cells is None:
            cells = self.nb_json['cells']
        if isinstance(cells, dict):
            cells = [cells]
        return self.CellList(self, cells)

    def __repr__(self):
        cls = type(self)
        return f"{cls.__name__}('{self.file_name}')"

    def load_notebook(self, nb_js):
        if isinstance(nb_js, dict):
            name = self.get_notebook_name(nb_js)
        elif isinstance(nb_js, str) and nb_js.strip().startswith('{'):
            name = self.get_notebook_name(nb_js)
            nb_js = json.loads(nb_js)
        else:
            name = nb_js
            nb_js = dev.read_json(nb_js)
        return name, nb_js
    def get_notebook_name(self, nb_js=None):
        if nb_js is None:
            nb_js = self.nb_json
        md_cells = self.cell_list(nb_js['cells']).find_cells_by_type('markdown')
        if len(md_cells) > 0:
            for c in md_cells:
                h = c.cell_header
                if h is not None and len(h) > 0: return h
            else:
                return md_cells[0].text.splitlines()[0].strip()
        else:
            return "Unnamed"
    @property
    def file_name(self):
        if self._nb_json is None:
            self._name, self._nb_json = self.load_notebook(self._init_data)
        return self._name

    @property
    def nb_json(self):
        if self._nb_json is None:
            self._name, self._nb_json = self.load_notebook(self._init_data)
        return self._nb_json


    @classmethod
    def get_notebook_files(cls, directory='.'):
        return [
            o for o in os.listdir(directory)
            if os.path.isfile(o) and os.path.splitext(o)[-1] == '.ipynb'
        ]
    @classmethod
    def sort_by_evaluation_time(cls, file_list, directory='.'):
        return list(sorted(
            file_list,
            key=lambda o:os.path.getmtime(os.path.join(directory, o))
        ))
    @classmethod
    def active_notebook(cls, directory='.'):
        nb_files = cls.sort_by_evaluation_time(cls.get_notebook_files(directory))
        if len(nb_files) == 0:
            return None
        else:
            return cls(nb_files[0])
