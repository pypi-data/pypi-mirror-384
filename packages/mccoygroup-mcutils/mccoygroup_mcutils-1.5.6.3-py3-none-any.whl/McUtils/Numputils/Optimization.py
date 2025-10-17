import collections, abc
import functools
import numpy as np
import itertools

from .. import Devutils as dev

# from scipy.optimize.linesearch import line_search_armijo
from . import VectorOps as vec_ops
from . import Misc as misc
from . import TransformationMatrices as tfs
from . import SetOps as set_ops

__all__ = [
    "iterative_step_minimize",
    "iterative_chain_minimize",
    "GradientDescentStepFinder",
    "NewtonStepFinder",
    "QuasiNewtonStepFinder",
    "ConjugateGradientStepFinder",
    "EigenvalueFollowingStepFinder",
    "NudgedElasticBandStepFinder",
    "jacobi_maximize",
    "LineSearchRotationGenerator",
    "GradientDescentRotationGenerator",
    "OperatorMatrixRotationGenerator",
    "displacement_localizing_rotation_generator"
]
default_jacobian_step_finder = 'conjugate-gradient'
default_hessian_step_finder = 'newton'
def lookup_method_name(method):
    return {
        'conjugate-gradient':ConjugateGradientStepFinder,
        'newton':NewtonStepFinder,
        'quasi-newton':QuasiNewtonStepFinder,
        'gradient-descent':GradientDescentStepFinder,
        'neb':NudgedElasticBandStepFinder
    }.get(method)
def get_step_finder(spec,
                    method=None,
                    jacobian=None,
                    hessian=None,
                    **extra_init):
    if not (isinstance(spec, dict) or hasattr(spec, 'supports_hessian')) and (
            jacobian is not None
            or method is not None
    ):
        spec = {
            'method':method,
            'func':spec,
            'jacobian':jacobian,
            'hessian':hessian
        }
    if isinstance(spec, dict):
        spec = spec.copy() # don't mutate user data
        method = spec.pop('method', method)
        func = spec.pop('func')
        if jacobian is None:
            jacobian = spec.pop('jacobian')
        else:
            jacobian = spec.pop('jacobian', jacobian)
        hessian = spec.pop('hessian', hessian)
        if method is None:
            if hessian is not None:
                method = default_hessian_step_finder
            else:
                method = default_jacobian_step_finder
        if isinstance(method, str):
            test_method = lookup_method_name(method)
            if test_method is None:
                raise ValueError(f"can't determine appropriate step finder for '{method}")
            method = test_method
        if hessian is not None and method.supports_hessian:
            spec = method(func, jacobian, hessian, **dict(spec, **extra_init))
        else:
            spec = method(func, jacobian, **dict(spec, **extra_init))
    return spec
oscillation_overlap_cutoff_min = 0.95
oscillation_overlap_cutoff_max = 1.05
def iterative_step_minimize_step(step_predictor,
                                 guess, mask, tol,
                                 orthogonal_projector, orthogonal_projection_generator,
                                 region_constraints, unitary, max_displacement, max_displacement_norm,
                                 generate_rotation, prev_steps, max_gradient_error, termination_function
                                 ):
    if unitary:
        projector = vec_ops.orthogonal_projection_matrix(guess.T)
        if orthogonal_projector is not None:
            projector = projector @ orthogonal_projector[np.newaxis]
        if orthogonal_projection_generator is not None:
            projector = projector @ orthogonal_projection_generator(guess)
    elif orthogonal_projector is not None:
        projector = orthogonal_projector[np.newaxis]
        if orthogonal_projection_generator is not None:
            projector = projector @ orthogonal_projection_generator(guess)
    elif orthogonal_projection_generator is not None:
        projector = orthogonal_projection_generator(guess)
    else:
        projector = None
    step, grad = step_predictor(guess, mask, projector=projector)
    if projector is not None:
        # just in case, will usually lead to non-convergence
        step = (step[..., np.newaxis, :] @ projector).reshape(step.shape)
        grad = (grad[..., np.newaxis, :] @ projector).reshape(step.shape)

    if max_displacement is not None:
        step_sizes = np.max(np.abs(step), axis=1)
        step *= max_displacement / np.clip(step_sizes, max_displacement, None)
    if max_displacement_norm is not None:
        step_sizes = np.linalg.norm(step, axis=1)
        step *= max_displacement / np.clip(step_sizes, max_displacement, None)
    if region_constraints is not None:
        #TODO: introduce this as a scaling
        max_step = region_constraints[np.newaxis, :, 1] - guess
        min_step = region_constraints[np.newaxis, :, 0] - guess
        step = np.array([
            np.clip(s, smin, smax)
            for s,smin,smax in zip(guess, min_step, max_step)
        ])
    if isinstance(mask, tuple):
        mask = mask[0]

    if max_gradient_error:
        errs = np.max(np.abs(grad), axis=1)
    else:
        errs = np.linalg.norm(grad, axis=1)
    rem = np.arange(len(mask))
    done = np.where(errs < tol)[0]
    if len(done) > 0:  # easy check
        rem = np.delete(rem, done)
        mask = np.delete(mask, done)
        if len(mask) == 0:
            return step, errs, [], done
    if termination_function is not None:
        done = np.where(termination_function(guess[rem,], step[rem,], mask))
        if len(done) > 0:  # easy check
            rem = np.delete(rem, done)
            mask = np.delete(mask, done)
            if len(mask) == 0:
                return step, errs, [], done

    step = step[rem,]

    if prev_steps is not None:
        prev_steps = prev_steps[mask,]
        cur_norms = np.linalg.norm(step, axis=1)[:, np.newaxis]
        pre_norms = np.linalg.norm(prev_steps, axis=2)
        overlaps = vec_ops.vec_tensordot(step, prev_steps, axes=[-1, -1], shared=1) / (cur_norms * pre_norms)
        overlaps = np.reshape(overlaps, prev_steps.shape[:2])
        osc = np.where(
            np.all(
                np.logical_and(
                    oscillation_overlap_cutoff_min < abs(overlaps),
                    abs(overlaps) < oscillation_overlap_cutoff_max
                ),
                axis=1
            )
        )

        if len(osc[0]) > 0:
            dist = np.reshape(overlaps[osc][:, np.newaxis, :] @ pre_norms[osc][:, :, np.newaxis], cur_norms.shape)
            osc2 = np.where(dist < 0)[:1]
            if len(osc2[0]) > 0:
                osc = osc[0][osc2]
                scaling = np.min([cur_norms[osc2], -dist[osc2] / 2], axis=0) / cur_norms[osc2]
                step[osc,] = step[osc,] * scaling

    if unitary:
        step = step
        norms = np.linalg.norm(step, axis=1)
        # norms = norms[rem,]
        v = np.linalg.norm(guess[rem,], axis=-1)
        r = np.sqrt(norms ** 2 + v ** 2)
        step = guess[rem,] * (1/r[:, np.newaxis] - 1) + step / r[:, np.newaxis]
        if generate_rotation:
            raise NotImplementedError(">3D rotations are complicated")
            axis = vec_ops.vec_crosses(g, guess[mask,])[0]
            ang = np.arctan2(norms / r, v / r)
            rot = tfs.rotation_matrix(axis, ang)
            rotations = rot @ rotations
    else:
        step = step[rem,]


    return step, errs, mask, done

