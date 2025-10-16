Many examples can be also found in the [root](./index.md) of this page.

## Unit Conversion

When `exact=True` is used, the exact conversion factor is returned.

```py title="docs/examples.py"
--8<-- "docs/examples.py:tsfc_example"
```
```
--8<-- "docs/examples.py:tsfc_output"
```

## Disambiguation

`isqx` defines many [quantity kinds][isqx.QtyKind] that are generic over
different unit systems (MKS, imperial...). Calling the quantity kind with a
particular unit will produce a [tagged][isqx.Tagged] expression:

```py title="docs/examples.py"
--8<-- "docs/examples.py:verbose_fmt_example"
```
```
--8<-- "docs/examples.py:verbose_fmt_output"
```

Both quantity kinds and tagged expressions can be indexed.
`B = A["some_tag"]` can roughly be interpreted as `B` is a subclass of `A`.
However, because tags are designed to avoid strict inheritance hierarchies.

Tagged expressions are incompatible with another and will raise an error:

```py title="docs/examples.py"
--8<-- "docs/examples.py:tagged_error_example"
```
```
--8<-- "docs/examples.py:tagged_error_output"
```

## Introspection

Annotations can be inspected at runtime.
One example is to dynamically generate docstrings from the annotations:

```py title="docs/examples.py"
--8<-- "docs/examples.py:decorator_def"
```

We can apply this decorator to an annotated function to automatically document
the units of its parameters:

```py title="docs/examples.py"
--8<-- "docs/examples.py:breguet_example"
```
```
--8<-- "docs/examples.py:breguet_output"
```
Or with a dataclass:
```py title="docs/examples.py"
--8<-- "docs/examples.py:dataclass_example"
```
```
--8<-- "docs/examples.py:dataclass_output"
```