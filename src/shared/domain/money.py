from decimal import ROUND_HALF_EVEN, Decimal
from typing import Union

from pydantic import BaseModel, ConfigDict, Field

from src.shared.domain.currency import Currency


class Money(BaseModel):
    """
    Immutable value object representing monetary values with strict currency safety
    and exact Decimal arithmetic.
    """

    model_config = ConfigDict(frozen=True)

    amount: Decimal = Field(default=Decimal("0.0000"))
    currency: Currency = Field(default=Currency.USD)

    def __init__(
        self,
        amount: Decimal | str | int = Decimal("0.0000"),
        currency: Currency | str = Currency.USD,
        **data,
    ):
        if isinstance(amount, float):
            raise TypeError(
                "Cannot initialize Money with float to prevent loss of precision. Use Decimal, str, or int."
            )
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        # Quantize to 4 decimal places internally
        amount = amount.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN)
        if isinstance(currency, str):
            currency = Currency(currency)
        super().__init__(amount=amount, currency=currency, **data)

    def __add__(self, other: "Money") -> "Money":
        if not isinstance(other, Money):
            raise TypeError(f"Cannot add {type(other)} to Money")
        if self.currency != other.currency:
            raise ValueError(
                f"Currency mismatch: cannot add {self.currency} and {other.currency} without conversion."
            )
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        if not isinstance(other, Money):
            raise TypeError(f"Cannot subtract {type(other)} from Money")
        if self.currency != other.currency:
            raise ValueError(
                f"Currency mismatch: cannot subtract {other.currency} from {self.currency} without conversion."
            )
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, scalar: Decimal | int | str) -> "Money":
        if isinstance(scalar, float):
            raise TypeError("Cannot multiply Money by float. Use Decimal, int, or str.")
        if not isinstance(scalar, Decimal):
            scalar = Decimal(str(scalar))
        return Money(self.amount * scalar, self.currency)

    def __truediv__(self, divisor: Union[Decimal, int, str, "Money"]) -> Union["Money", Decimal]:
        if isinstance(divisor, float):
            raise TypeError("Cannot divide Money by float. Use Decimal, int, or str.")
        if isinstance(divisor, Money):
            if self.currency != divisor.currency:
                raise ValueError("Cannot compute ratio between different currencies.")
            if divisor.amount == Decimal("0"):
                raise ZeroDivisionError("Cannot divide by zero money.")
            return (self.amount / divisor.amount).quantize(
                Decimal("0.000001"), rounding=ROUND_HALF_EVEN
            )
        if not isinstance(divisor, Decimal):
            divisor = Decimal(str(divisor))
        if divisor == Decimal("0"):
            raise ZeroDivisionError("Cannot divide money by zero.")
        return Money(self.amount / divisor, self.currency)

    def __neg__(self) -> "Money":
        return Money(-self.amount, self.currency)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other: "Money") -> bool:
        self._ensure_same_currency(other)
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        self._ensure_same_currency(other)
        return self.amount <= other.amount

    def __gt__(self, other: "Money") -> bool:
        self._ensure_same_currency(other)
        return self.amount > other.amount

    def __ge__(self, other: "Money") -> bool:
        self._ensure_same_currency(other)
        return self.amount >= other.amount

    def _ensure_same_currency(self, other: "Money") -> None:
        if not isinstance(other, Money):
            raise TypeError(f"Cannot compare Money with {type(other)}")
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot compare different currencies: {self.currency} and {other.currency}"
            )

    @property
    def is_zero(self) -> bool:
        return self.amount == Decimal("0.0000")

    @property
    def is_positive(self) -> bool:
        return self.amount > Decimal("0.0000")

    @property
    def is_negative(self) -> bool:
        return self.amount < Decimal("0.0000")

    def to_display_amount(self) -> Decimal:
        """Returns 2 decimal places for typical fiat display."""
        return self.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

    @classmethod
    def zero(cls, currency: Currency = Currency.USD) -> "Money":
        return cls(Decimal("0.0000"), currency)