def iterative_step_minimize(
        guess,
        step_predictor,
        jacobian=None,
        hessian=None,
        *,
        method=None,
        unitary=False,
        generate_rotation=False,
        dtype='float64',
        orthogonal_directions=None,
        orthogonal_projection_generator=None,
        region_constraints=None,
        function=None,
        max_displacement=None,
        max_displacement_norm=None,
        oscillation_damping_factor=None,
        termination_function=None,
        prevent_oscillations=None,
        tol=1e-8,
        use_max_for_error=True,
        max_iterations=100,
        convergence_metric=None,
        track_best=False,
        logger=None,
        log_guess=True
):
    logger = dev.Logger.lookup(logger)

    step_predictor = get_step_finder(step_predictor,
                                     method=method,
                                     jacobian=jacobian,
                                     hessian=hessian,
                                     logger=logger)
    guess = np.array(guess, dtype=dtype)
    base_shape = guess.shape[:-1]
    guess = guess.reshape(-1, guess.shape[-1])
    if track_best:
        best = guess.copy()
        best_errs = np.full(guess.shape[0], -1, dtype=float)
        if function is not None:
            best_vals = np.full(guess.shape[0], np.inf, dtype=float)
        else:
            best_vals = None
    else:
        best = None
        best_errs = None
        best_vals = None
    its = np.zeros(guess.shape[0], dtype=int)
    errs = np.zeros(guess.shape[0], dtype=float)
    mask = np.arange(guess.shape[0])
    if orthogonal_directions is not None:
        orthogonal_directions = vec_ops.orthogonal_projection_matrix(orthogonal_directions)
    if unitary and generate_rotation:
        rotations = vec_ops.identity_tensors(guess.shape[:-1], guess.shape[-1])
    else:
        rotations = None

    if prevent_oscillations is None:
        prevent_oscillations = (
                unitary
                or orthogonal_projection_generator is not None
                or orthogonal_directions is not None
        )
    if prevent_oscillations is True:
        prevent_oscillations = 1
    prev_step = None
    prev_errs = None

    converged = True
    for i in range(max_iterations):
        with logger.block(tag=f"Iteration {i}"):
            step, step_errs, new_mask, _ = iterative_step_minimize_step(
                step_predictor, guess[mask,],
                mask, tol,
                orthogonal_directions, orthogonal_projection_generator,
                region_constraints, unitary, max_displacement, max_displacement_norm,
                generate_rotation, prev_step, use_max_for_error, termination_function
            )
            fvals = None
            if best is not None:
                if i == 0:
                    if best_vals is not None:
                        fvals = function(guess[mask,], mask)
                        best_vals[mask,] = fvals
                    best_errs[mask,] = step_errs
                    best[mask,] = guess[mask,]
                else:
                    if best_vals is not None:
                        fvals = function(guess[mask,], mask)
                        new_vals = fvals
                        improved = np.where(new_vals < best_vals[mask,])
                        if len(improved[0]) > 0:
                            imp_mask = mask[improved]
                            best_vals[imp_mask,] = new_vals[improved,]
                            best[imp_mask,] = guess[imp_mask,]
                            best_errs[imp_mask,] = step_errs[improved,]
                    else:
                        improved = np.where(step_errs < best_errs[mask,])
                        if len(improved[0]) > 0:
                            imp_mask = mask[improved]
                            best_errs[imp_mask,] = step_errs[improved,]
                            best[imp_mask,] = guess[imp_mask,]


            if log_guess:
                logger.log_print("Guess: {guess}", guess=guess[mask,])
            logger.log_print("Predicted steps: {step}", step=step)
            logger.log_print("Step errors: {errs}", errs=step_errs)
            if fvals is not None:
                logger.log_print("Function values: {fvals}", fvals=fvals)
            if best_vals is not None:
                logger.log_print("Best value found: {mins}", mins=best_vals[mask,])
            elif best_errs is not None:
                logger.log_print("Best error found: {mins}", mins=best_errs[mask,])
            if prevent_oscillations:
                if prev_step is None:
                    prev_step = np.random.uniform(size=(step.shape[0], prevent_oscillations, step.shape[1])).astype(step.dtype)
                p = i % prevent_oscillations
                prev_step[new_mask, p] = step
            if (not unitary) and oscillation_damping_factor is not None:
                if prev_errs is None:
                    prev_errs = step_errs
                else:
                    prev_errs[new_mask,] = step_errs

                inc_err = np.where(step_errs >= prev_errs[new_mask] - 1e-6) # add some flexibility
                if len(inc_err[0]) > 0:
                    oscillation_damping_factor /= 2
                else:
                    oscillation_damping_factor = np.min([oscillation_damping_factor * 1.2, 1.0])
                step = step * oscillation_damping_factor
                logger.log_print("Oscillation damping factor: {damp}", damp=oscillation_damping_factor)

            errs[mask,] = step_errs
            if len(new_mask) == 0:
                break

            mask = new_mask
            guess[mask,] += step
            its[mask,] += 1
    else:
        converged = False
        its[mask,] = max_iterations
        if best is not None:
            guess[mask,] = best[mask,]
            errs[mask,] = best_errs[mask,]

    guess = guess.reshape(base_shape + (guess.shape[-1],))
    errs = errs.reshape(base_shape)
    its = its.reshape(base_shape)

    if unitary and generate_rotation:
        res = (guess, rotations), converged, (errs, its)
    else:
        res = guess, converged, (errs, its)

    return res

default_chain_step_finder='neb'
def iterative_chain_minimize(
        chain_guesses, step_predictors,
        jacobian=None,
        hessian=None,
        *,
        method=None,
        unitary=False,
        generate_rotation=False,
        dtype='float64',
        orthogonal_directions=None,
        orthogonal_projection_generator=None,
        prevent_oscillations=None,
        region_constraints=None,
        convergence_metric=None,
        termination_function=None,
        reparametrizer=None,
        max_displacement=None,
        max_displacement_norm=None,
        tol=1e-8, max_iterations=100,
        use_max_for_error=True,
        periodic=False,
        reembed=None,
        embedding_options=None,
        fixed_images=None,
        logger=None
):
    guesses = np.array(chain_guesses, dtype=dtype)
    base_shape = guesses.shape[:-2]
    guesses = guesses.reshape((-1,) + guesses.shape[-2:])
    if reembed is None:
        reembed = embedding_options is not None
    if embedding_options is None:
        embedding_options = {}

    try:
        iter(step_predictors)
    except TypeError:
        step_predictors = [step_predictors] * guesses.shape[-2]
    step_predictors = [
        get_step_finder(predictor,
                        method=default_chain_step_finder if method is None else method,
                        jacobian=jacobian,
                        hessian=hessian)
        for predictor in step_predictors
    ]
    its = np.zeros(guesses.shape[0], dtype=int)
    errs = np.zeros(guesses.shape[0], dtype=float)
    submasks = np.full(guesses.shape[:2], True, dtype=bool)
    if fixed_images is not None:
        submasks[..., fixed_images] = False
    mask = np.arange(guesses.shape[0])
    if orthogonal_directions is not None:
        orthogonal_directions = vec_ops.orthogonal_projection_matrix(orthogonal_directions)
    # if unitary and generate_rotation:
    #     rotations = vec_ops.identity_tensors(guess.shape[:-1], guess.shape[-1])
    # else:
    #     rotations = None

    if prevent_oscillations is None:
        prevent_oscillations = (
                unitary
                or orthogonal_projection_generator is not None
                or orthogonal_directions is not None
        )
    if prevent_oscillations:
        prev_step = np.zeros_like(guesses)
    else:
        prev_step = None
    nimg = guesses.shape[-2]
    n = nimg - 1

    if fixed_images is None:
        fixed_images = []

    if reparametrizer is not None:
        image_numbers = np.full(guesses.shape[0], nimg, dtype=int)
    else:
        image_numbers = None

    converged = True
    for i in range(max_iterations):
        # for each unoptimized chain, we only move image `j` if
        # or it's neihbors weren't optimized at the last step, every time an image is moved
        # it's neighbors are marked as moveable again
        errs[mask,] = 0
        for j in range(nimg):
            submask = mask[submasks[mask,][:, j]]
            prev_im = j-1
            next_im = j+1
            if j == 0:
                if periodic:
                    prev_im = n
                else:
                    prev_im = None
            elif j == n:
                if periodic:
                    next_im = 0
                else:
                    next_im = None


            step_predictor = step_predictors[j]
            ps = prev_step[submask,][:, j] if prev_step is not None else prev_step
            step, step_errs, new_mask, done = iterative_step_minimize_step(
                step_predictor, guesses[submask],
                (submask, (j, prev_im, next_im)), tol,
                orthogonal_directions, orthogonal_projection_generator,
                region_constraints, unitary, max_displacement, max_displacement_norm,
                generate_rotation, ps,
                use_max_for_error, termination_function
            )
            if prevent_oscillations:
               prev_step[new_mask, j] = step

            # set which chains are done or not
            done = submask[done]
            submasks[done, j] = False
            if j not in fixed_images:
                submasks[new_mask, j] = True
            if j == 0:
                if j + 1 not in fixed_images:
                    submasks[new_mask, j+1] = True
                if periodic and n not in fixed_images: #TODO: add O(1) check
                    submasks[new_mask, n] = True
            elif j == n:
                if j-1 not in fixed_images:
                    submasks[new_mask, j-1] = True
                if periodic and 0 not in fixed_images:
                    submasks[new_mask, 0] = True
            else:
                if j+1 not in fixed_images:
                    submasks[new_mask, j+1] = True
                if j-1 not in fixed_images:
                    submasks[new_mask, j-1] = True

            errs[mask,] += step_errs
            guesses[submask, j] += step
            if reembed: # implies Cartesian
                from .CoordinateFrames import eckart_embedding

                if j == 0:
                    if periodic:
                        ref = n
                    else:
                        ref = 1
                else:
                    ref = j-1
                ref = guesses[submask, ref]
                coords = guesses[submask, j]
                emb = eckart_embedding(
                    ref.reshape(ref.shape[0], -1, 3),
                    coords.reshape(coords.shape[0], -1, 3),
                    **embedding_options
                )
                guesses[submask, j] = emb.coordinates.reshape(coords.shape[0], -1)

        if reparametrizer is not None:
            # for methods that want to satisfy some density function on
            # the number of images
            new_chains, is_static, fixed_images = reparametrizer(guesses[mask,], fixed_images)
            nimg_new = new_chains.shape[1]
            if nimg_new != nimg:
                guesses = np.pad(guesses,  [[0, 0], [0, nimg_new-nimg], [0, 0]])
                submasks = np.pad(submasks, [[0, 0], [0, nimg_new-nimg]])
                submasks[mask, :] = True
                guesses[mask,] = new_chains
                image_numbers[mask,] = nimg_new
            else:
                submasks[mask, :] = np.logical_and(
                    submasks[mask, :],
                    is_static
                )

            if prev_step is not None:
                prev_step = np.zeros_like(guesses)

        done = np.where(
            np.logical_not(np.any(submasks[mask,], axis=1))
        )[0]
        if len(done) > 0:  # easy check
            mask = np.delete(mask, done)
            if len(mask) == 0:
                break
        its[mask,] += 1
    else:
        converged = False
        its[mask,] = max_iterations

    guesses = guesses.reshape(base_shape + guesses.shape[-2:])
    errs = errs.reshape(base_shape)
    its = its.reshape(base_shape)

    if unitary and generate_rotation:
        raise NotImplementedError(...)
        res = (guess, rotations), converged, (errs, its)
    else:
        res = (guesses, image_numbers), converged, (errs, its)

    return res

