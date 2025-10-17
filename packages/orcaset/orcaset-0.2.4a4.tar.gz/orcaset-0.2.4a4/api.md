
## API Reference
This section provides a reference for the public API of the `orcaset` package.

### Required Imports

```python
from datetime import date
import datetime
from dateutil.relativedelta import relativedelta
from typing import Any, Callable, Generator, Iterable, Iterator, NamedTuple, Self
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
```

## Package Exports

### orcaset

```python
__all__ = [
    "Node",
    "NodeDescriptor",
    "cached_generator",
    "date_series",
    "merge_distinct",
    "take_first_range",
    "typed_property",
    "yield_and_return",
]
```

### orcaset.financial

```python
__all__ = [
    "Accrual",
    "AccrualSeries",
    "AccrualSeriesBase",
    "Period",
    "YF",
    "merged_periods",
    "Balance",
    "BalanceSeries",
    "BalanceSeriesBase",
    "Payment",
    "PaymentSeries",
    "PaymentSeriesBase",
]
```

## Core Module

### Node

```python
class Node[P]:
    """
    Base class for nodes. Generic with respect to its parent type.
    """

    @property
    def parent(self) -> P:
        """Return the parent of the node."""

    @parent.setter
    def parent(self, parent: P):
        """Set the parent of the node."""

    @property
    def child_nodes(self) -> list["Node"]:
        """
        Immediate children of the node.

        Return a list of all attributes (excluding the `parent`) that are instances of `Node`.
        """

    def cache_clear(self) -> None:
        """Clear cache of the object and any children."""

    def __enter__(self):
        """Context manager returns a deep copy of the entire tree with a cleared cache."""

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the context manager."""

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Implement setattr(self, name, value).
        Sets parent reference for Node instances.
        """

    def __getstate__(self):
        """Helper for pickle. Removes cache from state."""
```

### Decorators

```python
def cached_generator(func):
    """Decorator to cache a generator function."""

def typed_property[T](func: Callable[[Any], T]) -> T:
    """
    Wraps the built-in `property` decorator with type hints equal to the return type.
    Allows subclasses to override attributes with computed properties and pass Pyright type checks.
    """
```

### Utils

```python
def merge_distinct(*iterables: Iterable):
    """
    Merges iterable results into a single sorted sequence without duplicates.

    Input iterables must be sorted. Input iterables are lazily evaluated and
    may be infinite generators.

    >>> merged = merge_distinct((i for i in [1, 3]), (i for i in range(5)))
    >>> list(merged)
    [0, 1, 2, 3, 4]
    """

def date_series(
    start: date, freq: relativedelta, end_offset: relativedelta | None = None
) -> Generator[date, None, None]:
    """
    Returns a generator of dates starting from `start` and incrementing by `freq`.
    If `end_offset` is provided, the series will end at `start + end_offset`.

    Increments dates by adding `i * freq` to `start` for `i` in `0...n`.
    """

def yield_and_return[T](i: Iterable[T]) -> Generator[T, None, T]:
    """
    Yields elements from an iterable and returns the last element.

    This function is useful for yielding from historical data and continuing from the last element.
    Raises ValueError if the iterable is empty.

    Example:
    >>> def continuation(gen):
    ...     last = yield from yield_and_return(gen)
    ...     yield from (last + 1, last + 2)
    >>> list(continuation(range(3)))
    [0, 1, 2, 3, 4]
    """

class take_first_range[T]:
    """
    Take the first range of consecutive items for which the predicate returns true.

    Example:
    >>> list(take_first_range(lambda c: c.isupper(), 'abCDefGHi'))
    ['C', 'D']
    """

    def __init__(
        self,
        iterable: Iterable[T],
        predicate: Callable[[T], bool],
    ):
        """Initialize with an iterable and predicate function."""

    def __iter__(self):
        """Return iterator."""

    def __next__(self) -> T:
        """Return next item matching predicate."""

@dataclass
class NodeDescriptor:
    """
    A description of a node structure, including its class name, attribute name, and children.
    """
    cls_name: str
    attr_name: str | None = None
    children: list["NodeDescriptor"] = field(default_factory=list)
    code: str | None = None

    def flatten(self) -> list[tuple[int, "NodeDescriptor"]]:
        """Flattened structure of the node and its children."""

    def dump(self):
        """Dump the structure to JSON format"""

    def pretty(self, indent: int = 0) -> str:
        """Pretty print the structure of the node."""

    @classmethod
    def describe(cls, node: type[Node]):
        """
        Describe the structure of a Node and its children.
        """
```

## Financial Module

### Period

