from datetime import datetime
from enum import auto, Enum
from typing import Any

import pytest
from munch import Munch

from panda_pytest_assertions.assert_object import (
    IsType,
    MappingSubset,
    ObjectAttributes,
    Stringified,
    Unordered,
    WithType,
)
from panda_pytest_assertions.assert_object.generators import (
    EqualityDef,
    generate_expectation,
    IsTypeDef,
    MappingDef,
    MappingSubsetDef,
    ObjectAttributesDef,
    OfTypeDef,
    StringifiedDef,
    uniform_ordered_def,
    UniformMappingDef,
    UniformMappingSubsetDef,
    UniformOrderedDef,
    UniformUnorderedDef,
    UnionDef,
    with_type_def,
    WithTypeDef,
)


def test_complex():
    class Language(Enum):
        PL = auto()
        EN = auto()
        IT = auto()

    object_: Munch[str, Any] = Munch(
        list_author='Jan Kowalski',
        created_at=datetime(2020, 6, 8, 12, 30),  # noqa: DTZ001
        books=[
            Munch(
                name='Hobbit',
                authors=['J. R. R. Tolkien'],
                language=Language.EN,
                translations={Language.PL: True, Language.IT: True},
            ),
            Munch(
                name='Good Omens',
                authors=['Terry Pratchett', 'Neil Gaiman'],
                language=Language.EN,
                translations={Language.PL: True},
            ),
            Munch(
                name='Dokąd nocą tupta jeż',
                authors=[],
                language=Language.PL,
            ),
            Munch(
                name='Otworzyć po mojej śmierci',
                authors=['Abelard Giza'],
                language=Language.PL,
                translations={Language.EN: False},
            ),
        ],
        movies=(
            {
                'english_title': 'Finding Neverland',
                'polish_title': 'Marzyciel',
                'prizes': {
                    'Oscars': 1,
                    "Critics' Choice": 2,
                },
            },
            {
                'english_title': 'Maestro',
                'prizes': {
                    'Satelites': 3,
                    'IATSE Local 706': 2,
                },
            },
            {
                'polish_title': 'Dzieci kukurydzy',
                'prizes': {},
            },
            {
                'polish_title': 'Czarna woda',
                'prizes': {},
            },
        ),
        songs=[],
    )
    definition = with_type_def(include_module=True)(
        ObjectAttributesDef(
            {
                'created_at': StringifiedDef,
                'books': UniformUnorderedDef(
                    UnionDef(
                        ObjectAttributesDef(
                            {
                                'name': EqualityDef,
                                'authors': StringifiedDef,
                                'language': EqualityDef,
                                'translation': UniformMappingSubsetDef(
                                    EqualityDef,
                                    with_type_def(include_module=False)(EqualityDef),
                                ),
                            },
                        ),
                        ObjectAttributesDef(
                            {
                                'name': EqualityDef,
                                'authors': StringifiedDef,
                                'language': EqualityDef,
                            },
                        ),
                    ),
                ),
                'movies': uniform_ordered_def(expectation_type=tuple)(
                    UnionDef(
                        MappingDef(
                            EqualityDef,
                            {
                                'prizes': UniformUnorderedDef(EqualityDef),
                                'polish_title': EqualityDef,
                                'english_title': EqualityDef,
                            },
                        ),
                        MappingDef(
                            EqualityDef,
                            {
                                'prizes': UniformUnorderedDef(EqualityDef),
                                'english_title': EqualityDef,
                            },
                        ),
                        MappingDef(
                            EqualityDef,
                            {
                                'prizes': UniformUnorderedDef(EqualityDef),
                                'polish_title': EqualityDef,
                            },
                        ),
                    ),
                ),
                'songs': IsTypeDef(),
            },
        ),
    )
    generate_expectation(object_, definition)


@pytest.mark.parametrize(
    'object_',
    [
        True,
        'abc',
        123,
        123.0,
        123.321,
        None,
    ],
)
@pytest.mark.parametrize('definition', [EqualityDef, EqualityDef()])
def test_equality(object_: Any, definition: Any):
    assert generate_expectation(object_, definition) is object_