class Damper:
    def __init__(self, damping_parameter=None, damping_exponent=None, restart_interval=10):
        self.n = 0
        self.u = damping_parameter
        self.exp = 1.0 if damping_exponent is None else damping_exponent
        self.restart = restart_interval

    def get_damping_factor(self):
        u = self.u
        if u is not None:
            if self.exp > 0:
                u = np.power(u, self.n*self.exp)
                self.n = (self.n + 1) % self.restart
        return u

class LineSearcher(metaclass=abc.ABCMeta):
    """
    Adapted from scipy.optimize to handle multiple structures at once
    """

    def __init__(self, func, min_alpha=0, **opts):
        self.func = func
        self.opts = opts
        self.min_alpha = min_alpha

    @abc.abstractmethod
    def check_scalar_converged(self, phi_vals, alphas, **opts):
        raise NotImplementedError("abstract")

    @abc.abstractmethod
    def update_alphas(self,
                      phi_vals, alphas, iteration,
                      old_phi_vals, old_alphas_vals,
                      mask,
                      **opts
                      ):
        raise NotImplementedError("abstract")

    default_alpha = 1e-3
    def get_default_alpha(self, am):
        return np.full_like(am, self.default_alpha)
    def scalar_search(self,
                      scalar_func,
                      guess_alpha,
                      min_alpha=None,
                      max_iterations=15,
                      history_length=1,
                      **opts):
        if min_alpha is None:
            min_alpha = self.min_alpha

        alphas = np.asanyarray(guess_alpha)
        mask = np.arange(len(alphas))

        phi_vals = scalar_func(alphas, mask)
        if history_length > 0:
            history = collections.deque(maxlen=history_length)
        else:
            history = None

        is_converged = np.full(len(mask), False)
        converged = np.where(self.check_scalar_converged(phi_vals, alphas, **opts))[0]
        if len(converged) > 0:
            is_converged[converged,] = True
            mask = np.delete(mask, converged)
            if len(mask) == 0:
                return alphas,  (phi_vals, is_converged)

        for i in range(max_iterations):
            if history is not None:
                phi_vals_old = [p[mask,] for p,a in history]
                alpha_vals_old = [a[mask,] for p,a in history]
            else:
                phi_vals_old = None
                alpha_vals_old = None

            new_alphas = self.update_alphas(phi_vals, alphas, i,
                                            phi_vals_old, alpha_vals_old,
                                            mask,
                                            **opts
                                            )
                # mask = np.delete(mask, problem_alphas)
                # if len(mask) == 0:
                #     break  # alphas, (phi_vals, is_converged)

            history.append([phi_vals.copy(), alphas.copy()])

            new_phi = scalar_func(new_alphas, mask)
            phi_vals[mask,] = new_phi
            # prev_alphas = alphas[mask,].copy()
            alphas[mask,] = new_alphas

            problem_alphas = np.where(new_alphas < min_alpha)[0]
            if len(problem_alphas) > 0:
                alphas[mask[problem_alphas,],] = min_alpha
                new_alphas = np.delete(new_alphas, problem_alphas)
                new_phi = np.delete(new_phi, problem_alphas)
                mask = np.delete(mask, problem_alphas)
                if len(mask) == 0:
                    break

            converged = np.where(self.check_scalar_converged(new_phi, new_alphas, **opts))[0]
            if len(converged) > 0:
                is_converged[mask[converged,],] = True
                mask = np.delete(mask, converged)
                if len(mask) == 0:
                    break

            # problem_alphas = np.where(np.abs(prev_alphas - alphas[mask,]) < 1e-8)[0]
            # if len(problem_alphas) > 0:
            #     mask = np.delete(mask, problem_alphas)
            #     if len(mask) == 0:
            #         break# alphas, (phi_vals, is_converged)
        else:
            am = alphas[mask,]
            default_alpha = self.get_default_alpha(am, **opts)
            alphas[mask,] = np.min(np.array([am, default_alpha]), axis=0)
        return alphas, (phi_vals, is_converged)

    def prep_search(self, initial_geom, search_dir, guess_alpha=1, **opts):
        return np.full(len(initial_geom), guess_alpha), opts, self._dir_func(self.func, initial_geom, search_dir)

    @classmethod
    def _dir_func(cls, func, initial_geom, search_dir):
        @functools.wraps(func)
        def phi(alphas, mask):
            return func(initial_geom[mask,] + alphas[:, np.newaxis] * search_dir[mask,], mask)

        return phi

    def __call__(self, initial_geom, search_dir, **base_opts):
        opts = dict(self.opts, **base_opts)
        guess_alpha, opts, phi = self.prep_search(initial_geom, search_dir, **opts)
        conv = self.scalar_search(
            phi,
            guess_alpha,
            **opts
        )
        return conv

class ArmijoSearch(LineSearcher):

    def __init__(self, func, c1=1e-4, min_alpha=None, fixed_step_cutoff=1e-8, der_max=1e2, guess_alpha=1):
        super().__init__(func, min_alpha=min_alpha, c1=c1)
        self.func = func
        self.der_max = der_max
        self.fixed_step_cutoff = fixed_step_cutoff
        self.guess_alpha = guess_alpha

    def prep_search(self, initial_geom, search_dir, *, initial_grad, min_alpha=None, **rest):
        mask = np.arange(len(initial_geom))
        derphi0 = np.reshape(initial_grad[:, np.newaxis, :] @ search_dir[:, :, np.newaxis], (-1,))
        derphi0 = np.clip(derphi0, -self.der_max, self.der_max)
        if min_alpha is None:
            min_alpha = self.min_alpha

        a0, opts, phi = super().prep_search(initial_geom, search_dir, **rest)
        if self.fixed_step_cutoff is None:
           if min_alpha is None:
               min_alpha = 1e-8
        else:
           if min_alpha is None:
               min_alpha = 1e-8 #if np.max(np.abs(derphi0)) > self.fixed_step_cutoff else 1
           a0 = (
                   (np.abs(derphi0) > self.fixed_step_cutoff) + (np.abs(derphi0) <= self.fixed_step_cutoff)
           ).astype(float)

        phi0 = phi(np.zeros_like(a0), mask)
        return a0, dict(opts, phi0=phi0, derphi0=derphi0, min_alpha=min_alpha), phi

    converged_tolerance = 1e-8
    def check_scalar_converged(self, phi_vals, alphas, *, phi0, c1, derphi0, tol=None):
        if tol is None:
            tol = self.converged_tolerance
        test = phi0 + c1 * alphas * derphi0
        return np.logical_and(
            np.logical_not(np.isnan(phi_vals)),
            np.logical_or(
                phi_vals < test,
                np.allclose(phi_vals, test, rtol=0, atol=tol)
            )
        )

    def get_default_alpha(self, am, *, phi0, **etc):
        return np.full_like(am, self.default_alpha / np.abs(phi0))

    def update_alphas(self,
                      phi_vals, alphas, iteration,
                      old_phi_vals, old_alphas_vals,
                      mask,
                      *,
                      phi0, c1, derphi0,
                      zero_cutoff=1e-16
                      ):
        phi0 = phi0[mask,]
        derphi0 = derphi0[mask,]

        if iteration == 0:
            factor = (phi_vals - phi0 - derphi0 * alphas)
            # alpha1 = alphas.copy()
            # safe_pos = np.where(np.abs(factor) > zero_cutoff)
            # alpha1[safe_pos,] = -(derphi0[safe_pos,]) * alphas[safe_pos] ** 2 / 2.0 / factor[safe_pos]
            # TODO: ensure stays numerically stable
            # print(".>>", phi0)
            alpha1 = -(derphi0) * alphas ** 2 / 2.0 / factor
            alpha_new = alpha1
        else:
            phi_a0 = old_phi_vals[0]
            phi_a1 = phi_vals
            alpha0 = old_alphas_vals[0]
            alpha1 = alphas

            # da = (alpha1 - alpha0)

            # safe_pos = np.where(np.abs(factor) < zero_cutoff)
            # factor = alpha0 ** 2 * alpha1 ** 2 * (alpha1 - alpha0)
            # a = alpha0 ** 2 * (phi_a1 - phi0 - derphi0 * alpha1) - \
            #     alpha1 ** 2 * (phi_a0 - phi0 - derphi0 * alpha0)
            # a = a / factor
            # b = -alpha0 ** 3 * (phi_a1 - phi0 - derphi0 * alpha1) + \
            #     alpha1 ** 3 * (phi_a0 - phi0 - derphi0 * alpha0)
            # b = b / factor

            # scaling = 1
            n0 = (phi_a0 - phi0 - derphi0 * alpha0)
            n1 = (phi_a1 - phi0 - derphi0 * alpha1)
            d0 = alpha0 ** 2 * (alpha1 - alpha0)
            d1 = alpha1 ** 2 * (alpha1 - alpha0)
            # if d0 < 1e-8 or d1 < 1e-8:
            #     scaling = 1e6
            #     d0 = d0 * scaling
            #     d1 = d1 * scaling
            f1 = n1 / d1
            f0 = n0 / d0

            a = f1 - f0
            b = alpha1 * f0 - alpha0 * f1

            alpha2 = (-b + np.sqrt(abs(b ** 2 - 3 * a * derphi0))) / (3.0 * a)
            # alpha2 = alpha2 / scaling

            halved_alphas = np.where(
                np.logical_or(
                    (alpha1 - alpha2) > alpha1 / 2.0,
                    (1 - alpha2 / alpha1) < 0.96
                )
            )
            alpha2[halved_alphas] = alpha1[halved_alphas] / 2.0

            alpha_new = alpha2

        bad_pos = np.where(np.isnan(alpha_new))
        alpha_new[bad_pos] = alphas[bad_pos] / 2
        return alpha_new

