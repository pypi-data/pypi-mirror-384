"""
Miscellaneous tools for interactive messing around in Jupyter environments
"""
import sys, os, types, importlib, inspect, io, tempfile as tf
import subprocess, threading

__all__ = [
    "ModuleReloader",
    "ExamplesManager",
    "NotebookExporter",
    "FormattedTable",
    "NoLineWrapFormatter",
    "OutputCapture",
    # "SlurmTools",
    "patch_pinfo"
]

__reload_hook__ = ['.NBExporter']

class ModuleReloader:
    """
    Reloads a module & recursively descends its 'all' tree
    to make sure that all submodules are also reloaded
    """

    def __init__(self, modspec):
        """
        :param modspec:
        :type modspec: str | types.ModuleType
        """
        if isinstance(modspec, str):
            modspec=sys.modules[modspec]
        self.mod = modspec

    def get_parents(self):
        """
        Returns module parents
        :return:
        :rtype:
        """
        split = self.mod.__name__.split(".")
        return [".".join(split[:i]) for i in range(len(split)-1, 0, -1)]

    def get_members(self):
        """
        Returns module members
        :return:
        :rtype:
        """

        base = self.mod.__all__ if hasattr(self.mod, '__all__') else dir(self.mod)
        if hasattr(self.mod, '__reload_hook__'):
            try:
                others = list(self.mod.__reload_hook__)
            except TypeError:
                pass
            else:
                base = [list(base), others]
        return base

    def reload_member(self, member,
        stack=None,
        reloaded=None, blacklist=None, reload_parents=True,
        verbose=False,
        print_indent=""
        ):

        # print(print_indent + " member:", member)
        if member.startswith('.'):
            how_many = 0
            while member[how_many] == ".":
                how_many += 1
                if how_many == len(member):
                    break
            main_name = self.mod.__name__.rsplit(".", how_many)[0]
            test_key = main_name + "." + member[how_many:]
        else:
            test_key = self.mod.__name__ + "." + member
        if test_key in sys.modules:
            type(self)(test_key).reload(
                reloaded=reloaded, blacklist=blacklist,
                verbose=verbose,
                reload_parents=reload_parents, print_indent=print_indent
            )
        else:
            obj = getattr(self.mod, member)
            if isinstance(obj, types.ModuleType):
                type(self)(obj).reload(
                    reloaded=reloaded, blacklist=blacklist,
                    verbose=verbose,
                    reload_parents=reload_parents, print_indent=print_indent
                )
            elif isinstance(obj, (type, types.MethodType, types.FunctionType)):
                type(self)(obj.__module__).reload(
                    reloaded=reloaded, blacklist=blacklist,
                    verbose=verbose,
                    reload_parents=reload_parents, print_indent=print_indent
                )
            else:
                # try:
                #     isinstance(obj, (type, types.FunctionType))
                # except Exception as e:
                #     print(e)
                # else:
                #     print("...things can be functions")
                obj = type(obj)
                type(self)(obj.__module__).reload(
                    reloaded=reloaded, blacklist=blacklist,
                    verbose=verbose,
                    reload_parents=reload_parents, print_indent=print_indent
                )

    blacklist_keys = ['site-packages', os.path.abspath(os.path.dirname(inspect.getfile(os)))]
    def reload(self, 
        stack=None,
        reloaded=None, blacklist=None, reload_parents=True, 
        verbose=False,
        print_indent=""
        ):
        """
        Recursively searches for modules to reload and then reloads them.
        Uses a cache to break cyclic dependencies of any sort.
        This turns out to also be a challenging problem, since we need to basically
        load depth-first, while never jumping too far back...


        :return:
        :rtype:
        """

        if reloaded is None:
            reloaded = set()

        if blacklist is None:
            blacklist = set()
        blacklist.update(sys.builtin_module_names)

        key = self.mod.__name__
        if (
                key not in reloaded
                and key not in blacklist
                and all(k not in inspect.getfile(self.mod) for k in self.blacklist_keys)
        ):
            if verbose:
                print(print_indent + "Reloading:", self.mod.__name__)
            reloaded.add(self.mod.__name__)

            print_indent += "  "

            mems = self.get_members()

            if isinstance(mems[0], list):
                req, opts = mems
            else:
                req = mems
                opts = []

            for member in req:
                self.reload_member(member,
                                   stack=stack,
                                   reloaded=reloaded,
                                   blacklist=blacklist,
                                   reload_parents=reload_parents,
                                   verbose=verbose,
                                   print_indent=print_indent
                                   )
            for member in opts:
                try:
                    self.reload_member(member,
                                       stack=stack,
                                       reloaded=reloaded,
                                       blacklist=blacklist,
                                       reload_parents=reload_parents,
                                       verbose=verbose,
                                       print_indent=print_indent
                                       )
                except:
                    pass

           
            
            if hasattr(self.mod, '__reload_hook__'):
                try:
                    self.mod.__reload_hook__()
                except TypeError:
                    pass
            if verbose:
                print(print_indent + "loading:", self.mod.__name__)
            importlib.reload(self.mod)


            load_parents = []
            if reload_parents:
                # make sure parents get loaded in the appropriate order...
                for parent in self.get_parents():
                    if parent in reloaded:
                        # prevent us from jumping back too far...
                        break
                    # print(" storing", parent)
                    load_parents.append(parent)
                    type(self)(parent).reload(
                        reloaded=reloaded, blacklist=blacklist, 
                        reload_parents=reload_parents, verbose=verbose,
                        print_indent=print_indent
                        )

    @classmethod
    def load_module(cls, module):
        if module in sys.modules:
            cls(module).reload()
        return importlib.import_module(module)

    @classmethod
    def import_from(cls, module, names, globs=None):
        mod = cls.load_module(module)
        objs = []
        single = isinstance(names, str)
        if single: names = [names]
        for name in names:
            obj = getattr(mod, name)
            if globs is not None:
                globs[name] = obj
            objs.append(obj)
        if single: objs = objs[0]
        return objs

