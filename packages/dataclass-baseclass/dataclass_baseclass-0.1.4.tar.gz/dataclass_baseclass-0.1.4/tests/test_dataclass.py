# mypy: disable-error-code="call-arg,attr-defined"

from pytest import raises

from collections.abc import Iterable
from dataclasses import FrozenInstanceError
from enum import StrEnum, auto
from typing import ClassVar, Protocol

from dataclass_baseclass import (
    BaseDataClass,
    BaseDataClassFrozen,
    Data,
    DataClass,
)

from .conftest import DataClassTestFactory, ToStr


class P(Protocol):
    c_lst: ClassVar[list[str]] = ["Something"]
    _c_lst: ClassVar[list[str]] = ["Something"]

    s: str
    _s: str = "S"

    def gimme_s(self) -> str:
        return self.s


def test_mutable_class_vars() -> None:
    class WithClassVars(DataClass, P):
        c_d: ClassVar[dict[str, str]] = {"s": "Something"}

    class C(WithClassVars):
        c_t: ClassVar[tuple[str, str]] = ("s", "Something")
        c_s: ClassVar[set[str]] = {"Something"}

    wcv = C(s="S")  # type: ignore[abstract]
    assert wcv.c_lst == ["Something"]
    assert wcv.c_d == {"s": "Something"}
    assert wcv.c_t == ("s", "Something")
    assert wcv.c_s == {"Something"}
    assert wcv.s == "S"


def test_wrong_params() -> None:
    with raises(
        TypeError,
        match=r"dataclass\(\) got an unexpected keyword argument 'something'",
    ):

        class UnknownArg(
            DataClass, dataclass_params={"something": "whatever"}
        ):
            pass

    with raises(AssertionError, match=r"kw_only"):

        class KWOnly(DataClass, dataclass_params={"kw_only": False}):
            pass


def test_load_interface(dc_test_factory: DataClassTestFactory) -> None:
    _dc, loader = dc_test_factory()

    with raises(
        ValueError,
        match=r"strict mode not supported",
    ):
        loader(strict=True)


def test_dataclass(
    dc_test_factory: DataClassTestFactory,
    test_data: Data,
    str_test_data: ToStr,
) -> None:
    dc, loader = dc_test_factory((P,))

    with raises(
        TypeError,
        match=r"C.__init__\(\) missing 1 required keyword-only argument:",
    ):
        e = loader()

    c_data = {**test_data["c"], **{"s": "Something"}}
    e = loader(c=c_data)
    assert e.gimme_s() == "what"
    assert e.d.gimme_s() == e.d.s
    assert e.c.gimme_s() == "Something"

    assert e._as_dict(public_only=False) == {
        "_s": e._s,
        "i": e.i,
        "s": e.s,
        "x": e.x,
        "ls": e.ls,
        "t": e.t,
        "game": e.game,
        "dct": e.dct,
        "c": {"_s": e.c._s, "i": e.c.i, "s": e.c.s},
        "d": {"_s": e.d._s, "i": e.d.i, "s": e.d.s},
    }
    assert e._as_dict() == {
        "i": e.i,
        "s": e.s,
        "x": e.x,
        "ls": e.ls,
        "t": e.t,
        "game": e.game,
        "dct": e.dct,
        "c": {"i": e.c.i, "s": e.c.s},
        "d": {"i": e.d.i, "s": e.d.s},
    }

    with raises(
        TypeError,
        match=r"__init__\(\) got an unexpected keyword argument 'unexpected_attr'",
    ):
        dc(i=1, unexpected_attr=True)

    data = str_test_data()
    e = dc(**data)
    assert e.gimme_s() == "what"
    assert type(e.c) is dict
    assert e._as_dict() == dict(e)


def test_dataclass_mutable(dc_test_factory: DataClassTestFactory) -> None:
    _dc, loader = dc_test_factory()

    e = loader()

    e.i = 12

    e_ro = e._frozen_copy()
    assert e_ro._as_dict() == e._as_dict()

    with raises(FrozenInstanceError, match=r"cannot assign to field"):
        e_ro.i = 2


def test_dataclass_frozen(dc_test_factory: DataClassTestFactory) -> None:
    _dc, loader = dc_test_factory(frozen=True)

    e = loader()

    with raises(FrozenInstanceError, match=r"cannot assign to field"):
        e.i = 12

    assert e.__class__._frozen_class() is e.__class__
    e_ro = e._frozen_copy()
    assert e_ro is e


def test_frozen_mix() -> None:
    class C(BaseDataClass):
        s: str = "Something"

    class CF(BaseDataClassFrozen, C):
        pass

    cf = CF()
    with raises(FrozenInstanceError, match=r"cannot assign to field"):
        cf.s = ""

    class CUF(BaseDataClass, CF):  # type: ignore[misc,metaclass]
        pass

    cuf = CUF()
    with raises(FrozenInstanceError, match=r"cannot assign to field"):
        cuf.s = ""

    class CRUF(CUF, dataclass_params={"frozen": False}):
        pass

    cruf = CRUF()
    cruf.s = ""
    assert cruf.s == ""

    class D(BaseDataClass):
        f: CF

    assert not D._frozen


def test_replace() -> None:
    class C(DataClass):
        s: str = "Something"

    c = C()
    with raises(
        TypeError,
        match=r"C.__init__\(\) got an unexpected keyword argument 'i'",
    ):
        c._replace(i=1)

    cr = c._replace(s="")
    assert cr.s == ""
    assert cr is not c


def test_protocol() -> None:
    class PP(P, Protocol):
        pass

    class PPP(PP, Protocol):
        pass

    class C(DataClass, PPP):
        pass

    assert set(f.name for f in C._fields()) == {"s"}

    class PPNP(PP):
        pass

    class D(DataClass, PPNP):
        pass

    assert set(f.name for f in D._fields()) == {"s"}

    class NP(P):
        pass

    class NPNP(NP):
        pass

    class E(DataClass, NPNP):
        pass

    assert set(f.name for f in D._fields()) == {"s"}


def test_default() -> None:
    class E(StrEnum):
        S = auto()

    class Q(Protocol):
        iter: Iterable[E] = []

    class C(DataClass, Q):
        pass

    c = C()
    assert list(c.iter) == []


def test_property_override() -> None:
    class C(DataClass):
        s: str

    class P(Protocol):
        p: str

    class CP(C, P):
        @property  # type: ignore[misc]
        def s(self) -> str:  # type: ignore[override]
            return "S"

        @property
        def p(self) -> str:  # type: ignore[override]
            return "P"

    cp = CP()
    assert cp.s == "S"
    assert cp.p == "P"

    assert isinstance(cp, C), CP.__bases__
