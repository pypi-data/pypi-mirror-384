from __future__ import annotations

import functools
import json
import os
import re
import shutil
import sys
from collections import deque
from collections.abc import Container, Hashable, Iterable, MutableSet
from collections.abc import Set as AbstractSet
from configparser import ConfigParser, SectionProxy
from enum import Enum, auto
from glob import iglob
from importlib.metadata import Distribution, PackageNotFoundError
from importlib.metadata import distribution as _get_distribution
from importlib.metadata import distributions as _get_distributions
from itertools import chain
from pathlib import Path
from shutil import rmtree
from subprocess import DEVNULL, PIPE, CalledProcessError, list2cmdline, run
from traceback import format_exception
from typing import (
    IO,
    Any,
    Callable,
    TypedDict,
    cast,
    overload,
)
from warnings import warn

import tomli
from jsonpointer import resolve_pointer  # type: ignore
from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name

_BUILTIN_DISTRIBUTION_NAMES: tuple[str] = ("distribute",)
_UNSAFE_CHARACTERS_PATTERN: re.Pattern = re.compile("[^A-Za-z0-9.]+")


class DefinitionExistsError(Exception):
    """
    This error is raised when an attempt is made to redefine
    a singleton class instance.
    """


_module_locals: dict[str, Any] = locals()


class Undefined:
    """
    This class is intended to indicate that a parameter has not been passed
    to a keyword argument in situations where `None` is to be used as a
    meaningful value.

    The `Undefined` class is a singleton, so only one instance of this class
    is permitted: `sob.UNDEFINED`.
    """

    __module__ = "sob"

    def __init__(self) -> None:
        # Only one instance of `Undefined` is permitted, so initialization
        # checks to make sure this is the first use.
        if "UNDEFINED" in _module_locals:
            message: str = f"{self!r} may only be instantiated once."
            raise DefinitionExistsError(message)

    def __repr__(self) -> str:
        # Represent instances of this class using the qualified name for the
        # constant `UNDEFINED`.
        return "sob.UNDEFINED"

    def __bool__(self) -> bool:
        # `UNDEFINED` cast as a boolean is `False` (as with `None`)
        return False

    def __hash__(self) -> int:
        return 0

    def __eq__(self, other: object) -> bool:
        # Another object is only equal to this if it shares the same id, since
        # there should only be one instance of this class defined
        return other is self

    def __reduce__(self) -> tuple[Callable[[], Undefined], tuple]:
        return _undefined, ()


UNDEFINED: Undefined = Undefined()


def _undefined() -> Undefined:
    return UNDEFINED


cache: Any
try:
    from functools import cache  # type: ignore
except ImportError:
    from functools import lru_cache

    cache = lru_cache(maxsize=None)


def as_tuple(
    user_function: Callable[..., Iterable[Any]],
) -> Callable[..., tuple[Any, ...]]:
    """
    This is a decorator which will return an iterable as a tuple.
    """

    def wrapper(*args: Any, **kwargs: Any) -> tuple[Any, ...]:
        return tuple(user_function(*args, **kwargs) or ())

    return functools.update_wrapper(wrapper, user_function)


def as_cached_tuple(
    maxsize: int | None = None, *, typed: bool = False
) -> Callable[[Callable[..., Iterable[Any]]], Callable[..., tuple[Any, ...]]]:
    """
    This is a decorator which will return an iterable as a tuple,
    and cache that tuple.

    Parameters:

    - maxsize (int|None) = None: The maximum number of items to cache.
    - typed (bool) = False: For class methods, should the cache be distinct for
      sub-classes?
    """
    return functools.lru_cache(maxsize=maxsize, typed=typed)(as_tuple)


def iter_distinct(items: Iterable[Hashable]) -> Iterable:
    """
    Yield distinct elements, preserving order
    """
    visited: set[Hashable] = set()
    item: Hashable
    for item in items:
        if item not in visited:
            visited.add(item)
            yield item


def get_exception_text() -> str:
    """
    When called within an exception, this function returns a text
    representation of the error matching what is found in
    `traceback.print_exception`, but is returned as a string value rather than
    printing.
    """
    return "".join(format_exception(*sys.exc_info()))


def _iter_parse_delimited_value(value: str, delimiter: str) -> Iterable[str]:
    return value.split(delimiter)


