# Overview

**Panda Pytest Assertions** is a library that provides a complex assertion mechanism for use when writing tests with pytest. The primary goal is to make test code more concise, readable, and maintainable.

The library consists of two modules that can be used separately or together:

- `assert_context` - used to assert that the block of code behaved as expected, raise or do not raise the exception and assert the value of a result;
- `assert_object` - used to assert the content of the object, when simple `==` is not enough.

## `assert_context`

This context manager asserts that a code block within a `with` block behaves according to expectations. It verifies whether an exception of a specific type was (or wasn't) raised within the block and whether the result of the block (settable by the user) matches the expected value. For example:

```python
with assert_context(exception=ValueError, result='something') as context:
    context.set('something')
    raise ValueError
```

## `assert_object`

This function is used to assert the content of a Python object (and possibly nested objects) against provided expectations. It goes beyond simple equality checks using `==`. For instance:

```python
asserted_object: Munch[str, Any] = Munch(
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

assert_object(expectation, asserted_object)
```
