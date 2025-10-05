import marimo

__generated_with = "0.16.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Fluent Python""")
    return


@app.cell
def _():
    from random import choice

    return (choice,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### The tip of an iceberg: Python Data Model
    * Ever wonder why we call `len(collection)`, instead of `collection.len()`? This oddity is the tip of an iceberg: the *Python Data Model*
    * it defines the **special methods** (often called *dunder methods*, like `__getitem__`, `__len__`, `__repr__`) that classes can implement.

    Hence, objects integrate naturally with Python’s syntax and built-ins: batteries included 🔋!

    `len(obj)` calls `obj.__len__()`

    `obj[i]` calls `obj.__getitem__(i)`

    `print(obj)` calls `obj.__str__()` or `obj.__repr__()`
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### Special Methods
    * To better appreciate the "batteries included"-aspect of implementing special methods consider this (see page 5):
    """
    )
    return


@app.cell
def _():
    import collections

    Card = collections.namedtuple("Card", ["rank", "suit"])

    class FrenchDeck:
        ranks = [str(n) for n in range(2, 11)] + list("JQKA")
        suits = "spades diamonds clubs hearts".split()

        def __init__(self):
            self._cards = [
                Card(rank, suit) for suit in self.suits for rank in self.ranks
            ]

        def __len__(self):
            return len(self._cards)

        def __getitem__(self, position):
            return self._cards[position]

    return Card, FrenchDeck


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Now we can be super flexible 🕺 with the batteries, e.g. like so:""")
    return


@app.cell
def _(FrenchDeck):
    deck = FrenchDeck()
    len(deck)
    return (deck,)


@app.cell
def _(choice, deck):
    choice(deck)
    return


@app.cell
def _(deck):
    type(deck)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""and/or like so (powered by `__getitem__` 👇):""")
    return


@app.cell(hide_code=True)
def _(deck):
    deck[:3]
    return


@app.cell
def _(deck):
    for card in deck:
        print(card)
    return


@app.cell
def _(deck):
    for reversed_card in reversed(deck):
        print(reversed_card)
    return


@app.cell
def _(Card, FrenchDeck, deck):
    suit_vals = {"spades": 3, "hearts": 2, "diamonds": 1, "clubs": 0}

    def spades_high(card: Card) -> int:
        rank_value = FrenchDeck.ranks.index(card.rank)
        return rank_value * len(suit_vals) + suit_vals[card.suit]

    for sorted_card in sorted(deck, key=spades_high):
        print(sorted_card)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    * so `__getitem__` enables us to
        - slice, iterate thru our instance and sort it!
        - why? cos when we implement special methods like `__getitem__` and `__len__`, `FrenchDeck` behaves like a standard Python *sequence* 💡!
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""While `FrenchDeck` implicitly inherits from `object`, **most of its functionality is not inherited**, but comes from leveraging the Data Model as well as from composition."""
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### How to use Special Methods
    * so, coming back to our initial question of why `len(collection)`, instead of `collection.len()`
        - special methods **are meant to be called by the Python interpreter, not by you**
        - meaning that if `my_object` is an instance of a user defined class, then `len(my_object)` calls the `__len__` you implemented
    * normally, you should be implementing special methods more often than invoking them explicitly;
        - if you need to invoke a special  method, it's usually better to call the related built-in function (e.g. `len`, `iter`, `str`,...) (the latter call special methods themselves, which is often faster )
        - the only exception `__init__`
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### The Most Important Uses of Special Methods
    * Emulating Numeric Types
    * String Representation
    * Boolean Value of a Custom Type

    ### Re Emulating Numeric Types: see pages 9-12
    ### String Representation: `__repr__` and `__str__`
    #### `__repr__`
    * The `__repr__` special medthos is called by the `repr` built-in to get the string-representation of the object for inspection
    * if you don’t implement it, Python falls back to the default implementation from object, which looks like
    ```python
    <ClassName object at 0x...>
    ```
    * if you do, your objects show meaningful info in:
    - The interactive console (REPL, Jupyter, etc.)
    - Debugging logs
    - Collections (lists, dicts) — because they call `repr` on their elements
    - Example usage
    ```python
    class Card:
        def __init__(self, rank, suit):
            self.rank = rank
            self.suit = suit

        def __repr__(self):
            return f"Card({self.rank!r}, {self.suit!r})"
    ```
    * `!r` in an f-string calls `repr()` on the variable, ensuring the representation is unambiguous (e.g., includes quotes around strings, as in `Vector(1,2)` vs `Vector('1','2')`)
    #### `__str__`
    * it's called by `str()` built-in and implicitly used by the `print` function: it **should return a string suitable for display to end users**
    #### `__repr__` vs `__str__`
    ##### Behavior
    * repr(obj) → calls obj.__repr__()
    * str(obj) → calls obj.__str__(), but falls back to __repr__() if not implemented
    * Interactive consoles (>>> obj) and containers ([obj]) use __repr__
    - Additional example
    ```python
    class Card:
        def __init__(self, rank, suit):
            self.rank = rank
            self.suit = suit

        def __repr__(self):
            # Developer-focused: unambiguous, includes quotes
            return f"Card({self.rank!r}, {self.suit!r})"

        def __str__(self):
            # User-focused: friendly, readable
            return f"{self.rank} of {self.suit}"
    ```
    and usage
    ```python
    c = Card("7", "hearts")

    print(repr(c))   # Calls __repr__
    # Output: Card('7', 'hearts')

    print(str(c))    # Calls __str__
    # Output: 7 of hearts

    print(c)         # Also calls __str__
    # Output: 7 of hearts

    cards = [c]
    print(cards)     # Uses __repr__ for contained objects
    # Output: [Card('7', 'hearts')]
    ```
    #### Best practices
    * Always implement __repr__ in custom classes — it’s invaluable for debugging
    * Make __repr__ unambiguous; use !r in f-strings for clarity
    * Use __str__ only if you want a different user-facing display. (if not, Python will fall back to __repr__ automatically)
    """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""### Examples""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r""" """)
    return


if __name__ == "__main__":
    app.run()