def iter_parse_delimited_values(
    values: Iterable[str], delimiter: str = ","
) -> Iterable[str]:
    """
    This function iterates over input values which have been provided as a
    list or iterable and/or a single string of character-delimited values.
    A typical use-case is parsing multi-value command-line arguments.
    """
    if isinstance(values, str):
        values = (values,)

    def iter_parse_delimited_value_(value: str) -> Iterable[str]:
        return _iter_parse_delimited_value(value, delimiter=delimiter)

    return chain(*map(iter_parse_delimited_value_, values))


def check_output(
    args: tuple[str, ...],
    cwd: str | Path = "",
    *,
    echo: bool = False,
) -> str:
    """
    This function mimics `subprocess.check_output`, but redirects stderr
    to DEVNULL, and ignores unicode decoding errors.

    Parameters:

    - command (tuple[str, ...]): The command to run
    """
    if echo:
        if cwd:
            print("$", "cd", cwd, "&&", list2cmdline(args))  # noqa: T201
        else:
            print("$", list2cmdline(args))  # noqa: T201
    output: str = run(
        args,
        stdout=PIPE,
        stderr=DEVNULL,
        check=True,
        cwd=cwd or None,
    ).stdout.decode("utf-8", errors="ignore")
    if echo:
        print(output)  # noqa: T201
    return output


def get_qualified_name(function: Callable[..., Any]) -> str:
    name: str = getattr(function, "__name__", "")
    if name:
        module: str = getattr(function, "__module__", "")
        if module not in (
            "builtins",
            "__builtin__",
            "__main__",
            "__init__",
            "",
        ):
            name = f"{module}.{name}"
    return name


def deprecated(message: str = "") -> Callable[..., Callable[..., Any]]:
    """
    This decorator marks a function as deprecated, and issues a
    deprecation warning when the function is called.
    """

    def decorating_function(
        function: Callable[..., Any],
    ) -> Callable[..., Any]:
        @functools.wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            name: str = get_qualified_name(function)
            warn(
                (
                    (
                        f"{name} is deprecated: {message}"
                        if message
                        else f"{name} is deprecated"
                    )
                    if name
                    else message
                ),
                DeprecationWarning,
                stacklevel=2,
            )
            return function(*args, **kwargs)

        return wrapper

    return decorating_function


def split_dot(path: str) -> tuple[str, ...]:
    return tuple(path.split("."))


def tuple_starts_with(
    a: tuple[str, ...],
    b: tuple[str, ...],
) -> bool:
    """
    Determine if tuple `a` starts with tuple `b`
    """
    return a[: len(b)] == b


def tuple_starts_with_any(
    a: tuple[str, ...],
    bs: tuple[tuple[str, ...], ...],
) -> bool:
    """
    Determine if tuple `a` starts with any tuple in `bs`
    """
    b: tuple[str, ...]
    return any(tuple_starts_with(a, b) for b in bs)


def iter_find_qualified_lists(
    data: dict[str, Any] | list,
    item_condition: Callable[[Any], bool],
    exclude_object_ids: AbstractSet[int] = frozenset(),
) -> Iterable[list]:
    """
    Recursively yield all lists where all items in the list
    satisfy the provided condition.

    Parameters:
        data: A dictionary or list to search
        item_condition: A function that returns True if the list item
            is the type we are looking for

    >>> tuple(
    ...     iter_find_qualified_lists(
    ...         {
    ...             "a": [
    ...                 1,
    ...                 2,
    ...                 3,
    ...             ],
    ...             "b": [
    ...                 "four",
    ...                 "five",
    ...                 "six",
    ...             ],
    ...             "c": [
    ...                 7,
    ...                 8,
    ...                 9,
    ...             ],
    ...             "d": [
    ...                 "ten",
    ...                 "eleven",
    ...                 "twelve",
    ...             ],
    ...             "e": {
    ...                 "aa": [
    ...                     13,
    ...                     14,
    ...                     15,
    ...                 ],
    ...                 "bb": [
    ...                     "sixteen",
    ...                     "seventeen",
    ...                     "eighteen",
    ...                 ],
    ...             },
    ...             "f": [
    ...                 [
    ...                     19,
    ...                     20,
    ...                     21,
    ...                 ],
    ...                 [
    ...                     "twenty-two",
    ...                     "twenty-three",
    ...                     "twenty-four",
    ...                 ],
    ...             ],
    ...         },
    ...         lambda item: isinstance(
    ...             item,
    ...             int,
    ...         ),
    ...     )
    ... )
    ([1, 2, 3], [7, 8, 9], [13, 14, 15], [19, 20, 21])
    """
    if id(data) in exclude_object_ids:
        return
    if isinstance(data, dict):
        value: Any
        for value in data.values():
            if isinstance(value, (list, dict)):
                yield from iter_find_qualified_lists(
                    value, item_condition, exclude_object_ids
                )
    elif isinstance(data, list) and data:
        matched: bool = True
        item: Any
        for item in data:
            if not item_condition(item):
                matched = False
            if isinstance(item, (list, dict)):
                yield from iter_find_qualified_lists(
                    item, item_condition, exclude_object_ids
                )
        if matched:
            yield data


