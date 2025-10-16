from typing import Any

from panda_pytest_assertions.assert_object import expectation_to_yaml


def test(complex_expectation: Any, complex_expectation_yaml_string: str):
    assert expectation_to_yaml(complex_expectation) == complex_expectation_yaml_string
