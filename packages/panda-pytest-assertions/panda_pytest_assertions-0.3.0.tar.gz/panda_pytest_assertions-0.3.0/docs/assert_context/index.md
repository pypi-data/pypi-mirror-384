# `assert_context`

The `assert_context` module exposes a context manager that verifies whether code within a `with` block behaves as expected. It checks whether a exception of a specific type matching specific value was (or wasn't) raised within the block and whether the result of the block (settable by the user) matches the expected value.

Module exposes `ExceptionMatch` class which allows to specify not only type of expected exception, but also a string which shall match raised exception value.

Additionally, it provides the `AssertContext` class, which can be useful for typing in more complex scenarios, as it is the type returned by the `__enter__` method.

## Basic Example

The following code snippet demonstrates how to use `assert_context`. It asserts that the result of `fun()` will be `'something'` and that `bar()` will raise a `ValueError`.

```python
with assert_context(exception=ValueError, result='something') as context:
    context.set(fun())
    bar()
```

## Parameters

The context manager defines three optional keyword parameters: `exception`, `result`, and `behaviour`. The pair of parameters (`exception`, `result`) is mutually exclusive with the `behaviour` parameter. If `behaviour` is set, the other parameters must remain unset.

### `exception` Parameter

- If the `exception` parameter is set to exception type, the `with` block is expected to raise an exception of the provided type.
- If the `exception` parameter is set to an instance of `ExceptionMatch` class, the `with` block is expected to raise an exception of type specified in `type_` field and the value that matches the string specified in `match_` field. For exact matching logic see `match` parameter of the `pytest.raises`.
- If the `exception` parameter is NOT set or is set to `None`, the `with` block is expected NOT to raise any exceptions.

#### Examples

Code not raising any exceptions:

```python
with assert_context():
    ...

with assert_context(exception=ValueError):
    raise ValueError
```

Code raising a `ValueError`:

```python
with assert_context():
    raise ValueError

with assert_context(exception=TypeError):
    raise ValueError
```

Code calling `pytest.fail` (equivalent to `pytest.raises(ValueError)`):

```python
with assert_context(exception=ValueError):
    ...
```

### `result` Parameter

- If the `result` parameter is set, its value is expected to be equal to the result of the `with` block.
- The `with` block result is set using the `set` method of an object yielded by the context manager.
- The comparison is performed using the `==` operator, with the `result` argument on the left side.
- If the `result` parameter is NOT set, the `set` method of the yielded object is expected not to be called at all.

#### Examples

Code not raising any exceptions:

```python
with assert_context() as context:
    ...

with assert_context(result='something') as context:
    context.set('something')
```

Code raising an `AssertionError`:

```python
with assert_context() as context:
    context.set('else')

with assert_context(result='something') as context:
    context.set('else')

with assert_context(result='something') as context:
    ...
```

### Combining `exception` and `result` Parameters

Both `exception` and `result` parameters can be set simultaneously to check more complex code.

#### Example

Code not raising any exceptions:

```python
with assert_context(exception=ValueError, result='something') as context:
    context.set('something')
    raise ValueError
```

### `behaviour` Parameter

- If `behaviour` is set to an exception type or `ExceptionMatch` instance, it is equivalent to setting `exception` to the same value and leaving `result` unset.
- If `behaviour` is set to any other value, it is treated as the value of `result`, and the `exception` parameter remains unset.

#### Examples

Code not raising any exceptions:

```python
with assert_context(behaviour=ValueError) as context:
    raise ValueError

with assert_context(result='something') as context:
    context.set('something')
```

Code raising exceptions:

```python
with assert_context(behaviour=ValueError) as context:
    context.set('else')

with assert_context(result='something') as context:
    raise ValueError
```
