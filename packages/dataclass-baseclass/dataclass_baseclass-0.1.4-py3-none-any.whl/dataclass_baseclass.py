"""`DataClass` - inheritable contagious base class.

Instead of (endless?) `@dataclass` decorating.

## Usage

```
class A(DataClass):  # it's a dataclass

class B(A):  # it's a dataclass too
```

as opposed to:

```
@dataclass
class A(): ...  # it's a dataclass

class B(A): ...  # it's *not* a dataclass, needs decorating

@dataclass
class B(A): ...  # now it's a dataclass
```

Also:

```
class B(DataClass, A): ...  # all attributes from A become fields
```

as opposed to:

```
class A():  ...

@dataclass
class B(A): ...  # no attributes from A are fields
```

## Instantiation

```
class C(DataClass):
    a: str
    b: str

defaults: Data = {"a": "A", "b": "B"}

c = C(defaults, a="a", b="b")

or just:

c = C(a="a", b="b")
```

It kind of supports freezing/unfreezing on the fly, but it is best to keep all
classes in the chain either frozen or not.

`frozen` attribute is dominant, ie as soon as you have one frozen
parent class in the mix, class becomes frozen. If you want it unfrozen you
need to specify `dataclass_params.frozen` as False:

```
class Unfrozen(Frozen, dataclass_params={"frozen": False}
```

## Gotchas and features

### Turning field into property in subclass

This works:

```
class C(DataClass):
    s: str

class CC(C):
    @property
    def s(self) -> str:
        return "S"

```

### Create a frozen (readonly)  copy with `_frozen_copy()`
"""

from __future__ import annotations

from collections.abc import Iterator
from copy import deepcopy
from dataclasses import (  # type: ignore[attr-defined]
    _PARAMS,
    MISSING,
    Field,
    _is_classvar,
    _is_type,
    asdict,
    field,
    fields,
    dataclass,
    is_dataclass,
    make_dataclass,
    replace,
)
from types import new_class
from typing import (
    _ProtocolMeta,
    Any,
    Callable,
    ClassVar,
    Generic,
    Self,
    Protocol,
    TypeVar,
    cast,
    dataclass_transform,
)
import dataclasses
import inspect

__pdoc__ = {}
__version__ = "0.1.4"

Data = dict[str, Any]

orig_get_field = dataclasses._get_field  # type: ignore[attr-defined]


# XXX this may not work for some corner cases
def our_get_field(
    cls: type,
    a_name: str,
    a_type: type,
    default_kw_only: bool,
) -> Field:
    try:
        default = getattr(cls, a_name)
        if isinstance(default, Field):
            if default.default.__class__.__hash__ is None:
                d = default.default
                default.default = MISSING
                default.default_factory = lambda: deepcopy(d)

        else:
            import typing

            if (
                default.__class__.__hash__ is None
                and not _is_classvar(a_type, typing)
                and not (
                    isinstance(a_type, str)
                    and _is_type(a_type, cls, typing, ClassVar, _is_classvar)
                )
            ):
                setattr(
                    cls,
                    a_name,
                    field(default_factory=lambda: deepcopy(default)),
                )
    except AttributeError:
        pass

    return orig_get_field(cls, a_name, a_type, default_kw_only)


__pdoc__["our_get_field"] = False


class DataClassField(Field):
    """Improved `dataclasses.Field` class."""

    def __init__(self, f: Field) -> None:
        for s in f.__slots__:  # type: ignore[attr-defined]
            setattr(self, s, getattr(f, s))

    def default_value(self) -> Any:
        """Get default value for the field.

        Takes in account `default` / `default_factory`.

        Returns:
            Any
        """

        return (
            self.default
            if self.default is not MISSING
            else self.default_factory()
            if self.default_factory is not MISSING
            else None
        )


