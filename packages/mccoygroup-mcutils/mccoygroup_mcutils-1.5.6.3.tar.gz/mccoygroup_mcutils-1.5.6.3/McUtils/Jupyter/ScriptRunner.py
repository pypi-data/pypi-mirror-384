import collections
import enum, types, ast
import os, sys, tempfile, uuid
import subprocess, inspect
import threading
import weakref

from ..Scaffolding import Checkpointer

__all__ = [
    "ScriptContext",
    "ScriptRunner"
]

class Sentinels(enum.Enum):
    Missing = 'missing'

class ScriptContext:
    def __init__(self,
                 objects:dict,
                 imports=None,
                 script_dir=None,
                 script_id=None,
                 context_file=None,
                 autodelete=None,
                 path=None):
        if script_dir is None:
            script_dir = self.get_dir()
        self.dir = script_dir
        self.imps = [] if imports is None else list(imports)
        self.objs = objects
        if path is None:
            path = sys.path
        self.path = path
        if script_id is None:
            script_id = str(uuid.uuid4())
        if context_file is None:
            if autodelete is None: autodelete = True
            context_file = self.get_context_file(script_id)
        self.autodelete = autodelete
        self.context_file = context_file
        self._depth = 0

    @classmethod
    def get_dir(cls):
        return os.getcwd()


    context_file_name = 'context-'
    context_file_extension = '.hdf5'
    @classmethod
    def get_context_file(cls, script_id):
        with tempfile.NamedTemporaryFile(prefix=cls.context_file_name+str(script_id), suffix=cls.context_file_extension) as tf:
            return tf.name

    def populate_context_file(self):
        if len(self.objs) > 0:
            mods = {
                k:v for k,v in self.objs.items()
                if isinstance(v, types.ModuleType)
            }
            imports = [
                name if val.__name__ == name else ["", val.__name__, name]
                for name, val in mods.items()
            ]
            objs = {
                k: v for k, v in self.objs.items()
                if not isinstance(v, types.ModuleType)
            }
            if len(mods) == len(self.objs):
                context_file = None
            else:
                with Checkpointer.from_file(self.context_file) as chk:
                    chk["_context_names"] = list(objs.keys())
                    for name,val in self.objs.items():
                        if not isinstance(val, types.ModuleType):
                            chk[name] = val
                context_file = self.context_file
            return self.imps + imports, context_file
        elif len(self.imps) > 0:
            return self.imps, None
        else:
            return None

    @classmethod
    def load_context(cls, context_file):
        chk = Checkpointer.from_file(context_file)
        keys = [
            k.decode() if not isinstance(k, str) else k
            for k in chk["_context_names"]
        ]
        with chk:
            return {
                k:chk[k]
                for k in keys
            }

    @classmethod
    def path_loader_template(cls, path):
        return f"""
import sys
for p in {path}:
    if p not in sys.path: sys.path.append(p)
"""

    @classmethod
    def context_loader_template(cls, context_file):
        return f"""
import McUtils.Jupyter as interactive
g = globals()
for k,v in interactive.ScriptContext.load_context("{context_file}").items():
    g[k] = v
"""

    @classmethod
    def chdir_template(cls, dir):
        return f"""
import os
os.chdir("{dir}")
"""

    @classmethod
    def imports_template(cls, imports):
        imp_lines = []

        for imp in imports:
            if isinstance(imp, str):
                imp_lines.append(f"import {imp}")
            else:
                if len(imp) == 1:
                    imp = ["", imp, ""]
                elif len(imp) == 2:
                    imp = [imp[0], imp[1], ""]

                from_, import_, as_ = ["" if i is None else i for i in imp]
                if len(from_) == 0:
                    if len(as_) == 0:
                        imp_lines.append(f"import {import_}")
                    else:
                        imp_lines.append(f"import {import_} as {as_}")
                else:
                    if len(as_) == 0:
                        imp_lines.append(f"from {from_} import {import_}")
                    else:
                        imp_lines.append(f"from {from_} import {import_} as {as_}")
        return "\n".join(imp_lines)

    def __enter__(self):
        # self.populate_context_file()
        self._depth += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._depth = max([0, self._depth-1])
        if self._depth == 0 and self.autodelete:
            try:
                os.remove(self.context_file)
            except FileNotFoundError:
                pass

    def create_context_loader(self):
        blocks = []
        if len(self.path) > 0:
            blocks.append(self.path_loader_template(self.path))
        if self.dir is not None:
            blocks.append(self.chdir_template(self.dir))

        context = self.populate_context_file()
        if context is not None:
            imports, chk = context
            if len(imports) > 0:
                blocks.append(self.imports_template(imports))
            if chk is not None:
                blocks.append(self.context_loader_template(chk))

        return "\n".join(blocks)

    @classmethod
    def _handle_import_name(cls, name):
        if isinstance(name, ast.Name):
            return [name]
        elif isinstance(name, ast.alias):
            return [name.name, name.asname]

    @classmethod
    def extract_names(cls, code):
        imports = []
        names = []

        queue = collections.deque()
        queue.extend(ast.iter_child_nodes(code))
        while queue:
            node = queue.pop()
            if isinstance(node, ast.Import):
                imports.extend(
                    cls._handle_import_name(name)
                    for name in node.names
                )
            elif isinstance(node, ast.ImportFrom):
                imports.extend(
                    [node.module] + cls._handle_import_name(name)
                    for name in node.names
                )
            elif isinstance(node, ast.Attribute):
                queue.append(node.value)
            elif isinstance(node, ast.Name):
                names.append(node.id)
            else:
                queue.extend(ast.iter_child_nodes(node))

        return imports, names

    @classmethod
    def find_globals(cls):
        for frame in inspect.stack(1):
            globs = frame.frame.f_globals
            if globs['__name__'] == '__main__':
                return globs
        else:
            return inspect.stack(1)[1].frame.f_globals

    @classmethod
    def from_script(cls,
                    script,
                    modules=None, globs=None,
                    objects=None,
                    imports=None,
                    script_dir=None,
                    script_id=None,
                    context_file=None,
                    autodelete=None,
                    path=None
                    ):
        if modules is None:
            modules = sys.modules
        if globs is None:
            globs = cls.find_globals()

        code = ast.parse(script, mode='exec')
        imps, names = cls.extract_names(code)

        if objects is None:
            objects = {
                name:globs[name]
                for name in names
                if name in globs
            }

            ded = []
            for k, v in objects.items():
                if isinstance(v, type) and v.__module__ in modules:
                    if k == v.__name__:
                        imps.append([v.__module__, k, ""])
                    else:
                        imps.append([v.__module__, v.__name__, k])
                    ded.append(k)
            for d in ded:
                del objects[d]

        if imports is None:
            imports = imps
        # imps = {
        #     name:modules[name]
        #     for name in names
        #     if name in modules
        # }

        return cls(
            objects,
            imports=imports,
            script_id=script_id,
            script_dir=script_dir,
            context_file=context_file,
            autodelete=autodelete,
            path=path
        )


