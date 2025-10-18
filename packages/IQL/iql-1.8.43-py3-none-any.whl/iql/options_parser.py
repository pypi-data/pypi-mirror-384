import ast
import logging
from typing import Dict, Iterable, Union

logger = logging.getLogger(__name__)

lastnode = None


def convert(node) -> Union[Iterable, object]:
    global lastnode
    lastnode = node
    if hasattr(node, "elts"):
        v = []
        for e in node.elts:
            val = convert(e)
            v.append(val)
        return v
    elif isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.Dict):
        return {convert(key): convert(value) for key, value in zip(node.keys, node.values, strict=False)}
    else:
        return node.id


def options_to_list(options: str) -> Dict[str, object]:
    p = ast.parse(options)

    results = {}

    for e in p.body:
        # This code is never reached now?
        # if isinstance(e.value, ast.Name):  # type: ignore
        #    results[e.value] = None  # type: ignore

        #    continue
        # else:
        for arg in e.value.args:  # type: ignore
            results[arg.value] = None

        for k in e.value.keywords:  # type: ignore
            r = convert(k.value)

            results[k.arg] = r

            continue

    return results
