# mypy: disable-error-code="call-arg,misc"

from pytest import mark, raises, fixture

from typing import TypeAlias, cast
import typedload

from dataclass_baseclass import Data, DataClass, DataClassT

from .conftest import DataClassTestDef, DataClassTestFactory, ToStr


@fixture
def typedload_test_factory(
    dc_test_factory: DataClassTestFactory,
) -> DataClassTestFactory:
    def dc_test(
        protocols: tuple[type[DataClass], ...] = tuple(), frozen: bool = False
    ) -> DataClassTestDef:
        dc, loader = dc_test_factory(protocols, frozen=frozen)

        class F(cast(TypeAlias, dc)):
            _loader = typedload_loader

        def load(
            dc: type[F] = F,
            *args,
            **kwargs,
        ) -> F:
            return loader(dc, *args, **kwargs)

        return (F, load)

    return dc_test


def typedload_loader(
    dc: type[DataClassT], data: Data, strict: bool = False
) -> DataClassT:
    return typedload.load(data, dc, basiccast=(not strict))


@mark.parametrize("strict", [False, True])
def test_apischema_deserialize_loose(
    typedload_test_factory: DataClassTestFactory, strict: bool
) -> None:
    dc, loader = typedload_test_factory()

    loader(strict=strict)


def test_apischema_deserialize_strict(
    typedload_test_factory: DataClassTestFactory, str_test_data: ToStr
) -> None:
    dc, loader = typedload_test_factory()
    data = str_test_data()

    with raises(ValueError):
        loader(strict=True, **data)

    loader(strict=False, **data)
