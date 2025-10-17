import os
import sys
from importlib import machinery


def scan_dir(path, namespace_package=False, need_main_py=False):
    """
    Return all the packages in the path without import
    contains：
      - .py file
      - directory with "__init__.py"
      - the .pyd/so file that has right ABI
    """
    if not os.path.isdir(path):
        return []

    suffixes = machinery.EXTENSION_SUFFIXES
    result = []

    for name in os.listdir(path):
        full_path = os.path.join(path, name)

        # .py file
        if name.endswith(".py") and os.path.isfile(full_path):
            modname = name[:-3]
            if modname.isidentifier():
                result.append(modname)

        # directory with "__init__.py"
        elif os.path.isdir(full_path):
            init_file = os.path.join(full_path, "__init__.py")
            main_file = os.path.join(full_path, "__main__.py")
            if namespace_package:
                condition = True
            elif not need_main_py:
                condition = os.path.isfile(init_file)
            else:
                condition = os.path.isfile(init_file) and os.path.isfile(main_file)
            if condition and name.isidentifier():
                result.append(name)

        # the .pyd/so file that has right ABI
        elif os.path.isfile(full_path):
            if need_main_py:
                continue
            for suf in suffixes:
                if name.endswith(suf):
                    modname = name[:-len(suf)]
                    if modname.isidentifier():
                        result.append(modname)
                    break

    return sorted(result)


def find_in_path(name, mod="normal"):
    kwargs = {}
    if mod == "all":
        kwargs = {"namespace_package": True}
    elif mod == "run_module":
        kwargs = {"need_main_py": True}
    if not name:
        return []
    if name in sys.modules:
        if not hasattr(sys.modules[name], '__path__'):
            return []
        return sum([scan_dir(i, **kwargs) for i in sys.modules[name].__path__], [])

    name_list = name.split(".")
    for i in sys.path:
        if i == "":
            i = "."
        list_d = scan_dir(i)
        if name_list[0] in list_d:
            break
    else:
        return []
    path = i
    for j in name_list:
        path = os.path.join(path, j)
    if not os.path.isdir(path):
        return []
    if not os.path.exists(os.path.join(path, "__init__.py")):
        return []
    return scan_dir(path, **kwargs)
