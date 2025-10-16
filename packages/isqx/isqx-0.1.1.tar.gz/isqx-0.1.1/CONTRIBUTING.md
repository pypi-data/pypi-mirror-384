# Development

```shell
$ git clone https://github.com/abc8747/isqx.git
$ cd isqx
$ uv venv
$ uv sync --dev
```

We use utility scripts under `scripts/` to lint, format and check for
typing issues. Dependencies are automatically managed by `uv`.

```shell
$ ./scripts/make.py
                                                                                
 Usage: make.py [OPTIONS] COMMAND [ARGS]...                                     
                                                                                
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ copy-docs-file   Copy a file from `path_in` to `path_out` with warnings.     │
│ check                                                                        │
│ check-katex      Highlight underscores in katex                              │
│ fix                                                                          │
╰──────────────────────────────────────────────────────────────────────────────╯
$ ./scripts/wikidata.py
                                                                                
 Usage: wikidata.py [OPTIONS] COMMAND [ARGS]...                                 
                                                                                
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ fetch-json              Execute a SPARQL query from a file and save the raw  │
│                         response as JSON.                                    │
│ quantities-to-parquet   Organise the raw quantities JSON response in a       │
│                         parquet file.                                        │
│ quantities-to-md        Organise the quantities parquet file in a            │
│                         human-readable markdown file.                        │
╰──────────────────────────────────────────────────────────────────────────────╯
```

To build and serve the documentation:

```shell
$ uv run mkdocs serve
```

Note that this loads in some custom extensions under `src/isqx/mkdocs` and
**overwrites** `docs/index.md` with the one from the top level `README.md`.

# Defining units and quantity kinds.

The ISO/IEC 80000 (`iso80000.py`) contains many useful core objects and is
considered complete. If you would like to add new definitions for your own
subfield, you should place them in two files:

- Core definitions (`src/isqx/{{domain}}.py`): this is where runtime objects like
  `QtyKind`, `BaseUnit` etc. are defined.
- Descriptive Details (`src/isqx/details/{{domain}}.py`): this is where
  non-essential metadata like `Wikidata`, `Symbol` and `Equation` etc. are defined.

## Units and constants

First, define the essential runtime objects.

- use `SCREAMING_SNAKE_CASE`
- for constants, prefer using stdlib `decimal.Decimal` and `fractions.Fraction`.
  downstream users are responsible for casting to float if they wish.

```py
from decimal import Decimal
from isqx import BaseDimension, BaseUnit

# base units
DIM_TIME = BaseDimension("T")
S = BaseUnit(DIM_TIME, "second")
# derived units
N = (KG * M * S**-2).alias("newton", allow_prefix=True)
# scaled units
FT = (Decimal("0.3048") * M).alias("foot")

# constants
from isqx import StdUncertainty  # optional
from typing import Annotated
G0: Annotated[Decimal, M * S**-2, StdUncertainty("12")] = Decimal("9.8065")
# do not do this:
G0 = isqx.Quantity(9.8065, M * S**-2)
```

## Quantity kinds

```py
from isqx import QtyKind

# must be defined with coherent SI units (i.e. not scaled)
# it can have optional tags.
ENERGY = QtyKind(J)
# add a tag: kinetic energy can be thought of a "subclass" of length.
KINETIC_ENERGY = LENGTH["kinetic"]
# alternatively, if it doesn't make sense to "subclass".
WORK_DONE = QtyKind(J, ("work_done",))

from isqx.usc import BTU
ENERGY_BTU = QtyKind(BTU)  # BAD!
```

# Defining details

Details are entirely optional.

```py
from isqx.definitions import _iso80000

MECHANICS: Details = {
    # keys should be direct object references
    _iso80000.MASS: (
        # values can be a tuple of detail objects or just a bare object
        # it is not required to specify the equation if it does not have one.
        Wikidata("Q11423"),
        Symbol(r"m")
    ),
    _iso80000.FORCE: (
        Wikidata("Q11402"),
        Equation(
            r"\boldsymbol{F} = m\boldsymbol{a}",
            {
                r"\boldsymbol{F}": SELF,
                "m": _iso80000.MASS,
                r"\boldsymbol{a}": _iso80000.ACCELERATION,
            },
        ),
    ),
}
```

## Equations and the where clause

- use the KaTeX subset (no macros)
- Vectors: use `\boldsymbol{...}` for vector quantities like force, velocity
- use `\mathrm{...}` for subscripts (where applicable)
- use `\text{...}` for subscripts that are descriptive words.

```py
# good
r"p = p_\text{total} - p_\text{static}"
r"(\eta_\text{th})_\text{max}"

# bad
r"p = p_{total} - p_{static}"
r"(\eta_{th})_{max}"
```

The where clause connects symbols in the KaTeX string to their meanings.

```py
from isqx import SELF

# good
_iso80000.PHASE_SPEED: (
    Equation(
        r"c = \frac{\omega}{k}",
        {
            "c": SELF,  # special marker to refer to the quantity being defined
            ...
        },
        assumptions={...}
    ),
    Symbol("v"), # alternative symbols are fine
    # do not add redundant `Symbol("c")` 
),
```

Always reference other quantities where possible. If it is awkward to define a
formal definition (e.g. "around some axis of rotation"), use a fragments of
strings.

```py
# good
{"m": _iso80000.MASS}

# bad
{"m": "mass"}
# do not create objects inline: mkdocs will be unable to generate a reference
{"m": _iso80000.MASS["body"]}
```

## Symbols

Use it to define alternative symbols, or when a quantity has no defining equation.

```py
_iso80000.MOLE_FRACTION: (
    # ...
    Symbol(
        r"y_\mathrm{X}",
        where={r"\mathrm{X}": "Substance"},
        remarks="for gaseous mixtures",  # provide context on when it should be used
    ),
)
```