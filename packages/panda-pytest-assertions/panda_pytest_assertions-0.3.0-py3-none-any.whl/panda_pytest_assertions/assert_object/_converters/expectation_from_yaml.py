from collections.abc import Callable
from typing import Any, cast, TypeVar

import yaml
from yaml.constructor import ConstructorError

from panda_pytest_assertions.assert_object._expectation_modificators import (
    IsType,
    MappingSubset,
    ObjectAttributes,
    Stringified,
    Unordered,
    WithType,
)


def expectation_from_yaml(yaml_string: str) -> Any:  # noqa: ANN401
    """
    Serialize expectation to YAML format.

    :param yaml_string: YAML string to create expectation from
    :return: YAML string representing expectation
    """
    return yaml.load(yaml_string, Loader=ExpectationYamlLoader)  # noqa: S506


_T = TypeVar('_T')
_Constructor = Callable[['ExpectationYamlLoader', yaml.Node], _T]


class ExpectationYamlLoader(yaml.SafeLoader):
    @classmethod
    def add_construct(cls, tag: str) -> Callable[[_Constructor[_T]], _Constructor[_T]]:
        def _wrapper(constructor: _Constructor[_T]) -> _Constructor[_T]:
            ExpectationYamlLoader.add_constructor(tag, constructor)
            return constructor

        return _wrapper


@ExpectationYamlLoader.add_construct('!MappingSubset')
def _(loader: ExpectationYamlLoader, node: yaml.Node) -> MappingSubset:
    if not isinstance(node, yaml.MappingNode):
        raise ConstructorError(
            problem=f'expected a mapping node, but found {type(node)}',
            problem_mark=node.start_mark,
        )
    return MappingSubset(loader.construct_mapping(node))


@ExpectationYamlLoader.add_construct('!ObjectAttributes')
def _(loader: ExpectationYamlLoader, node: yaml.Node) -> ObjectAttributes:
    if not isinstance(node, yaml.MappingNode):
        raise ConstructorError(
            problem=f'expected a mapping node, but found {type(node)}',
            problem_mark=node.start_mark,
        )
    node_data = loader.construct_mapping(node)
    if any(not isinstance(key, str) for key in node_data):
        raise ConstructorError(
            problem='all keys in ObjectAttributes must be strings',
            problem_mark=node.start_mark,
        )
    return ObjectAttributes(cast('dict[str, Any]', node_data))


@ExpectationYamlLoader.add_construct('!Stringified')
def _(loader: ExpectationYamlLoader, node: yaml.Node) -> Stringified:
    if not isinstance(node, yaml.ScalarNode):
        raise ConstructorError(
            problem=f'expected a scalar node, but found {type(node)}',
            problem_mark=node.start_mark,
        )
    # I was not able to produce yaml that would return something else than a string
    node_data = loader.construct_scalar(node)
    return Stringified(node_data)


@ExpectationYamlLoader.add_construct('!Unordered')
def _(loader: ExpectationYamlLoader, node: yaml.Node) -> Unordered:
    if not isinstance(node, yaml.SequenceNode):
        raise ConstructorError(
            problem=f'expected a sequence node, but found {type(node)}',
            problem_mark=node.start_mark,
        )
    return Unordered(loader.construct_sequence(node))


_WITH_TYPE_KEYS = {'expectation', 'expected_type_name', 'expected_type_module'}


@ExpectationYamlLoader.add_construct('!WithType')
def _(loader: ExpectationYamlLoader, node: yaml.Node) -> WithType:
    if not isinstance(node, yaml.MappingNode):
        raise ConstructorError(
            problem=f'expected a mapping node, but found {type(node)}',
            problem_mark=node.start_mark,
        )
    node_data = loader.construct_mapping(node)
    if node_data.keys() != _WITH_TYPE_KEYS:
        raise ConstructorError(
            problem=f'WithType keys must be {_WITH_TYPE_KEYS}',
            problem_mark=node.start_mark,
        )
    if not isinstance(expected_type_name := node_data['expected_type_name'], str):
        raise ConstructorError(
            problem='value of WithType "expected_type_name" must be a string',
            problem_mark=node.start_mark,
        )
    if not isinstance(expected_type_module := node_data['expected_type_module'], str | None):
        raise ConstructorError(
            problem='value of WithType "expected_type_module" must be a string or None',
            problem_mark=node.start_mark,
        )
    return WithType(node_data['expectation'], expected_type_name, expected_type_module)


_IS_TYPE_KEYS = {'expected_type_name', 'expected_type_module'}


@ExpectationYamlLoader.add_construct('!IsType')
def _(loader: ExpectationYamlLoader, node: yaml.Node) -> IsType:
    if not isinstance(node, yaml.MappingNode):
        raise ConstructorError(
            problem=f'expected a mapping node, but found {type(node)}',
            problem_mark=node.start_mark,
        )
    node_data = loader.construct_mapping(node)
    if node_data.keys() != _IS_TYPE_KEYS:
        raise ConstructorError(
            problem=f'IsType keys must be {_IS_TYPE_KEYS}',
            problem_mark=node.start_mark,
        )
    if not isinstance(expected_type_name := node_data['expected_type_name'], str):
        raise ConstructorError(
            problem='value of IsType "expected_type_name" must be a string',
            problem_mark=node.start_mark,
        )
    if not isinstance(expected_type_module := node_data['expected_type_module'], str | None):
        raise ConstructorError(
            problem='value of IsType "expected_type_module" must be a string or None',
            problem_mark=node.start_mark,
        )
    return IsType(expected_type_name, expected_type_module)
