from friendly_module_not_found_error.handle_path import scan_dir
from friendly_module_not_found_error.traceback_change import _calculate_closed_name
import sys, importlib.abc, importlib.util
import unittest
import traceback

sys.path.append(sys.modules["friendly_module_not_found_error"].__path__[0])

MODULE_TREE = {
    "__init__": "print('mymodule init'); x = 1",
    "submodule": "print('submodule init'); y = 2",
    "subpackage": {
        "__init__": "print('subpackage init'); z = 3"
    }
}


class DictLoader(importlib.abc.Loader):
    def __init__(self, fullname, node):
        self.fullname = fullname
        self.node = node

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        if isinstance(self.node, dict):
            code = self.node.get("__init__")
        else:
            code = self.node
        if code:
            exec(code, module.__dict__)


class DictFinder(importlib.abc.MetaPathFinder):
    def __init__(self, name, tree):
        self.name = name
        self.tree = tree

    def find_spec(self, fullname, path, target=None):
        if not fullname.startswith(self.name):
            return None
        parts = fullname.split(".")
        node = self.tree
        for p in parts[1:]:
            if isinstance(node, dict) and p in node:
                node = node[p]
            else:
                return None
        loader = DictLoader(fullname, node)
        ispkg = isinstance(node, dict)
        return importlib.util.spec_from_loader(fullname, loader, is_package=ispkg)

    def __find__(self, name=None):
        if not name:
            return [self.name]
        else:
            name_list = name.split(".")
            if name_list[0] != self.name:
                return []
            module_dict = self.tree
            for i in name_list[1:]:
                if i not in module_dict:
                    return []
                module_dict = module_dict[i]
            a = list(module_dict.keys())  # wrong in code
            a.append("a")
            return a


sys.meta_path.insert(0, DictFinder("mymodule", MODULE_TREE))


def except_suggestion(top_name):
    suggest_list = []
    all_result = []
    for i in sys.meta_path:
        try:
            func = getattr(i, '__find__', None)
            if callable(func):
                list_d = func()
                if list_d:
                    suggest_list.append(list_d)
        except:
            pass
    for paths in sys.path:
        suggest_list.append(scan_dir(paths))
    for i in suggest_list:
        result = _calculate_closed_name(top_name, i)
        if result:
            all_result.append(result)
    return _calculate_closed_name(top_name, sorted(all_result))


ant_suggestion = except_suggestion("ant")
module_suggestion = except_suggestion("module")
if _calculate_closed_name("aa", ["a"]) == "a":
    aa_suggestion_sentence = ". Did you mean: 'a'?"
else:
    aa_suggestion_sentence = ""


class ExceptionTest(unittest.TestCase):
    def test_top_import_exception(self):
        import_error_tuple = (
            ("import ant", ModuleNotFoundError, f"No module named 'ant'. Did you mean: {ant_suggestion!r}?"),
        )
        for i in import_error_tuple:
            if i:
                self.check_message(i[0], i[1], i[2])

    def test_non_packages_import_exception(self):
        import_error_tuple = (
            ("import os.path.a", ModuleNotFoundError,
             "module 'os.path' has no child module 'a'; 'os.path' is not a package"),
            ("import ast.a", ModuleNotFoundError, "module 'ast' has no child module 'a'; 'ast' is not a package")
        )
        for i in import_error_tuple:
            if i:
                self.check_message(i[0], i[1], i[2])

    def test_packages_import_exception(self):
        import_error_tuple = (
            ("import multiprocessing.dumy", ModuleNotFoundError,
             "module 'multiprocessing' has no child module 'dumy'. Did you mean: 'dummy'?"),
        )
        for i in import_error_tuple:
            if i:
                self.check_message(i[0], i[1], i[2])

    def test_wrong_module_exception(self):
        import_error_tuple = (
            ("import wrong_module", ModuleNotFoundError,
             "module 'wrong_module' has no child module 'wrong_module'"),
            ("import wrong_child_module.wrong_child_module", ModuleNotFoundError,
             "module 'wrong_child_module.wrong_child_module' has no child module 'wrong_child_module'. Did you mean: 'wrong_child_modules'?")
        )
        for i in import_error_tuple:
            if i:
                self.check_message(i[0], i[1], i[2])

    def test_custom_module_hook(self):
        import_error_tuple = (
            ("import module", ModuleNotFoundError, f"No module named 'module'. Did you mean: {module_suggestion!r}"),
            ("import mymodule.a", ModuleNotFoundError, "module 'mymodule' has no child module 'a', "
                                                       "but it appear in the final result from 'DictFinder.__find__'. "
                                                       "Is the code in 'DictFinder.__find__' or 'DictFinder.find_spec' wrong "
                                                       "or is the wrong in the environment?"
             ),
            ("import mymodule.submodule.b", ModuleNotFoundError,
             "module 'mymodule.submodule' has no child module 'b'; 'mymodule.submodule' is not a package"),
            ("import mymodule.subpackage.aa", ModuleNotFoundError,
             f"module 'mymodule.subpackage' has no child module 'aa'{aa_suggestion_sentence}")
        )
        for i in import_error_tuple:
            if i:
                self.check_message(i[0], i[1], i[2])

    def test_wrong_find(self):
        class WrongHook1:
            def find_spec(*args, **kwargs):
                return None

            def __find__(self, name=None):
                raise ValueError

        class WrongHook2:
            def find_spec(*args, **kwargs):
                return None

            def __find__(self, name=None):
                raise ImportError("this is not ImportError")

        sys.meta_path.append(WrongHook1())
        sys.meta_path.append(WrongHook2())

        try:
            import abs
        except ModuleNotFoundError:
            msg = traceback.format_exc()
            self.assertIn("Exception ignored in 'WrongHook1.__find__'", msg)
            self.assertIn("ImportError found in 'WrongHook2.__find__'", msg)
            self.assertNotIn("this is not ImportError", msg)
        except:
            pass
        finally:
            sys.meta_path = sys.meta_path[:-2]

    @unittest.skipIf(sys.version_info[1] < 11, "No BaseExceptionGroup")
    def test_BaseExceptionGroup_ignored(self):
        class WrongHook3:
            def find_spec(*args, **kwargs):
                return None

            def __find__(self, name=None):
                raise ExceptionGroup("", [ValueError(), SyntaxError()])

        class WrongHook4:
            def find_spec(*args, **kwargs):
                return None

            def __find__(self, name=None):
                raise ExceptionGroup("", [ValueError(), ImportError("this is not ImportError")])

        sys.meta_path.append(WrongHook3())
        sys.meta_path.append(WrongHook4())
        try:
            import abs
        except ModuleNotFoundError:
            msg = traceback.format_exc()
            self.assertIn("Exception ignored in 'WrongHook3.__find__'", msg)
            self.assertIn("ImportError found in 'WrongHook4.__find__'", msg)
            self.assertNotIn("this is not ImportError", msg)
        except:
            pass
        finally:
            sys.meta_path = sys.meta_path[:-2]

    def check_message(self, code, exc_type, exc_msg):
        try:
            exec(code)
        except exc_type:
            self.assertIn(exc_msg, traceback.format_exc())
        except:
            pass


def main():
    unittest.main(module=__name__, exit=False)


if __name__ == '__main__':
    main()