class _WolfeLineSearch(LineSearcher):
    """
    Adapted from scipy.optimize
    """

    def __init__(self, func, grad, **opts):
        super().__init__(func)
        self.grad = grad

    @classmethod
    def _grad_func(cls, jac, initial_geom, search_dir):
        @functools.wraps(jac)
        def derphi(alphas, mask):
            pk = search_dir[mask,]
            grad = jac(initial_geom[mask,] + alphas[:, np.newaxis] * pk, mask)
            return (grad[: np.newaxis, :] @ pk[:, :, np.newaxis]).reshape(-1)

        return derphi

    def prep_search(self, initial_geom, search_dir):
        raise NotImplementedError()
        a_guess, opts, phi = super().prep_search(initial_geom, search_dir)
        derphi = self._grad_func(self.grad, initial_geom, search_dir)
        gfk = self.grad(initial_geom)
        derphi0 = derphi(np.zeros_like(a_guess), np.arange(len(a_guess)))

        # stp, fval, old_fval = scalar_search_wolfe1(
        #     phi, derphi, old_fval, old_old_fval, derphi0,
        #     c1=c1, c2=c2, amax=amax, amin=amin, xtol=xtol)

        # return stp, fc[0], gc[0], fval, old_fval, gval[0]

    def check_scalar_converged(self, phi_vals, alphas, **opts):
        ...

class GradientDescentStepFinder:
    supports_hessian = False
    line_search = ArmijoSearch

    def __init__(self, func, jacobian, damping_parameter=None, damping_exponent=None,
                 line_search=True, restart_interval=10, logger=None):
        self.func = func
        self.jac = jacobian
        self.damper = Damper(
            damping_parameter=damping_parameter,
            damping_exponent=damping_exponent,
            restart_interval=restart_interval
        )

        if line_search is True:
            line_search = self.line_search(func)
        elif line_search is False:
            line_search = None
        self.searcher = line_search
        self.logger = logger

    def __call__(self, guess, mask, projector=None):
        if isinstance(mask, tuple):  # for chain minimizers
            mask, (j, _, _) = mask
            guess = guess[:, j]

        jacobian = self.jac(guess, mask)

        new_step_dir = -jacobian
        if projector is not None:
            new_step_dir = (new_step_dir[..., np.newaxis, :] @ projector).reshape(new_step_dir.shape)

        if self.searcher is not None:
            alpha, (fvals, is_converged) = self.searcher(guess, new_step_dir, initial_grad=jacobian)
            new_step_dir = alpha[:, np.newaxis] * new_step_dir

        # h = func(guess, mask)
        u = self.damper.get_damping_factor()
        if u is not None:
            new_step_dir = new_step_dir * u

        return new_step_dir, jacobian

class NetwonDirectHessianGenerator:

    line_search = ArmijoSearch
    def __init__(self, func, jacobian, hessian, hess_mode='direct', line_search=True,
                 damping_parameter=None, damping_exponent=None, restart_interval=10
                 ):
        hessian = self.wrap_hessian(hessian, hess_mode)
        self.jacobian = jacobian
        self.hessian_inverse = hessian
        self.damper = Damper(
            damping_parameter=damping_parameter,
            damping_exponent=damping_exponent,
            restart_interval=restart_interval
        )
        if line_search is True:
            line_search = self.line_search(func)
        elif line_search is False:
            line_search = None
        self.searcher = line_search

    def wrap_hessian(self, func, mode):
        if mode == 'direct':
            @functools.wraps(func)
            def hessian_inverse(guess, mask):
                h = func(guess, mask)
                # u = self.damper.get_damping_factor()
                # if u is not None:
                #     h = h + u * vec_ops.identity_tensors(guess.shape[:-1], guess.shape[-1])
                return np.linalg.inv(h)
        else:
            hessian_inverse = func
            # @functools.wraps(func)
            # def hessian_inverse(guess, mask):
            #     return h

        return hessian_inverse

    def __call__(self, guess, mask, projector=None):

        jacobian, hessian_inv = self.jacobian(guess, mask), self.hessian_inverse(guess, mask)

        new_step_dir = -(hessian_inv @ jacobian[:, :, np.newaxis]).reshape(jacobian.shape)
        if projector is not None:
            new_step_dir = (new_step_dir[:, np.newaxis, :] @ projector).reshape(new_step_dir.shape)
        if self.searcher is not None:
            alpha, (fvals, is_converged) = self.searcher(guess, new_step_dir, initial_grad=jacobian)
            new_step_dir = alpha[:, np.newaxis] * new_step_dir

        # h = func(guess, mask)
        u = self.damper.get_damping_factor()
        if u is not None:
            new_step_dir = new_step_dir * u

        return new_step_dir, jacobian

class NewtonStepFinder:
    supports_hessian = True
    def __init__(self, func, jacobian=None, hessian=None, *, check_generator=True, logger=None, **generator_opts):
        if check_generator:
            generator = self._prep_generator(func, jacobian, hessian, generator_opts)
        else:
            generator = jacobian
        self.generator = generator
        self.logger = logger

    @classmethod
    def _prep_generator(cls, func, jac, hess, opts):
        if (hasattr(func, 'jacobian') and hasattr(func, 'hessian_inverse')):
            return func
        else:
            if hess is None:
                raise ValueError(
                    "Direct Netwon requires a Hessian or a generator for the Jacobian and Hessian inverse. "
                    "Consider using Quasi-Newton if only the Jacobian is fast to compute.")
            return NetwonDirectHessianGenerator(func, jac, hess, **opts)

    def __call__(self, guess, mask, projector=None):
        if isinstance(mask, tuple):  # for chain minimizers
            mask, (j, _, _) = mask
            guess = guess[:, j]
        return self.generator(guess, mask, projector=projector)

class QuasiNewtonStepFinder:
    supports_hessian = False

    def __init__(self, func, jacobian, approximation_type='bfgs', logger=None, **generator_opts):
        self.hess_appx = self.hessian_approximations[approximation_type.lower()](func, jacobian, **generator_opts)
    @classmethod
    def get_hessian_approximations(cls):
        return {
            'bfgs': BFGSApproximator,
            'broyden': BroydenApproximator,
            'dfp': DFPApproximator,
            'sr1': SR1Approximator,
            'psb': PSBQuasiNewtonApproximator,
            'bofill': BofillApproximator,
            'schelegel': SchelgelApproximator,
            'greenstadt': GreenstadtNewtonApproximator
        }
    @property
    def hessian_approximations(self):
        return self.get_hessian_approximations()

    def __call__(self, guess, mask, projector=None):
        if isinstance(mask, tuple):  # for chain minimizers
            mask, (j, _, _) = mask
            guess = guess[:, j]
        return self.hess_appx(guess, mask, projector=projector)

class QuasiNetwonHessianApproximator:
    orthogonal_dirs_cutoff = 1e-16#1e-8
    line_search = ArmijoSearch
    def __init__(self, func, jacobian, initial_beta=1,
                 damping_parameter=None, damping_exponent=None,
                 line_search=True, restart_interval=10,
                 restart_hessian_norm=1e-12,
                 # approximation_mode='direct'
                 approximation_mode='inverse'
                 ):
        self.func = func
        self.jac = jacobian
        self.initial_beta = initial_beta
        self.base_hess = None
        self.prev_jac = None
        self.prev_step = None
        self.prev_hess_inv = None
        self.eye_tensors = None
        self.damper = Damper(
            damping_parameter=damping_parameter,
            damping_exponent=damping_exponent,
            restart_interval=restart_interval
        )
        if line_search is True:
            line_search = self.line_search(func)
        elif line_search is False:
            line_search = None
        self.searcher = line_search
        self.restart_hessian_norm = restart_hessian_norm
        self.approximation_mode = approximation_mode

    def identities(self, guess, mask):
        if self.eye_tensors is None:
            self.eye_tensors = vec_ops.identity_tensors(guess.shape[:-1], guess.shape[-1])
            return self.eye_tensors
        else:
            return self.eye_tensors[mask,]

    def initialize_hessians(self, guess, mask):
        if self.approximation_mode == 'direct':
            return self.initial_beta * self.identities(guess, mask)
        else:
            return (1/self.initial_beta) * self.identities(guess, mask)

    @classmethod
    def take_nonzero_norm_regions(cls, norms, tensors, cutoff=None):
        if cutoff is None:
            cutoff = cls.orthogonal_dirs_cutoff
        mask = np.full(norms[0].reshape(-1,).shape, True)
        if cutoff is not None:
            for n in norms:
                mask = np.logical_and(mask, np.abs(n.reshape(-1)) > cutoff)

        # good_pos = np.where(np.logical_and(*[
        #     np.abs(n.reshape(-1, )) > cutoff
        #     for n in norms
        # ]))
        good_pos = np.where(mask)
        return good_pos, [t[good_pos] for t in tensors]

    def get_hessian_update(self, identities, jacobian_diffs, prev_steps, prev_hess):
        raise NotImplementedError("abstract")

    def get_jacobian_updates(self, guess, mask):
        new_jacs = self.jac(guess, mask)
        if self.prev_jac is None:
            jac_diffs = new_jacs
        else:
            prev_jacs = self.prev_jac[mask,]
            jac_diffs = new_jacs - prev_jacs
        return new_jacs, jac_diffs

    def restart_hessian_approximation(self):
        if np.any(self.prev_step > 1e80): # a divide by zero in a previous Hessian update
            return True
        prev_norm = np.linalg.norm(self.prev_step, axis=-1)
        restart = np.any(prev_norm < self.restart_hessian_norm)
        return restart

    def __call__(self, guess, mask, projector=None):
        new_jacs, jacobian_diffs = self.get_jacobian_updates(guess, mask)
        if self.prev_step is None or self.restart_hessian_approximation():
            new_hess = self.initialize_hessians(guess, mask)
        else:
            prev_steps = self.prev_step[mask,]
            prev_hess = self.prev_hess_inv[mask,]
            #TODO: check the update to make sure the Hessian approx. isn't crashing
            new_hess = self.get_hessian_update(self.identities(guess, mask), jacobian_diffs, prev_steps, prev_hess)

        if self.approximation_mode == 'direct':
            B = np.linalg.inv(new_hess)
        else:
            B = new_hess
        new_step_dir = -(B @ new_jacs[:, :, np.newaxis]).reshape(new_jacs.shape)
        if projector is not None:
            new_step_dir = (new_step_dir[:, np.newaxis, :] @ projector).reshape(new_step_dir.shape)
        if self.searcher is not None:
            alpha, (fvals, is_converged) = self.searcher(guess, new_step_dir, initial_grad=new_jacs)
        else:
            alpha = np.ones(len(new_step_dir))
        # handle convergence issues?
        new_step = alpha[:, np.newaxis] * new_step_dir
        # print(np.isnan(guess).any(), np.isnan(alpha).any(), np.linalg.norm(new_step_dir))
        u = self.damper.get_damping_factor()
        if u is not None:
            new_step = new_step * u

        if self.prev_jac is None:
            self.prev_jac = new_jacs
        else:
            self.prev_jac[mask,] = new_jacs

        if self.prev_step is None:
            self.prev_step = new_step
        else:
            self.prev_step[mask,] = new_step

        if self.prev_hess_inv is None:
            self.prev_hess_inv = new_hess
        else:
            self.prev_hess_inv[mask,] = new_hess

        return new_step, new_jacs

