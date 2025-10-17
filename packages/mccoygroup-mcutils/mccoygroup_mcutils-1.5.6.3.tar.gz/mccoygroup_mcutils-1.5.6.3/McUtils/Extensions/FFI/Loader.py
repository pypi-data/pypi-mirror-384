"""
Provides a Loader object to load a potential from a C++ extension
"""

import os, numpy as np
import platform

from .. import CLoader, ModuleLoader
from .Module import FFIModule

__all__ = [
    "FFILoader"
]

class FFILoader:
    """
    Provides a standardized way to load and compile a potential using a potential template
    """
    __props__ = [
        "src_ext",
        "description",
        "version",
        "include_dirs",
        "linked_libs",
        "macros",
        "source_files",
        "build_script",
        "requires_make",
        "out_dir",
        "cleanup_build",
        'build_kwargs'
        'nodebug',
        'threaded',
        'extra_compile_args',
        'extra_link_args',
        'recompile'
    ]

    # src_folder = os.path.join(os.path.dirname(__file__), "src")
    libs_folder = os.path.join(os.path.dirname(__file__), "libs")
    cpp_std = '-std=c++17'
    def __init__(self,
                 name,
                 src=None,
                 src_ext='src',
                 load_path=None,
                 description="A compiled potential",
                 version="1.0.0",
                 include_dirs=None,
                 linked_libs=None,
                 runtime_dirs=None,
                 macros=None,
                 source_files=None,
                 build_script=None,
                 requires_make=True,
                 out_dir=None,
                 cleanup_build=True,
                 pointer_name=None,
                 build_kwargs=None,
                 nodebug=False,
                 threaded=False,
                 extra_compile_args=None,
                 extra_link_args=None,
                 recompile=False
                 ):
        # if python_potential is False:

        if include_dirs is None:
            include_dirs = []
        include_dirs = (
                               tuple(include_dirs)
                               + (self.libs_folder, np.get_include())
                               # + (PotentialCaller.TBB_CentOS, PotentialCaller.TBB_Ubutu)
        )
        if linked_libs is None:
            linked_libs = []
        linked_libs = ("ffi",) + tuple(linked_libs) #+ ("plzffi", )

        self.threaded = threaded
        if macros is None:
            macros = []
        if nodebug:
            macros = list(macros) + [('_NODEBUG', True)]
        threading_flags = (["-fopenmp"] if self.threaded else [])
        # if platform.system() == "Darwin":
        #     threading_flags = ['-Xprepocessor'] + threading_flags
        self.c_loader = CLoader(
            name,
            src,
            load_path=load_path,
            src_ext=src_ext,
            description=description,
            version=version,
            include_dirs=include_dirs,
            runtime_dirs=runtime_dirs,
            linked_libs=(("omp",) if self.threaded else ()) + linked_libs,
            macros=macros,
            source_files=source_files,
            build_script=build_script,
            requires_make=requires_make,
            out_dir=out_dir,
            cleanup_build=cleanup_build,
            extra_compile_args=threading_flags + [self.cpp_std] + ([] if extra_compile_args is None else list(extra_compile_args)),
            extra_link_args=[] if extra_link_args is None else list(extra_link_args),
            recompile=recompile,
            **({} if build_kwargs is None else build_kwargs)
        )
        # else:
        #     self.c_loader = None

        # Need to insert code here to allow for new caller API to work
        self._lib = None

        self._attr = pointer_name
        # self.function_name = pointer_name

    @property
    def lib(self):
        if self._lib is None:
            self._lib = self.c_loader.load()
        return self._lib
    @property
    def caller_api_version(self):
        if hasattr(self.lib, "_FFIModule"): # currently how we're dispatching
            return 2
        else:
            return 1
    @property
    def call_obj(self):
        """
        The object that defines how to call the potential.
        Can either be a pure python function, an FFIModule, or a PyCapsule

        :return:
        :rtype:
        """
        return FFIModule.from_module(self.lib)