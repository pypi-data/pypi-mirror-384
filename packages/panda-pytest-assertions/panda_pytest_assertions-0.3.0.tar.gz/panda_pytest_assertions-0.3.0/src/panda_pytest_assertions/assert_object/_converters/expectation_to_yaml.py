from collections.abc import Callable
from enum import Enum
from typing import Any, TypeVar

import yaml

from panda_pytest_assertions.assert_object._expectation_modificators import (
    IsType,
    MappingSubset,
    ObjectAttributes,
    Stringified,
    Unordered,
    with_type,
    WithType,
)


def expectation_to_yaml(expectation: Any) -> str:  # noqa: ANN401
    """
    Serialize expectation to YAML format.

    :param expectation: expectation to be dumped to YAML
    :return: YAML string representing expectation
    """
    return yaml.dump(expectation, Dumper=ExpectationYamlDumper, width=10000)


_T = TypeVar('_T')

_Representer = Callable[['ExpectationYamlDumper', _T], yaml.Node]


class ExpectationYamlDumper(yaml.SafeDumper):
    @classmethod
    def add_repr(
        cls,
        data_type: type[_T],
        *,
        is_multi: bool = False,
    ) -> Callable[[_Representer[_T]], _Representer[_T]]:
        def _wrapper(representer: _Representer[_T]) -> _Representer[_T]:
            if is_multi:
                ExpectationYamlDumper.add_multi_representer(data_type, representer)
            else:
                ExpectationYamlDumper.add_representer(data_type, representer)
            return representer

        return _wrapper


@ExpectationYamlDumper.add_repr(MappingSubset)
def _(dumper: ExpectationYamlDumper, data: MappingSubset) -> yaml.MappingNode:
    return dumper.represent_mapping('!MappingSubset', data.items_expectations)


@ExpectationYamlDumper.add_repr(ObjectAttributes)
def _(dumper: ExpectationYamlDumper, data: ObjectAttributes) -> yaml.MappingNode:
    return dumper.represent_mapping('!ObjectAttributes', data.attributes_expectations)


@ExpectationYamlDumper.add_repr(Stringified)
def _(dumper: ExpectationYamlDumper, data: Stringified) -> yaml.ScalarNode:
    return dumper.represent_scalar('!Stringified', data.stringified_value)


@ExpectationYamlDumper.add_repr(Unordered)
def _(dumper: ExpectationYamlDumper, data: Unordered) -> yaml.SequenceNode:
    return dumper.represent_sequence('!Unordered', data.elements_expectations)


@ExpectationYamlDumper.add_repr(WithType)
def _with_type_representer(dumper: ExpectationYamlDumper, data: WithType) -> yaml.MappingNode:
    return dumper.represent_mapping('!WithType', data.__dict__)


@ExpectationYamlDumper.add_repr(IsType)
def _(dumper: ExpectationYamlDumper, data: IsType) -> yaml.MappingNode:
    return dumper.represent_mapping('!IsType', data.__dict__)


@ExpectationYamlDumper.add_repr(Enum, is_multi=True)
def _(dumper: ExpectationYamlDumper, data: Enum) -> yaml.Node:
    expectation = with_type(type(data))(Stringified(str(data)))
    return _with_type_representer(dumper, expectation)