def normalize_name(name: str) -> str:
    """
    Normalize a project/distribution name
    """
    return _UNSAFE_CHARACTERS_PATTERN.sub("-", canonicalize_name(name)).lower()


class ConfigurationFileType(Enum):
    REQUIREMENTS_TXT = auto()
    SETUP_CFG = auto()
    TOX_INI = auto()
    PYPROJECT_TOML = auto()
    TOML = auto()


@functools.lru_cache
def get_configuration_file_type(
    path: str | Path, default: Any = UNDEFINED
) -> ConfigurationFileType:
    if isinstance(path, str):
        path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    basename: str = path.name.lower()
    if basename == "setup.cfg":
        return ConfigurationFileType.SETUP_CFG
    if basename == "tox.ini":
        return ConfigurationFileType.TOX_INI
    if basename == "pyproject.toml":
        return ConfigurationFileType.PYPROJECT_TOML
    if basename.endswith(".txt"):
        return ConfigurationFileType.REQUIREMENTS_TXT
    if basename.endswith(".toml"):
        return ConfigurationFileType.TOML
    if default is UNDEFINED:
        message: str = (
            f"{path!s} is not a recognized type of configuration file."
        )
        raise ValueError(message)
    return default


def is_configuration_file(path: str) -> bool:
    return get_configuration_file_type(path, default=None) is not None


@overload
def iter_configuration_files(path: str) -> Iterable[str]: ...


@overload
def iter_configuration_files(path: Path) -> Iterable[Path]: ...


def iter_configuration_files(path: str | Path) -> Iterable[Path | str]:
    """
    Iterate over the project configuration files for the given path.
    If the path is a file path—yields only that path. If the path is a
    directory, yields all configuration files in that directory.
    """
    if os.path.exists(path):
        if os.path.isdir(path):
            child: Path
            for child in filter(
                Path.is_file,
                (
                    path.iterdir()
                    if isinstance(path, Path)
                    else Path(path).iterdir()
                ),
            ):
                if (
                    get_configuration_file_type(child, default=None)
                    is not None
                ):
                    yield (
                        child
                        if isinstance(path, Path)
                        else str(child.absolute())
                    )
        elif get_configuration_file_type(path, default=None) is not None:
            yield path


def _iter_editable_project_locations() -> Iterable[tuple[str, str]]:
    metadata: PackageMetadata
    for name, metadata in map_pip_list().items():
        editable_project_location: str | None = metadata.get(
            "editable_project_location"
        )
        if editable_project_location:
            yield (
                name,
                editable_project_location,
            )


@functools.lru_cache
def map_editable_project_locations() -> dict[str, str]:
    """
    Get a mapping of (normalized) editable distribution names to their
    locations.
    """
    return dict(_iter_editable_project_locations())


class PackageMetadata(TypedDict, total=False):
    name: str
    version: str
    editable_project_location: str


def _iter_pip_list() -> Iterable[tuple[str, PackageMetadata]]:
    uv: str | None = shutil.which("uv")
    command: tuple[str, ...]
    if uv:
        command = (
            uv,
            "pip",
            "list",
            "--python",
            sys.executable,
            "--format=json",
        )
    else:
        # If `uv` is not available, use `pip`
        command = (
            sys.executable,
            "-m",
            "pip",
            "list",
            "--format=json",
        )
    metadata: PackageMetadata
    for metadata in json.loads(check_output(command)):
        yield (
            normalize_name(metadata["name"]),
            metadata,
        )