@dataclass_transform()
class DataClassMeta(_ProtocolMeta):
    """`DataClass` metaclass.

    Turns class with attributes into `dataclass` with fields

    `dataclass` can only inherit from another `dataclass`. This is not a problem
    for vertical inheritance, but may pose a challenge for horizontal
    (multiple) inheritance, eg. adding protocols. In those cases
    a non-dataclass mix-in is cloned, and the infected clone is used instead.

    It mandates `kw_only = True`, which means that classes can only be
    instantiated with keyword args. For that reason, we can modify class
    instantiator footprint to accept both dict and kwargs.

    Usage:

    ```
    class C(metaclass=DataClassMeta, dataclass_params={}): ...

    defaults: Data = {}

    c = C(defaults, a="a", b="b" ...)
    ```

    Defaults and keyword args are shallowly merged.
    """

    @classmethod
    def is_metaclass(metacls, cls: Any) -> bool:
        return issubclass(type(cls), metacls)

    @staticmethod
    def __new__(
        metacls: type,
        name: str,
        bases: tuple[type, ...],
        defs: dict[str, Any],
        /,
        dataclass_params: Data | None = None,
        **kwargs: Any,
    ) -> type:
        if dataclass_params is None:
            dataclass_params = {}

        assert "kw_only" not in dataclass_params, "kw_only is not negotiable"

        dc_params = {}
        frozen: bool | None = None

        for b in reversed(bases):
            if is_dataclass(b):
                dcp = getattr(b, _PARAMS)
                dc_params.update({s: getattr(dcp, s) for s in dcp.__slots__})
                if dcp.frozen:
                    frozen = True

        if "frozen" in dataclass_params:
            assert dataclass_params["frozen"] is not None, (
                "frozen cannot be None"
            )

            frozen = dataclass_params["frozen"]
        else:
            if frozen is None:
                frozen = False
            dataclass_params["frozen"] = frozen

        dc_params.update(dataclass_params)
        dc_params["kw_only"] = True

        def is_protocol(
            tp: type, /
        ) -> bool:  # copied from typing, it is not there before 3.13
            return getattr(tp, "_is_protocol", False) and tp != Protocol

        def into_dataclass(cls: type) -> type:
            bases = tuple(
                into_dataclass(b)
                for b in cls.__bases__
                if not is_dataclass(b) and is_protocol(b)
            )

            cls_copy = new_class(
                cls.__name__,
                ((cls,) + bases),
                exec_body=lambda ns: ns.update(cls.__dict__),
            )
            params = {**dc_params}
            if getattr(cls, "_is_protocol", None) is True:
                params["init"] = False

            return dataclass(cls_copy, **dc_params)

        # Frozen and non-frozen (fresh?) dataclasses dont mix.
        # We need to align them, recursively.
        def munge_base(cls: type) -> tuple[type, bool]:
            if not is_dataclass(cls):
                cls = into_dataclass(cls)

            dcp = getattr(cls, _PARAMS)

            # Copy dataclass with toggled frozen attr.
            # Super flakey.
            fld_changed = False
            flds = []
            for f in fields(cls):
                t = f.type
                if DataClassMeta.is_metaclass(t):
                    t, _ = munge_base(cast(DataClassMeta, t))

                if f.name in defs:
                    f.init = False
                    fld_changed = True

                flds.append((f.name, t, f))

            if dcp.frozen is frozen and not fld_changed:
                return cls, False

            methods = {
                m: classmethod(f.__func__)
                if inspect.ismethod(f) and f.__self__ is cls
                else f
                for m, f in inspect.getmembers(
                    cls,
                    predicate=lambda m: inspect.ismethod(m)
                    or inspect.isfunction(m),
                )
                if m
                not in (
                    "__delattr__",
                    "__setattr__",
                    "__init_subclass__",
                )
            }
            b_cls = type(cls.__name__, (), methods)
            return make_dataclass(
                cls.__name__, flds, bases=(b_cls,), **dc_params
            ), dcp.frozen is frozen

        defs["_frozen"] = frozen
        defs["_is_protocol"] = False  # py 3.11

        # Monkey patching for pleasure and profit.
        dataclasses._get_field = our_get_field  # type: ignore[attr-defined]
        try:
            dc_bases: list[type] = []
            dc_inherit: list[type] = []
            for b in bases:
                mb, frozen_not_changed = munge_base(b)
                dc_bases.append(mb)

                # Try to make isinstance() work
                if (
                    mb is not b
                    and frozen_not_changed  # except that frozen mix inheritance does not work
                    and b.__name__
                    not in (
                        "BaseDataClass",
                        "DataClass",
                        "DataClassFrozen",
                    )
                ):
                    dc_inherit.append(b)

            cls = super().__new__(  # type: ignore[misc]
                metacls, name, tuple(dc_bases), defs, **kwargs
            )

            try:
                cls = dataclass(cls, **dc_params)
                if dc_inherit:
                    cls.__bases__ = tuple(list(cls.__bases__) + dc_inherit)
                return cls
            except TypeError as e:
                raise TypeError(*e.args, cls, dc_bases, defs, dc_params) from e
        finally:
            dataclasses._get_field = orig_get_field  # type: ignore[attr-defined]

    def __call__(cls, defaults: Data = {}, /, **kwargs) -> DataClass:
        data = {**defaults, **kwargs}

        return super().__call__(**data)


