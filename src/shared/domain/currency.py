from enum import StrEnum


class Currency(StrEnum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"
    JPY = "JPY"
    CHF = "CHF"

    @classmethod
    def default(cls) -> "Currency":
        return cls.USD
