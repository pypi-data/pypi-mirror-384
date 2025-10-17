# friendly_module_not_found_error

<img width="800" height="430" alt="Windows PowerShell 2025_8_10 21_54_12" src="https://github.com/user-attachments/assets/29f81573-3784-4d44-b75f-4bd1c518727b" />

This is a Python package that provides the monkey patch for handling module not found errors in a friendly way.
When you spell a module name incorrectly, the package will change the exception with a friendly message and suggestions for the possible correct module name.

## Installation

To install the package, run the following command:

```cmd/bash
pip install friendly_module_not_found_error
```

## Usage

No need to import the package. It use a file named "hatch_autorun_friendly_module_not_found_error.pth" to import the packages at the beginning.

You can use the code to test the effects of the package:

```python
import ant
```

The message raised will change to : "No module named 'ant'. Did you mean 'ast'?"
The suggestion may be change according to the packages you have installed.

```python
import multiprocessing.dumy
```

The message raised will change to : "module 'multiprocessing' has no child module 'dumy'. Did you mean 'dummy'?"

You can also run "testmodule" to test the effects of the python.

If there is not "hatch_autorun_friendly_module_not_found_error.pth" in the "site-packages" folder, you can add the file to the "site-packages" folder and add the following code to the file:

```pth
import friendly_module_not_found_error
```

On linux (or if the ".pth" file doesn't work), you can add "sitecustomize.py" to the "site-packages" folder of the python and add the code above.

When uninstall the package, you need also to remove the file above.

In version 1.0.6, it provide two api:

- friendly_module_not_found_error.unchange(): restore the original behavior of the module not found error.
- friendly_module_not_found_error.rechange(): change the behavior of the module not found error to the friendly way.

In version 1.0.20, it add two keywords:

- unchange(full_recovery=False): If "full_recovery" is False, when `sys.excepthook` is not `sys.__excepthook__`, it only recovery the `sys.__excepthook__` and won't touch the `sys.excepthook`
- rechange(full_rechange=False): If "full_rechange" is False, when `sys.excepthook` is not `sys.__excepthook__`, it only change the `sys.__excepthook__` and won't touch the `sys.excepthook`

## Effect and explain

The example:

```python
import xxx.yyy.zzz
```

If "xxx" not exist, the message is:
"**No module named 'xxx'**"

If "xxx" exist but "yyy" not exist, the message is:
"**module 'xxx' has no child module 'yyy'**"

Then the message add like the text below:

The final name will be compared to all module at that path. If at the top, it first compared with stdlib and then compared with the path in `sys.path`. Or, if the module before is not a package and the now module not exist, the message will add "module '...' is not a package". For the non-package module, it won't support for this condition: module has a child module, and it has child module. For package, it will scan the attribute "\_\_path\_\_" to get all possible child module to compare.

The change can clearly show the specific error in import and give the near name suggestion. For example, the original is "No module named 'xxx.yyy.zzz'", we cannot get message that which step is wrong, now we can see which step is wrong:
"No module named 'xxx'" means the top, "module 'xxx' has no child module 'yyy'" means the second, and ''module 'xxx.yyy' has no child module 'zzz'" means the third, and so on. And like `NameError` and `AttributeError`, it will suggest the possible name.

## Require

python3.7+

In friendly_module_not_found_error version 0.4.2+, it supports python3.7+.

## License

This package is licensed under the MIT License. See the LICENSE file for more information.

## Issues

If you have any questions or suggestions, please open an [issue](https://github.com/Locked-chess-official/friendly_module_not_found_error/issues) on GitHub.

## Contributing

Contributions are welcome! Please submit a [pull request](https://github.com/Locked-chess-official/friendly_module_not_found_error/pulls) with your changes.

## Do it with python

Now the [branch](https://github.com/Locked-chess-official/cpython/tree/finally_suggestion_in_module) for it is available.

This branch uses the mode of this package. You can try that.

## Data

The test for "\_\_main\_\_.py" here (old data in the environment where the number of the site packages is about 260):

| No. | number of entries | used time(/s) | average time(/s) | result |
|-- | -- | -- | -- | -- |
| 1 | 5 | 0.064 | 0.013 | success |
| 2 | 5 | 0.072 | 0.014 | success |
| 3 | 5 | 0.052 | 0.010 | success |
| 4 | 5 | 0.056 | 0.011 | success |
| 5 | 5 | 0.057 | 0.011 | success |
| 6 | 6 | 0.081 | 0.014 | success |
| 7 | 6 | 0.062 | 0.010 | success |
| 8 | 6 | 0.091 | 0.015 | success |
| 9 | 6 | 0.064 | 0.011 | success |
| 10 | 6 | 0.064 | 0.011 | success |

The speed test here:

| tool | function | arg | number | average time(/ms) |
| -- | -- | -- | -- | -- |
| timeit | find_all_packages | (no args) | 1000 | 8.567 |
| timeit | scan_dir | path/to/site-packages | 1000 | 4.845 |

The function "find_all_packages" defined here:

```python
def find_all_packages() -> list[str]:
    """
    Find all packages in the given path.
    If top is True, return all top packages.
    """
    return sorted(sum([scan_dir(i) if
                isinstance(i, str) else []
                for i in sys.path], []) + 
                list(sys.builtin_module_names))

```

## Note

If a module that is not a package contains submodules, and those submodules also contain their own submodules, this nested module structure is not supported.
When this situation occurs, you should reorganize the code using proper package structure. This approach violates Python's packaging best practices and should be avoided.

To make your custom import hook be supported, you need to define a magic method "\_\_find\_\_" to return the list of all modules.
For example:

```python
class MyImportHook:
    def __find__(self, name: str=None) -> list[str]:
        """
        Return a list of all modules that are available to the import hook without import them.
        If the "name" is provided, the method should return a list of all submodules that under the module named "name".
        parameter name: The name of the module to find submodules for. If None, return all top modules.
        """
        return []
```

The "\_\_find\_\_" method should return a list of all modules that are available to the import hook without import them.

If the "name" is provided, the method should return a list of all submodules that under the module named "name" (without "."). Or it needs to return all top modules if the "name" is None.
The name should be the full name of the module, such as:

```plaintext
topmodule/
    __init__.py
    subpackage/
        __init__.py
        submodule/
            __init__.py
            nonpackage.py
```

The name of the top module is "topmodule", the name of the subpackage is "topmodule.subpackage", and the name of the submodule is "topmodule.subpackage.submodule".

If exception raised in the method "\_\_find\_\_", the exception will be ignored:

- If the all of the exceptions in the exception chain ("\_\_cause\_\_", "\_\_context\_\_", "BaseExceptionGroup") are not `ImportError`, it will be printed as warning.
- Otherwise, the message will be ignored and the module will tips that don't import any modules in the method "\_\_find\_\_".

If [PEP810](https://peps.python.org/pep-0810/) is accepted, when use this module, please ensure that no lazy import in the method "\_\_find\_\_".

## Warning

When your code raises the "ModuleNotFoundError", if there is the suggestion given by the package, you need to check it.

Anyway, if your IDE suggests you to `pip install` the wrong name module, check it instead of following it blindly. It may be a malicious package.

## Rejected suggestion

- Build a cache for site-packages when install: The code runs fast, so it can find all of the packages fast. Before that finding costs, the computer has been almost broken.
- Suggest for "pip install xxx": spelling mistakes are often closely associated with homograph attacks and typosquatting attacks. Suggesting for it will help the attacker.

## Credits

This package was created by Locked-chess-official and is maintained by Locked-chess-official