def test_mapping_subset():
    definition = MappingSubsetDef(
        EqualityDef,
        {
            'attr_1': EqualityDef,
            'attr_2': StringifiedDef,
        },
    )
    object_ = {
        'attr_1': 'value_1',
        'attr_2': 'value_2',
        'attr_3': 'value_3',
    }
    expectation = generate_expectation(object_, definition)

    assert isinstance(expectation, MappingSubset)
    assert expectation.items_expectations.keys() == {'attr_1', 'attr_2'}
    assert expectation.items_expectations['attr_1'] == 'value_1'
    assert isinstance(expectation.items_expectations['attr_2'], Stringified)
    assert expectation.items_expectations['attr_2'].stringified_value == 'value_2'


def test_equality_key_mapping():
    definition = {
        'attr_1': EqualityDef,
        'attr_2': StringifiedDef,
    }
    object_ = {
        'attr_1': 'value_1',
        'attr_2': 'value_2',
    }
    expectation = generate_expectation(object_, definition)

    assert isinstance(expectation, dict)
    assert expectation.keys() == {'attr_1', 'attr_2'}
    assert expectation['attr_1'] == 'value_1'
    assert isinstance(expectation['attr_2'], Stringified)
    assert expectation['attr_2'].stringified_value == 'value_2'


def test_mapping():
    definition = MappingDef(
        EqualityDef,
        {
            'attr_1': EqualityDef,
            'attr_2': StringifiedDef,
        },
    )
    object_ = {
        'attr_1': 'value_1',
        'attr_2': 'value_2',
    }
    expectation = generate_expectation(object_, definition)

    assert isinstance(expectation, dict)
    assert expectation.keys() == {'attr_1', 'attr_2'}
    assert expectation['attr_1'] == 'value_1'
    assert isinstance(expectation['attr_2'], Stringified)
    assert expectation['attr_2'].stringified_value == 'value_2'


def test_object_attributes():
    definition = ObjectAttributesDef(
        {
            'attr_1': EqualityDef,
            'attr_2': StringifiedDef,
        },
    )
    object_: Munch[str, Any] = Munch(
        attr_1='value_1',
        attr_2='value_2',
        attr_3='value_3',
    )
    expectation = generate_expectation(object_, definition)

    assert isinstance(expectation, ObjectAttributes)
    assert expectation.attributes_expectations.keys() == {'attr_1', 'attr_2'}
    assert expectation.attributes_expectations['attr_1'] == 'value_1'
    assert isinstance(expectation.attributes_expectations['attr_2'], Stringified)
    assert expectation.attributes_expectations['attr_2'].stringified_value == 'value_2'


def test_of_type():
    definition = UnionDef(
        OfTypeDef(int, StringifiedDef),
        OfTypeDef(str, EqualityDef),
        OfTypeDef(None, EqualityDef),
    )

    expectation = generate_expectation(123, definition)
    assert isinstance(expectation, Stringified)
    assert expectation.stringified_value == '123'

    expectation = generate_expectation('abc', definition)
    assert expectation == 'abc'

    expectation = generate_expectation(None, definition)
    assert expectation is None


@pytest.mark.parametrize('expectation_type', [list, tuple])
def test_ordered(expectation_type: type[list[Any]] | type[tuple[Any, ...]]):
    definition = expectation_type((EqualityDef, StringifiedDef, EqualityDef))
    object_: Munch[str, Any] = Munch(
        attr_1='value_1',
        attr_2='value_2',
        attr_3='value_3',
    )
    expectation = generate_expectation(object_, definition)

    assert isinstance(expectation, expectation_type)
    assert len(expectation) == len(object_)
    assert expectation[0] == 'attr_1'
    assert isinstance(expectation[1], Stringified)
    assert expectation[1].stringified_value == 'attr_2'
    assert expectation[2] == 'attr_3'


@pytest.mark.parametrize(
    'object_',
    [
        True,
        'abc',
        123,
        123.0,
        123.321,
        None,
    ],
)
@pytest.mark.parametrize('definition', [StringifiedDef, StringifiedDef()])
def test_stringified(object_: Any, definition: Any):
    expectation = generate_expectation(object_, definition)

    assert isinstance(expectation, Stringified)
    assert expectation.stringified_value == str(object_)


