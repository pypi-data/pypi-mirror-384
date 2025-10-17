
import abc
import functools
import os

import numpy as np
import uuid
from .NodeCommServer import NodeCommHandler, NodeCommClient

__all__ = [
    'EvaluationHandler',
    'EvaluationClient'
]

class EvaluationHandler(NodeCommHandler):
    @abc.abstractmethod
    def get_evaluators(self) -> 'dict[str,method]':
        ...

    def wrap_evaluator(self, name, evaluation_function):
        @functools.wraps(evaluation_function)
        def evaluate(args, kwargs):
            coords = args[0]
            use_file_io = isinstance(coords, str)
            if use_file_io:
                # we assume we got a .npz file of coords
                coords = np.load(coords)
            res = evaluation_function(coords, **kwargs)
            if use_file_io:
                #TODO: write this to temporary file
                id = str(uuid.uuid4())
                output = f'{name}-{id}'
                if isinstance(res, np.ndarray):
                    res = {'outfile':np.save(output+'.npy')}
                else:
                    res = {'outfile':np.save(output+'.npz')}
            else:
                if isinstance(res, np.ndarray):
                    res = {'result_array':res.tolist()}
                else:
                    res = {
                        k: v.tolist() if isinstance(v, np.ndarray) else v
                        for k, v in res.items()
                    }
            return res


        return evaluate

    def get_methods(self) -> 'dict[str,method]':
        return {
            k:self.wrap_evaluator(k,v)
            for k,v in self.get_evaluators().items()
        }

class EvaluationClient(NodeCommClient):
    def call(self, evaluator:str, coords:np.ndarray, filename=None, **kwargs):
        if filename is not None:
            coords = np.save(filename, coords)
        else:
            coords = np.asarray(coords).tolist()
        kwargs = {
            k:v.tolist() if isinstance(v, np.ndarray) else v
            for k,v in kwargs.items()
        }
        res = self.communicate(evaluator, (coords,), kwargs)
        if 'result_array' in res:
            res = res['result_array']
        else:
            if 'outfile' in res:
                oof = res['outfile']
                try:
                    res = np.load(oof)
                finally:
                    os.remove('outfile')
        return res