@cache
def map_pip_list() -> dict[str, PackageMetadata]:
    return dict(_iter_pip_list())


def cache_clear() -> None:
    """
    Clear distribution metadata caches
    """
    map_pip_list.cache_clear()
    get_installed_distributions.cache_clear()
    map_editable_project_locations.cache_clear()
    is_editable.cache_clear()
    is_installed.cache_clear()
    get_requirement_string_distribution_name.cache_clear()


def refresh_editable_distributions() -> None:
    """
    Update distribution information for editable installs
    """
    name: str
    location: str
    for name, location in map_editable_project_locations().items():
        _install_requirement_string(location, name=name, editable=True)


@functools.lru_cache
def get_installed_distributions() -> dict[str, Distribution]:
    """
    Return a dictionary of installed distributions.
    """
    refresh_editable_distributions()
    installed: dict[str, Distribution] = {}
    for distribution in _get_distributions():
        name: str = distribution.metadata["Name"]
        if distribution.version is None:
            # If no version can be found, use pip to find the version
            distribution.metadata["Version"] = (
                map_pip_list().get(name, {}).get("version")
            )
        installed[normalize_name(name)] = distribution
    return installed


def get_distribution(name: str) -> Distribution:
    return get_installed_distributions()[normalize_name(name)]


@functools.lru_cache
def is_installed(distribution_name: str) -> bool:
    return normalize_name(distribution_name) in get_installed_distributions()


def get_requirement_distribution_name(requirement: Requirement) -> str:
    return normalize_name(requirement.name)


@functools.lru_cache
def get_requirement_string_distribution_name(requirement_string: str) -> str:
    return get_requirement_distribution_name(
        get_requirement(requirement_string)
    )


@functools.lru_cache
def is_requirement_string(requirement_string: str) -> bool:
    try:
        Requirement(requirement_string)
    except InvalidRequirement:
        return False
    return True


def _iter_file_requirement_strings(path: str) -> Iterable[str]:
    lines: list[str]
    requirement_file_io: IO[str]
    with open(path) as requirement_file_io:
        lines = requirement_file_io.readlines()
    return filter(is_requirement_string, lines)


def _iter_setup_cfg_requirement_strings(path: str) -> Iterable[str]:
    parser: ConfigParser = ConfigParser()
    parser.read(path)
    requirement_strings: Iterable[str] = ()
    if ("options" in parser) and ("install_requires" in parser["options"]):
        requirement_strings = chain(
            requirement_strings,
            filter(
                is_requirement_string,
                parser["options"]["install_requires"].split("\n"),
            ),
        )
    if "options.extras_require" in parser:
        extras_require: SectionProxy = parser["options.extras_require"]
        extra_requirements_string: str
        for extra_requirements_string in extras_require.values():
            requirement_strings = chain(
                requirement_strings,
                filter(
                    is_requirement_string,
                    extra_requirements_string.split("\n"),
                ),
            )
    return iter_distinct(requirement_strings)


def _iter_tox_ini_requirement_strings(
    path: str | Path | ConfigParser = "",
    string: str = "",
) -> Iterable[str]:
    """
    Parse a tox.ini file and yield the requirements found in the `deps`
    options of each section.

    Parameters:

    - path (str|Path) = "": The path to a tox.ini file
    - string (str) = "": The contents of a tox.ini file
    """
    parser: ConfigParser = ConfigParser()
    message: str
    if path:
        if string:
            message = (
                "Either `path` or `string` arguments may be provided, but not "
                "both"
            )
            raise ValueError(message)
        parser.read(path)
    else:
        if not string:
            message = "Either a `path` or `string` argument must be provided"
            raise ValueError(message)
        parser.read_string(string)

    def get_section_option_requirements(
        section_name: str, option_name: str
    ) -> Iterable[str]:
        if parser.has_option(section_name, option_name):
            return filter(
                is_requirement_string,
                parser.get(section_name, option_name).split("\n"),
            )
        return ()

    def get_section_requirements(section_name: str) -> Iterable[str]:
        requirements: Iterable[str] = get_section_option_requirements(
            section_name, "deps"
        )
        if section_name == "tox":
            requirements = chain(
                requirements,
                get_section_option_requirements(section_name, "requires"),
            )
        return requirements

    return iter_distinct(
        chain(("tox",), *map(get_section_requirements, parser.sections()))
    )