class ScriptRunner:

    def __init__(self, context, script_name='script-', script_suffix='.py', python=None, autodelete=None):
        self.context = context
        self.python = self.get_python(python)
        self.prefix = script_name
        self.suffix = script_suffix
        self.autodelete = autodelete or (autodelete is None)

    @classmethod
    def get_python(cls, python):
        if python is None:
            python = sys.executable
        return python

    class Result:
        __slots__ = ["script", "process", "thread"]
        def __init__(self, script, process=None, thread=None):
            self.script = script
            self.process = process
            self.thread = thread
        def join(self, timeout=None):
            if self.thread is not None:
                self.thread.join(timeout=timeout)
        @property
        def result(self):
            self.join()
            return self.process.stdout.decode()


    def _run_py_subprocess(self, result, script, dry_run=False, runner=None):
        py_script = None
        try:
            with tempfile.NamedTemporaryFile(prefix=self.prefix, suffix=self.suffix, mode='w+', delete=False) as py_script:
                py_script.write(script)
                py_file = py_script.name
            if dry_run:
                return (self.python, py_file)
            proc = subprocess.run([self.python, py_file], capture_output=True)
        finally:
            if not dry_run and self.autodelete and py_script is not None:
                try:
                    os.remove(py_script.name)
                except FileNotFoundError:
                    pass
            if self.context is not None:
                self.context.__exit__(None, None, None)
        result.process = proc
        if proc.returncode > 0:
            raise Exception(proc.stderr.decode())
        return proc.stdout.decode()

    def prep_script(self, script):
        if self.context is not None:
            script = self.context.create_context_loader() + script
        return script


    def run_script(self, script, dry_run=False, background=True, interactive=False):
        if self.context is not None:
            self.context.__enter__()
        script = self.prep_script(script)
        result = self.Result(script)

        if dry_run:
            return self._run_py_subprocess(result, script, dry_run=dry_run)
        elif interactive:
            from .Apps import DelayedResult
            return DelayedResult(self._run_py_subprocess, result, script, parent=self)
        elif background:
            thread = threading.Thread(target=self._run_py_subprocess, args=(result, script,))
            result.thread = thread
            thread.start()
            return result
        else:
            return self._run_py_subprocess(result, script)

    @classmethod
    def run(cls,
            script,
            modules=None, globs=None,
            objects=None,
            imports=None,
            script_dir=None,
            script_id=None,
            context_file=None,
            autodelete=None,
            path=None,
            background=True,
            interactive=False,
            dry_run=False
            ):
        context = ScriptContext.from_script(
            script,
            modules=modules, globs=globs,
            objects=objects,
            imports=imports,
            script_dir=script_dir,
            script_id=script_id,
            context_file=context_file,
            autodelete=autodelete,
            path=path
        )

        return cls(context, autodelete=autodelete).run_script(script,
                                                              dry_run=dry_run,
                                                              background=background,
                                                              interactive=interactive
                                                              )