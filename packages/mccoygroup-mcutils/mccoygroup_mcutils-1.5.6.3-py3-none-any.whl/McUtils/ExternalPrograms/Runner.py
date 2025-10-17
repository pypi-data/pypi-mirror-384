
import subprocess, os, tempfile as tf

__all__ = [
    "ExternalProgramRunner"
]

class ExternalProgramRunner:

    default_opts = {}
    def __init__(self, binary,
                 parser=None, prefix=None, suffix=None, delete=True,
                 **runtime_opts
                 ):
        if os.path.isfile(binary):
            binary = os.path.abspath(binary)
        self.binary = binary
        self.parser = parser
        self.opts = dict(self.default_opts, prefix=prefix, suffix=suffix, delete=delete, **runtime_opts)

    class _write_dir:
        def __init__(self, dir=None, dir_prefix=None, dir_suffix=None, delete=True):
            self.dir = dir
            self._temp_dirs = []
            self.delete = delete
            self.opts = {'prefix':dir_prefix, 'suffix':dir_suffix}
        def __enter__(self):
            if self.dir is None:
                td = tf.TemporaryDirectory(**self.opts)
                self._temp_dirs.append(td)
                return td.__enter__()
            else:
                return self.dir
        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.dir is None:
                td = self._temp_dirs.pop()
                td.__exit__(exc_type, exc_val, exc_tb)

    def prep_dir(self, dir):
        ...

    @classmethod
    def subprocess_run(cls, binary, input_file, **subprocess_opts):
        if os.path.isfile(binary):
            binary = os.path.abspath(binary)
        res = subprocess.run([binary, input_file], **subprocess_opts)
        return res

    text_file_extensions = ['.out', '.txt', '.log']
    @classmethod
    def _load_aux_file(cls, dir, file, delete):
        test = os.path.join(dir, file)
        if os.path.isfile(test):
            file = test
        if os.path.isfile(file):
            if delete:
                if os.path.splitext(file)[1] in cls.text_file_extensions:
                    mode = 'r'
                else:
                    mode = 'rb'
                with open(file, mode) as data:
                    # can't be sure if it's a binary file or not
                    return data.read()
            else:
                return file

    blacklist_files = [".DS_Store", ".git"]
    @classmethod
    def run_job(cls,
                binary, job,
                dir=None, dir_prefix=None, dir_suffix=None,
                mode='w',
                runner=None, prep_dir=None, prep_job=None, prep_results=None,
                return_auxiliary_files=True,
                prefix=None, suffix=None, delete=True,
                raise_errors=True,
                **subprocess_opts
                ):

        results = {}
        with cls._write_dir(dir=dir, dir_prefix=dir_prefix, dir_suffix=dir_suffix) as dir:
            if prep_dir is not None:
                prep_dir(dir)
            with tf.NamedTemporaryFile(dir=dir, mode=mode, prefix=prefix, suffix=suffix, delete=False) as inp:
                if not isinstance(job, str) and hasattr(job, 'format'):
                    job = job.format()
                if prep_job is not None:
                    job = prep_job(job)
                results['input_file'] = job
                inp.write(results['input_file'])
            try:
                if return_auxiliary_files is True:
                    existing_files = set(os.listdir(dir))
                else:
                    existing_files = set()
                if runner is None:
                    runner = cls.subprocess_run
                res = runner(binary, inp.name, **dict(capture_output=True, cwd=dir, **subprocess_opts))
                results['process_output'] = res
                if prep_results is not None:
                    results.update(prep_results(dir))
                if return_auxiliary_files is True:
                    for file in os.listdir(dir):
                        if file not in existing_files and file not in cls.blacklist_files:
                            results[file] = cls._load_aux_file(dir, file, delete)
                elif isinstance(return_auxiliary_files, dict):
                    for k,v in return_auxiliary_files.items():
                        data = cls._load_aux_file(dir, v.format(name=inp.name), delete)
                        if data is not None:
                            results[k] = data
                elif return_auxiliary_files:
                    if isinstance(return_auxiliary_files, str):
                        return_auxiliary_files = [return_auxiliary_files]
                    for v in return_auxiliary_files:
                        data = cls._load_aux_file(dir, v.format(name=inp.name), delete)
                        if data is not None:
                            results[v] = data
                err = res.stderr.decode().strip()
                if raise_errors and len(err) > 0:
                    raise IOError(err)

                if not delete:
                    return inp, results
                else:
                    return results

            finally:
                if delete:
                    try:
                        os.remove(inp.name)
                    except OSError:
                        pass
        # if dir is not None:

    def run(self, job,
            dir=None, dir_prefix=None, dir_suffix=None,
            mode=None,
            runner=None, prep_dir=None, prep_job=None, prep_results=None,
            return_auxiliary_files=None,
            prefix=None, suffix=None, delete=None,
            raise_errors=None,
            **job_opts):

        defaults = {
            k: v
            for k,v in dict(
                dir=dir, dir_prefix=dir_prefix, dir_suffix=dir_suffix,
                mode=mode,
                runner=runner, prep_dir=prep_dir, prep_job=prep_job, prep_results=prep_results,
                return_auxiliary_files=return_auxiliary_files,
                prefix=prefix, suffix=suffix, delete=delete,
                raise_errors=raise_errors
            ).items() if v is not None
        }
        return self.run_job(
            self.binary,
            job,
            **{
                **self.opts,
                'prep_dir':self.prep_dir,
                **defaults,
                **job_opts
            }
        )

        # with open(os.path.join(dir, 'atomicMasses.xml'), 'w+') as mass_file:
        #     mass_file.write(self.format_masses_file(self.atom_map) + "\n\n")

        # for key, ext in {"parallel": ".spectrum_parallel", "duschinsky": '.spectrum_dushinsky'}.items():
        #     test = inp.name + ext
        #     if os.path.isfile(test):
        #         with open(test) as strm:
        #             results[key] = strm.read()