def _is_installed_requirement_string(item: Any) -> bool:
    """
    Determine if an item is a valid requirement string for an installed
    package.

    Parameters:
        item: An item to evaluate.
    """
    if not isinstance(item, str):
        return False
    try:
        requirement: Requirement = Requirement(item)
    except InvalidRequirement:
        return False
    return is_installed(requirement.name)


def iter_find_requirements_lists(
    document: dict[str, Any] | list,
    include_pointers: tuple[str, ...] = (),
    exclude_pointers: tuple[str, ...] = (),
) -> Iterable[list[str]]:
    """
    Recursively yield all lists of valid requirement strings for installed
    packages. Exclusions are resolved before inclusions.

    Parameters:
        document: A dictionary or list of JSON-compatible data elements.
        include_pointers: JSON pointers of elements to include.
        exclude_pointers: JSON pointers of elements to exclude.
    """
    exclude_object_ids: AbstractSet[int]
    if exclude_pointers:
        exclude_object_ids = set(
            map(
                id,
                filter(
                    None,
                    map(
                        functools.partial(
                            resolve_pointer, document, default=None
                        ),
                        exclude_pointers,
                    ),
                ),
            )
        )
    else:
        exclude_object_ids = frozenset()
    if include_pointers:
        included_element: Any
        for included_element in filter(
            None,
            map(
                functools.partial(resolve_pointer, document, default=None),
                include_pointers,
            ),
        ):
            if isinstance(included_element, (list, dict)):
                yield from iter_find_qualified_lists(
                    included_element,
                    item_condition=_is_installed_requirement_string,
                    exclude_object_ids=exclude_object_ids,
                )
    else:
        yield from iter_find_qualified_lists(
            document,
            item_condition=_is_installed_requirement_string,
            exclude_object_ids=exclude_object_ids,
        )


def _iter_toml_requirement_strings(
    path: str,
    include_pointers: tuple[str, ...] = (),
    exclude_pointers: tuple[str, ...] = (),
) -> Iterable[str]:
    """
    Read a TOML file and yield the requirements found.

    Parameters:
        Path: The path to a TOML file.
        include_pointers: A tuple of JSON pointers indicating elements to
            include (defaults to all elements).
        exclude_pointers: A tuple of JSON pointers indicating elements to
            exclude (defaults to no exclusions).
    """
    # Parse pyproject.toml
    try:
        with open(path, "rb") as pyproject_io:
            document: dict[str, Any] = tomli.load(pyproject_io)
    except FileNotFoundError:
        return
    # Find requirements
    yield from iter_distinct(
        chain(
            *iter_find_requirements_lists(
                document,
                include_pointers=include_pointers,
                exclude_pointers=exclude_pointers,
            )
        )
    )


def iter_configuration_file_requirement_strings(
    path: str,
    *,
    include_pointers: tuple[str, ...] = (),
    exclude_pointers: tuple[str, ...] = (),
) -> Iterable[str]:
    """
    Read a configuration file and yield the parsed requirements.

    Parameters:
        path: The path to a configuration file
        include_pointers: A tuple of JSON pointers indicating elements to
            include (defaults to all elements).
        exclude_pointers: A tuple of JSON pointers indicating elements to
            exclude (defaults to no exclusions).
    """
    configuration_file_type: ConfigurationFileType = (
        get_configuration_file_type(path)
    )
    if configuration_file_type == ConfigurationFileType.SETUP_CFG:
        return _iter_setup_cfg_requirement_strings(path)
    if configuration_file_type in (
        ConfigurationFileType.PYPROJECT_TOML,
        ConfigurationFileType.TOML,
    ):
        return _iter_toml_requirement_strings(
            path,
            include_pointers=include_pointers,
            exclude_pointers=exclude_pointers,
        )
    if configuration_file_type == ConfigurationFileType.TOX_INI:
        return _iter_tox_ini_requirement_strings(path=path)
    if configuration_file_type != ConfigurationFileType.REQUIREMENTS_TXT:
        raise ValueError(configuration_file_type)
    return _iter_file_requirement_strings(path)


