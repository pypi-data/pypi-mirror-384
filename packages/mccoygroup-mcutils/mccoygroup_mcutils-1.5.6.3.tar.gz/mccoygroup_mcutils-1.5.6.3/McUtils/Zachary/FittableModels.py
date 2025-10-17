"""
Defines classes for providing different approaches to fitting.
For the most part, the idea is to use `scipy.optimize` to do the actual fitting process,
but we layer on conveniences w.r.t. specification of bases and automation of the actual fitting process
"""
import abc

from .. import Devutils as dev

import numpy as np, scipy.optimize as opt, enum
from collections import OrderedDict as odict

__all__ = [
    "FittedModel"
]

class FittedModel:
    def __init__(self,
                 fit_basis,
                 expansion_coeffs=None,
                 basis_parameters=None,
                 **kwargs
                 ):
        self.fit_basis, self.basis_parameters = self.canonicalize_basis(fit_basis, basis_parameters)
        self.coeffs = expansion_coeffs
        self.opts = kwargs

    @classmethod
    def canonicalize_basis(cls, fit_basis, basis_parameters):
        if callable(fit_basis):
            fit_basis = [fit_basis]
        if basis_parameters is None or dev.is_dict_like(basis_parameters):
            basis_parameters = [basis_parameters] * len(fit_basis)

        return fit_basis, basis_parameters

    def __call__(self, pts, order=None, **opts):
        opts = dict(self.opts, **opts)
        return self.evaluate_kernel(
            self.fit_basis,
            self.basis_parameters,
            pts,
            coeffs=self.coeffs,
            order=order,
            **opts
        )

    @classmethod
    def evaluate_kernel(cls,
                        fit_basis,
                        basis_parameters,
                        pts,
                        coeffs=None,
                        order=None,
                        **opts
                        ):
        if order is None:
            kernel_expansions = [
                [
                    f(pts, **(params if params is not None else {}), **opts)
                    for f, params in zip(fit_basis, basis_parameters)
                ]
            ]
        else:
            kernel_expansions = [
                f(pts, order=order, **(params if params is not None else {}), **opts)
                for f, params in zip(fit_basis, basis_parameters)
            ]
            kernel_expansions = [
                [k[o] for k in kernel_expansions]
                for o in range(order + 1)
            ]

        if coeffs is not None:
            val_expansions = [np.dot(coeffs, k) for k in kernel_expansions]
        else:
            val_expansions = [sum(k) for k in kernel_expansions]

        if order is None:
            return val_expansions[0]
        else:
            return val_expansions

    @classmethod
    def _handle_nl_fit_params(cls,
                              params,
                              kernels,
                              param_names,
                              include_expansion_coefficients=True
                              ):
        if include_expansion_coefficients:
            n = len(kernels)
            coeffs, params = params[-n:], params[:-n]
        else:
            coeffs = None

        parameter_lists = []
        k = 0
        for pl in param_names:
            e = k+len(pl)
            parameter_lists.append(
                zip(pl, params[k:e])
            )
            k = e
        if k < len(params) - 1:
            raise ValueError(f"params of len {len(params)} don't distribute into names {param_names}")

        return coeffs, parameter_lists

    @classmethod
    def get_kernel_and_opts(cls, k):
        func, opts = k  # TODO: make this more flexible down the line
        if dev.is_dict_like(opts):
            names = list(opts.keys())
            vals = list(opts.values())
        else:
            names = list(opts)
            vals = [None] * len(names)
        vals = [
            v
                if v is not None else
            np.random.rand()
            for v in vals
        ]
        return func, names, vals
    @classmethod
    def parse_kernel_specs(cls, kernels):
        if dev.is_dict_like(kernels):
            kernels = [kernels]
        funcs = []
        param_names = []
        param_defaults = []
        for k in kernels:
            f, n, d = cls.get_kernel_and_opts(k)
            funcs.append(f)
            param_names.append(n)
            param_defaults.extend(d)

        return funcs, param_names, param_defaults

    @classmethod
    def nonlinear_fit(cls,
                      kernel_specs,
                      pts,
                      observations,
                      include_expansion_coefficients=True,
                      **fit_params
                      ):
        kernels, param_names, param_defaults = cls.parse_kernel_specs(kernel_specs)
        if include_expansion_coefficients:
            param_defaults = np.concatenate([np.array(param_defaults, dtype=float), np.ones(len(kernels), dtype=float)])
        def f(x, params):
            coeffs, basis_parameters = cls._handle_nl_fit_params(
                params,
                kernels,
                param_names,
                include_expansion_coefficients=include_expansion_coefficients
            )
            return cls.evaluate_kernel(
                kernels,
                basis_parameters,
                x,
                coeffs=coeffs
            )
        # def jac():

        opt_params, _ = opt.curve_fit(
            f,
            pts,
            observations,
            param_defaults,
            fit_params,
            full_output=False
        )

        coeffs, param_dicts = cls._handle_nl_fit_params(
            opt_params, kernels, param_names,
            include_expansion_coefficients=include_expansion_coefficients
        )

        return cls(
            kernels,
            expansion_coeffs=coeffs,
            basis_parameters=param_dicts
        )
        # return cls.from_fit(
        #     kernels,
        #     param_names,
        #     fit
        # )

    @classmethod
    def get_fit_methods(cls):
        return {
            'nonlinear_fit':cls.nonlinear_fit
        }

    _fit_dispatch = dev.uninitialized
    default_fit_method = 'nonlinear_fit'
    @classmethod
    def get_fit_dispatch(cls):
        cls._fit_dispatch = dev.handle_uninitialized(
            cls._fit_dispatch,
            dev.OptionsMethodDispatch,
            args=(cls.get_fit_methods,),
            kwargs=dict(
                default_method=cls.default_fit_method,
                # attributes_map=cls.get_evaluators_by_attributes()
            )
        )
        return cls._fit_dispatch
    @classmethod
    def fit(cls,
            kernels,
            pts,
            observations,
            method=None,
            **opts
            ):

        fit_method, method_opts = cls.get_fit_dispatch().resolve(method)
        return fit_method(
            kernels,
            pts,
            observations,
            **dict(method_opts, **opts)
        )




