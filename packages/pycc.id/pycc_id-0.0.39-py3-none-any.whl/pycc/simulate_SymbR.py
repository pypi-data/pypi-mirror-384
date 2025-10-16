"""
simulate_SymbR.py

Forward simulator compatible with the output of train_SymbR.train_SymbR and
with post-processed models coming from NN + Symbolic Regression (SR).

This single module implements simulate_SymbR(equations, params) with flexible
handling of model objects so it works for:
  - PySR models returned by train_SymbR (dict with 'pysr_model' / 'const')
  - SR results that expose a callable under 'func' (e.g. sr_results['f1']['func'])
  - simple callables supplied directly as models (e.g. models['f1']=lambda x: ...)
  - discrete evaluations (x,y arrays) produced by NN evaluation or SR evals

Parameters (params dict):
  - 'models' : dict returned by train_SymbR (f_name -> dict) or SR-callables
  - 'evals'  : optional list [x_f1, f1_vals, x_f2, f2_vals, ...] if models not
               provided (from NN/SR evals)
  - 'sr_results': optional dict with SR outputs (e.g. sr_results['f1']['expr'])
  - 'obtained_coefs' or 'scalar_params' : dict of scalar coefficients (a1,a2,...)
  - 'local_funcs' : dict of user-provided callables (e.g. F_ext(t) )
  - 't_span'  : (t0, tf)
  - 'y0'      : initial state vector (ordered according to equations)
  - 't_eval', 'method', 'atol', 'rtol', 'check_nan'
  - 'print_models' : bool, if True (default) prints a summary of f_i used
  - 'print_x_samples': list of floats to evaluate sample outputs for printing

Returns: (sol, derivatives_array)
  - sol: SolveIVP result
  - derivatives_array: shape (n_states, len(sol.t)) array with evaluated RHS at each time

"""

import warnings
from typing import Dict, Any, List, Tuple, Callable
import numpy as np
from scipy.integrate import solve_ivp
import sympy as sp


def _parse_equation(eq: str) -> Tuple[str, sp.Expr]:
    s = eq.replace("^", "**")
    if '=' not in s:
        raise ValueError("Equation must contain '='")
    lhs, rhs = s.split('=', 1)
    lhs_name = lhs.strip()
    rhs_expr = sp.sympify(rhs, evaluate=False)
    return lhs_name, rhs_expr


def _attach_attr(fn: Callable, **attrs):
    """Attach attributes to a callable for introspection in summaries."""
    for k, v in attrs.items():
        try:
            setattr(fn, k, v)
        except Exception:
            pass
    return fn


