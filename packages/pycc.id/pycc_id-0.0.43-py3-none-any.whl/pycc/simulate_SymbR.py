"""
simulate_SymbR.py

Simplified and corrected forward simulator compatible with train_SymbR output
and with post-processed SR results or raw evaluations (evals).

Behavior:
 - If params['models'] is provided, those models are used (supports PySR-style
   dicts, callables, SR-result dicts with 'func', or discrete x/y arrays).
 - If params['evals'] is provided, the code will try to fit a PySR model to each
   (x,y) pair using params['sr_params'] (or fallback to interpolation if PySR
   is not installed). You can also pass 'function_names' to name the functions
   (defaults to ['f1','f2',...]).

API:
    sol, derivatives = simulate_SymbR(equations, params)

See docstrings for details.
"""

import warnings
from typing import Dict, Any, List, Tuple, Callable, Optional
import numpy as np
from scipy.integrate import solve_ivp
import sympy as sp


# Optional import of PySR (only used when fitting from evals)
try:
    from pysr import PySRRegressor
except Exception:
    PySRRegressor = None


def _parse_equation(eq: str) -> Tuple[str, sp.Expr]:
    s = eq.replace("^", "**")
    if '=' not in s:
        raise ValueError("Equation must contain '='")
    lhs, rhs = s.split('=', 1)
    lhs_name = lhs.strip()
    rhs_expr = sp.sympify(rhs, evaluate=False)
    return lhs_name, rhs_expr


def _attach_attr(fn: Callable, **attrs):
    for k, v in attrs.items():
        try:
            setattr(fn, k, v)
        except Exception:
            pass
    return fn


def _make_model_pred(model_obj: Any):
    """Return a callable that accepts a 1D numpy array and returns 1D array.

    Supports:
      - None -> zero function
      - callable -> used directly (if scalar-only, will be vectorized)
      - dict with 'pysr_model' and optional 'A0','A1' or 'const'
      - dict with 'func' -> callable (SR postproc)
      - dict with 'x' and 'y' arrays -> linear interpolation
    """
    if model_obj is None:
        fn = lambda x: np.zeros_like(np.asarray(x, dtype=float), dtype=float)
        return _attach_attr(fn, _source='zero')

    if callable(model_obj):
        def wrap_callable(xq, fn=model_obj):
            xq = np.asarray(xq, dtype=float)
            try:
                yq = fn(xq)
            except Exception:
                # try element-wise
                yq = np.array([fn(float(xi)) for xi in xq])
            return np.asarray(yq).ravel().astype(float)
        return _attach_attr(wrap_callable, _source='callable')

    if isinstance(model_obj, dict):
        # PySR-style dict
        if ('pysr_model' in model_obj) or ('const' in model_obj):
            if model_obj.get('pysr_model') is None:
                const_val = float(model_obj.get('const', 0.0))
                fn = lambda x, c=const_val: np.full_like(np.asarray(x, dtype=float), c, dtype=float)
                return _attach_attr(fn, _source='pysr_const', _const=const_val)
            pm = model_obj.get('pysr_model')
            A0 = float(model_obj.get('A0', 0.0))
            A1 = float(model_obj.get('A1', 1.0))
            def pred_pysr(xq, pm=pm, A0=A0, A1=A1):
                xq = np.asarray(xq, dtype=float)
                z = (xq - A0) / A1
                Xz = z.reshape(-1, 1)
                try:
                    yhat = pm.predict(Xz)
                except Exception as e:
                    warnings.warn(f"PySR predict failed: {e}")
                    yhat = np.zeros(len(Xz))
                return np.asarray(yhat).ravel().astype(float)
            return _attach_attr(pred_pysr, _source='pysr', _A0=A0, _A1=A1, _pymodel=pm)

        # SR postproc exposing 'func'
        if 'func' in model_obj and callable(model_obj['func']):
            return _make_model_pred(model_obj['func'])

        # discrete eval arrays
        xarr = None
        yarr = None
        if 'x' in model_obj and 'y' in model_obj:
            xarr = np.asarray(model_obj['x'], dtype=float)
            yarr = np.asarray(model_obj['y'], dtype=float)
        elif 'x_plot' in model_obj and 'y_plot' in model_obj:
            xarr = np.asarray(model_obj['x_plot'], dtype=float)
            yarr = np.asarray(model_obj['y_plot'], dtype=float)
        if xarr is not None and yarr is not None:
            idx = np.argsort(xarr)
            xp = xarr[idx]
            yp = yarr[idx]
            def interp_fn(xq, xp=xp, yp=yp):
                xq = np.asarray(xq, dtype=float)
                yq = np.interp(xq, xp, yp, left=yp[0], right=yp[-1])
                return yq.astype(float)
            return _attach_attr(interp_fn, _source='interp', _xp=xp, _yp=yp)

    raise ValueError('Unsupported model object passed to _make_model_pred')


