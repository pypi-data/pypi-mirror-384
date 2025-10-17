from pathlib import Path
from typing import Union, Any, Iterable, Callable, Optional

from nip.parser.parse_func import parse, parse_string
from nip.update import update_flatten, update
from . import elements
from .constructor import Constructor
from .convertor import Convertor
from .dumper import Dumper
from .non_seq_constructor import NonSequentialConstructor
from .dict import DictObject

__all__ = [
    "parse",
    "parse_string",
    "construct",
    "load",
    "load_string",
    "run",
    "dump",
    "dump_string",
    "convert",
    "update",
    "update_flatten",
]


def construct(
    config: elements.Node,
    base_config: elements.Node = None,
    strict_typing: bool = False,
    nonsequential: bool = True,
    as_dictobj: bool = True,
) -> Any:
    """Constructs python object based on config and known nip-objects

    Parameters
    ----------
    config: Element
        Config node to be constructed.
    base_config:
        Base config, in case of construction a part of a config with external links.
    strict_typing:
        If True, raises Exception when typing mismatch.
    nonsequential:
        If True, allows to use links before creation.
        Always true if base_config is specified.
    as_dictobj:
        Returns DictObj if true and possible

    Returns
    -------
    obj: Any
    """
    if nonsequential or base_config is not None:
        base_config = base_config or config._get_root()
        constructor = NonSequentialConstructor(base_config, strict_typing=strict_typing, as_dictobj=as_dictobj)
    else:
        constructor = Constructor(strict_typing=strict_typing, as_dictobj=as_dictobj)
    result = constructor.construct(config)
    return result


def _iter_load(configs, strict_typing, nonsequential, as_dictobj):  # Otherwise load() will always be an iterator
    for config in configs:
        yield construct(config, strict_typing=strict_typing, nonsequential=nonsequential, as_dictobj=as_dictobj)


def load(
    path: Union[str, Path],
    always_iter: bool = False,
    strict: bool = False,
    nonsequential: bool = True,
    as_dictobj: bool = False,
) -> Union[Any, Iterable[Any]]:
    """Parses config and constructs python object
    Parameters
    ----------
    path: str or Path
        Path to config file
    always_iter: bool
        If True will always return iterator over configs.
    strict:
        If True, raises Exception when typing mismatch or overwriting dict key.
    nonsequential:
        If True, allows to use links before creation.
    as_dictobj:
        Returns DictObj if true and possible

    Returns
    -------
    obj: Any or Iterable[Any]
    """
    config = parse(path, always_iter, strict=strict)

    if isinstance(config, Iterable):
        return _iter_load(config, strict, nonsequential, as_dictobj)

    return construct(config, strict_typing=strict, nonsequential=nonsequential, as_dictobj=as_dictobj)


def load_string(
    config_string: str,
    always_iter: bool = False,
    strict: bool = False,
    nonsequential: bool = True,
    as_dictobj: bool = True,
) -> Union[Any, Iterable[Any]]:
    """Parses config and constructs python object
    Parameters
    ----------
    config_string: str
        Config as a string.
    always_iter: bool
        If True will always return iterator over configs.
    strict:
        If True, raises Exception when typing mismatch or overwriting dict key.
    nonsequential:
        If True, allows to use links before creation.
    as_dictobj:
        Returns DictObj if true and possible

    Returns
    -------
    obj: Any or Iterable[Any]
    """
    config = parse_string(config_string, always_iter, strict=strict)

    if isinstance(config, Iterable):
        return _iter_load(config, strict, nonsequential, as_dictobj)

    return construct(config, strict_typing=strict, nonsequential=nonsequential, as_dictobj=as_dictobj)


def dump(path: Union[str, Path], obj: Union[elements.Node, object]):
    """Dumps config tree to file.

    Parameters
    ----------
    path: str or Path
        Path to save the config.
    obj: Element or object
        Read or generated config if Element. In case of any other object `convert` will be called.
    """
    if not isinstance(obj, elements.Node):
        obj = convert(obj)  # mb: wrap with Document to ensure getting `---` at the beginning of the file.
    dumper = Dumper()
    dumper.dump(path, obj)


def dump_string(obj: Union[elements.Node, object]) -> str:
    """Dumps config tree to string.

    Parameters
    ----------
    obj: Element
        Read or generated config tree.

    Returns
    -------
    string: str
        Dumped element as a string.
    """
    if not isinstance(obj, elements.Node):
        obj = convert(obj)
    dumper = Dumper()
    return dumper.dumps(obj)