```python
class Period(NamedTuple):
    """A time period with a start and end date."""

    start: date
    end: date

    @classmethod
    def series(
        cls, start: date, freq: relativedelta, end_offset: relativedelta | None = None
    ) -> Generator[Self, Any, None]:
        """
        Generator of consecutive periods starting from `start`. 
        
        Ends at `start + end_offset` or if `end_offset` is not `None`, otherwise infinite.
        
        Args:
            start: Start date of the first period.
            freq: Period duration.
            end_offset: Optional offset to determine the end date of the last period.
        """

def merged_periods(
    first: Iterable[Period], second: Iterable[Period]
) -> Iterable[Period]:
    """
    Lazily merge two overlapping iterables of periods into a contiguous iterable of distinct periods.

    Requires that the periods in each iterable are sorted by start date.
    """
```

### Year Fraction (YF)

```python
class YF:
    """Common year fraction functions."""

    class _NA:
        def __call__(self, _: date, __: date) -> float:
            """
            Raises NotImplementedError.
            
            No valid YF function. This may be the result of combining Accruals with different year fractions.
            """

        def __repr__(self):
            """Return string representation."""

    class _Actual360:
        def __call__(self, dt1: date, dt2: date) -> float:
            """Returns the fraction of a year between dt1 and dt2 using actual/360 day count convention."""

        def __repr__(self):
            """Return string representation."""

    class _Thirty360:
        def __call__(self, dt1: date, dt2: date) -> float:
            """
            Returns the fraction of a year between `dt1` and `dt2` on 30 / 360 day count basis.
            """

        def __repr__(self):
            """Return string representation."""

    class _CMonthly:
        def __call__(self, dt1: date, dt2: date) -> float:
            """
            Year fraction from but excluding `dt1` to and including `dt2` where each calendar
            month is 1/12th of a year.
            Partial calendar months are treated as actual days elapsed over actual days in the month.

            Example:
            >>> YF.cmonthly(date(2020, 1, 31), date(2020, 2, 29))
            0.08333333333333333
            >>> # Not equal to 1/12th of a year because June and July have different number of days
            >>> # equals [(29/30) + (1/31)] / 12
            >>> YF.cmonthly(date(2020, 6, 1), date(2020, 7, 1))
            0.0832437275985663
            """

        def __repr__(self):
            """Return string representation."""

    actual360 = _Actual360()
    thirty360 = _Thirty360()
    cmonthly = _CMonthly()
    na = _NA()
```

### Accrual

```python
class Accrual:
    """
    An accrual over a period of time with an associated function to calculate partial period accruals.

    Pass a zero argument function as the value to delay evaluation.
    Accessing the value property or comparing equality will force the evaluation of the function.

    Args:
        period: The period of time over which the accrual is calculated.
        value: The value of the accrual for the period.
        yf: A function that takes two dates and returns the fraction of a year between them.
    """

    def __init__(
        self,
        period: Period,
        value: float | Callable[[], float],
        yf: Callable[[date, date], float] | YF._Actual360 | YF._CMonthly | YF._Thirty360,
    ):
        """Initialize an accrual."""

    @property
    def value(self) -> float:
        """Get the accrual value, evaluating if necessary."""

    @classmethod
    def act360(cls, period: Period, value: float | Callable[[], float]) -> "Accrual":
        """Create an accrual using the actual/360 day count convention as the yf."""

    @classmethod
    def cmonthly(cls, period: Period, value: float | Callable[[], float]) -> "Accrual":
        """Create an accrual using the calendar monthly day count convention as the yf."""

    @classmethod
    def thirty360(cls, period: Period, value: float | Callable[[], float]) -> "Accrual":
        """Create an accrual using the 30/360 day count convention as the yf."""

    def split(self, split_date: date) -> tuple["Accrual", "Accrual"]:
        """
        Split an accrual at a given date, proportionally allocating the value.

        Args:
            split_date: The date at which to split the accrual. Must be greater than the start date and less than the end date of the accrual period.
        """

    def __add__(self, other: float | int):
        """Add a scalar value to the accrual value."""

    def __radd__(self, other: float | int):
        """Support for right addition with a scalar value."""

    def __sub__(self, other: float | int):
        """Subtract a scalar value from the accrual value."""

    def __mul__(self, other: float | int):
        """Multiply the accrual value by a scalar."""

    def __rmul__(self, other: float | int):
        """Support for right multiplication with a scalar value."""

    def __truediv__(self, other: float | int):
        """Divide the accrual value by a scalar."""

    def __neg__(self):
        """Negate the accrual value."""

    def __repr__(self) -> str:
        """Return string representation."""

    def __eq__(self, value: object) -> bool:
        """Check equality with another accrual."""
```

### AccrualSeries