class NotebookExporter:
    tag_filters = {
        'cell':('ignore',),
        'output':('ignore',),
        'input':('ignore',),
    }
    def __init__(self, name,
                 src_dir=None,
                 img_prefix=None,
                 img_dir=None,
                 output_dir=None,
                 tag_filters=None
                 ):
        self.name = name
        self.src_dir = src_dir
        self.out_dir = output_dir
        self.img_dir = img_dir
        self.img_prefix = img_prefix
        self.tag_filters = self.tag_filters if tag_filters is None else tag_filters

    def load_preprocessor(self):
        from .NBExporter import MarkdownImageExtractor
        prefix = '' if self.img_prefix is None else self.img_prefix

        return MarkdownImageExtractor(prefix=prefix)#lambda *args,prefix=prefix,**kw:print(args,kw)

    def load_filters(self):
        from traitlets.config import Config

        # Setup config
        c = Config()

        # Configure tag removal - be sure to tag your cells to remove  using the
        # words remove_cell to remove cells. You can also modify the code to use
        # a different tag word

        if 'cell' in self.tag_filters:
            c.TagRemovePreprocessor.remove_cell_tags = self.tag_filters['cell']
        if 'output' in self.tag_filters:
            c.TagRemovePreprocessor.remove_all_outputs_tags = self.tag_filters['output']
        if 'input' in self.tag_filters:
            c.TagRemovePreprocessor.remove_input_tags = self.tag_filters['input']
        c.TagRemovePreprocessor.enabled = True

        # Configure and run out exporter
        c.MarkdownExporter.preprocessors = [
            self.load_preprocessor(),
            "nbconvert.preprocessors.TagRemovePreprocessor"
        ]

        return c

    def load_nb(self):
        import nbformat

        this_nb = self.name + '.ipynb'
        if self.src_dir is not None:
            this_nb = os.path.join(self.src_dir, self.name+".ipynb")
        with open(this_nb) as nb:
            nb_cells = nbformat.reads(nb.read(), as_version=4)
        return nb_cells

    def save_output_file(self, filename, body):
        fn = os.path.abspath(filename)
        if fn != filename and self.img_dir is not None:
            filename = os.path.join(self.img_dir, filename)
        with open(filename, 'wb') as out:
            out.write(body)
        return filename

    def export(self):
        from nbconvert import MarkdownExporter
        nb_cells = self.load_nb()

        exporter = MarkdownExporter(config=self.load_filters())

        (body, resources) = exporter.from_notebook_node(nb_cells)

        # raise Exception(resources)
        if len(resources['outputs']) > 0:
            for k,v in resources['outputs'].items():
                self.save_output_file(k, v)

        out_md = self.name + '.md'
        if self.out_dir is not None:
            out_md = os.path.join(self.out_dir, self.name + ".md")

        with open(out_md, 'w+') as md:
            md.write(body)

        return out_md

# class DefaultExplorerInterface:
#     def ...
# class Explorer:
#     """
#     Provides a uniform interface for exploring what objects can do.
#     Hooks into the Jupyter runtime to provide nice interfaces
#     and has support for
#     """
#     def __init__(self, obj):
#         self.obj = obj
#
#     def _ipython_display_(self):
#         raise NotImplementedError("...")

