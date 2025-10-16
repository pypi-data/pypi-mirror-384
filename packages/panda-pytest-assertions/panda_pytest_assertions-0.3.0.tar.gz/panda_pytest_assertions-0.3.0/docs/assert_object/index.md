# `assert_object`

The `assert_object` module exposes a function that asserts whether the content of a Python object (including possibly nested objects) fulfills provided expectations.

## Basic Example

Consider the following code snippet, which asserts the return value of `fun()` against specific expectations.

- The object must have at least two attributes: `created_at` and `books`.
- The `created_at` attribute, when stringified, must match `'2020-06-08 12:30:00'`.
- The `books` attribute must be an iterable with exactly two elements.
- The order of the `books` elements does not matter.
- One of the `books` elements must have at least `name`, `authors`, and `translations` attributes.
- Another `books` element must have at least `name`, `authors`, and `language` attributes.
- The values of the `books` elements' attributes are also checked against specified expectations.

```python
expectation = ObjectAttributes(
    {
        'created_at': Stringified('2020-06-08 12:30:00'),
        'books': Unordered(
            [
                ObjectAttributes(
                    {
                        'name': 'Otworzyć po mojej śmierci',
                        'authors': ['Abelard Giza'],
                        'translations': MappingSubset({}),
                    },
                ),
                ObjectAttributes(
                    {
                        'name': 'Hobbit',
                        'authors': Stringified("['J. R. R. Tolkien']"),
                        'language': 'en',
                    },
                ),
            ],
        ),
    },
)

assert_object(expectation, foo())
```

Example of an object that fulfills the above expectation:

```python
Munch(
    list_author='Jan Kowalski',
    created_at=datetime(2020, 6, 8, 12, 30),
    books=[
        Munch(
            name='Hobbit',
            authors=['J. R. R. Tolkien'],
            language='en',
            translations={'pl': 1963, 'it': 1973},
        ),
        Munch(
            name='Otworzyć po mojej śmierci',
            authors=['Abelard Giza'],
            language='pl',
            translations={},
        ),
    ],
)
```
