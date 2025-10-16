import pytest
from yaml.constructor import ConstructorError

from panda_pytest_assertions.assert_object import expectation_from_yaml, expectation_to_yaml


def test(complex_expectation_yaml_string: str):
    generated_expectation = expectation_from_yaml(complex_expectation_yaml_string)
    assert expectation_to_yaml(generated_expectation) == complex_expectation_yaml_string


@pytest.mark.parametrize(
    'input_yaml',
    [
        (
            """\
!MappingSubset
- 1
- 2
"""
        ),
        (
            """\
!ObjectAttributes
- 1
- 2
"""
        ),
        (
            """\
!ObjectAttributes
1: 2
"""
        ),
        (
            """\
!Stringified
- 1
- 2
"""
        ),
        (
            """\
!Unordered
1: 2
"""
        ),
        (
            """\
!WithType
- 1
- 2
"""
        ),
        (
            """\
!WithType
expected_type_name: abc
expected_type_module: abc
"""
        ),
        (
            """\
!WithType
incorrect: 1
expectation: 2
expected_type_name: abc
expected_type_module: abc
"""
        ),
        (
            """\
!WithType
expectation: 2
expected_type_name: 1
expected_type_module: abc
"""
        ),
        (
            """\
!WithType
expectation: 2
expected_type_name: abc
expected_type_module: 1
"""
        ),
        (
            """\
!IsType
- 1
- 2
"""
        ),
        (
            """\
!IsType
expected_type_module: abc
"""
        ),
        (
            """\
!IsType
expected_type_name: abc
"""
        ),
        (
            """\
!IsType
incorrect: 1
expected_type_name: abc
expected_type_module: abc
"""
        ),
        (
            """\
!IsType
expected_type_name: 1
expected_type_module: abc
"""
        ),
        (
            """\
!IsType
expected_type_name: abc
expected_type_module: 1
"""
        ),
    ],
)
def test_exceptions(input_yaml: str):
    with pytest.raises(ConstructorError):
        expectation_from_yaml(input_yaml)