class BFGSApproximator(QuasiNetwonHessianApproximator):

    orthogonal_dirs_cutoff = 1e-16 #1e-8
    def get_hessian_update(self, identities, jacobian_diffs, prev_steps, prev_hess):
        I = identities
        dx = prev_steps[:, :, np.newaxis]
        dx_T = prev_steps[:, np.newaxis, :]
        y = jacobian_diffs[:, :, np.newaxis]
        y_T = jacobian_diffs[:, np.newaxis, :]
        B = prev_hess.copy()
        increment = False
        if self.approximation_mode == 'direct':
            diff_norm = y_T @ dx
            h_step = (B @ dx)
            h_norm = dx_T @ h_step
            good_pos, (
                I, H, dx, dx_T, y, y_T,
                h_step, h_norm, diff_norm
            ) = self.take_nonzero_norm_regions([diff_norm, h_norm],
                                               [I, B, dx, dx_T, y, y_T,
                                                h_step, h_norm, diff_norm])
            h_step_T = np.moveaxis(h_step, -1, -2)

            diff_outer = y_T * y
            step_outer = h_step_T * h_step
            diff_step = diff_outer / diff_norm
            step_step = step_outer / h_norm
            update = diff_step - step_step
            increment = True
        else:
            diff_norm = y_T @ dx
            good_pos, (
                I, H, dx, dx_T, y, y_T,
                diff_norm
            ) = self.take_nonzero_norm_regions([diff_norm],
                                               [I, B, dx, dx_T, y, y_T,
                                                diff_norm])

            diff_outer = np.moveaxis(dx_T * y, -1, -2)
            diff_step = I - diff_outer / diff_norm
            step_outer = dx_T * dx
            step_step = step_outer / diff_norm
            update = diff_step @ H @ np.moveaxis(diff_step, -1, -2) + step_step
            increment = False

        if increment:
            B[good_pos] += update
        else:
            B[good_pos] = update
        return B

class DFPApproximator(QuasiNetwonHessianApproximator):

    orthogonal_dirs_cutoff = 1e-8
    def get_hessian_update(self, identities, jacobian_diffs, prev_steps, prev_hess):
        I = identities
        dx = prev_steps[:, :, np.newaxis]
        dx_T = prev_steps[:, np.newaxis, :]
        y = jacobian_diffs[:, :, np.newaxis]
        y_T = jacobian_diffs[:, np.newaxis, :]
        B = prev_hess.copy()
        if self.approximation_mode == 'direct':
            norm = y_T @ dx
            good_pos, (
                I, H, dx, dx_T, y, y_T,
                norm
            ) = self.take_nonzero_norm_regions([norm],
                                               [I, B, dx, dx_T, y, y_T,
                                                norm])

            proj = I - (y @ dx_T) / norm
            update = proj @ H[good_pos] @ np.moveaxis(proj, -1, -2)

            update = update + (y @ y_T)/norm
        else:
            norm = y_T @ dx
            h_step = B @ y
            h_norm = y_T @ h_step
            good_pos, (
                I, H, dx, dx_T, y, y_T,
                norm, h_step, h_norm
            ) = self.take_nonzero_norm_regions([norm, h_norm],
                                               [I, B, dx, dx_T, y, y_T,
                                                norm, h_step, h_norm])

            update = dx @ dx_T - (h_step/h_norm) @ np.moveaxis(h_step, -1, -2)

        B[good_pos] += update
        return B

class BroydenApproximator(QuasiNetwonHessianApproximator):

    orthogonal_dirs_cutoff = 1e-8
    def get_hessian_update(self, identities, jacobian_diffs, prev_steps, prev_hess):
        I = identities
        dx = prev_steps[:, :, np.newaxis]
        dx_T = prev_steps[:, np.newaxis, :]
        y = jacobian_diffs[:, :, np.newaxis]
        y_T = jacobian_diffs[:, np.newaxis, :]
        B = prev_hess.copy()
        if self.approximation_mode == 'direct':
            dx_norm = dx_T * dx
            good_pos, (
                I, H, dx, dx_T, y, y_T,
                dx_norm
            ) = self.take_nonzero_norm_regions([dx_norm],
                                               [I, B, dx, dx_T, y, y_T,
                                                dx_norm])

            h_step = (H @ dx)
            update = (y - h_step)/dx_norm * dx_T

            B[good_pos] += update * dx_T
        else:
            h_y = B @ y
            h_x = B @ dx
            h_norm = dx_T @ h_y
            good_pos, (
                I, H, dx, dx_T, y, y_T,
                h_y, h_x, h_norm
            ) = self.take_nonzero_norm_regions([h_norm],
                                               [I, B, dx, dx_T, y, y_T,
                                                h_y, h_x, h_norm])

            h_step = (dx - h_y) / h_norm
            update = h_step * np.moveaxis(h_x, -1, -2)

        B[good_pos] += update
        return B

class SR1Approximator(QuasiNetwonHessianApproximator):

    orthogonal_dirs_cutoff = 1e-8
    def get_hessian_update(self, identities, jacobian_diffs, prev_steps, prev_hess):
        I = identities
        dx = prev_steps[:, :, np.newaxis]
        dx_T = prev_steps[:, np.newaxis, :]
        y = jacobian_diffs[:, :, np.newaxis]
        y_T = jacobian_diffs[:, np.newaxis, :]
        B = prev_hess.copy()
        if self.approximation_mode == 'direct':
            h_step = y - (B @ dx)
            h_step_T = np.moveaxis(h_step, -1, -2)
            h_norm = dx_T @ h_step
            good_pos, (
                I, H, dx, dx_T, y, y_T,
                h_step, h_step_T, h_norm
            ) = self.take_nonzero_norm_regions([h_norm],
                                               [I, B, dx, dx_T, y, y_T,
                                                h_step, h_step_T, h_norm])
            update = (h_step_T * h_step) / h_norm
        else:
            h_step = dx - (B @ y)
            h_step_T = np.moveaxis(h_step, -1, -2)
            h_norm = y_T @ h_step
            good_pos, (
                I, H, dx, dx_T, y, y_T,
                h_step, h_step_T, h_norm
            ) = self.take_nonzero_norm_regions([h_norm],
                                               [I, B, dx, dx_T, y, y_T,
                                                h_step, h_step_T, h_norm])
            update = (h_step_T * h_step) / h_norm

        B[good_pos] += update
        return B

class CompactQuasiNewtonApproximator(QuasiNetwonHessianApproximator):
    @classmethod
    def get_direct_hessian_update_vector(cls, H, dx, y):
        raise NotImplementedError("abstract")
    @classmethod
    def get_inverse_hessian_update_vector(cls, H, dx, y):
        raise NotImplementedError("abstract")

    def get_hessian_update(self, identities, jacobian_diffs, prev_steps, prev_hess):
        I = identities
        dx = prev_steps[:, :, np.newaxis]
        dx_T = prev_steps[:, np.newaxis, :]
        y = jacobian_diffs[:, :, np.newaxis]
        y_T = jacobian_diffs[:, np.newaxis, :]
        B = prev_hess.copy()

        if self.approximation_mode == 'direct':
            v = self.get_direct_hessian_update_vector(
                B, dx, y
            )
        else:
            v = self.get_inverse_hessian_update_vector(
                B, dx, y
            )
            y, y_T, dx, dx_T = dx, dx_T, y, y_T

        norm = v @ dx_T
        good_pos, (
            I, H, dx, dx_T, y, y_T,
            v, norm
        ) = self.take_nonzero_norm_regions([norm],
                                           [I, B, dx, dx_T, y, y_T,
                                            v, norm])

        d = (dx - H @ y) / norm
        d_T = np.moveaxis(d, -1, -2)
        v_T = np.moveaxis(v, -1, -2)
        dv = d * v_T
        dv_T = np.moveaxis(dv, -1, -2)

        B[good_pos,] += dv + dv_T - ((d_T @ y) / norm) * (v * v_T)

        return B