@functools.lru_cache
def is_editable(name: str) -> bool:
    """
    Return `True` if the indicated distribution is an editable installation.
    """
    return bool(normalize_name(name) in map_editable_project_locations())


def _get_setup_cfg_metadata(path: str, key: str) -> str:
    if os.path.basename(path).lower() != "setup.cfg":
        if not os.path.isdir(path):
            path = os.path.dirname(path)
        path = os.path.join(path, "setup.cfg")
    if os.path.isfile(path):
        parser: ConfigParser = ConfigParser()
        parser.read(path)
        if "metadata" in parser:
            return parser.get("metadata", key, fallback="")
        warn(
            f"No `metadata` section found in: {path}",
            stacklevel=2,
        )
    return ""


def _get_setup_py_metadata(path: str, args: tuple[str, ...]) -> str:
    """
    Execute a setup.py script with `args` and return the response.

    Parameters:

    - path (str)
    - args ([str])
    """
    value: str = ""
    current_directory: str = os.path.abspath(os.curdir)
    directory: str = path
    try:
        if os.path.basename(path).lower() == "setup.py":
            directory = os.path.dirname(path)
            os.chdir(directory)
        else:
            if not os.path.isdir(path):
                directory = os.path.dirname(path)
            os.chdir(directory)
            path = os.path.join(directory, "setup.py")
        if os.path.isfile(path):
            command: tuple[str, ...] = (sys.executable, path, *args)
            try:
                value = check_output(command).strip().split("\n")[-1]
            except CalledProcessError:
                warn(
                    f"A package name could not be found in {path}, "
                    "attempting to refresh egg info"
                    f"\nError ignored: {get_exception_text()}",
                    stacklevel=2,
                )
                # re-write egg info and attempt to get the name again
                setup_egg_info(directory)
                try:
                    value = check_output(command).strip().split("\n")[-1]
                except Exception:  # noqa: BLE001
                    warn(
                        f"A package name could not be found in {path}"
                        f"\nError ignored: {get_exception_text()}",
                        stacklevel=2,
                    )
    finally:
        os.chdir(current_directory)
    return value


def _get_pyproject_toml_project_metadata(path: str, key: str) -> str:
    if os.path.basename(path).lower() != "pyproject.toml":
        if not os.path.isdir(path):
            path = os.path.dirname(path)
        path = os.path.join(path, "pyproject.toml")
    if os.path.isfile(path):
        pyproject_io: IO[str]
        with open(path) as pyproject_io:
            pyproject: dict[str, Any] = tomli.loads(pyproject_io.read())
            if "project" in pyproject:
                return pyproject["project"].get(key, "")
    return ""


def get_setup_distribution_name(path: str) -> str:
    """
    Get a distribution's name from setup.py, setup.cfg or pyproject.toml
    """
    return normalize_name(
        _get_setup_cfg_metadata(path, "name")
        or _get_pyproject_toml_project_metadata(path, "name")
        or _get_setup_py_metadata(path, ("--name",))
    )


def get_setup_distribution_version(path: str) -> str:
    """
    Get a distribution's version from setup.py, setup.cfg or pyproject.toml
    """
    return (
        _get_setup_cfg_metadata(path, "version")
        or _get_pyproject_toml_project_metadata(path, "version")
        or _get_setup_py_metadata(path, ("--version",))
    )


def _setup(arguments: tuple[str, ...]) -> None:
    try:
        check_output((sys.executable, "setup.py", *arguments))
    except CalledProcessError:
        warn(f"Ignoring error: {get_exception_text()}", stacklevel=2)


def _setup_location(
    location: str | Path, arguments: Iterable[tuple[str, ...]]
) -> None:
    if isinstance(location, str):
        location = Path(location)
    # If there is no setup.py file, we can't update egg info
    if not location.joinpath("setup.py").is_file():
        return
    if isinstance(arguments, str):
        arguments = (arguments,)
    current_directory: Path = Path(os.curdir).absolute()
    os.chdir(location)
    try:
        deque(map(_setup, arguments), maxlen=0)
    finally:
        os.chdir(current_directory)


def get_editable_distribution_location(name: str) -> str:
    return map_editable_project_locations().get(normalize_name(name), "")


