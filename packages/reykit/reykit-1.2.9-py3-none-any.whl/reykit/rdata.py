# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2022-12-05
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Data methods.
"""


from typing import Any, TypedDict, Literal, overload
from collections import Counter, defaultdict as Defaultdict, ChainMap
from collections.abc import Callable, Iterable, Generator, AsyncGenerator
from itertools import chain as IChain
from decimal import Decimal
from json import dumps as json_dumps
from jwt import encode as jwt_encode, decode as jwt_decode
from jwt.exceptions import InvalidTokenError
from bcrypt import gensalt as bcrypt_gensalt, hashpw as bcrypt_hashpw, checkpw as bcrypt_checkpw

from .rbase import T, KT, VT, Base, Null, throw, check_least_one, check_most_one, is_iterable


__all__ = (
    'to_json',
    'count',
    'flatten',
    'split',
    'unique',
    'in_arrs',
    'objs_in',
    'chain',
    'default_dict',
    'FunctionGenerator',
    'encode_jwt',
    'decode_jwt',
    'hash_bcrypt',
    'is_hash_bcrypt'
)


CountResult = TypedDict('CountResult', {'element': Any, 'number': int})


def to_json(
    data: Any,
    compact: bool = True
) -> str:
    """
    Convert data to JSON format string.

    Parameters
    ----------
    data : Data.
    compact : Whether compact content.

    Returns
    -------
    JSON format string.
    """

    # Parameter.
    if compact:
        indent = None
        separators = (',', ':')
    else:
        indent = 4
        separators = None

    # Convert.
    default = lambda value: (
        value.__float__()
        if type(value) == Decimal
        else repr(value)
    )
    string = json_dumps(
        data,
        ensure_ascii=False,
        indent=indent,
        separators=separators,
        default=default
    )

    return string


def count(data: Iterable) -> list[CountResult]:
    """
    Group count data element value.

    Parameters
    ----------
    data : Data.

    Returns
    -------
    Count result.

    Examples
    --------
    >>> count([1, True, False, 0, (2, 3)])
    [{'element': 1, 'number': 2}, {'element': False, 'number': 2}, {'element': (2, 3), 'number': 1}]
    """

    # Count.
    counter = Counter(data)

    # Convert.
    result = [
        {'element': elem, 'number': num}
        for elem, num in counter.items()
    ]

    return result


def flatten(data: Any, *, _flattern_data: list | None = None) -> list:
    """
    Flatten data.

    Parameters
    ----------
    data : Data.
    _flattern_data : Recursion cumulative data.

    Returns
    -------
    Data after flatten.
    """

    # Parameter.
    _flattern_data = _flattern_data or []

    # Flatten.

    ## Recursion dict object.
    if type(data) == dict:
        for elem in data.values():
            _flattern_data = flatten(
                elem,
                _flattern_data = _flattern_data
            )

    ## Recursion iterator.
    elif is_iterable(data, (str, bytes)):
        for elem in data:
            _flattern_data = flatten(
                elem,
                _flattern_data = _flattern_data
            )

    ## Other.
    else:
        _flattern_data.append(data)

    return _flattern_data


@overload
def split(data: Iterable[T], share: int) -> list[list[T]]: ...

@overload
def split(data: Iterable[T], *, bin_size: int) -> list[list[T]]: ...

def split(data: Iterable[T], share: int | None = None, bin_size: int | None = None) -> list[list[T]]:
    """
    Split data into multiple data.

    Parameters
    ----------
    data : Data.
    share : Number of split share.
    bin_size : Size of each bin.

    Returns
    -------
    Split data.
    """

    # Check parameter.
    check_least_one(share, bin_size)
    check_most_one(share, bin_size)

    # Parameter.
    data = list(data)

    # Split.
    data_len = len(data)
    _data = []
    _data_len = 0

    ## by number of share.
    if share is not None:
        average = data_len / share
        for n in range(share):
            bin_size = int(average * (n + 1)) - int(average * n)
            _data = data[_data_len:_data_len + bin_size]
            _data.append(_data)
            _data_len += bin_size

    ## By size of bin.
    elif bin_size is not None:
        while True:
            _data = data[_data_len:_data_len + bin_size]
            _data.append(_data)
            _data_len += bin_size
            if _data_len > data_len:
                break

    return _data


def unique(data: Iterable[T]) -> list[T]:
    """
    De duplication of data.

    Parameters
    ----------
    data : Data.

    Returns
    -------
    List after de duplication.
    """

    # Parameter.
    data = tuple(data)

    # Delete duplicate.
    data_unique = list(set(data))
    data_unique.sort(key=data.index)
    return data_unique


def in_arrs(ojb: Any, *arrs: Iterable, mode: Literal['or', 'and'] = 'or') -> bool:
    """
    Judge whether the one object is in multiple arrays.

    Parameters
    ----------
    obj : One object.
    arrs : Multiple arrays.
    mode : Judge mode.
        - `Literal['or']`: Judge whether the in a certain array.
        - `Literal['and']`: Judge whether the in all arrays.

    Returns
    -------
    Judge result.
    """

    # Judge.
    match mode:

        ## Or.
        case 'or':
            for arr in arrs:
                if ojb in arr:
                    return True

            return False

        ## And.
        case 'and':
            for arr in arrs:
                if ojb not in arr:
                    return False

            return True


def objs_in(arr: Iterable, *objs: Any, mode: Literal['or', 'and'] = 'or') -> bool:
    """
    Judge whether the multiple objects is in one array.

    Parameters
    ----------
    arr : One array.
    objs : Multiple objects.
    mode : Judge mode.
        - `Literal['or']`: Judge whether contain a certain object.
        - `Literal['and']`: Judge whether contain all objects.

    Returns
    -------
    Judge result.
    """

    # Judge.
    match mode:

        ## Or.
        case 'or':
            for obj in objs:
                if obj in arr:
                    return True

            return False

        ## And.
        case 'and':
            for obj in objs:
                if obj not in arr:
                    return False

            return True


@overload
def chain(*iterables: dict[KT, VT]) -> ChainMap[KT, VT]: ...

@overload
def chain(*iterables: Iterable[T]) -> IChain[T]: ...

def chain(*iterables: dict[KT, VT] | Iterable[T]) -> ChainMap[KT, VT] | IChain[T]:
    """
    Connect multiple iterables.

    Parameters
    ----------
    iterables : Multiple iterables.
        - `dict`: Connect to chain mapping.
        - `Iterable`: Connect to chain.

    Returns
    -------
    Chain instance.
    """

    # Dict.
    if all(
        [
            isinstance(iterable, dict)
            for iterable in iterables
        ]
    ):
        data = ChainMap(*iterables)

    # Other.
    else:
        data = IChain(*iterables)

    return data


def default_dict(default: T | Null.Type = Null, data: dict[KT, VT] | None = None) -> Defaultdict[KT, VT | T]:
    """
    Set `dict` instance, default value when key does not exist.

    Parameters
    ----------
    default : Default value.
        - `Null.Type`: Nest function self.
        - `Callable`: Use call return value.
    data : `dict` instance.
        - `None`: Empty `dict`.
    """

    # Parameter.

    ## Null.
    if default == Null:
        default_factory = default_dict

    ## Callable.
    elif callable(default):
        default_factory = default

    ## Not callable.
    else:
        default_factory = lambda: default

    data = data or {}

    # Instance.
    dict_set = Defaultdict(default_factory, data)

    return dict_set


class FunctionGenerator(Base):
    """
    Function generator type.

    Examples
    --------
    >>> func = lambda arg1, arg2: arg1 + arg2
    >>> fgenerator = FunctionGenerator(func, 10)
    >>> fgenerator.add(1)
    >>> fgenerator.add(2)
    >>> list(fgenerator)
    [11, 12]
    """


    def __init__(
        self,
        func: Callable,
        *args: Any,
        **kwargs: Any
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        func : Generate function.
        args : Function default position arguments.
        kwargs : Function default keyword arguments.
        """

        # Set attribute.
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.params: list[tuple[tuple, dict]] = []


    def generator(self) -> Generator[Any, Any, None]:
        """
        Create generator.

        Parameters
        ----------
        Generator.
        """

        # Loop.
        while True:

            # Break.
            if self.params == []:
                break

            # Generate.
            args, kwargs = self.params.pop(0)
            result = self.func(*args, **kwargs)

            # Return.
            yield result


    async def agenerator(self) -> AsyncGenerator[Any, Any]:
        """
        Asynchronous create generator.

        Parameters
        ----------
        Generator.
        """

        # Loop.
        while True:

            # Break.
            if self.params == []:
                break

            # Generate.
            args, kwargs = self.params.pop(0)
            result = self.func(*args, **kwargs)

            # Return.
            yield result


    def add(
        self,
        *args: Any,
        **kwargs: Any
    ) -> None:
        """
        Add once generate.

        Parameters
        ----------
        args : Function position arguments.
        kwargs : Function keyword arguments.
        """

        # Parameter.
        func_args = (
            *self.args,
            *args
        )
        func_kwargs = {
            **self.kwargs,
            **kwargs
        }

        # Add.
        item = (
            func_args,
            func_kwargs
        )
        self.params.append(item)


    __call__ = add


    def __next__(self) -> Any:
        """
        Generate once from generator.

        Returns
        -------
        Generate value.
        """

        # Generate.
        generator = self.generator()
        result = next(generator)

        return result


    def __iter__(self) -> Generator[Any, Any, None]:
        """
        Iterating generator.
        """

        # Iterating.
        generator = self.generator()

        return generator


    async def __anext__(self) -> Any:
        """
        Asynchronous generate once from generator.

        Returns
        -------
        Generate value.
        """

        # Generate.
        agenerator = await self.agenerator()
        result = anext(agenerator)

        return result


    async def __aiter__(self) -> AsyncGenerator[Any, Any]:
        """
        Asynchronous iterating generator.
        """

        # Iterating.
        agenerator = await self.agenerator()

        return agenerator


