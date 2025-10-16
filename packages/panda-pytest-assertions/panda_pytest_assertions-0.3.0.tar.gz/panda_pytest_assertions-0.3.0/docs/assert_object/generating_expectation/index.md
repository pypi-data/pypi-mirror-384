# Generating Expectations

When dealing with very complex objects, especially in the context of end-to-end (E2E) tests, manually writing expectations can be cumbersome. In such scenarios, it may be beneficial to automatically generate expectations from an existing object (produced by tested code), review them, and store them as input for the test. This can be achieved using the `generators` submodule available in this module.

The internal structure of generators closely resembles that of the main module:

- Instead of an "expectation," there is an "expectation definition" - an object that defines the structure of the generated expectation.
- Instead of an "asserter," there is a "generator" - a class that implements the logic for generating expectations based on a specific definition.
- Finally, instead of an "asserter factory," there is a "generator factory" - a class that creates a generator for a specific generator definition.

Expectation definitions are necessary because there is no universal way to represent an object in an expectation. For example, every object might be stringified or used as-is. If you want to generate an `ObjectAttributes` expectation, it would be atypical to include all attributes for asserting. Therefore, expectation definitions help define the structure of a generated expectation, determine the appropriate expectation type, and specify the values to include.

The function used to generate an expectation is called `generate_expectation`. It accepts the following parameters:

- the object from which expectation values will be taken,
- the definition describing the expectation structure,
- optionally, a custom generator factory.

Here's an example:

```python
object_: Munch[str, Any] = Munch(
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
        ),
    ],
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
        },
    ),
)
expectation = generate_expectation(object_, definition)
```

```yaml title='Generated Expectation'
!WithType
expectation: !ObjectAttributes
  books: !Unordered
  - !ObjectAttributes
    authors: !Stringified '[''J. R. R. Tolkien'']'
    language: en
    name: Hobbit
  - !ObjectAttributes
    authors: !Stringified '[''Abelard Giza'']'
    language: pl
    name: "Otworzy\u0107 po mojej \u015Bmierci"
  created_at: !Stringified '2020-06-08 12:30:00'
expected_type_module: munch
expected_type_name: Munch
```
