# mypy: disable-error-code="call-arg,misc"

from pytest import fixture

from dataclasses_json import DataClassJsonMixin
from dataclasses_json.core import _decode_dataclass
from typing import TypeAlias, cast
import json

from dataclass_baseclass import Data, DataClass, DataClassT

from .conftest import DataClassTestDef, DataClassTestFactory, ToStr


@fixture
def dataclasses_json_test_factory(
    dc_test_factory: DataClassTestFactory,
) -> DataClassTestFactory:
    def dc_test(
        protocols: tuple[type[DataClass], ...] = tuple(), frozen: bool = False
    ) -> DataClassTestDef:
        dc, loader = dc_test_factory(protocols, frozen=frozen)

        class F(cast(TypeAlias, dc)):
            _loader = dataclasses_json_loader

        def load(
            dc: type[F] = F,
            *args,
            **kwargs,
        ) -> F:
            return loader(dc, *args, **kwargs)

        return (F, load)

    return dc_test


def dataclasses_json_loader(
    dc: type[DataClassT], data: Data, strict: bool = False
) -> DataClassT:
    if strict is True:
        raise ValueError("strict mode not supported")

    return _decode_dataclass(dc, data, False)


def test_dataclasses_json_mixin() -> None:
    class DCJ(DataClass, DataClassJsonMixin):
        pass

    class C(DCJ):
        s: str

    data = {"s": "I am a string"}
    c = C.from_json(json.dumps(data))
    c_data = json.loads(c.to_json())
    # Unfortunately we turn dataclass_json_config into an attribute...
    c_data.pop("dataclass_json_config", None)
    assert c_data == data


def test_dataclasses_json_deserialize(
    dataclasses_json_test_factory: DataClassTestFactory,
) -> None:
    dc, loader = dataclasses_json_test_factory()

    loader()


def test_dataclasses_json_deserialize_string(
    dataclasses_json_test_factory: DataClassTestFactory, str_test_data: ToStr
) -> None:
    dc, loader = dataclasses_json_test_factory()
    data = str_test_data()

    loader(**data)
