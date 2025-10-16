Unlike RDBMS where data lives in predefined schemas (with `FOREIGN KEY`
constraints and `JOIN` operations), [Wikidata](https://en.wikipedia.org/wiki/Wikidata)
stores data in a directed labeled graph:

| triple    | description                                | wikidata                   | example                    |
| --------- | ------------------------------------------ | -------------------------- | -------------------------- |
| subject   | node/statement                             | item (`wd:` Q-number)      | the concept of mass        |
| predicate | edge connecting between subject and object | property (`wdt:` P-number) | has symbol                 |
| object    | value of the statement                     | item or literal            | string `m` or number `100` |

[SPARQL](https://www.wikidata.org/wiki/Wikidata:SPARQL_tutorial) is the language
used to query data.

## useful codes

- `P279`: subclass of
- `Q568496`: ISO/IEC 80000
- `P527`: has part
- `P361`: part of
- `P629`: edition or translation of
- `P747`: has edition or translation
- `P1366`: replaced by 
- `P1343`: described by source
- `P958`: section, verse, paragraph or clause
- `P1810`: subject named as
- `P577`: publication date
- `P7973`: symbol

### unit

- `P5061`: unit symbol (monolingual text)
- `P2370`: conversion to si (quantity)
- `P111`: measured physical quantity
- `P12571`: derived from base unit
- `P12956`: exponent of base unit
- `P7431`: Wolfram Language entity ID
- `P8393`: QUDT ID

### quantity

- `Q71550118`: individual quantity
- `P4020`: isqx dimension (math)
- `P2534`: defining formula (math)
- `P7235`: in defining formula
- `P9758`: symbol represents
- `P8111`: recommended unit of measurement*