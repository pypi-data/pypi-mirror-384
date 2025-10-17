#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
from argparse import Namespace
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, Optional, Type, Union

from pythonwrench.functools import function_alias
from pythonwrench.typing import DataclassInstance, NamedTupleInstance
from typing_extensions import TypeAlias

from torchwrench.core.packaging import _OMEGACONF_AVAILABLE, _YAML_AVAILABLE
from torchwrench.serialization.common import as_builtin

if not _YAML_AVAILABLE:
    from torchwrench.extras.yaml import _yaml_fallback as yaml
    from torchwrench.extras.yaml._yaml_fallback import (
        BaseLoader,
        CBaseLoader,
        CFullLoader,
        CLoader,
        CSafeLoader,
        CUnsafeLoader,
        FullLoader,
        Loader,
        MappingNode,
        Node,
        ParserError,
        SafeLoader,
        ScalarNode,
        ScannerError,
        SequenceNode,
        UnsafeLoader,
    )

else:
    import yaml
    from yaml import (
        BaseLoader,
        CBaseLoader,
        CFullLoader,
        CLoader,
        CSafeLoader,
        CUnsafeLoader,
        FullLoader,
        Loader,
        MappingNode,
        Node,
        SafeLoader,
        ScalarNode,
        SequenceNode,
        UnsafeLoader,
    )
    from yaml.parser import ParserError
    from yaml.scanner import ScannerError


if _OMEGACONF_AVAILABLE:
    from omegaconf import OmegaConf  # type: ignore


YamlLoaders: TypeAlias = Union[
    Type[Loader],
    Type[BaseLoader],
    Type[FullLoader],
    Type[SafeLoader],
    Type[UnsafeLoader],
    Type[CLoader],
    Type[CBaseLoader],
    Type[CFullLoader],
    Type[CSafeLoader],
    Type[CUnsafeLoader],
]


def dump_yaml(
    data: Union[
        Iterable[Any],
        Mapping[str, Any],
        Namespace,
        DataclassInstance,
        NamedTupleInstance,
    ],
    fpath: Union[str, Path, None] = None,
    *,
    overwrite: bool = True,
    to_builtins: bool = False,
    make_parents: bool = True,
    resolve: bool = False,
    encoding: Optional[str] = "utf-8",
    # YAML dump kwargs
    sort_keys: bool = False,
    indent: Union[int, None] = None,
    width: Union[int, None] = 1000,
    allow_unicode: bool = True,
    **yaml_dump_kwds,
) -> str:
    """Dump content to yaml format."""
    if not _YAML_AVAILABLE:
        msg = f"Cannot use python module {__file__} since pyyaml package is not installed. Please install it with `pip install torchwrench[extras]`."
        raise ImportError(msg)

    if not _OMEGACONF_AVAILABLE and resolve:
        msg = (
            "Cannot resolve yaml config without omegaconf package."
            "Please use resolve=False or install omegaconf with `pip install torchwrench[extras]`."
        )
        raise ValueError(msg)

    if fpath is not None:
        fpath = Path(fpath).resolve().expanduser()
        if not overwrite and fpath.exists():
            raise FileExistsError(f"File {fpath} already exists.")
        elif make_parents:
            fpath.parent.mkdir(parents=True, exist_ok=True)

    if resolve:
        data = OmegaConf.create(data)  # type: ignore
        data = OmegaConf.to_container(data, resolve=True)  # type: ignore

    if to_builtins:
        data = as_builtin(data)

    content = yaml.dump(
        data,
        sort_keys=sort_keys,
        indent=indent,
        width=width,
        allow_unicode=allow_unicode,
        **yaml_dump_kwds,
    )
    if fpath is not None:
        fpath.write_text(content, encoding=encoding)
    return content


@function_alias(dump_yaml)
def dumps_yaml(*args, **kwargs): ...


@function_alias(dump_yaml)
def save_yaml(*args, **kwargs): ...


