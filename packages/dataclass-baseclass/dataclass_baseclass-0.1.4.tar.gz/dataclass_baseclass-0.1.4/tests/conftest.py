# mypy: disable-error-code=misc

from pytest import fixture

from typing import Any, Callable, Self, TypeAlias

from dataclass_baseclass import (
    _PARAMS,
    Data,
    DataClass,
    DataClassFrozen,
    DataClassT,
)

DataClassTestDef = tuple[
    type[DataClassT],
    Callable[[type[DataClassT], Data, bool, ...], DataClassT],
]
DataClassTestFactory = Callable[[tuple[type, ...], bool], DataClassTestDef]
ToStr = Callable[[Data], Data]


def to_str(data: Data) -> Data:
    return {
        k: to_str(v) if type(v) is dict else str(v) for k, v in data.items()
    }


@fixture(scope="session")
def test_data() -> Data:
    return dict(i=1, c={"i": 2}, d={"i": 3, "s": "hey"})


@fixture(scope="session")
def str_test_data(test_data: Data) -> ToStr:
    def to_str_data(data: Data = test_data) -> Data:
        return to_str(data)

    return to_str_data


@fixture(scope="session")
def dc_test_factory(test_data: Data) -> DataClassTestFactory:
    def dc_test(
        protocols: tuple[type[DataClass], ...] = tuple(), frozen: bool = False
    ) -> DataClassTestDef:
        Base: TypeAlias = DataClass
        if frozen:
            Base = DataClassFrozen

        class C(Base, *protocols):
            i: int

            @classmethod
            def _cm(cls) -> type[Self]:
                return cls

            def _im(self) -> bool:
                return True

        class D(C):
            s: str = "what"

        class X:
            x: float = 1.1

            def __init__(self, x: float) -> None:
                raise Exception("We should not be here")

        class E(D, X):
            c: C
            d: D
            ls: list[str] = ["woah"]
            t: tuple[str, ...] = ("meh",)
            game: set[str] = {"match"}
            dct: dict[str, str] = DataClass._field(default={"ho": "hum"})

        assert E._cm() is E
        assert E._frozen is frozen, (
            f"{E._frozen} {getattr(Base, _PARAMS).frozen}"
        )
        for f in E._fields():
            assert f.kw_only is True, str(f)

            if f.name == "x":
                assert f.default_value() == 1.1
            if f.name == "ls":
                assert f.default_value() == ["woah"]
            if f.name == "dct":
                assert f.default_value() == {"ho": "hum"}

        def load(
            dc: type[E] = E,
            defaults: Data = test_data,
            strict: bool = False,
            **kwargs: Any,
        ) -> E:
            e = dc._load(defaults, strict, **kwargs)
            assert e._im()
            assert e.i == 1
            assert e.s == "what"
            assert e.x == 1.1
            assert e.c.i == 2
            assert e.d.i == 3
            assert e.d.s == "hey"

            return e

        return (E, load)  # type: ignore[return-value]

    return dc_test
