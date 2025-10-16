from enum import auto, Enum
from typing import Any

import pytest
from munch import Munch

from panda_pytest_assertions.assert_object import (
    assert_object,
    Is,
    IsType,
    MappingSubset,
    ObjectAttributes,
    Stringified,
    Unordered,
    with_type,
    WithType,
)


@pytest.mark.parametrize(
    ['object_', 'expectation', 'message_start'],
    [
        # primitives
        (1, 3, 'Object assertion failed. assert 3 == 1'),
        ('xyz', 'abc', "Object assertion failed. assert 'abc' == 'xyz'"),
        # is
        ('xyz', Is('abc'), "Object assertion failed. assert 'abc' is 'xyz'"),
        ({}, Is({}), 'Object assertion failed. assert {} is {}'),
        # mapping
        (
            {'abc': 1, 'xyz': 2},
            {'abc': 1, 'xyz': 3},
            'Object assertion failed. Mapping value for key "xyz" is invalid. assert 3 == 2',
        ),
        (
            {'abc': 1, 'xyz': 2},
            {'abc': 1},
            'Object assertion failed. Object keys must be equal to expectation keys.',
        ),
        (
            {'abc': 1},
            {'abc': 1, 'xyz': 3},
            'Object assertion failed. Object keys must be equal to expectation keys.',
        ),
        ('abc', {'abc': 1}, "Object assertion failed. Object must be a mapping. Got: <class 'str'>."),
        # mapping subset
        (
            {'abc': 1, 'xyz': 2},
            MappingSubset({'abc': 1, 'xyz': 3}),
            'Object assertion failed. Mapping value for key "xyz" is invalid. assert 3 == 2',
        ),
        (
            {'abc': 1},
            MappingSubset({'abc': 1, 'xyz': 3}),
            'Object assertion failed. Object keys must be a superset of expectation keys.',
        ),
        (
            'abc',
            MappingSubset({'abc': 1}),
            "Object assertion failed. Object must be a mapping. Got: <class 'str'>.",
        ),
        # object attributes
        (
            Munch(abc=1, xyz=2),
            ObjectAttributes({'abc': 1, 'xyz': 3}),
            'Object assertion failed. Objects attribute "xyz" has invalid value. assert 3 == 2',
        ),
        (
            Munch(abc=1),
            ObjectAttributes({'abc': 1, 'xyz': 3}),
            'Object assertion failed. Objects is missing attribute "xyz".',
        ),
        # ordered elements
        ([1, 2], [1, 3], 'Object assertion failed. Element with index [1] has invalid value. assert 3 == 2'),
        (
            [1, 2],
            [1],
            (
                'Object assertion failed. Length of an object (2) does not equal to the number of '
                'expectations (1).',
            ),
        ),
        (
            [1],
            [1, 3],
            (
                'Object assertion failed. Length of an object (1) does not equal to the number of '
                'expectations (2).',
            ),
        ),
        (123, [1, 3], "Object assertion failed. Object must be iterable. Got: <class 'int'>."),
        # stringified
        (123, Stringified('12'), 'Object assertion failed. Stringified value of an object is invalid.'),
        # unordered elements
        (
            [1, 2],
            Unordered([1, 3]),
            ('Object assertion failed. None of the elements of a collection has fulfilled expectation "3"',),
        ),
        (
            [1, 2],
            Unordered([1]),
            (
                'Object assertion failed. Length of an object (2) does not equal to the number of '
                'expectations (1)'
            ),
        ),
        (
            [1],
            Unordered([1, 3]),
            (
                'Object assertion failed. Length of an object (1) does not equal to the number of '
                'expectations (2)'
            ),
        ),
        # with type
        (1, WithType(2, 'int', 'builtins'), 'Object assertion failed. Object is invalid. assert 2 == 1'),
        (
            1,
            WithType(1, 'str', 'builtins'),
            (
                'Object assertion failed. Object type ("<class \'int\'>") has invalid name. '
                'Expected "str", got "int".'
            ),
        ),
        (
            1,
            WithType(1, 'int', 'munch'),
            (
                'Object assertion failed. Object type ("<class \'int\'>") is from invalid module. '
                'Expected "munch", got "builtins".'
            ),
        ),
        # is type
        (
            1,
            IsType('str', 'builtins'),
            (
                'Object assertion failed. Object type ("<class \'int\'>") has invalid name. '
                'Expected "str", got "int".'
            ),
        ),
        (
            1,
            IsType('int', 'munch'),
            (
                'Object assertion failed. Object type ("<class \'int\'>") is from invalid module. '
                'Expected "munch", got "builtins".'
            ),
        ),
    ],
)
def test_messages(object_: Any, expectation: Any, message_start: str):
    with pytest.raises(AssertionError) as exc_info:
        assert_object(expectation, object_)
    assert str(exc_info.value).startswith(message_start)


def test_complex_messages():
    class Language(Enum):
        PL = auto()
        EN = auto()
        IT = auto()

    object_: Munch[str, Any] = Munch(
        books=[
            Munch(
                name='Good Omens',
                authors=['Terry Pratchett', 'Neil Gaiman'],
                language=Language.EN,
                translations={Language.PL: True},
            ),
        ],
    )
    expectation = with_type('Munch', 'munch')(
        ObjectAttributes(
            {
                'books': Unordered(
                    [
                        ObjectAttributes(
                            {
                                'authors': ['Neil Gaiman', 'Terry Pratchett'],
                            },
                        ),
                    ],
                ),
            },
        ),
    )
    message_start = (
        'Object assertion failed. Object is invalid. Objects attribute "books" has invalid value. '
        'None of the elements of a collection has fulfilled expectation '
        "\"ObjectAttributes({'authors': ['Neil Gaiman', 'Terry Pratchett']})\""
    )

    with pytest.raises(AssertionError) as exc_info:
        assert_object(expectation, object_)
    assert str(exc_info.value).startswith(message_start)