class PSBQuasiNewtonApproximator(CompactQuasiNewtonApproximator):
    @classmethod
    def get_direct_hessian_update_vector(cls, H, dx, y):
        raise NotImplementedError("PSB only does inverse mode")
    @classmethod
    def get_inverse_hessian_update_vector(cls, H, dx, y):
        return dx

class GreenstadtNewtonApproximator(CompactQuasiNewtonApproximator):
    @classmethod
    def get_direct_hessian_update_vector(cls, H, dx, y):
        raise y

    @classmethod
    def get_inverse_hessian_update_vector(cls, H, dx, y):
        raise NotImplementedError("Greenstadt only does direct mode")

class WeightedQuasiNewtonApproximator(QuasiNetwonHessianApproximator):

    base_approximators = None
    def __init__(
            self,
            func, jacobian, initial_beta=1,
            damping_parameter=None, damping_exponent=None,
            line_search=True, restart_interval=10,
            restart_hessian_norm=1e-5,
            approximation_mode='direct'
    ):
        super().__init__(
            func, jacobian,
            initial_beta=initial_beta,
            damping_parameter=damping_parameter, damping_exponent=damping_exponent,
            line_search=line_search, restart_interval=restart_interval,
            restart_hessian_norm=restart_hessian_norm,
            approximation_mode=approximation_mode
        )
        self.approximators = [
            app(
                None, None,
                initial_beta=initial_beta,
                damping_parameter=damping_parameter, damping_exponent=damping_exponent,
                line_search=line_search, restart_interval=restart_interval,
                restart_hessian_norm=restart_hessian_norm,
                approximation_mode=approximation_mode
            )
            for app in self.base_approximators
        ]

    def get_direct_weights(self, jacobian_diffs, prev_steps, prev_hess):
        raise NotImplementedError("abstract")
    def get_inverse_weights(self, jacobian_diffs, prev_steps, prev_hess):
        raise NotImplementedError("abstract")


    def get_hessian_update(self, identities, jacobian_diffs, prev_steps, prev_hess):
        if self.approximation_mode == 'direct':
            weights = self.get_direct_weights(jacobian_diffs, prev_steps, prev_hess)
        else:
            weights = self.get_inverse_weights(jacobian_diffs, prev_steps, prev_hess)

        base_updates = np.array([
            app.get_hessian_update(identities, jacobian_diffs, prev_steps, prev_hess)
            for app in self.approximators
        ])

        # weights is kxb array and base_updates is bxkxnxn
        avg = weights[:, np.newaxis, :] @ np.moveaxis(base_updates, 1, 0)[:, :, np.newaxis, :, :]
        return avg.reshape(base_updates.shape[1:])

class BofillApproximator(WeightedQuasiNewtonApproximator):
    base_approximators = [
        SR1Approximator,
        PSBQuasiNewtonApproximator
    ]
    def get_direct_weights(self, jacobian_diffs, prev_steps, prev_hess):
        raise NotImplementedError("only inverse supported")

    @classmethod
    def get_psi(self, jacobian_diffs, prev_steps, prev_hess):
        psi = np.ones_like(prev_steps)

        dx = prev_steps[:, :, np.newaxis]
        dx_T = prev_steps[:, np.newaxis, :]
        y = jacobian_diffs[:, :, np.newaxis]
        y_T = jacobian_diffs[:, np.newaxis, :]
        H = prev_hess
        h_step = y + H @ dx
        h_step_T = np.moveaxis(h_step, -2, -1)
        h_norm = h_step_T @ h_step
        s_norm = dx_T @ dx
        good_pos, (
            H, dx, dx_T, y, y_T,
            s_norm, h_norm
        ) = self.take_nonzero_norm_regions([s_norm, h_norm],
                                           [H, dx, dx_T, y, y_T,
                                            s_norm, h_norm])
        step_disp = h_step_T @ dx

        psi[good_pos] = np.reshape( (step_disp**2)/(s_norm * h_norm), -1)

        return psi

    def get_inverse_weights(self, jacobian_diffs, prev_steps, prev_hess):
            psi = self.get_psi(jacobian_diffs, prev_steps, prev_hess)
            return [psi, 1-psi]

class SchelgelApproximator(BofillApproximator):
    base_approximators = [
        SR1Approximator,
        BFGSApproximator
    ]
    def get_direct_weights(self, jacobian_diffs, prev_steps, prev_hess):
        raise NotImplementedError("only inverse supported")

    def get_psi(self, jacobian_diffs, prev_steps, prev_hess):
        psi = np.sqrt(BofillApproximator.get_psi())

        return psi

    def get_inverse_weights(self, jacobian_diffs, prev_steps, prev_hess):
            psi = np.sqrt(BofillApproximator.get_psi(jacobian_diffs, prev_steps, prev_hess))
            return [psi, 1-psi]

class ConjugateGradientStepFinder:
    supports_hessian = False

    def __init__(self, func, jacobian, approximation_type='polak-ribiere', logger=None, **generator_opts):
        self.step_appx = self.beta_approximations[approximation_type.lower()](func, jacobian, **generator_opts)
        self.logger = logger
    @property
    def beta_approximations(self):
        return {
            'fletcher-reeves':FletcherReevesApproximator,
            'polak-ribiere':PolakRibiereApproximator
        }

    def __call__(self, guess, mask, projector=None):
        if isinstance(mask, tuple):  # for chain minimizers
            mask, (j, _, _) = mask
            guess = guess[:, j]
        return self.step_appx(guess, mask, projector=projector)

class ConjugateGradientStepApproximator:
    line_search = ArmijoSearch

    def __init__(self, func, jacobian,
                 damping_parameter=None, damping_exponent=None,
                 restart_interval=50, restart_parameter=0.9,
                 line_search=True):
        self.func = func
        self.jac = jacobian
        self.base_hess = None
        self.prev_jac = None
        self.prev_step_dir = None
        self.damper = Damper(
            damping_parameter=damping_parameter,
            damping_exponent=damping_exponent,
            restart_interval=restart_interval
        )
        self.n = 0
        self.restart_interval = restart_interval
        self.restart_parameter = restart_parameter
        if line_search is True:
            line_search = self.line_search(func)
        elif line_search is False:
            line_search = None
        self.searcher = line_search

    def get_beta(self, new_jacs, prev_jac, prev_step_dir):
        raise NotImplementedError("abstract")

    def determine_restart(self, new_jacs, mask):
        if self.n == 0: return True
        if self.restart_parameter is not None:
            prev_jac = self.prev_jac[mask,]
            new_norm = np.abs(new_jacs[:, np.newaxis, :] @ prev_jac[:, :, np.newaxis]).flatten()
            old_norm = (prev_jac[:, np.newaxis, :] @ prev_jac[:, :, np.newaxis]).flatten()
            return np.any(
                self.restart_parameter * old_norm < new_norm
            )

    def __call__(self, guess, mask, projector=None):
        new_jacs = self.jac(guess, mask)

        if self.prev_jac is None or self.determine_restart(new_jacs, mask):
            new_step_dir = -new_jacs
        else:
            prev_jac = self.prev_jac[mask,]
            prev_step_dir = self.prev_step_dir[mask,]
            beta = self.get_beta(new_jacs, prev_jac, prev_step_dir)
            new_step_dir = -new_jacs + beta[:, np.newaxis] * prev_step_dir

        if projector is not None:
            new_step_dir = (new_step_dir[:, np.newaxis, :] @ projector).reshape(new_step_dir.shape)

        if self.searcher is not None:
            alpha, (fvals, is_converged) = self.searcher(guess, new_step_dir, initial_grad=new_jacs)
        else:
            alpha = np.ones(len(new_step_dir))
        # handle convergence issues?
        new_step = alpha[:, np.newaxis] * new_step_dir

        u = self.damper.get_damping_factor()
        if u is not None:
            new_step = new_step * u

        if self.prev_jac is None:
            self.prev_jac = new_jacs
        else:
            self.prev_jac[mask,] = new_jacs

        if self.prev_step_dir is None:
            self.prev_step_dir = new_step_dir
        else:
            self.prev_step_dir[mask,] = new_step_dir

        self.n = (self.n + 1) % self.restart_interval

        return new_step, new_jacs

class FletcherReevesApproximator(ConjugateGradientStepApproximator):
    def get_beta(self, new_jacs, prev_jac, prev_step_dir):
        return (
                (new_jacs[:, np.newaxis, :] @ new_jacs[:, :, np.newaxis]) /
                (prev_jac[:, np.newaxis, :] @ prev_jac[:, :, np.newaxis])
        ).reshape(len(new_jacs))

class PolakRibiereApproximator(ConjugateGradientStepApproximator):
    def get_beta(self, new_jacs, prev_jac, prev_step_dir):
        return (
                (new_jacs[:, np.newaxis, :] @ (new_jacs[:, :, np.newaxis] - prev_jac[:, :, np.newaxis])) /
                (prev_jac[:, np.newaxis, :] @ prev_jac[:, :, np.newaxis])
        ).reshape(len(new_jacs))