class ExamplesManager:
    data_path = ("ci", "tests", "TestData")
    examples_path = ("ci", "examples")
    def __init__(self, root, data_path=None, examples_path=None, globs=None):
        self.root = root
        if os.path.isdir(root):
            root = root
        else:
            if isinstance(root, str) and "/" not in root:
                root = importlib.import_module(root)
            if not isinstance(root, str):
                root = os.path.dirname(root.__file__)
        if data_path is None:
            data_path = self.data_path
        if isinstance(data_path, str):
            data_path = [data_path]
        self.test_dir = os.path.join(root, *data_path)
        if examples_path is None:
            examples_path = self.examples_path
        if isinstance(examples_path, str):
            examples_path = [examples_path]
        self.examples_dir = os.path.join(root, *examples_path)
        if globs is None:
            globs = inspect.stack(1)[1].frame.f_globals
        self.globs = globs

    def test_data(cls, *path):
        return os.path.join(cls.test_dir, *path)
    def examples_data(cls, *path):
        return os.path.join(cls.examples_dir, *path)

    def load_module(self, module, modify_relative_imports=True):
        if modify_relative_imports:
            if module.startswith(".") and (
                    self.root in sys.modules
                    or not os.path.isdir(self.root)
            ):
                module = self.root + module
        return ModuleReloader.load_module(module)

    def import_from(self, module, names, modify_relative_imports=True, globs=None):
        if modify_relative_imports:
            if module.startswith(".") and (
                    self.root in sys.modules
                    or not os.path.isdir(self.root)
            ):
                module = self.root + module
        if globs is None:
            globs = self.globs
        return ModuleReloader.import_from(module, names, globs=globs)


    @classmethod
    def parse_x3d_view_matrix(cls, vs, view_all=True):
        import json, numpy as np
        from .. import Numputils as nput

        # To download the image:
        """
(function(){
  var link = document.createElement('a');
  let path_array = window.location.pathname.split("/");
  let base_name = path_array[path_array.length - 1].split('.')[0];
  link.download = base_name + '.png';
  link.href = document.getElementsByTagName('canvas')[0].toDataURL()
  link.click();
})()
       """

        # vs from JSON.stringify(document.getElementById('x3d').runtime.viewMatrix())
        # vs from JSON.stringify(document.getElementsByTagName('x3d')[0].runtime.viewMatrix())
        vm = json.loads(vs)
        vm = np.linalg.inv([
            [vm[f"_{i}{j}"] for j in range(4)]
            for i in range(4)
        ])
        ang, ax = nput.extract_rotation_angle_axis(vm[:3, :3])
        v_pos = vm[:3, -1].tolist()
        v_ort = np.array(list(ax) + [ang]).tolist()
        opts = {"position": v_pos, "orientation": v_ort}
        if view_all:
            opts['viewAll'] = True
        return opts

class NoLineWrapFormatter:
    def __init__(self, *objs, white_space="pre", **opts):
        self.objs = [self._canonicalize(o) for o in objs]
        self.opts = dict(opts, white_space=white_space)
        self._widg = None
    def _canonicalize(self, o):
        if hasattr(o, 'to_widget') or hasattr(o, 'to_tree'):
            return o
        else:
            return str(o)
    def create_obj(self):
        from .JHTML import JHTML
        return JHTML.Pre(*self.objs, **self.opts)
    def to_widget(self):
        if self._widg is None:
            self._widg = self.create_obj()
        return self._widg
    # def show(self):
    #     return self.to_widget()
    def _ipython_display_(self):
        return self.to_widget()._ipython_display_()

class FormattedTable(NoLineWrapFormatter):
    def __init__(self, table_data, column_formats="8.3f", **format_opts):
        from ..Formatters import TableFormatter
        super().__init__(
            TableFormatter(column_formats, **format_opts).format(table_data)
        )