def load_yaml(
    file: Union[str, Path, io.TextIOBase],
    *,
    Loader: YamlLoaders = SafeLoader,
    on_error: Literal["raise", "ignore"] = "raise",
) -> Any:
    """Load content from yaml filepath."""
    if not _YAML_AVAILABLE:
        msg = f"Cannot use python module {__file__} since pyyaml package is not installed. Please install it with `pip install torchwrench[extras]`."
        raise ImportError(msg)

    if isinstance(file, (str, Path)):
        with open(file, "r") as buffer:
            return loads_yaml(buffer, Loader=Loader, on_error=on_error)
    elif isinstance(file, io.TextIOBase):
        return loads_yaml(file, Loader=Loader, on_error=on_error)
    else:
        msg = f"Invalid argument type {type(file)}."
        raise TypeError(msg)


def loads_yaml(
    content: Union[str, io.TextIOBase],
    *,
    Loader: YamlLoaders = SafeLoader,
    on_error: Literal["raise", "ignore"] = "raise",
) -> Any:
    if isinstance(content, str):
        with io.StringIO(content) as buffer:
            return loads_yaml(buffer, Loader=Loader, on_error=on_error)

    try:
        data = yaml.load(content, Loader=Loader)  # type: ignore
    except (ScannerError, ParserError) as err:
        if on_error == "ignore":
            return None
        else:
            raise err
    return data


@function_alias(load_yaml)
def read_yaml(*args, **kwargs): ...


class IgnoreTagLoader(SafeLoader):  # type: ignore
    """SafeLoader that ignores yaml tags.

    Examples
    ========

    ```python
    >>> dumped = "a: !!python/tuple\n- 1\n- 2"
    >>> yaml.load(dumped, Loader=IgnoreTagLoader)
    ... {"a": [1, 2]}
    >>> yaml.load(dumped, Loader=FullLoader)
    ... {"a": (1, 2)}
    >>> yaml.load(dumped, Loader=SafeLoader)  # raises ConstructorError
    ```
    """

    def construct_with_tag(self, tag: str, node: Node) -> Any:
        if isinstance(node, MappingNode):
            return self.construct_mapping(node)
        elif isinstance(node, ScalarNode):
            return self.construct_scalar(node)
        elif isinstance(node, SequenceNode):
            return self.construct_sequence(node)
        else:
            msg = f"Unsupported node type {type(node)} with {tag=}."
            raise NotImplementedError(msg)


class SplitTagLoader(SafeLoader):  # type: ignore
    """SafeLoader that store tags inside value.

    Examples
    ========

    ```python
    >>> dumped = "a: !!python/tuple\n- 1\n- 2"
    >>> yaml.load(dumped, Loader=SplitTagLoader)
    ... {'a': {'_target_': 'yaml.org,2002:python/tuple', '_args_': [1, 2]}}
    ```
    """

    def __init__(
        self,
        stream,
        *,
        tag_key: str = "_target_",
        args_key: str = "_args_",
    ) -> None:
        super().__init__(stream)
        self.tag_key = tag_key
        self.args_key = args_key

    def construct_with_tag(self, tag: str, node: Node) -> Any:
        if isinstance(node, MappingNode):
            result = self.construct_mapping(node)
        elif isinstance(node, ScalarNode):
            result = self.construct_scalar(node)
        elif isinstance(node, SequenceNode):
            result = self.construct_sequence(node)
        else:
            msg = f"Unsupported node type {type(node)} with {tag=}."
            raise NotImplementedError(msg)

        result = {
            self.tag_key: tag,
            self.args_key: result,
        }
        return result


if _YAML_AVAILABLE:
    IgnoreTagLoader.add_multi_constructor("!", IgnoreTagLoader.construct_with_tag)
    IgnoreTagLoader.add_multi_constructor("tag:", IgnoreTagLoader.construct_with_tag)

    SplitTagLoader.add_multi_constructor("!", SplitTagLoader.construct_with_tag)
    SplitTagLoader.add_multi_constructor("tag:", SplitTagLoader.construct_with_tag)