def setup_egg_info(directory: str | Path, egg_base: str = "") -> None:
    """
    Refresh egg-info for the editable package installed in
    `directory` (only applicable for packages using a `setup.py` script)
    """
    if isinstance(directory, str):
        directory = Path(directory)
    directory = directory.absolute()
    if not directory.is_dir():
        directory = directory.parent
    # If there is a setup.py, and a *.dist-info directory, but that
    # *.dist-info directory has no RECORD, we need to remove the *.dist-info
    # directory
    if directory.joinpath("setup.py").is_file():
        dist_info: str
        for dist_info in iglob(str(directory.joinpath("*.dist-info"))):
            dist_info_path: Path = Path(dist_info)
            if not dist_info_path.joinpath("RECORD").is_file():
                rmtree(dist_info_path)
    _setup_location(
        directory,
        (("-q", "egg_info") + (("--egg-base", egg_base) if egg_base else ()),),
    )


def get_requirement(
    requirement_string: str,
) -> Requirement:
    try:
        return Requirement(requirement_string)
    except InvalidRequirement as error:
        # Try to parse the requirement as an installation target location,
        # such as can be used with `pip install`
        location: str = requirement_string
        extras: str = ""
        if "[" in requirement_string and requirement_string.endswith("]"):
            parts: list[str] = requirement_string.split("[")
            location = "[".join(parts[:-1])
            extras = f"[{parts[-1]}"
        location = os.path.abspath(location)
        name: str = get_setup_distribution_name(location)
        if not name:
            message: str = f"No distribution found in {location}"
            raise FileNotFoundError(message) from error
        return Requirement(f"{name}{extras}")


def get_required_distribution_names(
    requirement_string: str,
    *,
    exclude: Iterable[str] = (),
    recursive: bool = True,
    echo: bool = False,
    depth: int | None = None,
) -> MutableSet[str]:
    """
    Return a `tuple` of all distribution names which are required by the
    distribution specified in `requirement_string`.

    Parameters:

    - requirement_string (str): A distribution name, or a requirement string
      indicating both a distribution name and extras.
    - exclude ([str]): The name of one or more distributions to *exclude*
      from requirements lookup. Please note that excluding a distribution will
      also halt recursive lookup of requirements for that distribution.
    - recursive (bool): If `True` (the default), required distributions will
      be obtained recursively.
    - echo (bool) = False: If `True`, commands and responses executed in
      subprocesses will be printed to `sys.stdout`
    - depth (int|None) = None: The maximum depth of recursion to follow
      requirements. If `None` (the default), recursion is not restricted.
    """
    if isinstance(exclude, str):
        exclude = {normalize_name(exclude)}
    else:
        exclude = set(map(normalize_name, exclude))
    return set(
        _iter_requirement_names(
            get_requirement(requirement_string),
            exclude=exclude,
            recursive=recursive,
            echo=echo,
            depth=depth,
        )
    )


def _get_requirement_name(requirement: Requirement) -> str:
    return normalize_name(requirement.name)


@deprecated(
    "dependence._utilities.install_requirement is deprecated and will be "
    "removed in a future release."
)
def install_requirement(requirement: str | Requirement) -> None:
    """
    Install a requirement

    Parameters:

    - requirement (str)
    - echo (bool) = True: If `True` (default), the `pip install`
      commands will be echoed to `sys.stdout`
    """
    if isinstance(requirement, str):
        requirement = Requirement(requirement)
    return _install_requirement(requirement)


def _install_requirement_string(
    requirement_string: str,
    name: str = "",
    *,
    editable: bool = False,
) -> None:
    """
    Install a requirement string with no dependencies, compilation, build
    isolation, etc.
    """
    command: tuple[str, ...]
    uv: str | None = shutil.which("uv")
    if uv:
        command = (
            uv,
            "pip",
            "install",
            "--python",
            sys.executable,
            "--no-deps",
            "--no-compile",
            *(
                (
                    "-e",
                    requirement_string,
                )
                if editable
                else (requirement_string,)
            ),
        )
    else:
        # If `uv` is not available, use `pip`
        command = (
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--no-compile",
            *(
                (
                    "-e",
                    requirement_string,
                )
                if editable
                else (requirement_string,)
            ),
        )
    try:
        check_output(command)
    except CalledProcessError as error:
        message: str = (
            (
                f"\nCould not install {name}:"
                f"\n$ {list2cmdline(command)}"
                f"\n{error.output.decode()}"
                if name == requirement_string
                else (
                    f"\nCould not install {name} from "
                    f"{requirement_string}:"
                    f"\n$ {list2cmdline(command)}"
                    f"\n{error.output.decode()}"
                )
            )
            if name
            else (
                f"\n{list2cmdline(command)}"
                f"\nCould not install {requirement_string}"
            )
        )
        if not editable:
            print(message)  # noqa: T201
            raise
        try:
            check_output((*command, "--force-reinstall"))
        except CalledProcessError:
            print(message)  # noqa: T201
            raise