class EigenvalueFollowingStepFinder:

    line_search = ArmijoSearch
    def __init__(self, func, jacobian, hessian, initial_beta=1,
                 damping_parameter=None, damping_exponent=None,
                 line_search=False, restart_interval=1,
                 restart_hessian_norm=1e-5,
                 hessian_approximator='bofill',
                 approximation_mode='direct',
                 target_mode=None,
                 logger=None
                 # approximation_mode='inverse'
                 ):
        self.base_approximator = QuasiNewtonStepFinder.get_hessian_approximations()[hessian_approximator.lower()](
            func, jacobian
        )
        self.logger = logger

        self.func = func
        self.jac = jacobian
        self.hess = hessian
        self.initial_beta = initial_beta
        self.base_hess = None
        self.prev_jac = None
        self.prev_step = None
        self.prev_evec = None
        self.prev_hess = None
        self.eye_tensors = None
        self.damper = Damper(
            damping_parameter=damping_parameter,
            damping_exponent=damping_exponent,
            restart_interval=restart_interval
        )
        if line_search is True:
            line_search = self.line_search(func)
        elif line_search is False:
            line_search = None
        self.searcher = line_search
        self.restart_hessian_norm = restart_hessian_norm
        self.approximation_mode = approximation_mode
        self.target_mode = target_mode

    def identities(self, guess, mask):
        if self.eye_tensors is None:
            self.eye_tensors = vec_ops.identity_tensors(guess.shape[:-1], guess.shape[-1])
            return self.eye_tensors
        else:
            return self.eye_tensors[mask,]

    def initialize_hessians(self, guess, mask):
        return self.hess(guess)

    def get_hessian_update(self, identities, jacobian_diffs, prev_steps, prev_hess):
        return self.base_approximator.get_hessian_update(identities, jacobian_diffs, prev_steps, prev_hess)

    negative_eigenvalue_offset = 0.015
    positive_eigenvalue_offset = 0.005
    mode_tracking_overlap_cutoff = 1e-5
    def get_shift(self, evals, tf_new, target_mode):
        if target_mode is None:
            target_ev = evals[0] # could do np.min(ev) if we had some other (or complex) eigensolver
        else:
            overlaps = np.abs(tf_new @ target_mode) # TODO: check if this makes sense, in principle under a
                                                    # quadratic appx. the "direction" of the step doesn't matter
            abs_ov = np.abs(overlaps)
            ev_pos = np.argmax(abs_ov)
            if abs_ov[ev_pos] < self.mode_tracking_overlap_cutoff:
                target_ev = evals[0]
            else:
                target_ev = evals[ev_pos]

        if target_ev < 0:
            shift = -target_ev + self.negative_eigenvalue_offset # make this very slightly positive
        else:
            shift = self.positive_eigenvalue_offset

        return shift

    def get_jacobian_updates(self, guess, mask):
        new_jacs = self.jac(guess, mask)
        if self.prev_jac is None:
            jac_diffs = new_jacs
        else:
            prev_jacs = self.prev_jac[mask,]
            jac_diffs = new_jacs - prev_jacs
        return new_jacs, jac_diffs

    def restart_hessian_approximation(self):
        restart = np.any(
            np.linalg.norm(self.prev_step, axis=-1) < self.restart_hessian_norm
        )
        return restart

    def __call__(self, guess, mask, projector=None):
        if isinstance(mask, tuple):  # for chain minimizers
            mask, (j, _, _) = mask
            guess = guess[:, j]

        new_jacs, jacobian_diffs = self.get_jacobian_updates(guess, mask)
        if self.prev_step is None or self.restart_hessian_approximation():
            new_hess = self.initialize_hessians(guess, mask)
        else:
            prev_steps = self.prev_step[mask,]
            prev_hess = self.prev_hess[mask,]
            new_hess = self.get_hessian_update(guess, self.identities(guess, mask), jacobian_diffs, prev_steps, prev_hess)

        if self.prev_evec is None:
            prev_evec = None
        else:
            prev_evec = self.prev_evec[mask,]

        evals, tf = np.linalg.eigh(new_hess)
        if misc.is_numeric(self.target_mode):
            self.target_mode = tf[:, self.target_mode]

        shift = self.get_shift(evals, tf, self.target_mode)

        tf_grad = -np.diag(
                np.moveaxis(tf, -1, -2) @ new_jacs[:, :, np.newaxis]
        ) / (evals[:, :, np.newaxis] + shift[:, np.newaxis, np.newaxis])
        new_step_dir = (tf_grad @ tf).reshape(new_jacs.shape)

        # print(new_hess)
        if projector is not None:
            new_step_dir = (new_step_dir[:, np.newaxis, :] @ projector).reshape(new_step_dir.shape)
        if self.searcher is not None:
            alpha, (fvals, is_converged) = self.searcher(guess, new_step_dir, initial_grad=new_jacs)
        else:
            alpha = np.ones(len(new_step_dir))
        # handle convergence issues?
        new_step = alpha[:, np.newaxis] * new_step_dir
        # print(np.isnan(guess).any(), np.isnan(alpha).any(), np.linalg.norm(new_step_dir))
        u = self.damper.get_damping_factor()
        if u is not None:
            new_step = new_step * u

        if self.prev_jac is None:
            self.prev_jac = new_jacs
        else:
            self.prev_jac[mask,] = new_jacs

        if self.prev_step is None:
            self.prev_step = new_step
        else:
            self.prev_step[mask,] = new_step

        if self.prev_hess is None:
            self.prev_hess = new_hess
        else:
            self.prev_hess[mask,] = new_hess

        return new_step, new_jacs

class ChainMinimizingStepFinder:
    supports_hessian = True
    def __init__(self,
                 func,
                 jacobian,
                 hessian=None,
                 step_finder='conjugate-gradient',
                 logger=None,
                 **opts
                 ):
        self.step_finder = get_step_finder({
            'method':step_finder,
            'func':self.wrap_func(func),
            'jacobian':self.wrap_jac(jacobian),
            'hessian':self.wrap_hess(hessian),
            **opts
        })
        self._mask_data = None
        self.logger = logger

    def adjust_jacobian(self, jac, guess, mask, cur, prev, next):
        return jac

    def adjust_hessian(self, hess, guess, mask, cur, prev, next):
        return hess

    @abc.abstractmethod
    def image_pairwise_contribution(self, guess, mask, cur, prev, next, order=0):
        raise NotImplementedError("abstract")

    def wrap_func(self, func):
        @functools.wraps(func)
        def wrapped_func(guess, mask):
            j, prev, next = self._mask_data
            return func(guess[:, j], mask) + self.image_pairwise_contribution(guess, mask, j, prev, next, order=0)
        return wrapped_func

    def wrap_jac(self, jac):
        @functools.wraps(jac)
        def wrapped_jac(guess, mask):
            j, prev, next = self._mask_data
            base_jac = self.adjust_jacobian(
                jac(guess[:, j], mask),
                guess, mask, j, prev, next
            )
            new_jac = self.image_pairwise_contribution(guess, mask, j, prev, next, order=1)
            # print(base_jac)
            # print(new_jac)
            # print("-"*20)
            return base_jac + new_jac
        return wrapped_jac

    def wrap_hess(self, hess):
        if hess is None:
            return hess
        @functools.wraps(hess)
        def wrapped_hess(guess, mask):
            j, prev, next = self._mask_data
            return self.adjust_hessian(
                hess(guess[:, j], mask),
                guess, mask, j, prev, next
            ) + self.image_pairwise_contribution(guess, mask, j, prev, next, order=2)
        return wrapped_hess

    def __call__(self, guess, mask, projector=None):
        mask, self._mask_data = mask
        return self.step_finder(guess, mask, projector=projector)

class NudgedElasticBandStepFinder(ChainMinimizingStepFinder):
    def __init__(self,
                 func,
                 jacobian,
                 hessian=None,
                 spring_constants=.1,
                 distance_function=None,
                 step_finder='gradient-descent',
                 logger=None,
                 **opts
                 ):
        self.image_potential = func
        super().__init__(func, jacobian, hessian=hessian, step_finder=step_finder, **opts)
        self.spring_constants = spring_constants
        self._spring_constants = None
        self.distance_function = distance_function
        self._last_tangent = None
        self.logger = logger

    def get_dist(self, p1, p2):
        return np.linalg.norm(p1 - p2, axis=-1)

    def get_tangent(self, guess, mask, cur, prev, next):

        cur_geom, prev_geom, next_geom = guess[:, cur], guess[:, prev], guess[:, next]

        prev_energy = self.image_potential(prev_geom, mask)
        cur_energy = self.image_potential(cur_geom, mask)
        next_energy = self.image_potential(next_geom, mask)
        if next_energy > cur_energy and cur_energy > prev_energy:
            tangent = next_geom - cur_geom
        elif next_energy <= cur_energy and cur_energy <= prev_energy:
            tangent = cur_geom - prev_geom
        else:
            dnext = abs(next_energy - cur_energy)
            dprev = abs(cur_energy - prev_energy)
            vmax = max(dnext, dprev) / (dnext + dprev)
            vmin = min(dnext, dprev) / (dnext + dprev)
            if next_energy > prev_energy:
                tangent = (next_geom - cur_geom) * vmax + (cur_geom - prev_geom) * vmin
            else:
                tangent = (next_geom - cur_geom) * vmin + (cur_geom - prev_geom) * vmax

        return vec_ops.vec_normalize(tangent)

    def adjust_jacobian(self, jac, guess, mask, cur, prev, next):
        if prev is None or next is None: return jac
        self._last_tangent = self.get_tangent(guess, mask, cur, prev, next)

        return vec_ops.project_out(jac, self._last_tangent[:, :, np.newaxis], orthonormal=True)

    def image_pairwise_contribution(self, guess, mask, cur, prev, next, order=0):
        if order > 2: return 0

        if prev is None or next is None:
            return 0

        cur_geom, prev_geom, next_geom = guess[:, cur], guess[:, prev], guess[:, next]

        prev_dist = self.get_dist(cur_geom, prev_geom)
        next_dist = self.get_dist(cur_geom, next_geom)

        dist = prev_dist - next_dist
        if misc.is_numeric(self.spring_constants):
            const = self.spring_constants
        else:
            const = self.spring_constants[cur]

        contribution = 0
        if order == 0:
            contribution = (const/2) * (dist**2)
        elif order == 1:
            tangent = self._last_tangent
            contribution = const * dist[..., np.newaxis] * tangent
        elif order == 2:
            contribution = const * vec_ops.identity_tensors(guess.shape[0], guess.shape[1])
        return contribution