def test_uniform_mapping_subset():
    definition = UniformMappingSubsetDef(EqualityDef, StringifiedDef)
    object_: Munch[str, Any] = Munch(
        attr_1='value_1',
        attr_2='value_2',
        attr_3='value_3',
    )
    expectation = generate_expectation(object_, definition)

    assert isinstance(expectation, MappingSubset)
    assert expectation.items_expectations.keys() == {'attr_1', 'attr_2', 'attr_3'}
    assert all(isinstance(value, Stringified) for value in expectation.items_expectations.values())
    assert expectation.items_expectations['attr_1'].stringified_value == 'value_1'
    assert expectation.items_expectations['attr_2'].stringified_value == 'value_2'
    assert expectation.items_expectations['attr_3'].stringified_value == 'value_3'


def test_uniform_mapping():
    definition = UniformMappingDef(EqualityDef, StringifiedDef)
    object_: Munch[str, Any] = Munch(
        attr_1='value_1',
        attr_2='value_2',
        attr_3='value_3',
    )
    expectation = generate_expectation(object_, definition)

    assert isinstance(expectation, dict)
    assert expectation.keys() == {'attr_1', 'attr_2', 'attr_3'}
    assert all(isinstance(value, Stringified) for value in expectation.values())
    assert expectation['attr_1'].stringified_value == 'value_1'
    assert expectation['attr_2'].stringified_value == 'value_2'
    assert expectation['attr_3'].stringified_value == 'value_3'


@pytest.mark.parametrize('expectation_type', [list, tuple])
def test_uniform_ordered(expectation_type: type[Any]):
    definition = UniformOrderedDef(StringifiedDef, expectation_type=expectation_type)
    object_: Munch[str, Any] = Munch(
        attr_1='value_1',
        attr_2='value_2',
        attr_3='value_3',
    )
    expectation = generate_expectation(object_, definition)

    assert isinstance(expectation, expectation_type)
    assert all(isinstance(element, Stringified) for element in expectation)
    assert [element.stringified_value for element in expectation] == ['attr_1', 'attr_2', 'attr_3']


def test_union():
    definition = UnionDef(
        MappingSubsetDef(EqualityDef, {'attr_42': EqualityDef}),
        ObjectAttributesDef({'attr_1': EqualityDef}),
        MappingSubsetDef(EqualityDef, {'attr_1': EqualityDef}),
    )
    object_: Munch[str, Any] = Munch(
        attr_1='value_1',
        attr_2='value_2',
        attr_3='value_3',
    )
    expectation = generate_expectation(object_, definition)

    assert isinstance(expectation, ObjectAttributes)
    assert expectation.attributes_expectations == {
        'attr_1': 'value_1',
    }


def test_unordered():
    definition = UniformUnorderedDef(StringifiedDef)
    object_: Munch[str, Any] = Munch(
        attr_1='value_1',
        attr_2='value_2',
        attr_3='value_3',
    )
    expectation = generate_expectation(object_, definition)

    assert isinstance(expectation, Unordered)
    assert all(isinstance(element, Stringified) for element in expectation.elements_expectations)
    assert [element.stringified_value for element in expectation.elements_expectations] == [
        'attr_1',
        'attr_2',
        'attr_3',
    ]


@pytest.mark.parametrize('include_module', [True, False])
def test_with_type(include_module: bool):
    definition = WithTypeDef(StringifiedDef, include_module=include_module)
    object_: Munch[str, Any] = Munch(
        attr_1='value_1',
        attr_2='value_2',
        attr_3='value_3',
    )
    expectation = generate_expectation(object_, definition)

    assert isinstance(expectation, WithType)
    assert isinstance(expectation.expectation, Stringified)
    assert expectation.expectation.stringified_value == str(object_)
    assert expectation.expected_type_name == 'Munch'
    assert expectation.expected_type_module == ('munch' if include_module else None)


@pytest.mark.parametrize('include_module', [True, False])
def test_is_type(include_module: bool):
    definition = IsTypeDef(include_module=include_module)
    object_: Munch[str, Any] = Munch(
        attr_1='value_1',
        attr_2='value_2',
        attr_3='value_3',
    )
    expectation = generate_expectation(object_, definition)

    assert isinstance(expectation, IsType)
    assert expectation.expected_type_name == 'Munch'
    assert expectation.expected_type_module == ('munch' if include_module else None)