```python
class AccrualSeriesBase[P](Node[P]):
    """A series of `Accrual` objects. Subclasses must override `_accruals` to provide consecutive values by ascending date."""

    def _accruals(self) -> Iterable[Accrual]:
        """Abstract method to provide accruals. Must be implemented by subclasses."""

    def __iter__(self) -> Iterator[Accrual]:
        """Iterate over accruals in the series."""

    def rebase(self, periods: Iterable[Period]) -> "AccrualSeries":
        """
        Rebase the accrual series to a new set of periods.

        This method will split existing accruals at the boundaries of the new periods
        and the original accrual periods. The resulting `AccrualSeries` will contain accruals
        for all unique, contiguous periods from both sources.

        Any (partial) periods that do not overlap with any existing accruals will be filled with `0.0`.

        Returns a new `AccrualSeries`.
        """


    def accrue(self, dt1: date, dt2: date) -> float:
        """Calculate the total accrued value of a series between two dates."""

    def w_avg(self, dt1: date, dt2: date) -> float:
        """
        Calculate the weighted average of accrual value between two dates.

        The weights are the year fractions of the accrual periods. Returns 0.0 if no overlap with accruals.
        """

    def after(self, dt: date) -> "AccrualSeries":
        """Get a new `AccrualSeries` containing accruals after the given date. Interpolates a partial accrual starting at `dt`."""

    def __add__(self, other: "AccrualSeriesBase | int | float") -> "AccrualSeriesBase":
        """Add two accrual series together or add a scalar to all accruals."""

    def __radd__(self, other: "AccrualSeriesBase | int | float"):
        """Support for right addition with another accrual series or scalar."""

    def __sub__(self, other: "float | int | AccrualSeriesBase") -> "AccrualSeries":
        """Subtract another accrual series or scalar from this one."""

    def __mul__(self, other: "AccrualSeriesBase | int | float") -> "AccrualSeries":
        """Multiply all accruals by a scalar or another accrual series."""

    def __rmul__(self, other: "AccrualSeriesBase | int | float"):
        """Support for right multiplication with a scalar or another accrual series."""

    def __neg__(self) -> "AccrualSeries":
        """Return a new AccrualSeries that negates the accruals of `self`."""

    def __truediv__(self, other: "AccrualSeriesBase | int | float") -> "AccrualSeries":
        """Divide all accruals by a scalar or another accrual series."""

@dataclass
class AccrualSeries[A: Iterable[Accrual], P](AccrualSeriesBase[P]):
    """
    A series of `Accrual` objects that takes a `series: Iterable[Accrual]` initializer parameter.

    Generic with respect to the type of accrual iterable for (de)serialization purposes.
    The accrual iterable type is taken as the first generic type parameter. Defining the iterable type
    allows the (de)serialization engine to correctly infer how `series` should be (de)serialized.
    """

    series: A

    def _accruals(self) -> Iterable[Accrual]:
        """Yield accruals from the series."""
```

### Payment and PaymentSeries

```python
class Payment:
    """
    Represents a payment made on a specific date.

    Pass a zero argument function as the value to lazily delay evaluation.
    Accessing the value property or comparing equality will force the evaluation of the function.
    """

    def __init__(self, date: datetime.date, value: float | Callable[[], float]):
        """Initialize a payment."""

    @property
    def value(self) -> float:
        """Get the payment value, evaluating if necessary."""

    def __add__(self, other: float | int):
        """Add a scalar value to the payment value."""

    def __radd__(self, other: float | int):
        """Support for right addition with a scalar value."""

    def __sub__(self, other: float | int):
        """Subtract a scalar value from the payment value."""

    def __mul__(self, other: float | int):
        """Multiply the payment value by a scalar."""

    def __rmul__(self, other: float | int):
        """Support for right multiplication with a scalar value."""

    def __truediv__(self, other: float | int):
        """Divide the payment value by a scalar."""

    def __neg__(self):
        """Negate the payment value."""

    def __repr__(self) -> str:
        """Return string representation."""

    def __eq__(self, other: object) -> bool:
        """Check equality with another payment."""

class PaymentSeriesBase[P](Node[P]):
    """A series of `Payment` objects. Subclasses must override `_payments` to provide consecutive values by ascending date."""

    def _payments(self) -> Iterable[Payment]:
        """Abstract method to provide payments. Must be implemented by subclasses."""

    def __iter__(self) -> Iterator[Payment]:
        """Iterate over payments in the series."""

    def on(self, dt: datetime.date) -> float:
        """
        Get the payment at a given date. Returns zero if no payment on the given date.
        """

    def over(self, from_date: datetime.date, to_date: datetime.date) -> float:
        """
        Get the total payment from and excluding `from_date` to and including `to_date`.
        Returns zero if no payments are made in the period.
        """

    def after(self, dt: datetime.date) -> "PaymentSeries":
        """Get a new `PaymentSeries` containing payments after the given date."""

    def __add__(self, other: "PaymentSeriesBase | float | int") -> "PaymentSeries":
        """Add two payment series together or add a scalar to all payments."""

    def __radd__(self, other: "PaymentSeriesBase | float | int"):
        """Support for right addition with another payment series or scalar."""

    def __sub__(self, other: "PaymentSeriesBase | float | int") -> "PaymentSeries":
        """Subtract another payment series or scalar from this one."""

    def __mul__(self, other: "PaymentSeriesBase | float | int") -> "PaymentSeries":
        """Multiply all payments by a scalar or another payment series."""

    def __rmul__(self, other: "PaymentSeriesBase | float | int"):
        """Support for right multiplication with a scalar or another payment series."""

    def __truediv__(self, other: "PaymentSeriesBase | float | int") -> "PaymentSeries":
        """Divide all payments by a scalar or another payment series."""

    def __neg__(self) -> "PaymentSeries":
        """Return a new PaymentSeries that negates the payments of `self`."""

@dataclass
class PaymentSeries[P](PaymentSeriesBase[P]):
    """A series of payments that takes a `payment_series: Iterable[Payment]` constructor variable."""

    payment_series: Iterable[Payment]

    def _payments(self) -> Iterable[Payment]:
        """Yield payments from the payment_series."""
```

