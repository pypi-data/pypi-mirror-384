from babel.dates import format_date, format_datetime
from babel.numbers import format_currency


def localizedcurrency(value, currency="EUR", locale="fr_FR"):
    try:
        return format_currency(value, currency, locale=locale)
    except Exception:
        return f"{value} {currency}"



def localizeddate(value, date_format='medium', time_format='medium', locale='fr_FR', tzinfo=None):
    """
    Format a date/datetime using Babel.

    :param value: A datetime or date object.
    :param date_format: The date format ('full', 'long', 'medium', 'short').
    :param time_format: The time format ('full', 'long', 'medium', 'short', or 'none' to omit time).
    :param locale: The locale to use (default 'fr_FR').
    :param tzinfo: Optional timezone info.
    :return: A formatted date/datetime string.
    """
    if time_format.lower() == 'none':
        # Format only the date portion.
        return format_date(value, format=date_format, locale=locale)
    else:
        # Format both date and time.
        return format_datetime(value, format=time_format, locale=locale, tzinfo=tzinfo)