def _fit_evals_with_pysr(evals: List[Any], function_names: Optional[List[str]] = None,
                         sr_params: Optional[Dict[str, Any]] = None):
    """Fit PySR models from evals = [x1,y1, x2,y2, ...].

    Returns dict mapping fname -> model_dict compatible with _make_model_pred.
    If PySR is not installed, returns interpolants instead.
    """
    if function_names is None:
        n = len(evals) // 2
        function_names = [f'f{i+1}' for i in range(n)]
    if len(evals) % 2 != 0:
        raise ValueError('evals must contain pairs [x1,y1,x2,y2,...]')

    models_out = {}
    nfuncs = len(evals) // 2
    for i in range(nfuncs):
        xp = np.asarray(evals[2*i], dtype=float)
        yp = np.asarray(evals[2*i+1], dtype=float)
        fname = function_names[i] if i < len(function_names) else f'f{i+1}'

        # compute simple scaling A0,A1
        A0 = float((xp.max() + xp.min())/2.0)
        A1 = float((xp.max() - xp.min())/2.0)
        if A1 == 0.0:
            A1 = 1.0

        # If PySR available, try to fit
        if PySRRegressor is not None:
            pysr_kwargs = sr_params.copy() if sr_params else {}
            # ensure features for single-var regression
            try:
                model = PySRRegressor(**pysr_kwargs)
                X = ((xp - A0) / A1).reshape(-1, 1)
                model.fit(X, yp)
                models_out[fname] = {'pysr_model': model, 'A0': A0, 'A1': A1}
                continue
            except Exception as e:
                warnings.warn(f'PySR fitting for {fname} failed, falling back to interp: {e}')

        # fallback: store discrete arrays
        models_out[fname] = {'x': xp, 'y': yp}

    return models_out


def _eval_sympy_symbr(expr: sp.Basic,
                      var_values: Dict[str, float],
                      t: float,
                      scalar_params: Dict[str, float],
                      local_funcs: Dict[str, Callable],
                      model_preds: Dict[str, Callable]):
    """Evaluate sympy expression using model_preds for f_i calls.

    Only implements basic arithmetic, pow and common numpy unary funcs.
    """
    # Numbers
    if expr.is_Number:
        return float(expr)
    if expr.is_Symbol:
        name = str(expr)
        if name in var_values:
            return float(var_values[name])
        if name in scalar_params:
            return float(scalar_params[name])
        if name in local_funcs:
            return float(local_funcs[name](t))
        raise ValueError(f"Unknown symbol '{name}' at t={t}")

    if expr.is_Function:
        fname = expr.func.__name__
        args = [ _eval_sympy_symbr(a, var_values, t, scalar_params, local_funcs, model_preds)
                 for a in expr.args ]
        # model functions
        if fname in model_preds:
            if len(args) != 1:
                raise ValueError(f"Model {fname} expected 1 arg, got {len(args)}")
            xval = np.asarray([args[0]], dtype=float)
            y = model_preds[fname](xval)
            return float(np.asarray(y).ravel()[0])
        # local funcs
        if fname in local_funcs:
            try:
                return float(local_funcs[fname](*args))
            except TypeError:
                return float(local_funcs[fname](t))
        # numpy mapping
        numpy_map = {
            'sin': np.sin, 'cos': np.cos, 'tan': np.tan,
            'asin': np.arcsin, 'acos': np.arccos, 'atan': np.arctan,
            'sinh': np.sinh, 'cosh': np.cosh, 'tanh': np.tanh,
            'exp': np.exp, 'log': np.log, 'sqrt': np.sqrt, 'abs': abs
        }
        if fname in numpy_map:
            return float(numpy_map[fname](args[0]))
        raise ValueError(f"Unknown function '{fname}' in expression")

    if expr.is_Add:
        return float(sum(_eval_sympy_symbr(a, var_values, t, scalar_params, local_funcs, model_preds) for a in expr.args))
    if expr.is_Mul:
        prod = 1.0
        for a in expr.args:
            prod *= _eval_sympy_symbr(a, var_values, t, scalar_params, local_funcs, model_preds)
        return float(prod)
    if expr.is_Pow:
        base = _eval_sympy_symbr(expr.args[0], var_values, t, scalar_params, local_funcs, model_preds)
        exp = _eval_sympy_symbr(expr.args[1], var_values, t, scalar_params, local_funcs, model_preds)
        return float(np.power(base, exp))

    raise NotImplementedError(f"Sympy node type not implemented: {type(expr)}")