class BaseDataClass(metaclass=DataClassMeta):
    """Base `dataclass` class.

    It is recommended that all non-field additions to the class be underscored,
    to minimise conflict possibility.
    """

    _frozen: ClassVar[bool]
    """Set to true if the class is frozen (a subclass of `DataClassFrozen`)"""

    @classmethod
    # Has to return Any, otherwise cannot declare attributes as
    # attr: some_type = DataClass._field(...)
    def _field(cls, **kwargs: Any) -> Any:
        """BaseDataClass field creator.

        A convenience for calling `dataclasses.field()`.

        Returns:
            Field
        """

        return field(**kwargs)

    @classmethod
    def _fields(
        cls, *, public_only: bool = True
    ) -> tuple[DataClassField, ...]:
        """BaseDataClass fields.

        A convenience for calling `dataclasses.fields()`.

        Parameters:
            public_only (bool): exclude fields with names starting with "_"

        Returns:
            tuple[Field, ...]
        """

        return tuple(
            DataClassField(f)
            for f in fields(cls)
            if not public_only or not f.name.startswith("_")
        )

    @classmethod
    def _frozen_class(cls) -> type[Self]:
        if cls._frozen:
            return cls

        frozen_cls = getattr(cls, "_frozen_cls", None)
        if frozen_cls is None:
            frozen_cls = new_class(
                f"{cls.__name__}Frozen",
                (cls,),
                dict(
                    metaclass=DataClassMeta, dataclass_params={"frozen": True}
                ),
            )
            setattr(cls, "_frozen_cls", frozen_cls)

        return frozen_cls

    def _as_dict(
        self,
        *,
        public_only: bool = True,
        dict_factory: Callable[[list[tuple[str, Any]]], dict] = dict,
    ) -> Data:
        """`BaseDataClass` serializer.

        A convenience for calling `dataclasses.asdict()` with addition of
        `public_only` filter.

        Parameters:
            public_only (bool): exclude fields with names starting with "_"
            dict_factory (Callable): degfaults to dict (see dataclasses)

        Returns:
            dict
        """

        d = asdict(self, dict_factory=dict_factory)
        if not public_only:
            return d

        def filter_private(d: Data) -> Data:
            return {
                k: filter_private(v) if isinstance(v, dict) else v
                for k, v in d.items()
                if not k.startswith("_")
            }

        return filter_private(d)

    def __iter__(self) -> Iterator[tuple[str, Any]]:
        return iter(self._as_dict().items())

    def _replace(self, **changes: Any) -> Self:
        """Copy `BaseDataClass` instance, applying changes.

        A convenience for calling `dataclasses.replace()`.

        Parameters:
            **changes (Any):

        Returns:
            BaseDataClass
        """

        return replace(self, **changes)

    def _frozen_copy(self) -> Self:
        """Copy `BaseDataClass` instance as a frozen object.

        If class is already frozen, returns `self`.

        Returns:
            BaseDataClass, frozen version
        """

        if self._frozen:
            return self

        return self._frozen_class()(**asdict(self))

    __pdoc__["DataClass._field"] = True
    __pdoc__["DataClass._fields"] = True
    __pdoc__["DataClass._frozen"] = True
    __pdoc__["DataClass._as_dict"] = True
    __pdoc__["DataClass._replace"] = True
    __pdoc__["DataClass._frozen_copy"] = True


