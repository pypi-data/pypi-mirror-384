"""Provides a little timer for testing

"""
import timeit, functools, time, sys, inspect
import uuid
from collections import deque

__all__ = ["Timer"]

class Timer:

    tag_printing_times = {}
    def __init__(self, tag=None, file=sys.stderr, rounding=6, message=None, format=None, print_times=-1, number=None, globals=None, **kw):
        self.kw = kw
        self.number = number
        self.file = file
        self.tag = tag
        self.message = message
        self.format = format
        self.rounding = rounding
        self.checkpoints = deque()
        self.print_times = print_times
        self.latest = None
        self.globals = globals
        self.laps = []

    def get_time_list(self, time_elapsed):
        run_time = [0, 0, time_elapsed]
        if run_time[2] > 60:
            run_time[1] = int(run_time[2] / 60)
            run_time[2] = run_time[2] % 60
            if run_time[1] > 60:
                run_time[0] = int(run_time[1] / 60)
                run_time[1] = run_time[1] % 60
        return run_time

    def start(self):
        self.checkpoints.append(time.time())

    def stop(self):
        t = time.time()
        cp = self.checkpoints.pop()
        return t - cp

    def log(self):
        t = time.time()
        self.laps.append([self.checkpoints[-1], t])

    def __enter__(self):
        self.start()
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.latest = self.stop()
        self.print_timing(self.latest)

    default_time_format = "{hours}:{minutes:0>2}:{seconds:0>{width}.{rounding}f}"
    def format_time(self, timelist, format=None, rounding=6):
        if format is None:
            format = self.format
        if format is None:
            format = self.default_time_format
        if rounding is not None:
            rounding = self.rounding
        if rounding is None:
            rounding = len(str(timelist[-1])) - len(str(int(timelist[-1]))) + 1
        return format.format(hours=timelist[0], minutes=timelist[1], seconds=timelist[2],
                          width=rounding+3,
                          rounding=rounding
                          )


    default_message = "{tag}: took {avg} per loop with {tot} overall"
    def format_timing(self, time_elapsed, *, message=None, format=None, rounding=None, tag=None, steps=None):
        run_time = self.get_time_list(time_elapsed)
        if tag is None:
            tag = self.tag
        if steps is None:
            steps = self.number
        if steps is None:
            steps = 1
        run_time_averaged = self.get_time_list(time_elapsed / steps)
        if message is None:
            message = self.message
        if message is None:
            message = self.default_message
        if rounding is None:
            rounding = self.rounding
        run_time_averaged = self.format_time(run_time_averaged, format=format, rounding=rounding)
        run_time = self.format_time(run_time, format=format, rounding=rounding)
        return message.format(
            tag=tag,
            avg=run_time_averaged,
            tot=run_time
        )

    def print_timing(self, time_elapsed, tag=None, steps=None):
        if tag is None:
            tag = self.tag
        if tag not in self.tag_printing_times:
            self.tag_printing_times[tag] = 0
        if self.print_times < 0 or self.tag_printing_times[tag] < self.print_times:
            print(self.format_timing(time_elapsed, tag=tag, steps=steps), file=self.file)
            self.tag_printing_times[tag] += 1

    def timeit(self, stmt, *args, **kwargs):
        globals = self.globals
        val = None
        number = self.number
        tag = self.tag
        id = "_" + str(uuid.uuid4()).replace("-", "_")
        if isinstance(stmt, str):
            if globals is None:
                globals = inspect.stack(1)[0].frame.f_locals
            timer = timeit.Timer(stmt)
            if tag is None:
                if hasattr(stmt, '__name__'):
                    tag = stmt.__name__
                else:
                    tag = str(stmt)
        else:
            if globals is None:
                try:
                    globals = stmt.__globals__
                except AttributeError:
                    globals = inspect.stack(1)[0].frame.f_locals

            globals[f'_{id}_func'] = stmt
            globals[f'_{id}_args'] = args
            globals[f'_{id}_kwargs'] = kwargs
            timer = timeit.Timer(
                f"""
global _{id}_val
_{id}_val = _{id}_func(*_{id}_args, **_{id}_kwargs)
""", globals=globals,
                **self.kw
            )
            if tag is None:
                if hasattr(stmt, '__name__'):
                    tag = stmt.__name__
                else:
                    tag = str(stmt)

        if number is None:
            number, elapsed_time = timer.autorange()
        else:
            elapsed_time = timer.timeit(number)

        if not isinstance(stmt, str):
            val = globals[f"_{id}_val"]

        self.print_timing(elapsed_time, steps=number, tag=tag)
        return val, elapsed_time, number

    def __call__(self, fn): # for use as a decorator
        @functools.wraps(fn)
        def timed_fn(*args, **kwargs):
            return self.timeit(fn, *args, **kwargs)[0]
        return timed_fn