def _install_requirement(
    requirement: Requirement,
) -> None:
    requirement_string: str = str(requirement)
    # Get the distribution name
    distribution: Distribution | None = None
    editable_location: str = ""
    try:
        distribution = _get_distribution(requirement.name)
        editable_location = get_editable_distribution_location(
            distribution.metadata["Name"]
        )
    except (PackageNotFoundError, KeyError):
        pass
    # If the requirement is installed and editable, re-install from
    # the editable location
    if distribution and editable_location:
        # Assemble a requirement specifier for the editable install
        requirement_string = editable_location
        if requirement.extras:
            requirement_string = (
                f"{requirement_string}[{','.join(requirement.extras)}]"
            )
    _install_requirement_string(
        requirement_string=requirement_string,
        name=normalize_name(requirement.name),
        editable=bool(editable_location),
    )
    # Refresh the metadata
    cache_clear()


def _get_installed_distribution(
    name: str,
) -> Distribution | None:
    if name in _BUILTIN_DISTRIBUTION_NAMES:
        return None
    try:
        return get_installed_distributions()[name]
    except KeyError:
        return None


def _iter_distribution_requirements(
    distribution: Distribution,
    extras: tuple[str, ...] = (),
    exclude: Container[str] = (),
) -> Iterable[Requirement]:
    if not distribution.requires:
        return
    requirement: Requirement
    for requirement in map(Requirement, distribution.requires):
        if (
            (requirement.marker is None)
            or any(
                requirement.marker.evaluate({"extra": extra})
                for extra in extras
            )
        ) and (normalize_name(requirement.name) not in exclude):
            yield requirement


def _iter_requirement_names(
    requirement: Requirement,
    *,
    exclude: MutableSet[str],
    recursive: bool = True,
    echo: bool = False,
    depth: int | None = None,
) -> Iterable[str]:
    name: str = normalize_name(requirement.name)
    extras: tuple[str, ...] = tuple(requirement.extras)
    if name in exclude:
        return ()
    # Ensure we don't follow the same requirement again, causing cyclic
    # recursion
    exclude.add(name)
    distribution: Distribution | None = _get_installed_distribution(name)
    if distribution is None:
        return ()
    requirements: tuple[Requirement, ...] = tuple(
        iter_distinct(
            _iter_distribution_requirements(
                distribution,
                extras=extras,
                exclude=exclude,
            ),
        )
    )
    lateral_exclude: MutableSet[str] = set()

    def iter_requirement_names_(
        requirement_: Requirement,
        depth_: int | None = None,
    ) -> Iterable[str]:
        if (depth_ is None) or depth_ >= 0:
            yield from _iter_requirement_names(
                requirement_,
                exclude=cast(
                    MutableSet[str],
                    exclude
                    | (
                        lateral_exclude - {_get_requirement_name(requirement_)}
                    ),
                ),
                recursive=recursive,
                echo=echo,
                depth=None if (depth_ is None) else depth_ - 1,
            )

    def not_excluded(name: str) -> bool:
        if name not in exclude:
            # Add this to the exclusions
            lateral_exclude.add(name)
            return True
        return False

    requirement_names: Iterable[str] = filter(
        not_excluded, map(_get_requirement_name, requirements)
    )
    if recursive:
        requirement_: Requirement
        requirement_names = chain(
            requirement_names,
            *(
                iter_requirement_names_(
                    requirement_, None if (depth is None) else depth - 1
                )
                for requirement_ in requirements
            ),
        )
    return requirement_names