def convert(obj):
    """Converts object to nip.Element

    Parameters
    ----------
    obj: nip-serializable object.

    Returns
    -------
    Element:
        Object representation as Nip.Element

    Notes
    -----
    Any standard python objects that can be casted to and from nip are supported.
    For custom classes method `__nip__` that casts them to the standard object are needed.
    Anything that is returned from `__nip__` method will be recursively converted.
    `__nip__` method is expected to return everything needed for object construction with __init__
    or any other used constructor.
    By default, tag specified in @nip or default class name otherwise will be used as a tag.
    """
    convertor = Convertor()
    return convertor.convert(obj)


def _run_return(value, config, return_values, return_configs):
    return_tuple = []
    if return_values:
        return_tuple.append(value)
    if return_configs:
        return_tuple.append(config)
    if len(return_tuple) == 0:
        return None
    if len(return_tuple) == 1:
        return return_tuple[0]
    return tuple(return_tuple)


def _single_run(
    config, func, verbose, return_values, return_configs, config_parameter, strict, nonsequential, as_dictobj
):
    if verbose:
        print("=" * 20)
        print("Running config:")
        print(dump_string(config))
        print("----")

    value = construct(config, strict_typing=strict, nonsequential=nonsequential, as_dictobj=as_dictobj)
    if func is not None:
        if isinstance(value, tuple) and isinstance(value[0], list) and isinstance(value[1], dict):
            args, kwargs = value
        elif isinstance(value, list):
            args, kwargs = value, {}
        elif isinstance(value, dict):
            args, kwargs = [], value
        else:
            raise RuntimeError("Value constructed by the config cant be parsed as args and kwargs")

        if config_parameter:
            if config_parameter in kwargs:
                raise RuntimeWarning(
                    f"nip.run() was asked to add config parameter '{config_parameter}', "
                    f"but it is already specified by the config. It will be overwritten."
                )
            kwargs[config_parameter] = config

        value = func(*args, **kwargs)

    if verbose:
        print("----")
        print("Run value:")
        print(value)

    return _run_return(value, config, return_values, return_configs)


def _iter_run(
    configs, func, verbose, return_values, return_configs, config_parameter, strict, nonsequential, as_dictobj
):
    for config in configs:
        run_return = _single_run(
            config, func, verbose, return_values, return_configs, config_parameter, strict, nonsequential, as_dictobj
        )
        if run_return:
            yield run_return


def run(
    path: Union[str, Path],
    func: Optional[Callable] = None,
    verbose: bool = True,
    strict: bool = False,
    nonsequential: bool = False,
    return_values: bool = True,
    return_configs: bool = False,
    always_iter: bool = False,
    config_parameter: Optional[str] = None,
    as_dictobj: bool = False,
):
    """Runs config. Config should be declared with function to run as a tag for the Document.
    In case of iterable configs we will iterate over and run each of them.

    Parameters
    ----------
    path: str or Path
        path to config to run.
    func:
        Function to be called with loaded configs.
        If not specified, config will be constructed as is.
    verbose: bool, optional
        Whether to print information about currently running experiment or not.
    strict:
        If True, raises Exception when typing mismatch or overwriting dict key.
    nonsequential:
        If True, allows to use links before creation.
    return_values: bool, optional
        Whether to return values of ran functions or not.
    return_configs: bool, optional
        Whether to return config for ran function or not.
    always_iter: bool, optional
        Result will always be iterable.
    config_parameter: str, optional
        If specified, parsed config will be passed to called function as a parameter with this name.
        `func` parameter must be specified.
    as_dictobj:
        Returns DictObj if true and possible

    Returns
    -------
    Iterator or single value depending on whether the config is iterable
    value or config or (value, config): Any or str or (Any, str)
        returned values and configs of runs
    """
    assert (
        config_parameter is None or config_parameter is not None and func is not None
    ), "`config_parameter` can be used only with specified `func`"
    config = parse(path, always_iter=always_iter, strict=strict)
    if isinstance(config, Iterable):
        return list(
            _iter_run(
                configs=config,
                func=func,
                verbose=verbose,
                return_values=return_values,
                return_configs=return_configs,
                config_parameter=config_parameter,
                strict=strict,
                nonsequential=nonsequential,
                as_dictobj=as_dictobj,
            )
        )  # mb iter?

    return _single_run(
        config=config,
        func=func,
        verbose=verbose,
        return_values=return_values,
        return_configs=return_configs,
        config_parameter=config_parameter,
        strict=strict,
        nonsequential=nonsequential,
        as_dictobj=as_dictobj,
    )
