`isqx` tries not to follow the patterns of existing units of measurement (UoM)
libraries: it prioritises incremental adoption over runtime enforcement.

It is inspired libraries like:

- [`annotated-types`](https://github.com/annotated-types/annotated-types) and
  [`fastapi`](https://github.com/fastapi/fastapi), which popularised the use of
  metadata objects with `typing.Annotated`,
- [`impunity`](https://achevrot.github.io/impunity/), which also use `Annotated`
to enforce dimension correctness.

## Why do existing UoM libraries not proliferate?

[McKeever et al. (2020)](https://doi.org/10.1002/spe.2926) cited the main
reasons being "solutions interfere with code too much" (31%) and the "effort of
learning" (28%). The frustrations are best captured by the survey responses:

- *"We depend on a number of libraries (`PETSc`, `Eigen`...) that interact very
  poorly with UoM libraries."*
- *"Very few languages have the affordances to make numbers with units both
  statically type-checked and as ergonomic to pass in and out of functions
  as bare numbers."*
- *"I tried working with `Boost.Units` multiple times ... simply setting up the
  whole system took more time than I had to invest."*
- *"I recently helped develop the simulation of fluid flow in Fortran and nobody
  ever asked for units anywhere, but everyone was really interested in
  performance."*
- *"manual conversions functions covered most use cases"*

`isqx` is designed to be opt-in only, decoupling the unit from the runtime value.
It builds upon the idea of what's already excellent: writing docstrings
*orthogonal* to the code responsible for computation.

## Problem 1: The friction of newtypes

Most UoM libraries, especially in compiled languages like
[C++ `Boost::Units`](https://github.com/boostorg/units) and
[Rust `uom`](https://github.com/iliekturtles/uom), model a "wrapper" or
"newtype" around a numerical value. This pattern uses the type system to enforce
dimensional correctness at compile-time, promising zero runtime overhead.

```rs title="pseudocode"
struct Quantity<V, U> {
    value: V,               // a numerical value: float, int...
    units: PhantomData<U>,  // zero-sized "ghost", erased at runtime
}
// operator overloads to enforce rules
impl<Ul, Ur, V> Mul<Quantity<V, Ur>> for Quantity<V, Ul> { /* ... */ }
// ... and so on for `Div`, `Add`, `Sub` ...

let length = Length::new::<meter>(1.0);
let time = Time::new::<second>(3.0);
let speed = length / time;    // ok, `Div` is implemented
let nonsense = length + time; // compile error  
```

While powerful, this newtype is immediately incompatible with the vast majority
of external libraries that expect a raw numerical type (`float`, `np.ndarray`...).
Users are forced to constantly unwrap the quantity and re-wrap it at every single
function boundary, leading to the frustrations described earlier.

??? note "Case study: `pint`"

    Python is a dynamic language with an optional (and relatively weak) type system.
    Trying to model this newtype pattern at runtime with operator overloads brings
    even more friction.

    Imagine developing a simple library with `pint`:
    ```py title="airspeed.py"
    from pint import UnitRegistry

    ureg = UnitRegistry()
    RHO_0 = 1.225 * (ureg.kilogram * ureg.meter**-3)
    """Density of air at mean sea level"""


    def eas(tas, air_density):
        """Converts TAS to EAS.

        :param tas: true airspeed (meters per second)
        :param air_density: atmospheric density (kilograms per meter cubed)
        :returns: equivalent airspeed (meters per second)
        """
        return tas * (air_density / RHO_0) ** 0.5
    ```

    Since `RHO_0` (a `pint.Quantity`) implements the `__array_ufunc__` protocol,
    any `numpy`-like array inputs should be not cause any problem.

    A downstream user, unfamiliar with `pint`, might perform a standard data
    processing task:
    ```pycon title="uv run --with pint --with polars --with jax python3"
    >>> import airspeed
    >>> import polars as pl
    >>> import numpy as np
    >>> df = pl.DataFrame({
    ...     "air_density": np.linspace(0.5, 1.13, 100),
    ...     "tas": np.linspace(200, 130, 100)
    ... })
    >>> eas = airspeed.eas(df["tas"], df["air_density"])
        return tas * (air_density / RHO_0) ** 0.5
                      ~~~~~~~~~~~~^~~~~~~
    TypeError: cannot convert Python type 'pint.Quantity' to Float64
    >>> # ok, maybe it wants numpy arrays instead.
    >>> eas = airspeed.eas(df["tas"].to_numpy(), df["air_density"].to_numpy())
    >>> df = df.with_columns(eas=eas)
    TypeError: cannot create expression literal for value of type Quantity.

    Hint: Pass `allow_object=True` to accept any value and create a literal of type
    Object.
    >>> eas  # what is a `Quantity`?
    <Quantity([127.775313   ... 124.85746976], 'meter ** 1.5 / kilogram ** 0.5')>
    ```

    The user might expect a `numpy` input to return a `numpy` output, but what
    they got was a new `Quantity` wrapper with nonsensical units. After reading
    the docs, the user understands to pass in a `Quantity` instead:

    ```pycon
    >>> u = airspeed.ureg
    >>> tas_with_u = df["tas"].to_numpy() * (u.meter * u.second**-2)
    >>> densities_with_u = df["air_density"].to_numpy() * (u.kilogram * u.meter**-3)
    >>> eas = airspeed.eas(tas_with_u, densities_with_u)
    >>> eas
    <Quantity([127.775313   ... 124.85746976], 'meter / second ** 2')>
    >>> # units are correct, create a df but make sure to get the magnitude
    >>> df = df.with_columns(eas=eas.m)
    ```

    Which works well, but the user had to guess whether the library supports a
    `Quantity` input. Will it support `scipy.optimize`? Or `einops.einsum`?
    Maybe, maybe not.

    The burden is not just on the user, but also the authors. Having to provide
    support for the ever-changing APIs of the entire Python ecosystem within the
    `Quantity` newtype is impossible.

    The user might also want to compute the gradient of `eas` and try to speedup
    the code with JIT, only to come to even more roadblocks:

    ```pycon
    >>> import jax
    >>> jax.vmap(jax.grad(airspeed.eas))(tas_with_u, densities_with_u)
    TypeError: Argument '[200.0 ... 130.0] meter / second ** 2' of type
    <class 'pint.Quantity'> is not a valid JAX type.
    >>> jax.vmap(jax.grad(airspeed.eas))(tas_with_u.m, densities_with_u.m)
    TypeError: Argument 'Traced<float32[100]>with<JVPTrace> with
      primal = Array([127.775314, ..., 124.85747 ],      dtype=float32)
      tangent = Traced<float32[100]>with<JaxprTrace> with
        pval = (ShapedArray(float32[100]), None)
        recipe = JaxprEqnRecipe(eqn_id=0, ...) meter ** 1.5 / kilogram ** 0.5'
        of type '<class 'pint.Quantity'>' is not a valid JAX type
    >>> jax.jit(airspeed.eas)(tas_with_u.m, densities_with_u.m)
    TypeError: function eas at /home/user/airspeed.py:7 traced for jit returned a
    value of type <class 'pint.Quantity'>, which is not a valid JAX type
    >>> import numba
    >>> numba.jit(airspeed.eas)(tas_with_u.m, densities_with_u.m)
    Untyped global name 'RHO_0': Cannot determine Numba type of
    <class 'pint.Quantity'>
    ```

    <figure markdown="span">
        ![benchmark](assets/design/bench.png)
        <figcaption>Performance analysis indicates up to an order of magnitude 
        slowdown due to the repeated runtime checks in the `Quantity` newtype.
        </figcaption>
    </figure>

    ??? note "bench script"

        ```py title="airspeed.py"
        --8<-- "docs/assets/design/airspeed.py"
        ```
        ```py title="bench.py"
        --8<-- "docs/assets/design/bench.py"
        ```

Python shines in its flexibility. Introducing a hard dependency on the
`Quantity` newtype interferes too much with what we're trying to achieve, and
`isqx` crucially avoids using the newtype pattern in the first place.

## Problem 2: Quantities of the same dimension but different kinds

Documenting code with units alone are often insufficient
(see [README](./index.md#quantity-kinds)). For example, annotating a function
parameter with `Joules` is too ambiguous: using
`the change in internal energy (joules)` is far more precise.

Surprisingly, most UoM libraries only offer units to work with (see
[`pint#551`](https://github.com/hgrecco/pint/issues/551)).

`isqx` tackles this with two key ideas:

- units can be "refined": `J["work"]` and `J["heat"]` both still represent
  `Joules`, but additional metadata stored within the expression makes sure
  they are not interchangeable.
- downstream users should be able to pick the unit they prefer
  (`MJ`, `GJ`, `Btu`...) easily.

The former idea is implemented with [`isqx.Tagged`][], responsible for binding
arbitrary metadata to a unit. Its design is strongly inspired by
`typing.Annotated` itself, providing a very flexible system to specify what they
want. `Expr.__getitem__` provides an ergonomic way to "refining" an existing
unit.

The latter idea is implemented with the [`isqx.QtyKind`][] factory, which also
stores the metadata but makes the unit "generic". `QtyKind.__call__` with any
user-defined, dimensionally-compatible unit produces a [`isqx.Tagged`][]
expression.

### Reusing `Tagged`

When users write `x: Annotated[float, M]`, it naturally reads: "the numeric
value of `x` is a point/measurement on the meter scale". But where is the
*origin* of the meter scale defined? Should the altitude be measured w.r.t.
to the center of the Earth, or above mean sea level, or above the ground
elevation?

Another point of confusion is that it can also be interpreted as: "the numeric
value of `x` represents the difference in length between two points on the meter
scale (position-independent)".

Because [`isqx.Tagged`][] can store any hashable object, one can use the
[`isqx.OriginAt`][] or [`isqx.DELTA`][] tags to reduce ambiguity.

### Note on `QtyKind`

One important caveat is that while [`isqx.Expr`][] can be composed with each
other to form a "larger tree", [`isqx.QtyKind`][] **cannot be further composed**.
This may sound surprising: wouldn't something like `force = mass * acceleration`,
`kinetic_energy = 0.5 * mass * velocity**2` be an ergonomic way of defining new
quantities?

While it makes sense to do so, `isqx` avoids this because many quantities are not
defined by simple products of powers:

| Quantity Kind                                  | Definition                                                     | Additional expression nodes needed |
| ---------------------------------------------- | -------------------------------------------------------------- | ---------------------------------- |
| [work][isqx.WORK]                               | $W = \int_C \mathbf{F} \cdot d\mathbf{s}$                      | integral, dot product              |
| [enthalpy][isqx.ENTHALPY]                       | $H = U + pV$                                                   | addition, subtraction              |
| [isentropic exponent][isqx.ISENTROPIC_EXPONENT] | $-\frac{V}{\rho} \left(\frac{\partial p}{\partial V}\right)_S$ | partial derivatives                |
| [poynting vector][isqx.POYNTING_VECTOR]         | $\mathbf{S} = \mathbf{E} \times \mathbf{H}$                    | cross product                      |
| [complex power][isqx.COMPLEX_POWER]             | $\underline{S} = \underline{U} \underline{I}^*$                | complex conjugate                  |

We would have to build another SymPy just to define a quantity kind and resolve
its units. `mp-units` tries to do exactly this, but it resorts to simplifying or
ignoring operations that are too hard to model.

`isqx` tries to keep it simple by storing its definitions in a separate (and
optional) [details dictionary][isqx.details.Details] under the [`isqx.details`][]
module instead. Our documentation uses a custom `mkdocstrings-python` and
`griffe` plugin to scan for expressions, generate cross-references. It is also
emits an JSON file for the [visualiser](./vis.md).

## Problem 3: Exact representation and formatting

Consider the unit for fuel economy, [miles per gallon][isqx.usc.MPG].
Dimensionally, this is equivalent to the inverse area:
$\frac{\mathsf{L}}{\mathsf{L}^3} = \mathsf{L}^{-2}$.

Many runtime libraries would eagerly simplify `MPG` to a base form like `m⁻²`
to improve performance in dimensional checks. This however, loses the
human-readable intent.

`isqx` preserving the exact tree representation.
This allows the formatted output to be exactly in the form the user defined it.

## FAQ

### What's the point if there is no runtime checks?

> Since `x` in `Annotated[T, x]` are ignored by the Python interpreter and
> you're not using `x` for checking dimension errors, isn't `isqx` just
> glorified comments?

Yes. `isqx` provides a machine-readable, centralised vocabulary for documentation.
It avoids the "newtype" friction by decoupling the documentation from the
runtime value.

Expressive, unambiguous documentation can significantly reduce accidental
errors without imposing runtime or interoperability costs.

> In that case, why not just use `pint.Unit` within `Annotated`, without
> the `Quantity` wrapper?

Indeed, many existing libraries already has solid support for units.
However, painpoints boil down to:

- inability to defining quantity kinds
- odd ways to define new units (e.g. modifying a file with DSL)
- no intersphinx
- LSP: inability to "jump to definition" all the way to its base units

`isqx` tries to be minimal.

> What about parsing the Python AST and collecting all `x` in functions or
> dataclasses, and building a static analyzer?

This is a direction that [`impunity`](https://achevrot.github.io/impunity/)
explored.

However, building a useful static analyser that doesn't produce too many
false positives is very difficult. Some challenges include:

- Complicated functions:
    - `numpy.fft.fft`: The relationship between the input and output units is
      non-trivial: if the input signal is in `volts` over an implicit
      time domain, then the output is in `volt-seconds` over an implicit
      frequency domain.
    - `einops.einsum`: The operation is defined by a string like `ij,jk->ik`.
      The analyzer would need to parse and interpret this string notation to
      understand which tensor operation is being performed before it could even
      begin to calculate the output unit.
- Complicated data structures like `polars.DataFrame` may have different units
  for different columns. Should we support `pandera`'s approach, or have a more
  generic way to annotate multidimensional arrays like `xarray`?
- Ambiguous operations: Should adding a `height` and `thickness` be an error?
  ISO 80000 permits this, but it might be physically questionable in some
  contexts (e.g. `force in the x direction` + `force in the y direction`)

`isqx` provides the necessary expressiveness to build a smart static analyzer.
If one is built, it should learn from the success of gradual typing systems
like mypy and offer configurable strictness levels.

### Why are details stored in a separate `isqx.details` module?

Some quantity kinds are defined in terms of quantity kinds that are defined
later. For example, [action][isqx.ACTION] [ISO 80000-3] is defined in terms of
[work][isqx.WORK] [ISO 80000-5]. We can either:

- couple details with the [`isqx.QtyKind`][] and forward-reference with strings
- define all [`isqx.QtyKind`][]s first and define definitions separately.

The latter is adopted because:

1. LSP support is far better: enables go-to-definition interactions.
   refactoring will be far easier.
2. Our [mkdocs plugin][isqx.mkdocs.plugin] will be able to easily build
   cross-references
3. Extensibility: downstream users can easily append their own domain-specific
   definitions.
4. Performance: avoids loading non-critical information on `import isqx`.
5. `USD <-> HKD` is not fixed

Similarly, the [formatting][isqx.Expr] of expressions are decoupled from their
definitions for the same reason. Users might want to maintain their own set of
symbols/locales and we don't want downstream users to have to monkeypatch
classes.

### How can I parse units from a string?

`isqx` does not come with a built-in parser because there are endless variety of
formats:

- plain text
- different flavours of $\LaTeX$,
- locale/subfield-specific symbols
- user defined custom tags

However, the expression tree of `isqx` can be used as a target for a custom
parser. A simple recursive descent or Pratt parser can be written to transform
a string into a [`isqx.Expr`][] object.

### Having to define `M = Annotated[_T, isqx.M]` is annoying. Why not make `isqx.M` a type instead of object?

Unfortunately, there is no way to create our own `Annotated` and have
static type checkers understand it. One possible path is:

```py
from typing import TypeVar, Generic, Annotated, Any
from typing_extensions import _AnnotatedAlias

T = TypeVar("T")

class Expr(Generic[T]):
    # mimic what `typing.Annotated` does
    def __class_getitem__(cls, params) -> Annotated[T, Any]:
        return _AnnotatedAlias(params, (cls,))

class M(Expr): # define meter as a type, not a runtime object
    pass

print(M[int]) # this indeed produces an `Annotated` at runtime
# typing.Annotated[int, <class '__main__.M'>]

# unfortunately mypy does not understand this as an `Annotated` special form:
def foo(bar: M[int], baz: M[float]):
    return bar / baz
# main.py:16: error: "M" expects no type arguments, but 1 given  [type-arg]
# main.py:17: error: Unsupported left operand type for / ("M")  [operator]
# Found 2 errors in 1 file (checked 1 source file)
```
See also:

- https://stackoverflow.com/questions/78536551/variable-not-allowed-in-type-expression-how-can-i-create-parameterized-typin
- https://stackoverflow.com/questions/78845949/how-to-define-a-typing-special-form-for-use-with-static-type-checking
