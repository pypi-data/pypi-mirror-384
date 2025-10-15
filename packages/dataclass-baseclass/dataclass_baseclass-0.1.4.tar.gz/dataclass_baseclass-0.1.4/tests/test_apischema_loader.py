# mypy: disable-error-code="call-arg,misc"

from pytest import mark, raises, fixture

from apischema import deserialize, fields, validation
from typing import TypeAlias, cast

from dataclass_baseclass import Data, DataClass, DataClassT

from .conftest import DataClassTestDef, DataClassTestFactory, ToStr


@fixture
def apischema_test_factory(
    dc_test_factory: DataClassTestFactory,
) -> DataClassTestFactory:
    def dc_test(
        protocols: tuple[type[DataClass], ...] = tuple(), frozen: bool = False
    ) -> DataClassTestDef:
        dc, loader = dc_test_factory(protocols, frozen=frozen)

        @fields.with_fields_set
        class F(cast(TypeAlias, dc)):
            _loader = apischema_loader

        def load(
            dc: type[F] = F,
            *args,
            **kwargs,
        ) -> F:
            return loader(dc, *args, **kwargs)

        return (F, load)

    return dc_test


def apischema_loader(
    dc: type[DataClassT], data: Data, strict: bool = False
) -> DataClassT:
    return deserialize(dc, data, coerce=(not strict))


@mark.parametrize("strict", [False, True])
def test_apischema_deserialize_loose(
    apischema_test_factory: DataClassTestFactory, strict: bool
) -> None:
    dc, loader = apischema_test_factory()

    f = loader(strict=strict)
    assert fields.fields_set(f) == {
        "i",
        "c",
        "d",
    }  # F.s not set explicitly


def test_apischema_deserialize_strict(
    apischema_test_factory: DataClassTestFactory, str_test_data: ToStr
) -> None:
    dc, loader = apischema_test_factory()
    data = str_test_data()

    with raises(validation.errors.ValidationError):
        loader(strict=True, **data)

    loader(strict=False, **data)