def encode_jwt(json: dict[str, Any], key: str | bytes) -> str:
    """
    Encode JSON data to JWT token, based on `HS256`.

    Parameters
    ----------
    json : JSON data.
    key : Key.

    Returns
    -------
    Token.
    """

    # Check.
    sub = json.get('sub', '')
    if type(sub) != str:
        throw(TypeError, sub)

    # Parameter.
    if type(key) != str:
        key = str(key)
    algorithm = 'HS256'

    # Encode.
    token = jwt_encode(json, key, algorithm=algorithm)

    return token


def decode_jwt(token: str | bytes, key: str| bytes) -> dict[str, Any] | None:
    """
    Decode JWT token to JSON data, based on `HS256`. When decode error, then return `None`.

    Parameters
    ----------
    token : JWT token.
    key : Key.

    Returns
    -------
    JSON data or null.
    """

    # Parameter.
    algorithm = 'HS256'

    # Decode.
    try:
        json = jwt_decode(token, key, algorithms=algorithm)
    except InvalidTokenError:
        return

    return json


def hash_bcrypt(password: str | bytes) -> bytes:
    """
    Get hash password, based on algorithm `bcrypt`.

    Parameters
    ----------
    password: Password.

    Returns
    -------
    Hashed password.
    """

    # Parameter.
    if type(password) == str:
        password = bytes(password, encoding='utf-8')

    # Hash.
    salt = bcrypt_gensalt()
    password_hash = bcrypt_hashpw(password, salt)

    return password_hash


def is_hash_bcrypt(password: str | bytes, password_hash: str | bytes) -> bool:
    """
    Whether is match password and hashed password.

    Parameters
    ----------
    password: Password.
    password_hash : Hashed password.

    Returns
    -------
    Judgment result.
    """

    # Parameter.
    if type(password) == str:
        password = bytes(password, encoding='utf-8')
    if type(password_hash) == str:
        password_hash = bytes(password_hash, encoding='utf-8')

    # Judge.
    result = bcrypt_checkpw(password, password_hash)

    return result