def _make_model_pred(model_dict: Any):
    """Return a callable pred(x_array)->array for a trained or provided model.

    Supported inputs:
      - None -> zero function
      - callable -> used directly (expects scalar input or numpy array)
      - dict with 'pysr_model'/'const' (train_SymbR output)
      - dict with 'func' -> callable (e.g. sr_results['f1']['func'])
      - dict with 'x' and 'y' (1D arrays): will create a 1D interpolator

    The returned callable always accepts a numpy array (1d) and returns a 1d array.
    The returned callable has introspection attributes like ._source, ._xp, ._yp, ._const
    where applicable.
    """
    # None -> zero
    if model_dict is None:
        fn = lambda x: np.zeros_like(np.asarray(x, dtype=float), dtype=float)
        return _attach_attr(fn, _source='zero')

    # If already a callable
    if callable(model_dict):
        def wrap_callable(x_arr, fn=model_dict):
            x_arr = np.asarray(x_arr, dtype=float)
            # try to call with array; if fails, call elementwise
            try:
                y = fn(x_arr)
            except Exception:
                y = np.array([fn(float(xi)) for xi in x_arr])
            return np.asarray(y).ravel().astype(float)
        return _attach_attr(wrap_callable, _source='callable')

    # If dict-like
    if isinstance(model_dict, dict):
        # PySR-like dict
        if ('pysr_model' in model_dict) or ('const' in model_dict):
            # reuse behavior from previous implementation
            if model_dict.get('pysr_model') is None:
                const_val = float(model_dict.get('const', 0.0))
                fn = lambda x, c=const_val: np.full_like(np.asarray(x, dtype=float), c, dtype=float)
                return _attach_attr(fn, _source='pysr_const', _const=const_val)
            py_model = model_dict.get('pysr_model')
            A0 = float(model_dict.get('A0', 0.0))
            A1 = float(model_dict.get('A1', 1.0))
            def pred_pysr(x_arr, pm=py_model, A0=A0, A1=A1):
                x_arr = np.asarray(x_arr, dtype=float)
                z = (x_arr - A0) / A1
                Xz = z.reshape(-1, 1)
                try:
                    yhat = pm.predict(Xz)
                except Exception as e:
                    warnings.warn(f"PySR model prediction failed: {e}")
                    yhat = np.zeros(len(Xz))
                return np.asarray(yhat).ravel()
            return _attach_attr(pred_pysr, _source='pysr', _A0=A0, _A1=A1, _pymodel=py_model)

        # SR output exposing 'func'
        if 'func' in model_dict and callable(model_dict['func']):
            fn = model_dict['func']
            wrapped = _make_model_pred(fn)
            return _attach_attr(wrapped, _source='sr_func', _sr_meta={k: model_dict.get(k) for k in model_dict.keys()})

        # discrete evaluation arrays (x,y) e.g. evals from NN/SR plotting
        # common keys: 'x','y' or 'x_plot','y_plot' or tuple/list with two arrays
        xarr = None
        yarr = None
        if 'x' in model_dict and 'y' in model_dict:
            xarr = np.asarray(model_dict['x'], dtype=float)
            yarr = np.asarray(model_dict['y'], dtype=float)
        elif 'x_plot' in model_dict and 'y_plot' in model_dict:
            xarr = np.asarray(model_dict['x_plot'], dtype=float)
            yarr = np.asarray(model_dict['y_plot'], dtype=float)
        elif 'xp' in model_dict and 'yp' in model_dict:
            xarr = np.asarray(model_dict['xp'], dtype=float)
            yarr = np.asarray(model_dict['yp'], dtype=float)

        if xarr is not None and yarr is not None:
            # ensure sorted
            idx = np.argsort(xarr)
            xp = xarr[idx]
            yp = yarr[idx]
            def interp_pred(xq, xp=xp, yp=yp):
                xq = np.asarray(xq, dtype=float)
                # numpy.interp returns left/right values as yp[0]/yp[-1] for OOB
                yq = np.interp(xq, xp, yp, left=yp[0], right=yp[-1])
                return yq.astype(float)
            return _attach_attr(interp_pred, _source='interp', _xp=xp, _yp=yp)

    # fallback: raise
    raise ValueError("Unsupported model object passed to _make_model_pred. Provide a callable, a PySR-style dict, a dict with 'func', or dict with 'x' and 'y' arrays.")


def _eval_sympy_symbr(expr: sp.Basic,
                      var_values: Dict[str, float],
                      t: float,
                      scalar_params: Dict[str, float],
                      local_funcs: Dict[str, Callable],
                      model_preds: Dict[str, Callable]):
    """Evaluate a sympy expression using provided maps.

    Behaves like simulate_SymbR previously but uses model_preds when f1,f2 appear.
    """
    # Number
    if expr.is_Number:
        return float(expr)

    # Symbol
    if expr.is_Symbol:
        name = str(expr)
        if name in var_values:
            return float(var_values[name])
        if name in scalar_params:
            return float(scalar_params[name])
        if name in local_funcs:
            try:
                return float(local_funcs[name](t))
            except Exception as e:
                raise RuntimeError(f"Calling local_funcs['{name}'] failed: {e}")
        raise ValueError(f"Unknown symbol '{name}' at t={t}")

    # Function call
    if expr.is_Function:
        fname = expr.func.__name__
        arg_vals = [_eval_sympy_symbr(a, var_values, t, scalar_params, local_funcs, model_preds)
                    for a in expr.args]

        # model functions f1,f2,...
        if fname in model_preds:
            if len(arg_vals) != 1:
                raise ValueError(f"Model function '{fname}' expected 1 arg, got {len(arg_vals)}")
            xval = np.asarray([arg_vals[0]], dtype=float)
            try:
                y = model_preds[fname](xval)
                return float(np.asarray(y).ravel()[0])
            except Exception as e:
                raise RuntimeError(f"Model '{fname}' prediction failed for input {xval}: {e}")

        # user-supplied local functions
        if fname in local_funcs:
            func = local_funcs[fname]
            try:
                return float(func(*arg_vals))
            except TypeError:
                try:
                    return float(func(t))
                except Exception as e:
                    raise RuntimeError(f"local_funcs['{fname}'] call failed: {e}")
            except Exception as e:
                raise RuntimeError(f"local_funcs['{fname}'] raised: {e}")

        numpy_map = {
            'sin': np.sin, 'cos': np.cos, 'tan': np.tan,
            'asin': np.arcsin, 'acos': np.arccos, 'atan': np.arctan,
            'sinh': np.sinh, 'cosh': np.cosh, 'tanh': np.tanh,
            'exp': np.exp, 'log': np.log, 'sqrt': np.sqrt, 'abs': abs
        }
        if fname in numpy_map:
            return float(numpy_map[fname](arg_vals[0]))

        raise ValueError(f"Unknown function '{fname}' in expression")

    # Add
    if expr.is_Add:
        return float(sum(_eval_sympy_symbr(a, var_values, t, scalar_params, local_funcs, model_preds) for a in expr.args))

    # Mul
    if expr.is_Mul:
        prod = 1.0
        for a in expr.args:
            prod *= _eval_sympy_symbr(a, var_values, t, scalar_params, local_funcs, model_preds)
        return float(prod)

    # Pow
    if expr.is_Pow:
        base = _eval_sympy_symbr(expr.args[0], var_values, t, scalar_params, local_funcs, model_preds)
        exp = _eval_sympy_symbr(expr.args[1], var_values, t, scalar_params, local_funcs, model_preds)
        return float(np.power(base, exp))

    raise NotImplementedError(f"Sympy node type not implemented: {type(expr)}")


