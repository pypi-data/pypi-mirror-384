import re
import unicodedata
import datetime


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def normalize_string(string: str, as_upper=False) -> str:
    string = unicodedata.normalize('NFKD', string).encode('ASCII', 'ignore').decode('utf-8')

    if as_upper:
        return string.upper()
    return string


def short_date(date: datetime.date):
    return format(date, '%-d%b%y').upper()


def short_date_without_year(date: datetime.date, data_format: str = '%d%b'):
    return format(date, data_format).upper()


def keep_alphanumeric(input_string):
    return re.sub(r'[^a-zA-Z0-9 ]', '', input_string)
