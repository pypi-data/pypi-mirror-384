from datetime import datetime
from enum import auto, Enum
from typing import Any

import pytest
from munch import Munch

from panda_pytest_assertions.assert_object import (
    assert_object,
    Is,
    is_type,
    MappingSubset,
    ObjectAttributes,
    Stringified,
    Unordered,
    with_type,
)


def test_complex_correct():
    class Language(Enum):
        PL = auto()
        EN = auto()
        IT = auto()

    asserted_object: Munch[str, Any] = Munch(
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
            bajki_robotow := Munch(  # type: ignore [var-annotated]
                name='Bajki robotów',
                authors=['Stanisław Lem'],
                language=Language.PL,
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
    expectation = with_type('Munch', 'munch')(
        ObjectAttributes(
            {
                'created_at': Stringified('2020-06-08 12:30:00'),
                'books': Unordered(
                    [
                        ObjectAttributes(
                            {
                                'name': 'Hobbit',
                                'authors': Stringified("['J. R. R. Tolkien']"),
                                'language': Language.EN,
                                'translations': MappingSubset({Language.PL: with_type(bool)(1)}),
                            },
                        ),
                        ObjectAttributes(
                            {
                                'authors': {'Neil Gaiman', 'Terry Pratchett'},
                            },
                        ),
                        ObjectAttributes(
                            {
                                'translations': MappingSubset({}),
                            },
                        ),
                        ObjectAttributes(
                            {
                                'name': 'Dokąd nocą tupta jeż',
                                'authors': [],
                            },
                        ),
                        Is(bajki_robotow),
                    ],
                ),
                'movies': (
                    MappingSubset(
                        {
                            'prizes': {"Critics' Choice": 2, 'Oscars': 1},
                            'polish_title': 'Marzyciel',
                        },
                    ),
                    {
                        'prizes': Unordered(['IATSE Local 706', 'Satelites']),
                        'english_title': 'Maestro',
                    },
                    MappingSubset({'prizes': {}}),
                    MappingSubset({'polish_title': 'Czarna woda'}),
                ),
                'songs': is_type(list),
            },
        ),
    )

    assert_object(expectation, asserted_object)


@pytest.mark.parametrize(
    ['expectation', 'object_'],
    [
        (True, True),
        ('abc', 'abc'),
        (123, 123),
        (123, 123.0),
        (123.0, 123),
        (123.321, 123.321),
        (None, None),
        (True, 1),
        (1, True),
        (False, 0),
        (0, False),
    ],
)
def test_primitives_correct(expectation: Any, object_: Any):
    assert_object(expectation, object_)


@pytest.mark.parametrize(
    ['expectation', 'object_'],
    [
        (None, False),
        (None, ''),
        (None, 0),
        (True, False),
        (True, 0),
        (True, 'some string'),
        (False, True),
        (False, 1),
        (False, ''),
        ('abc', 'ab'),
        ('123', 123),
        ('123.321', 123.321),
        (123, 124),
        (123, '123'),
        (0, True),
        (1, False),
        (123.0, 123.1),
    ],
)
def test_primitives_incorrect(expectation: Any, object_: Any):
    with pytest.raises(AssertionError):
        assert_object(expectation, object_)


def test_flat_object():
    asserted_object: Munch[str, Any] = Munch(color='brown', legs=4)

    assert_object(ObjectAttributes({'color': 'brown', 'legs': 4}), asserted_object)
    assert_object(ObjectAttributes({'color': 'brown'}), asserted_object)
    assert_object(ObjectAttributes({'legs': 4}), asserted_object)
    assert_object(Stringified("Munch({'color': 'brown', 'legs': 4})"), asserted_object)
    assert_object(with_type()(asserted_object), asserted_object)
    assert_object(with_type(Munch)(Stringified("Munch({'color': 'brown', 'legs': 4})")), asserted_object)
    assert_object(is_type(Munch), asserted_object)
    assert_object(is_type('Munch', 'munch'), asserted_object)
    assert_object(Is(asserted_object), asserted_object)

    with pytest.raises(AssertionError):
        assert_object(ObjectAttributes({'color': 'brown', 'legs': 4, 'fur': True}), asserted_object)
    with pytest.raises(AssertionError):
        assert_object(ObjectAttributes({'color': 'blue'}), asserted_object)
    with pytest.raises(AssertionError):
        assert_object(ObjectAttributes({'legs': 8}), asserted_object)
    with pytest.raises(AssertionError):
        assert_object(Stringified('Munch()'), asserted_object)
    with pytest.raises(AssertionError):
        assert_object(with_type(str)(Stringified("Munch({'color': 'brown', 'legs': 4})")), asserted_object)
    with pytest.raises(AssertionError):
        assert_object(is_type(str), asserted_object)
    with pytest.raises(AssertionError):
        assert_object(Is(Munch(color='brown', legs=4)), asserted_object)


def test_lists():
    asserted_object: list[Munch[str, Any]] = [
        Munch(color='brown', legs=4),
        Munch(env='water', fur=False),
    ]

    assert_object(
        [
            with_type(Munch)(Stringified("Munch({'color': 'brown', 'legs': 4})")),
            {'env': 'water', 'fur': False},
        ],
        asserted_object,
    )
    assert_object(
        Unordered(
            [
                {'env': 'water', 'fur': False},
                with_type(Munch)(Stringified("Munch({'color': 'brown', 'legs': 4})")),
            ],
        ),
        asserted_object,
    )

    with pytest.raises(AssertionError):
        assert_object(
            [
                {'env': 'water', 'fur': False},
                with_type(Munch)(Stringified("Munch({'color': 'brown', 'legs': 4})")),
            ],
            asserted_object,
        )
    with pytest.raises(AssertionError):
        assert_object(
            [
                with_type(Munch)(Stringified("Munch({'color': 'brown', 'legs': 4})")),
            ],
            asserted_object,
        )
    with pytest.raises(AssertionError):
        assert_object(
            Unordered(
                [
                    {'env': 'water', 'fur': True},
                    {},
                ],
            ),
            asserted_object,
        )
    with pytest.raises(AssertionError):
        assert_object(
            Unordered(
                [
                    {'env': 'water', 'fur': False},
                    with_type(Munch)(Stringified("Munch({'color': 'brown', 'legs': 4})")),
                    {},
                ],
            ),
            asserted_object,
        )


def test_mapping():
    asserted_object: dict[int, Munch[str, Any]] = {
        1: Munch(color='brown', legs=4),
        2: Munch(env='water', fur=False),
    }

    assert_object(
        {
            2: {'env': 'water', 'fur': False},
            1: with_type(Munch)(Stringified("Munch({'color': 'brown', 'legs': 4})")),
        },
        asserted_object,
    )
    assert_object(
        MappingSubset(
            {
                1: with_type(Munch)(Stringified("Munch({'color': 'brown', 'legs': 4})")),
            },
        ),
        asserted_object,
    )

    with pytest.raises(AssertionError):
        assert_object(
            {
                2: {'env': 'water', 'fur': False},
            },
            asserted_object,
        )
    with pytest.raises(AssertionError):
        assert_object(
            MappingSubset(
                {
                    1: with_type(Munch)(Stringified("Munch({'color': 'brown', 'legs': 4})")),
                    3: {'env': 'water', 'fur': False},
                },
            ),
            asserted_object,
        )
