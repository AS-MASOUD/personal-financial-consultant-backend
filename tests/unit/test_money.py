from decimal import Decimal

import pytest

from src.shared.domain.currency import Currency
from src.shared.domain.money import Money


def test_money_initialization():
    m1 = Money(Decimal("100.50"), Currency.USD)
    assert m1.amount == Decimal("100.5000")
    assert m1.currency == Currency.USD

    # Test initialization from string and int
    m2 = Money("50.25", "EUR")
    assert m2.amount == Decimal("50.2500")
    assert m2.currency == Currency.EUR

    m3 = Money(25, Currency.USD)
    assert m3.amount == Decimal("25.0000")


def test_money_float_disallowed():
    with pytest.raises(TypeError, match="Cannot initialize Money with float"):
        Money(10.5, Currency.USD)  # type: ignore[arg-type]


def test_money_addition_and_subtraction():
    m1 = Money("100.00", Currency.USD)
    m2 = Money("45.50", Currency.USD)

    result_add = m1 + m2
    assert result_add.amount == Decimal("145.5000")
    assert result_add.currency == Currency.USD

    result_sub = m1 - m2
    assert result_sub.amount == Decimal("54.5000")


def test_money_currency_mismatch():
    m_usd = Money("100.00", Currency.USD)
    m_eur = Money("100.00", Currency.EUR)

    with pytest.raises(ValueError, match="Currency mismatch"):
        _ = m_usd + m_eur

    with pytest.raises(ValueError, match="Currency mismatch"):
        _ = m_usd - m_eur

    with pytest.raises(ValueError, match="Cannot compare different currencies"):
        _ = m_usd < m_eur


def test_money_multiplication_and_division():
    m = Money("50.00", Currency.USD)
    assert (m * 3).amount == Decimal("150.0000")
    assert (m * Decimal("1.5")).amount == Decimal("75.0000")

    with pytest.raises(TypeError):
        _ = m * 2.5  # type: ignore[operator]

    divided = m / 2
    assert isinstance(divided, Money)
    assert divided.amount == Decimal("25.0000")

    # Ratio of two moneys of same currency
    m2 = Money("100.00", Currency.USD)
    ratio = m / m2
    assert ratio == Decimal("0.500000")


def test_money_comparisons():
    m1 = Money("10.00", Currency.USD)
    m2 = Money("20.00", Currency.USD)
    m3 = Money("10.00", Currency.USD)

    assert m1 < m2
    assert m2 > m1
    assert m1 <= m3
    assert m1 == m3
    assert m1.is_positive
    assert not m1.is_zero
    assert Money.zero(Currency.USD).is_zero