### Balance and BalanceSeries

```python
class Balance:
    """
    Represents a financial balance at a specific date.

    Pass a zero argument function as the value to lazily delay evaluation.
    Accessing the value property or comparing equality will force the evaluation of the function.
    """

    def __init__(self, date: datetime.date, value: float | Callable[[], float]):
        """Initialize a balance."""

    @property
    def value(self) -> float:
        """Get the balance value, evaluating if necessary."""

    def __add__(self, other: float | int):
        """Add a scalar value to the balance value."""

    def __radd__(self, other: float | int):
        """Support for right addition with a scalar value."""

    def __sub__(self, other: float | int):
        """Subtract a scalar value from the balance value."""

    def __mul__(self, other: float | int):
        """Multiply the balance value by a scalar."""

    def __rmul__(self, other: float | int):
        """Support for right multiplication with a scalar value."""

    def __truediv__(self, other: float | int):
        """Divide the balance value by a scalar."""

    def __neg__(self):
        """Negate the balance value."""

    def __repr__(self) -> str:
        """Return string representation."""

    def __eq__(self, other: object) -> bool:
        """Check equality with another balance."""

class BalanceSeriesBase[P](Node[P]):
    """A series of `Balance` objects. Subclasses must override `_balances` to provide consecutive values by ascending date."""

    def _balances(self) -> Iterable["Balance"]:
        """Abstract method to provide balances. Must be implemented by subclasses."""

    def __iter__(self) -> Iterator[Balance]:
        """Iterate over balances in the series."""

    def at(self, dt: datetime.date) -> float:
        """Get the balance at a given date. Returns zero balance if date is outside the range of the series."""

    def rebase(self, dates: Iterable[datetime.date]) -> "BalanceSeries[None]":
        """
        Rebase the balance series to include balances on dates in `dates`.

        Pads with zero balances if for any date in `dates` that is before the series starts.
        """

    def after(self, dt: datetime.date) -> "BalanceSeries":
        """Return a new `BalanceSeries` from and including `dt`. Interpolates the balance at `dt` if it does not exist."""

    def avg(self, dt1: datetime.date, dt2: datetime.date, yf: YfType) -> float:
        """Return the average balance between two dates. First date must not be after second date."""

    def __add__(self, other: "float | int | BalanceSeriesBase") -> "BalanceSeries":
        """Add two balance series together or add a scalar to all balances."""

    def __sub__(self, other: "float | int | BalanceSeriesBase") -> "BalanceSeries":
        """Subtract another balance series or scalar from this one."""

    def __mul__(self, other: "float | int | BalanceSeriesBase") -> "BalanceSeries":
        """Multiply all balances by a scalar or another balance series."""

    def __truediv__(self, other: "float | int | BalanceSeriesBase") -> "BalanceSeries":
        """Divide all balances by a scalar or another balance series."""

    def __neg__(self) -> "BalanceSeries":
        """Return a new BalanceSeries that negates the balances of `self`."""

@dataclass
class BalanceSeries[P](BalanceSeriesBase[P]):
    """A convenience class for creating a balance series from an `Iterable[Balance]`."""

    series: Iterable[Balance]

    def _balances(self) -> Iterable[Balance]:
        """Yield balances from the series."""
```