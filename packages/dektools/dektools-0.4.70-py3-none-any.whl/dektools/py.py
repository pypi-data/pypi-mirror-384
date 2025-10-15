import os
import sys
from .file import read_text


def get_whl_name(path):
    return os.path.basename(path).rsplit('-', 4)[0]


def eval_lines(s, context=None):
    globals_ = {} if context is None else context
    locals_ = {}
    exec(s, globals_, locals_)
    return locals_


def eval_file(filepath, context=None):
    return eval_lines(read_text(filepath, default=''), context)


def get_inner_vars(*var_name_list, full=True):
    def walk(attr):
        depth = 1
        while True:
            try:
                frame = sys._getframe(depth)
            except ValueError:
                return
            scope = getattr(frame, attr)
            for i, name in enumerate(var_name_list):
                if result[i] is unset:
                    if name in scope:
                        result[i] = scope[name]
            if not list_unset():
                break
            depth += 1

    def list_unset():
        return [var_name_list[i] for i, x in enumerate(result) if x is unset]

    unset = object()
    result = [unset] * len(var_name_list)
    walk('f_globals')
    if full and list_unset():
        walk('f_locals')
    lu = list_unset()
    if lu:
        raise ValueError(f"Can't find: {lu}")
    if len(result) == 1:
        return result[0]
    return tuple(result)
