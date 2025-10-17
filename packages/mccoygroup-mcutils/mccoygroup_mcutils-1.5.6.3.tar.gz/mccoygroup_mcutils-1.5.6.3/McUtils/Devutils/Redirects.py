import sys, os
import tempfile as tf, io

__all__ = [
    "OutputRedirect",
    "DefaultDirectory"
]

class OutputRedirect:
    def __init__(self,
                 redirect=True,
                 stdout=None, stderr=None,
                 capture_output=False,
                 capture_errors=None,
                 file_handles=False
                 ):
        self.redirect = redirect
        if capture_errors is None:
            capture_errors = capture_output
        self.capture_output = capture_output
        self.capture_errors = capture_errors
        if capture_output:
            stdout = self.get_handle(stdout, file_handles)
        if capture_errors:
            stderr = self.get_handle(stderr, file_handles)
        self._tmp = [None, None]
        self._stdout = None
        self._stderr = None
        self._devnull = None
        self._out_stream = stdout
        self._err_stream = stderr

    @classmethod
    def get_handle(cls, handles=None, file_handles=False):
        if handles is not None:
            return handles
        if not file_handles:
            return io.StringIO()
        else:
            return None

    @classmethod
    def get_temp_stream(cls):
        return tf.NamedTemporaryFile(mode='w+').__enter__()

    def __enter__(self):
        if self.redirect:
            self._stdout = sys.stdout
            self._stderr = sys.stderr
            if (
                    not self.capture_output
                    and self._out_stream is None
            ) or (
                    not self.capture_errors
                    and self._err_stream is None
            ):
                self._devnull = open(os.devnull, 'w+').__enter__()

            if self._out_stream is None:
                if self.capture_output:
                    self._tmp[0] = self.get_temp_stream()
                    sys.stdout = self._tmp[0]
                else:
                    sys.stdout = self._devnull
            else:
                if isinstance(self._out_stream, str):
                    self._tmp[0] = open(self._out_stream, 'a').__enter__()
                    sys.stdout = self._tmp[0]
                else:
                    sys.stdout = self._out_stream

            if self._err_stream is None:
                if self.capture_errors:
                    self._tmp[1] = self.get_temp_stream()
                    sys.stderr = self._tmp[1]
                else:
                    sys.stderr = self._devnull
            else:
                if isinstance(self._err_stream, str):
                    self._tmp[1] = open(self._err_stream, 'a').__enter__()
                    sys.stderr = self._tmp[1]
                else:
                    sys.stderr = self._err_stream
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.redirect:
            sys.stdout = self._stdout
            sys.stderr = self._stderr
            if self._devnull is not None:
                self._devnull.__exit__(exc_type, exc_val, exc_tb)
                self._devnull = None
            self._stdout = None
            self._stderr = None

            if self._tmp[0] is not None:
                self._tmp[0].__exit__(exc_type, exc_val, exc_tb)
                self._tmp[0] = None
            if self._tmp[1] is not None:
                self._tmp[1].__exit__(exc_type, exc_val, exc_tb)
                self._tmp[1] = None

class DefaultDirectory:
    def __init__(self, output_dir=None, chdir=True, **tempdir_opts):
        self.chdir = chdir
        self._outdir = output_dir
        self._curdir = None
        self._tmp = None
        self._opts = tempdir_opts

    def get_temp_dir(self):
        return tf.TemporaryDirectory(**self._opts).__enter__()

    @property
    def dirname(self):
        if self._tmp is None:
            return None
        if isinstance(self._tmp, str):
            return self._tmp
        else:
            return self._tmp.name

    def __enter__(self):
        if self._outdir is None:
            self._tmp = self.get_temp_dir()
        else:
            self._tmp = self._outdir
        if self.chdir:
            self._curdir = os.getcwd()
            os.chdir(self.dirname)
        return self._tmp

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.chdir:
            os.chdir(self._curdir)
        if self._outdir is None:
            self._tmp.__exit__()
        self._tmp = None