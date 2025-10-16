from enum import auto, Enum
from typing import Any

import pytest

from panda_pytest_assertions.assert_object import (
    is_type,
    MappingSubset,
    ObjectAttributes,
    Stringified,
    Unordered,
    with_type,
)


class Language(Enum):
    PL = auto()
    EN = auto()
    IT = auto()


@pytest.fixture
def complex_expectation() -> Any:  # noqa: ANN401
    return with_type('Munch', 'munch')(
        ObjectAttributes(
            {
                'created_at': Stringified('2020-06-08 12:30:00+00:00'),
                'books': Unordered(
                    [
                        ObjectAttributes(
                            {
                                'name': 'Hobbit',
                                'authors': Stringified("['J. R. R. Tolkien']"),
                                'language': with_type('Language', None)(Stringified(str(Language.EN))),
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


@pytest.fixture
def complex_expectation_yaml_string() -> str:
    return """\
!WithType
expectation: !ObjectAttributes
  books: !Unordered
  - !ObjectAttributes
    authors: !Stringified '[''J. R. R. Tolkien'']'
    language: !WithType
      expectation: !Stringified 'Language.EN'
      expected_type_module: null
      expected_type_name: Language
    name: Hobbit
    translations: !MappingSubset
      ? !WithType
        expectation: !Stringified 'Language.PL'
        expected_type_module: tests.panda_pytest_assertions.assert_object._converters.conftest
        expected_type_name: Language
      : !WithType
        expectation: 1
        expected_type_module: builtins
        expected_type_name: bool
  - !ObjectAttributes
    authors: !!set
      Neil Gaiman: null
      Terry Pratchett: null
  - !ObjectAttributes
    translations: !MappingSubset {}
  - !ObjectAttributes
    authors: []
    name: "Dok\\u0105d noc\\u0105 tupta je\\u017C"
  created_at: !Stringified '2020-06-08 12:30:00+00:00'
  movies:
  - !MappingSubset
    polish_title: Marzyciel
    prizes:
      Critics' Choice: 2
      Oscars: 1
  - english_title: Maestro
    prizes: !Unordered
    - IATSE Local 706
    - Satelites
  - !MappingSubset
    prizes: {}
  - !MappingSubset
    polish_title: Czarna woda
  songs: !IsType
    expected_type_module: builtins
    expected_type_name: list
expected_type_module: munch
expected_type_name: Munch
"""
