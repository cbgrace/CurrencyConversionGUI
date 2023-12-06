"""
The currency module contains a class to model a currency object with a country name, currency name, and exchange rate.

Methods:
--------
    convert(self, usd_amount: float) -> str:
        converts usd amount to a given currency (self._currency_name) by multiplying usd amount by self._conversion_rate

"""


class Currency:
    def __init__(self, country_name, currency_name, conversion_rate):
        self._country_name = country_name
        self._currency_name = currency_name
        self._conversion_rate = conversion_rate

    def __str__(self):
        return f"{self._country_name}, {self._currency_name}: {self._conversion_rate}"

    def __repr__(self):
        return f"{self._country_name}, {self._currency_name}: {self._conversion_rate}"

    def convert(self, usd_amount: float) -> str:
        """
        converts usd amount to a given currency (self._currency_name) by multiplying usd amount by self._conversion_rate
        :param usd_amount: USD amount to convert (from gui/user)
        :return: A string e.g. "$100.00 USD = 94.00 Euro"
        """
        converted_currency = usd_amount * float(self._conversion_rate)
        return f"${usd_amount:,.2f} USD = {converted_currency:,.2f} {self._currency_name}"