def simulate_SymbR(equations: List[str], params: Dict[str, Any]):
    """Simulate ODEs using SymbR-trained models or SR post-processed models.

    Flexible input accepted in params:
      - 'models': dict f_name -> model-obj (see _make_model_pred doc)
      - or 'evals' : list like [x_f1, f1_vals, x_f2, f2_vals, ...] (from NN train output)
      - 'obtained_coefs' or 'scalar_params' : dict of scalar coefficients (a1,a2,...)
      - 'local_funcs' : user callables for F_ext etc
      - 't_span','y0' required
    Returns: sol, derivatives_array
    """
    models = params.get('models', None)
    evals = params.get('evals', None)
    sr_results = params.get('sr_results', {}) or {}
    if models is None and evals is None:
        raise ValueError("params must include 'models' (preferred) or 'evals' for NN/SR-supplied functions")

    local_funcs = params.get('local_funcs', {}) or {}
    t_span = params.get('t_span', None)
    y0 = params.get('y0', None)
    t_eval = params.get('t_eval', None)
    method = params.get('method', 'LSODA')
    atol = params.get('atol', 1e-8)
    rtol = params.get('rtol', 1e-6)
    check_nan = params.get('check_nan', True)

    scalar_params = params.get('scalar_params', params.get('obtained_coefs', {})) or {}
    try:
        import torch
        scalar_params = {k: (float(v.detach().cpu().item()) if (isinstance(v, torch.nn.Parameter) or isinstance(v, torch.Tensor)) else float(v))
                         for k, v in scalar_params.items()}
    except Exception:
        scalar_params = {k: float(v) for k, v in scalar_params.items()} if scalar_params else {}

    if t_span is None or y0 is None:
        raise ValueError("params must include 't_span' and 'y0' for SymbR simulation")

    # parse equations
    parsed = [_parse_equation(eq) for eq in equations]
    lhs = [p[0] for p in parsed]
    rhs_exprs = [p[1] for p in parsed]

    # state var inference
    state_vars = []
    for name in lhs:
        if name.endswith('_dot'):
            state_vars.append(name[:-4])
        else:
            state_vars.append(name)

    if len(state_vars) != len(y0):
        raise ValueError(f"len(state_vars)={len(state_vars)} doesn't match len(y0)={len(y0)}")

    # create model_preds mapping
    model_preds = {}
    if models is not None:
        for fname, m in models.items():
            model_preds[fname] = _make_model_pred(m)
    else:
        # parse evals list -> build interpolants
        # expects [x1,y1,x2,y2,...]
        if len(evals) % 2 != 0:
            raise ValueError("params['evals'] must contain pairs [x_f1, f1_vals, x_f2, f2_vals, ...]")
        nfuncs = len(evals) // 2
        for i in range(nfuncs):
            xp = np.asarray(evals[2*i], dtype=float)
            yp = np.asarray(evals[2*i+1], dtype=float)
            model_preds[f'f{i+1}'] = _make_model_pred({'x': xp, 'y': yp})

    # RHS for integrator
    def rhs(t, y):
        var_values = {state_vars[i]: float(y[i]) for i in range(len(state_vars))}
        dydt = np.zeros_like(y, dtype=float)
        for i, expr in enumerate(rhs_exprs):
            val = _eval_sympy_symbr(expr, var_values, float(t), scalar_params, local_funcs, model_preds)
            dydt[i] = float(val)
        return dydt

    # --- Print model summaries & sample evaluations (user-facing) ---
    # Controlled by params['print_models'] (default True) and params['print_x_samples']
    print_models_flag = bool(params.get('print_models', True))
    print_x_samples = params.get('print_x_samples', None) or [-1.0, 0.0, 1.0]

    def _model_summary(fname, original_obj, pred_callable, sr_meta=None):
        """Return a short string summarizing the model and sample evaluations."""
        lines = [f"Model '{fname}':"]
        # original object description
        if original_obj is not None:
            if callable(original_obj):
                lines.append("  source: callable")
            elif isinstance(original_obj, dict):
                if 'pysr_model' in original_obj or 'const' in original_obj:
                    lines.append("  source: PySR-style dict")
                    if 'const' in original_obj:
                        lines.append(f"    constant: {original_obj.get('const')}")
                    # try printing expr if present
                    for key in ('expr', 'expression', 'sympy', 'sym_expr'):
                        if key in original_obj and original_obj[key] is not None:
                            lines.append(f"    {key}: {original_obj[key]}")
                elif 'func' in original_obj and callable(original_obj['func']):
                    lines.append("  source: SR result dict with 'func' callable")
                    # print symbolic if present
                    for key in ('expr', 'expression', 'sympy', 'sym_expr'):
                        if key in original_obj and original_obj[key] is not None:
                            lines.append(f"    {key}: {original_obj[key]}")
                elif 'x' in original_obj and 'y' in original_obj:
                    lines.append(f"  source: discrete eval arrays, n={len(original_obj.get('x'))}")
                else:
                    lines.append("  source: dict (unknown format)")
            else:
                lines.append(f"  source: {type(original_obj)}")
        else:
            # inspect pred_callable attributes (attached at creation)
            src = getattr(pred_callable, '_source', None)
            if src is not None:
                lines.append(f"  source (inferred): {src}")
                if src == 'pysr':
                    A0 = getattr(pred_callable, '_A0', None)
                    A1 = getattr(pred_callable, '_A1', None)
                    if A0 is not None and A1 is not None:
                        lines.append(f"    A0={A0}, A1={A1}")
                if src == 'interp':
                    xp = getattr(pred_callable, '_xp', None)
                    if xp is not None:
                        lines.append(f"    interp points: n={len(xp)} range=[{xp.min():.4g},{xp.max():.4g}]")
                if src == 'pysr_const':
                    const = getattr(pred_callable, '_const', None)
                    lines.append(f"    const={const}")
            else:
                lines.append("  source: (unknown)")

            # if sr_meta provided, print expr if present
            if sr_meta is not None:
                for key in ('expr', 'expression', 'sympy', 'sym_expr'):
                    if key in sr_meta and sr_meta[key] is not None:
                        lines.append(f"  {key}: {sr_meta[key]}")

        # sample evaluations (try safe calls)
        try:
            xs = np.asarray(print_x_samples, dtype=float)
            ys = pred_callable(xs)
            ys = np.asarray(ys, dtype=float).ravel()
            sample_str = ", ".join([f"{x}->{y:.4g}" for x, y in zip(xs, ys)])
            lines.append(f"  samples: {sample_str}")
        except Exception as e:
            lines.append(f"  samples: (evaluation failed: {e})")

        return "\n".join(lines)

    if print_models_flag:
        print('\n=== Models to be used in simulation ===')
        # try to map back to original 'models' entries where available
        for fname in sorted(model_preds.keys()):
            original_obj = None
            sr_meta = None
            if models is not None and fname in models:
                original_obj = models[fname]
                sr_meta = models[fname] if isinstance(models[fname], dict) else None
            # check sr_results parameter as fallback
            if original_obj is None and fname in sr_results:
                original_obj = sr_results[fname]
                sr_meta = sr_results[fname]
            try:
                info = _model_summary(fname, original_obj, model_preds[fname], sr_meta=sr_meta)
            except Exception as e:
                info = f"Model '{fname}': (summary failed: {e})"
            print(info)
            print('-------------------------------------')
        print('\n=== End of model summaries ===\n')

    sol = solve_ivp(rhs, t_span, y0, t_eval=t_eval, method=method, atol=atol, rtol=rtol)

    if check_nan:
        if np.any(np.isnan(sol.y)) or np.any(np.isinf(sol.y)):
            raise RuntimeError("SymbR simulation produced NaN or Inf in solution.")

    # compute derivatives array at each saved time step
    derivatives = []
    for i in range(len(sol.t)):
        tval = sol.t[i]
        yvals = sol.y[:, i]
        dydt_vals = rhs(tval, yvals)
        derivatives.append(dydt_vals)

    derivatives_array = np.array(derivatives).T

    return sol, derivatives_array


if __name__ == '__main__':
    print('This module provides simulate_SymbR(equations, params). Import and call from your script.')