def simulate_SymbR(equations: List[str], params: Dict[str, Any]):
    """Simulate ODEs using models or evals.

    Required params:
      - 't_span' (t0, tf), 'y0' initial vector
    Either provide:
      - 'models': dict mapping function names -> model objects (see _make_model_pred)
      - OR 'evals': list [x1,y1,x2,y2,...] and optional 'function_names' and 'sr_params'

    Optional:
      - 'local_funcs' (e.g. {'F_ext': lambda t: ...}),
      - 'obtained_coefs' or 'scalar_params' (dict of a1,a2...)
      - 't_eval','method','atol','rtol','check_nan','print_models','print_x_samples'

    Returns (sol, derivatives_array)
    """
    models = params.get('models', None)
    evals = params.get('evals', None)
    function_names = params.get('function_names', None)
    sr_params = params.get('sr_params', None)

    local_funcs = params.get('local_funcs', {}) or {}
    t_span = params.get('t_span', None)
    y0 = params.get('y0', None)
    t_eval = params.get('t_eval', None)
    method = params.get('method', 'LSODA')
    atol = params.get('atol', 1e-8)
    rtol = params.get('rtol', 1e-6)
    check_nan = params.get('check_nan', True)

    scalar_params = params.get('scalar_params', params.get('obtained_coefs', {})) or {}
    # convert torch tensors if present
    try:
        import torch
        scalar_params = {k: (float(v.detach().cpu().item()) if (isinstance(v, torch.nn.Parameter) or isinstance(v, torch.Tensor)) else float(v))
                         for k, v in scalar_params.items()}
    except Exception:
        scalar_params = {k: float(v) for k, v in scalar_params.items()} if scalar_params else {}

    if t_span is None or y0 is None:
        raise ValueError("params must include 't_span' and 'y0'")

    parsed = [_parse_equation(eq) for eq in equations]
    lhs = [p[0] for p in parsed]
    rhs_exprs = [p[1] for p in parsed]

    # derive state variable names
    state_vars = [name[:-4] if name.endswith('_dot') else name for name in lhs]
    if len(state_vars) != len(y0):
        raise ValueError(f"len(state_vars)={len(state_vars)} doesn't match len(y0)={len(y0)}")

    # Build model_preds mapping
    model_preds: Dict[str, Callable] = {}
    original_models = {}
    if models is not None:
        for fname, obj in models.items():
            model_preds[fname] = _make_model_pred(obj)
            original_models[fname] = obj
    elif evals is not None:
        # fit pysr if available, else interp
        fitted = _fit_evals_with_pysr(evals, function_names=function_names, sr_params=sr_params)
        for fname, obj in fitted.items():
            model_preds[fname] = _make_model_pred(obj)
            original_models[fname] = obj

    # integrator RHS
    def rhs(t, y):
        var_map = {state_vars[i]: float(y[i]) for i in range(len(state_vars))}
        dydt = np.zeros_like(y, dtype=float)
        for i, expr in enumerate(rhs_exprs):
            val = _eval_sympy_symbr(expr, var_map, float(t), scalar_params, local_funcs, model_preds)
            dydt[i] = float(val)
        return dydt

    # optional printing
    if bool(params.get('print_models', True)):
        print('=== Models used in simulation ===')
        for fname in sorted(model_preds.keys()):
            src = getattr(model_preds[fname], '_source', None)
            line = f"{fname}: source={src}"
            if src == 'pysr':
                line += f" (A0={getattr(model_preds[fname],'_A0',None)}, A1={getattr(model_preds[fname],'_A1',None)})"
            print(line)
        print('=== end models ===')

    sol = solve_ivp(rhs, t_span, y0, t_eval=t_eval, method=method, atol=atol, rtol=rtol)

    if check_nan and (np.any(np.isnan(sol.y)) or np.any(np.isinf(sol.y))):
        raise RuntimeError('Simulation produced NaN or Inf in solution')

    derivatives = [rhs(sol.t[i], sol.y[:, i]) for i in range(len(sol.t))]
    derivatives_array = np.array(derivatives).T

    return sol, derivatives_array


if __name__ == '__main__':
    print('This module provides simulate_SymbR(equations, params). Import and call from your script.')