class AdjustedChainStepFinder(ChainMinimizingStepFinder):
    def __init__(self,
                 pairwise_image_function,
                 func,
                 jacobian,
                 hessian=None,
                 logger=None,
                 **opts
                 ):
        super().__init__(
            func,
            jacobian,
            hessian=hessian,
            **opts
        )
        self.pairwise_function = pairwise_image_function
        self.logger = logger

    def image_pairwise_contribution(self,guess, mask, cur, prev, next, order=0):
        return self.pairwise_function(guess, mask, cur, prev, next, order=order)

class ChainReparametrizer:
    @abc.abstractmethod
    def __call__(self, *args, **kwargs) -> '(np.ndarray, np.ndarray, np.ndarray)':
        ...

class InterpolatingReparametrizer(ChainReparametrizer):
    #TODO: add in some kind of density function
    def __init__(self, interpolator_type):
        self.interpolator_type = interpolator_type

    def __call__(self, images, fixed_positions):
        interp = self.interpolator_type(images)
        new = interp(np.linspace(len(images)))
        interp[fixed_positions] = images[fixed_positions]
        return new


def jacobi_maximize(initial_matrix, rotation_generator, max_iterations=100, contrib_tol=1e-16, tol=1e-8):
    mat = np.asanyarray(initial_matrix).copy()

    k = initial_matrix.shape[1]
    perms = list(itertools.combinations(range(k), 2))
    U = np.eye(k)

    total_delta = -1
    iteration = -1
    for iteration in range(max_iterations):
        total_delta = 0
        for n, (p_i, q_i) in enumerate(perms):
            A, B, delta = rotation_generator(mat, p_i, q_i)

            if delta > 0:
                total_delta += delta

                new_pi = A * mat[:, p_i] + B * mat[:, q_i]
                new_qi = A * mat[:, q_i] - B * mat[:, p_i]
                mat[:, p_i] = new_pi
                mat[:, q_i] = new_qi

                rot_pi = A * U[:, p_i] + B * U[:, q_i]
                rot_qi = A * U[:, q_i] - B * U[:, p_i]
                U[:, p_i] = rot_pi
                U[:, q_i] = rot_qi

        if abs(total_delta) < tol:
            break

    return mat, U, (total_delta, iteration)

class LineSearchRotationGenerator:
    def __init__(self, column_function, tol=1e-16, max_iterations=10):
        self.one_e_func = column_function
        self.tol = tol
        self.max_iter = max_iterations

    @classmethod
    def quadratic_opt(self,
                  g0, g1, g2,
                  f0, f1, f2
                  ):
        g02 = g0**2
        g12 = g1**2
        g22 = g2**2
        denom = (2*f1*g0 - 2*f2*g0 - 2*f0*g1 + 2*f2*g1 + 2*f0*g2 - 2*f1*g2)
        if abs(denom) < 1e-8:
            return None
        else:
            return (
                    (f1*g02 - f2*g02 - f0*g12 + f2*g12 + f0*g22 - f1*g22)
                      / denom
            )

    def _phi(self, g, f_i, f_j):
        c = np.cos(g)
        s = np.sin(g)
        f_i, f_j = (
            c * f_i + s * f_j,
            -s * f_i + c * f_j
        )
        val = sum(self.one_e_func(f) for f in [f_i, f_j])
        return val, (c, s), (f_i, f_j)

    def __call__(self, mat, col_i, col_j):
        f_i, f_j = [mat[:, x] for x in [col_i, col_j]]
        phi0 = sum(self.one_e_func(f) for f in [f_i, f_j])

        g0 = 0
        g1 = np.pi
        g2 = 2*np.pi

        f0 = phi0
        f1, (c, s), _ = self._phi(g1, f_i, f_j)
        f2 = phi0

        prev = max([f0, f1, f2])
        for it in range(self.max_iter):
            g = self.quadratic_opt(
                  g0, g1, g2,
                  f0, f1, f2
                  )
            if g is None or g < g0 or g > g2:
                if f2 > f0:
                    g0 = g1
                    f0 = f1
                else:
                    g2 = g1
                    f2 = f1
                g = (g0 + g2) / 2
                f, (c, s), _ = self._phi(g, f_i, f_j)
            else:
                f, (c, s), _ = self._phi(g, f_i, f_j)
                if f <= min([f0, f1, f2]):
                    if f2 > f0:
                        g0 = g1
                        f0 = f1
                    else:
                        g2 = g1
                        f2 = f1
                    g = (g0 + g2) / 2
                    f, (c, s), _ = self._phi(g, f_i, f_j)
                else:
                    if g < g1:
                        g2 = g1
                        f2 = f1
                    else:
                        g0 = g1
                        f0 = f1
            # if abs(f - prev) < self.tol:
            #     break
            f1 = f
            g1 = g

        return c, s, f1 - prev

class GradientDescentRotationGenerator:
    def __init__(self, column_function, gradient, tol=1e-16, max_iterations=10,
                 damping_parameter=.9,
                 damping_exponent=1.1,
                 restart_interval=3
                 ):
        self.one_e_func = column_function
        self.grad = gradient
        self.tol = tol
        self.max_iter = max_iterations
        self.damper = Damper(
            damping_parameter=damping_parameter,
            damping_exponent=damping_exponent,
            restart_interval=restart_interval
        )

    def __call__(self, mat, col_i, col_j):
        f_i, f_j = [mat[:, x] for x in [col_i, col_j]]
        cur_val = sum(self.one_e_func(f) for f in [f_i, f_j])

        g = 0
        c = 1
        s = 0
        cur_grads = np.array([self.grad(f) for f in [f_i, f_j]])

        new_i, new_j = f_i, f_j
        for it in range(self.max_iter):
            grads = [np.dot(f, g) for f,g in zip([new_i, new_j], cur_grads)]
            step = sum(grads)
            if abs(step) < self.tol:
                break
            else:
                u = self.damper.get_damping_factor()
                if u is not None:
                    step *= u
                g = (g + step) % (2*np.pi)
                # if abs(g) > np.pi/2: g = np.sign(g) * np.pi/2
                c = np.cos(g)
                s = np.sin(g)
                new_i, new_j = (
                    c * f_i + s * f_j,
                    -s * f_i + c * f_j
                )
                cur_grads = np.array([self.grad(f) for f in [new_i, new_j]])


        new_vals = sum(self.one_e_func(f) for f in [new_i, new_j])
        return c, s, new_vals - cur_val

class OperatorMatrixRotationGenerator:
    def __init__(self, one_e_func, matrix_func):
        self.one_e_func = one_e_func
        self.mat_func = matrix_func
    def __call__(self, mat, col_i, col_j):
        f_i, f_j = [mat[:, x] for x in [col_i, col_j]]
        cur_val = sum(self.one_e_func(f) for f in [f_i, f_j])
        a, b, c = self.mat_func(f_i, f_j)

        test_mat = np.array([[a, b], [b, c]])
        # rot = np.linalg.eigh(test_mat)[1] # do this analytically...
        # print(rot)
        # cos_g = rot[0, 0]
        # sin_g = np.sign(rot[0, 0] * rot[1, 1]) * rot[1, 0]
        # new_rot = np.array([
        #     [cos_g, -sin_g],
        #     [sin_g, cos_g]
        # ])
        # explicit 2x2 form
        tau = (c - a) / (2 * b)
        t = np.sign(tau) / (abs(tau) + np.sqrt(1 + tau ** 2))
        cos_g = 1 / np.sqrt(1 + t ** 2)
        sin_g = -cos_g * t
        # new_rot = np.array([
        #         [cos_g, -sin_g],
        #         [sin_g, cos_g]
        #     ])
        # print(new_rot.T @ test_mat @ new_rot)

        f_i, f_j = (
            cos_g * f_i + sin_g * f_j,
            -sin_g * f_i + cos_g * f_j
        )
        new_val = sum(self.one_e_func(f) for f in [f_i, f_j])


        return cos_g, sin_g, new_val - cur_val

def displacement_localizing_rotation_generator(mat, col_i, col_j):
    # Foster-Boys localization

    p = mat[:, col_i].reshape(-1, 3)
    q = mat[:, col_j].reshape(-1, 3)
    pq_norms = vec_ops.vec_dots(p, q, axis=-1)
    pp_norms = vec_ops.vec_dots(p, p, axis=-1)
    qq_norms = vec_ops.vec_dots(q, q, axis=-1)

    pqpq = np.dot(pq_norms, pq_norms)
    pppp = np.dot(pp_norms, pp_norms)
    qqqq = np.dot(qq_norms, qq_norms)
    ppqq = np.dot(pp_norms, qq_norms)
    pppq = np.dot(pp_norms, pq_norms)
    qqqp = np.dot(qq_norms, pq_norms)

    A = pqpq - (pppp + qqqq - 2 * ppqq) / 4
    B = pppq - qqqp

    AB_norm = np.sqrt(A ** 2 + B ** 2)

    return A / AB_norm, B / AB_norm, A