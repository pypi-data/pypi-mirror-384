"""
simulate_SymbR.py

Simulator compatible with train_SymbR output and SR postprocessing. Updated
printing to display symbolic expressions when available (from sr_results or
from PySR model objects).

Also supports fitting PySR models from discrete evals; defaults for PySR are
set to safer operators and default niterations/populations as requested.
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
    if model_obj is None:
        fn = lambda x: np.zeros_like(np.asarray(x, dtype=float), dtype=float)
        return _attach_attr(fn, _source='zero')

    if callable(model_obj):
        def wrap_callable(xq, fn=model_obj):
            xq = np.asarray(xq, dtype=float)
            try:
                yq = fn(xq)
            except Exception:
                yq = np.array([fn(float(xi)) for xi in xq])
            return np.asarray(yq).ravel().astype(float)
        return _attach_attr(wrap_callable, _source='callable')

    if isinstance(model_obj, dict):
        if ('pysr_model' in model_obj) or ('const' in model_obj):
            if model_obj.get('pysr_model') is None:
                const_val = float(model_obj.get('const', 0.0))
                fn = lambda x, c=const_val: np.full_like(np.asarray(x, dtype=float), c, dtype=float)
                return _attach_attr(fn, _source='pysr_const', _const=const_val, _expr=model_obj.get('expr'))
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
            return _attach_attr(pred_pysr, _source='pysr', _A0=A0, _A1=A1, _pymodel=pm, _expr=model_obj.get('expr'))

        if 'func' in model_obj and callable(model_obj['func']):
            return _make_model_pred(model_obj['func'])

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


def _extract_expr_from_pysr(pm) -> Optional[str]:
    if pm is None:
        return None
    try:
        if hasattr(pm, 'get_best'):
            best = pm.get_best()
            try:
                if hasattr(best, 'iloc'):
                    for col in ('sympy', 'equation', 'program'):
                        if col in best.columns:
                            return str(best[col].iloc[0])
                if isinstance(best, dict):
                    for key in ('sympy', 'equation', 'program'):
                        if key in best:
                            return str(best[key])
            except Exception:
                pass
        if hasattr(pm, 'best_program_'):
            return str(pm.best_program_)
        if hasattr(pm, 'programs_'):
            try:
                head = pm.programs_.head(1)
                for col in ('sympy', 'equation', 'program'):
                    if col in head.columns:
                        return str(head[col].iloc[0])
            except Exception:
                pass
        return str(pm)
    except Exception:
        return None


def _fit_evals_with_pysr(evals: List[Any], function_names: Optional[List[str]] = None,
                         sr_params: Optional[Dict[str, Any]] = None):
    """Fit PySR models from evals = [x1,y1, x2,y2, ...].

    Defaults requested by user:
        niterations = 200, populations = 15
        unary_operators = ["cos","sin","exp","log","sqrt","tanh"]
        binary_operators = ["+","-","*"]
        model_selection = "best"
        loss = "loss(x, y) = (x - y)^2"

    The user may pass sr_params={'niterations':..,'populations':.., ...} to override.
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

        A0 = float((xp.max() + xp.min())/2.0)
        A1 = float((xp.max() - xp.min())/2.0)
        if A1 == 0.0:
            A1 = 1.0

        if PySRRegressor is not None:
            # prepare PySR kwargs with requested defaults and allow overrides
            user_params = dict(sr_params) if sr_params else {}
            niterations = int(user_params.pop('niterations', 200))
            populations = int(user_params.pop('populations', 15))
            # base kwargs
            base_kwargs = {
                'niterations': niterations,
                'populations': populations,
                'binary_operators': ["+", "-", "*"],
                'unary_operators': ["cos", "sin", "exp", "log", "sqrt", "tanh"],
                'model_selection': "best",
                'loss': "loss(x, y) = (x - y)^2",
                'verbosity': 0,
            }
            # merge user params (remaining keys) overriding defaults
            pysr_kwargs = {**base_kwargs, **user_params}
            try:
                model = PySRRegressor(**pysr_kwargs)
                X = ((xp - A0) / A1).reshape(-1, 1)
                model.fit(X, yp)
                expr = _extract_expr_from_pysr(model)
                models_out[fname] = {'pysr_model': model, 'A0': A0, 'A1': A1, 'expr': expr}
                continue
            except Exception as e:
                warnings.warn(f'PySR fitting for {fname} failed, falling back to interp: {e}')

        models_out[fname] = {'x': xp, 'y': yp}

    return models_out


