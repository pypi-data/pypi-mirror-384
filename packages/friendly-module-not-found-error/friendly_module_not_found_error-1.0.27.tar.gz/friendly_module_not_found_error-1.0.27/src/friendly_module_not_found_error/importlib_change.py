import importlib
import sys
import _warnings

original_find_and_load_unlocked = importlib._bootstrap._find_and_load_unlocked
_ERR_MSG_PREFIX = 'No module named '
_CHILD_ERR_MSG = 'module {!r} has no child module {!r}'
major, minor = sys.version_info[:2]
_call_with_frames_removed = importlib._bootstrap._call_with_frames_removed
_find_spec = importlib._bootstrap._find_spec
_load_unlocked = importlib._bootstrap._load_unlocked


def _find_and_load_unlocked_v7(name, import_):
    path = None
    parent, _, child = name.rpartition('.')
    if parent:
        if parent not in sys.modules:
            _call_with_frames_removed(import_, parent)
        # Crazy side-effects!
        if name in sys.modules:
            return sys.modules[name]
        parent_module = sys.modules[parent]
        try:
            path = parent_module.__path__
        except AttributeError:
            msg = _CHILD_ERR_MSG.format(parent, child) + f'; {parent!r} is not a package'
            raise ModuleNotFoundError(msg, name=name) from None
    spec = _find_spec(name, path)
    if spec is None:
        if not parent:
            msg = f'{_ERR_MSG_PREFIX}{name!r}'
        else:
            msg = _CHILD_ERR_MSG.format(parent, child)
        raise ModuleNotFoundError(msg, name=name)
    else:
        module = _load_unlocked(spec)
    if parent:
        # Set the module as an attribute on its parent.
        parent_module = sys.modules[parent]
        setattr(parent_module, name.rpartition('.')[2], module)
    return module


def _find_and_load_unlocked_v9(name, import_):
    path = None
    parent, _, child = name.rpartition('.')
    if parent:
        if parent not in sys.modules:
            _call_with_frames_removed(import_, parent)
        # Crazy side-effects!
        if name in sys.modules:
            return sys.modules[name]
        parent_module = sys.modules[parent]
        try:
            path = parent_module.__path__
        except AttributeError:
            msg = _CHILD_ERR_MSG.format(parent, child) + f'; {parent!r} is not a package'
            raise ModuleNotFoundError(msg, name=name) from None
    spec = _find_spec(name, path)
    if spec is None:
        if not parent:
            msg = f'{_ERR_MSG_PREFIX}{name!r}'
        else:
            msg = _CHILD_ERR_MSG.format(parent, child)
        raise ModuleNotFoundError(msg, name=name)
    else:
        module = _load_unlocked(spec)
    if parent:
        # Set the module as an attribute on its parent.
        parent_module = sys.modules[parent]
        try:
            setattr(parent_module, child, module)
        except AttributeError:
            msg = f"Cannot set an attribute on {parent!r} for child module {child!r}"
            _warnings.warn(msg, ImportWarning)
    return module


def _find_and_load_unlocked_v11(name, import_):
    path = None
    parent, _, child = name.rpartition('.')
    parent_spec = None
    if parent:
        if parent not in sys.modules:
            importlib._bootstrap._call_with_frames_removed(import_, parent)
        # Crazy side-effects!
        module = sys.modules.get(name)
        if module is not None:
            return module
        parent_module = sys.modules[parent]
        try:
            path = parent_module.__path__
        except AttributeError:
            msg = _CHILD_ERR_MSG.format(parent, child) + f'; {parent!r} is not a package'
            raise ModuleNotFoundError(msg, name=name) from None
        parent_spec = parent_module.__spec__
        if getattr(parent_spec, '_initializing', False):
            importlib._bootstrap._call_with_frames_removed(import_, parent)
        # Crazy side-effects (again)!
        module = sys.modules.get(name)
        if module is not None:
            return module
    spec = importlib._bootstrap._find_spec(name, path)
    if spec is None:
        if not parent:
            msg = f'{_ERR_MSG_PREFIX}{name!r}'
        else:
            msg = _CHILD_ERR_MSG.format(parent, child)
        raise ModuleNotFoundError(msg, name=name)
    else:
        if parent_spec:
            # Temporarily add child we are currently importing to parent's
            # _uninitialized_submodules for circular import tracking.
            parent_spec._uninitialized_submodules.append(child)
        try:
            module = importlib._bootstrap._load_unlocked(spec)
        finally:
            if parent_spec:
                parent_spec._uninitialized_submodules.pop()
    if parent:
        # Set the module as an attribute on its parent.
        parent_module = sys.modules[parent]
        try:
            setattr(parent_module, child, module)
        except AttributeError:
            msg = f"Cannot set an attribute on {parent!r} for child module {child!r}"
            _warnings.warn(msg, ImportWarning)
    return module


final_dict = {
    7: _find_and_load_unlocked_v7,
    8: _find_and_load_unlocked_v7,
    9: _find_and_load_unlocked_v9,
    10: _find_and_load_unlocked_v9,
    11: _find_and_load_unlocked_v11,
    12: _find_and_load_unlocked_v11,
    13: _find_and_load_unlocked_v11,
    14: _find_and_load_unlocked_v11,
    15: _find_and_load_unlocked_v11
}

if minor >= 7:
    _find_and_load_unlocked = final_dict.get(minor, _find_and_load_unlocked_v11)
else:
    _find_and_load_unlocked = importlib._bootstrap._find_and_load_unlocked
importlib._bootstrap._find_and_load_unlocked = _find_and_load_unlocked