class OutputCapture:
    def __init__(self,
                 handles=None,
                 bind_global=True,
                 # bind_jupyter=None,
                 file_handles=True, autoclose=None, save_output=True):
        self.stdout, self.stderr = self.get_handles(handles, file_handles)
        self._old_stdout = None
        self._old_stderr = None
        self.bind = bind_global
        # if bind_jupyter is None:
        #     bind_jupyter = bind_global
        # self.bind_jupyter = bind_jupyter
        self._jupyter_bind = None
        if autoclose is None: autoclose = bool(file_handles)
        if autoclose is True:
            self._close = [True, True]
        elif autoclose is False:
            self._close = [False, False]
        else:
            self._close = [autoclose[0], autoclose[1]]
        self._tmp = [False, False]
        self.save = save_output
        self.outputs = None

    @classmethod
    def get_handles(cls, handles=None, file_handles=False):
        if handles is not None:
            return handles
        if not file_handles:
            return io.StringIO(), io.StringIO()
        else:
            return None, None

    @classmethod
    def get_temp_stream(cls):
        return tf.NamedTemporaryFile(mode='w+').__enter__()

    def __enter__(self):
        if self.stdout is None:
            self._tmp[0] = True
            self.stdout = self.get_temp_stream()
        if self.stderr is None:
            self._tmp[1] = True
            self.stderr = self.get_temp_stream()
        self.outputs = None
        # if self.bind_jupyter:
        #     # try:
        #     from IPython.utils import io as jio
        #     # except ImportError:
        #     #     pass
        #     # else:
        #     self._jupyter_bind = jio.capture_output(std)
        #     self._jupyter_bind.__enter__()
        if self.bind:
            self._old_stdout = sys.stdout
            self._old_stderr = sys.stderr
            sys.stdout = self.stdout
            sys.stderr = self.stderr
        return self

    def __exit__(self, *args):
        try:
            if self.save:
                try:
                    self.stdout.seek(0)
                except io.UnsupportedOperation:
                    ...
                try:
                    self.stderr.seek(0)
                except io.UnsupportedOperation:
                    ...
                self.outputs = [self.stdout.read(), self.stderr.read()]
        finally:
            if self._tmp[0]:
                self.stdout.__exit__(*args)
                self.stdout = None
            if self._tmp[1]:
                self.stderr.__exit__(*args)
                self.stderr = None
            # if self.bind_jupyter:
            #     self._jupyter_bind.__exit__(*args)
            if self.bind:
                sys.stdout = self._old_stdout
                sys.stderr = self._old_stderr


class SlurmInterface:

    @classmethod
    def format_kwargs(cls, kwargs):
        return [
            "".join([
                (
                    k
                    if k.startswith("-") else
                    "--" + k
                    if len(k) > 1 else
                    "-" + k
                ),
                " " if len(k.strip("-")) == 1 else "=",
                "" if v is True else str(v)
            ])
            for k, v in kwargs.items()
            if v is not None
        ]
    @classmethod
    def run(cls, cmd, *args, **kwargs):
        return subprocess.run([cmd, *args, *cls.format_kwargs(kwargs)],
                              capture_output=True)

    @classmethod
    def parse_slurm_table(cls, tab:str, headers=True, sep=None):
        lines = [l.strip() for l in tab.splitlines()]
        if headers:
            headers = lines[0].split(sep)
            split_rows = [r.split(sep) for r in lines[1:]]
            split_len = max(len(r) for r in split_rows)
            if split_len > len(headers):
                headers = headers + ["extra_{i}" for i in range(split_len - len(headers))]
            return [
                dict(zip(headers, r))
                for r in split_rows
            ]
        else:
            return [l.split(sep) for l in lines]

    @classmethod
    def sinfo(cls, all=None, format=None, **kw):
        if all is None: all = format is None
        if all:
            return cls.parse_slurm_table(cls.run("sinfo", format="%all").stdout.decode(), sep='|')
        else:
            base = cls.run("sinfo", format=format, **kw).stdout.decode().split("\n", 1)[-1]
            return cls.parse_slurm_table(base)

    @classmethod
    def squeue(cls, user=None, all=None, format=None, **kw):
        if all is None: all = format is None
        if all:
            return cls.parse_slurm_table(cls.run("squeue", format="%all", user=user, **kw).stdout.decode(), sep='|')
        else:
            base = cls.run("sinfo", format=format, user=user, **kw).stdout.decode().split("\n", 1)[-1]
            return cls.parse_slurm_table(base)



def patch_pinfo():
    from IPython.core.oinspect import Inspector
    from IPython.core.display import display

    if not hasattr(Inspector, '_og_pinfo'):
        Inspector._og_pinfo = Inspector.pinfo

    def pinfo(self, obj, oname='', formatter=None, info=None, detail_level=0, enable_html_pager=True):
        if hasattr(obj, '_ipython_pinfo_'):
            display(obj._ipython_pinfo_())
        else:
            return Inspector._og_pinfo(self, obj, oname=oname, formatter=formatter, info=info, detail_level=detail_level, enable_html_pager=enable_html_pager)

    Inspector.pinfo = pinfo