def _eval_sympy_symbr(expr: sp.Basic,
                      var_values: Dict[str, float],
                      t: float,
                      scalar_params: Dict[str, float],
                      local_funcs: Dict[str, Callable],
                      model_preds: Dict[str, Callable]):
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
        if fname in model_preds:
            if len(args) != 1:
                raise ValueError(f"Model {fname} expected 1 arg, got {len(args)}")
            xval = np.asarray([args[0]], dtype=float)
            y = model_preds[fname](xval)
            return float(np.asarray(y).ravel()[0])
        if fname in local_funcs:
            try:
                return float(local_funcs[fname](*args))
            except TypeError:
                return float(local_funcs[fname](t))
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
    models = params.get('models', None)
    evals = params.get('evals', None)
    function_names = params.get('function_names', None)
    sr_params = params.get('sr_params', None)
    sr_results = params.get('sr_results', {}) or {}

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
        raise ValueError("params must include 't_span' and 'y0'")

    parsed = [_parse_equation(eq) for eq in equations]
    lhs = [p[0] for p in parsed]
    rhs_exprs = [p[1] for p in parsed]

    state_vars = [name[:-4] if name.endswith('_dot') else name for name in lhs]
    if len(state_vars) != len(y0):
        raise ValueError(f"len(state_vars)={len(state_vars)} doesn't match len(y0)={len(y0)}")

    model_preds: Dict[str, Callable] = {}
    original_models = {}
    if models is not None:
        for fname, obj in models.items():
            model_preds[fname] = _make_model_pred(obj)
            original_models[fname] = obj
    elif evals is not None:
        fitted = _fit_evals_with_pysr(evals, function_names=function_names, sr_params=sr_params)
        for fname, obj in fitted.items():
            model_preds[fname] = _make_model_pred(obj)
            original_models[fname] = obj

    def rhs(t, y):
        var_map = {state_vars[i]: float(y[i]) for i in range(len(state_vars))}
        dydt = np.zeros_like(y, dtype=float)
        for i, expr in enumerate(rhs_exprs):
            val = _eval_sympy_symbr(expr, var_map, float(t), scalar_params, local_funcs, model_preds)
            dydt[i] = float(val)
        return dydt

    if bool(params.get('print_models', True)):
        print('=== Models used in simulation ===')
        for fname in sorted(model_preds.keys()):
            expr_str = None
            if fname in sr_results and isinstance(sr_results[fname], dict):
                for key in ('expr', 'expression', 'sympy', 'sym_expr'):
                    if key in sr_results[fname] and sr_results[fname][key] is not None:
                        expr_str = str(sr_results[fname][key])
                        break
            if expr_str is None and fname in original_models and isinstance(original_models[fname], dict):
                for key in ('expr', 'expression', 'sympy', 'sym_expr'):
                    if key in original_models[fname] and original_models[fname][key] is not None:
                        expr_str = str(original_models[fname][key])
                        break
            if expr_str is None:
                pred = model_preds[fname]
                pm = getattr(pred, '_pymodel', None)
                if pm is not None:
                    try:
                        expr_from_pm = _extract_expr_from_pysr(pm)
                        if expr_from_pm is not None:
                            expr_str = expr_from_pm
                    except Exception:
                        pass
            if expr_str is not None:
                try:
                    print(f"{fname}(x) = {expr_str}")
                except Exception:
                    print(f"{fname}: (expression available)")
                try:
                    xs = np.array(params.get('print_x_samples', [-1.0, 0.0, 1.0]), dtype=float)
                    ys = model_preds[fname](xs)
                    sample_str = ', '.join([f"{x}->{y:.4g}" for x, y in zip(xs, np.asarray(ys).ravel())])
                    print(f"  samples: {sample_str}")
                except Exception:
                    pass
            else:
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