DataClassT = TypeVar("DataClassT", bound=BaseDataClass)


class BaseDataClassFrozen(BaseDataClass, dataclass_params={"frozen": True}):
    """Base dataclass class, frozen version."""


class DataClassLoader(Generic[DataClassT]):
    """Minimal? version of `DataClass` non-validating recursive loader.

    Parameters:
        dataclass (type):
        data (dict):

    Usage:

    ```
    DataClassLoader.load(SomeDataClassDerivative, data)
    ```

    or

    ```
    loader = DataClassLoader(SomeDataClassDerivative)
    data_obj = loader.load_data(data)
    ```
    """

    dataclass: type[DataClassT]
    """`DataClass` derivative, the load into container spec"""

    @classmethod
    def load(
        cls, dc: type[DataClassT], data: Data, strict: bool = False
    ) -> DataClassT:
        """Load data.

        Classmethod, suitable for `DataClassLoadProtocol._loader` property.

        Parameters:
            dc (type):  Load into this `DataClass` spec
            data (dict):

        Returns:
            DataClass instance
        """

        return cls(dc).load_data(data, strict)

    def __init__(self, dataclass: type[DataClassT]) -> None:
        self.dataclass = dataclass

    def load_data(self, data: Data, strict: bool = False) -> DataClassT:
        """Load data into instance.

        Parameters:
            data (dict):

        Returns:
            DataClass instance

        Raises:
            ValueError
        """

        if strict is True:
            raise ValueError("strict mode not supported")

        def convert(k: str, v: Any) -> Any:
            if k in self.dataclass.__annotations__:
                k_type = self.dataclass.__annotations__[k]
                if DataClassMeta.is_metaclass(k_type) and not isinstance(
                    v, k_type
                ):
                    return self.load(k_type, v, strict)
            return v

        return self.dataclass(**{k: convert(k, v) for k, v in data.items()})


class DataClassLoadProtocol(Protocol):
    """Add loader to `DataClass` family.

    For proper resolution of embedded fields of `DataClass` type.
    Can be validating or not. Validating loaders may or may not support strict
    and loose modes, ie strict type compliance or implicit conversion if
    possible.

    Default loader is `DataClassLoader.load`
    """

    _loader: ClassVar[Callable[[type[Self], Data, bool], Self]] = (
        DataClassLoader.load  # type: ignore[assignment]
    )
    """Class attribute, actual loader function

        Parameters:
        cls (type(DataClass)):  Load into this class spec
        data (dict):
        strict (bool):
            Load in strict mode, ie no implicit type conversion, optional
    """

    @classmethod
    def _load(
        cls, defaults: Data = {}, strict: bool = False, /, **kwargs: Data
    ) -> Self:
        """Load data into this class

        Classmethod.
        `defaults` is a convenience mechanism, so you can load either a
        dict or with kwargs, or both. See `DataClassMeta`.

        Parameters:
            defaults (dict): Data to load, overriden by kwargs

        Returns:
            Self: Loaded class instance
        """

        data = {**defaults, **kwargs}

        return cls._loader(cls, data, strict)

    __pdoc__["DataClassLoadProtocol._load"] = True
    __pdoc__["DataClassLoadProtocol._loader"] = True


class DataClass(BaseDataClass, DataClassLoadProtocol):
    """Base dataclass with `DataClassLoadProtocol`."""


class DataClassFrozen(DataClass, dataclass_params={"frozen": True}):
    """DataClass, frozen version."""
