from __future__ import annotations

import ast
import random
from pathlib import Path
from typing import Any, Dict, Mapping

from .evaluator import EvaluationInput, evaluate_policy, load_policy as _load_policy_file, PolicyEvaluationError

_POLICY_CACHE: Dict[str, Dict[str, Any]] = {}


def call(ctx: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    state = _ensure_state(state)
    step_name = ctx.get("step")
    config = ctx.get("config", {})
    call_spec = config.get("call") if isinstance(config, Mapping) else None
    if not isinstance(call_spec, Mapping):
        raise RuntimeError("Call step missing configuration")

    target = call_spec.get("target")
    args_spec = call_spec.get("args", {})
    evaluated_args = _evaluate_value(args_spec, state)

    if isinstance(target, str):
        handler = _HANDLERS.get(target, _default_handler)
    else:
        handler = _default_handler

    result = handler(ctx, state, evaluated_args)
    if not isinstance(result, dict):
        raise RuntimeError(f"Handler for '{target}' must return a dict")
    if isinstance(step_name, str):
        state["steps"][step_name] = result
    state["current"] = result
    return state


def switch(ctx: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    # Switch steps are evaluated by the runtime via edges; we just mirror state.
    state = _ensure_state(state)
    state["current"] = {"config": dict(ctx.get("config", {}))}
    return state


def emit_outputs(ctx: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    state = _ensure_state(state)
    config = ctx.get("config", {})
    outputs_spec = config.get("outputs", {})
    evaluated = _evaluate_value(outputs_spec, state)
    if not isinstance(evaluated, dict):
        raise RuntimeError("Outputs step must evaluate to a mapping")
    state["outputs"] = evaluated
    state["current"] = evaluated
    return state


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _ensure_state(state: Dict[str, Any]) -> Dict[str, Any]:
    if "steps" not in state or not isinstance(state.get("steps"), dict):
        inputs = dict(state)
        state.clear()
        state["inputs"] = inputs
        state["steps"] = {}
        state["current"] = {}
    else:
        state.setdefault("inputs", {})
        state.setdefault("current", {})
    return state


def _evaluate_value(value: Any, state: Dict[str, Any]) -> Any:
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("$input."):
            return _lookup_path(state.get("inputs", {}), text[len("$input.") :])
        if text.startswith("$step."):
            step_path = text[len("$step.") :]
            step_name, _, remainder = step_path.partition(".")
            step_data = state.get("steps", {}).get(step_name, {})
            if remainder:
                return _lookup_path(step_data, remainder)
            return step_data
        try:
            return ast.literal_eval(text)
        except Exception:
            current = state.get("current", {})
            return current.get(text, text)
    if isinstance(value, list):
        return [_evaluate_value(item, state) for item in value]
    if isinstance(value, dict):
        return {key: _evaluate_value(val, state) for key, val in value.items()}
    return value


def _lookup_path(root: Any, dotted: str) -> Any:
    cur = root
    for part in dotted.split("."):

        if isinstance(cur, Mapping):
            cur = cur.get(part)
        else:
            return None
    return cur


# ---------------------------------------------------------------------------
# Call handlers
# ---------------------------------------------------------------------------
def _default_handler(ctx: Dict[str, Any], state: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    target = ctx.get("config", {}).get("call", {}).get("target")
    return {"target": target, "args": args}


def _handle_opcua_read(ctx: Dict[str, Any], state: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    endpoint = args.get("endpoint")
    node_ids = args.get("node_ids", [])
    values: Dict[str, Any] = {}
    if isinstance(node_ids, list):
        for node in node_ids:
            values[str(node)] = 80.0
    return {"endpoint": endpoint, "values": values}


def _handle_opcua_write(ctx: Dict[str, Any], state: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    endpoint = args.get("endpoint")
    node_id = args.get("node_id")
    value = args.get("value")
    return {"endpoint": endpoint, "node_id": node_id, "value": value, "status": "ok"}


def _handle_policy_apply(ctx: Dict[str, Any], state: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    config = ctx.get("config", {})
    policy_path = config.get("policy_ref")
    policy_id = config.get("policy_id")
    values = args.get("values")
    if not isinstance(values, Mapping):
        values = {}
    try:
        policy = _load_policy(policy_path)
        result = evaluate_policy(
            policy,
            EvaluationInput(values=values, epsilon=None, random_func=random.random),
        )
    except (PolicyEvaluationError, RuntimeError) as exc:
        return {
            "action": "NONE",
            "policy_id": policy_id,
            "values": values,
            "error": str(exc),
        }
    result.setdefault("policy_id", policy_id)
    return result


_HANDLERS = {
    "opcua.read": _handle_opcua_read,
    "opcua.write": _handle_opcua_write,
    "policy.apply": _handle_policy_apply,
}


def _load_policy(path: Any) -> Dict[str, Any]:
    if not isinstance(path, str):
        raise RuntimeError("policy.apply step requires policy_ref path")
    cached = _POLICY_CACHE.get(path)
    if cached is None:
        resolved = Path(path)
        data = _load_policy_file(resolved)
        if not isinstance(data, dict):
            raise RuntimeError(f"Policy file '{path}' must contain an object")
        _POLICY_CACHE[path] = data
        cached = data
    return cached


__all__ = ["call", "switch", "emit_outputs"]
