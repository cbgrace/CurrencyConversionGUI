import dal
import models
import requests
import functools
from datetime import datetime, timedelta
from exceptions import BusinessLogicException, DalException
from logging_config import get_logger

"""
This module contains method for retrieving data from the DAL and parsing it into a usable format for the GUI layer

Methods:
--------
    find_last_quarter_date():
        Generates the last day of the last quarter. (so currently, 2023-09-30, but will work indefinitely.)
    get_currency_data():
        Retrieves conversion rate data response from the DAL
    handle_request_errors(func):
        Wrapper to handle errors for the below method (just wanted to implement one of these...)
    parse_treasury_response(response):
        Parses the conversion rate data from the API response into JSON, then into a dict of Currency objects.
        
Constants:
----------
    APRIL: the numeric value for the month of (see name)
    ONE_YEAR_IN_DAYS: the number of days in one year
    JULY: the numeric value for the month of (see name)
    OCTOBER: the numeric value for the month of (see name)
    DECEMBER: the numeric value for the month of (see name)
"""

APRIL = 4
ONE_YEAR_IN_DAYS = 365
JULY = 7
OCTOBER = 10
DECEMBER = 12
logger = get_logger(__name__)


def find_last_quarter_date():
    """
    Generates the last day of the previous quarter. (so currently, 2023-09-30, but will work indefinitely.)
    :return: the last day of the previous quarter (datetime.date object)
    """
    today = datetime.now()
    logger.info(f"Grabbing today's date, {today.date()}")
    if today.month < APRIL:
        today -= timedelta(days=ONE_YEAR_IN_DAYS)  # years=1 is not an option?
        last_quarter = datetime.strptime(f"{today.year}-12-31", '%Y-%m-%d').date()
        logger.info(f"Established last quarter as {last_quarter}")
        return last_quarter
    elif today.month < JULY:
        last_quarter = datetime.strptime(f"{today.year}-03-31", '%Y-%m-%d').date()
        logger.info(f"Established last quarter as {last_quarter}")
        return last_quarter
    elif today.month < OCTOBER:
        last_quarter = datetime.strptime(f"{today.year}-06-30", '%Y-%m-%d').date()
        logger.info(f"Established last quarter as {last_quarter}")
        return last_quarter
    elif today.month <= DECEMBER:
        last_quarter = datetime.strptime(f"{today.year}-09-30", '%Y-%m-%d').date()
        logger.info(f"Established last quarter as {last_quarter}")
        return last_quarter
    else:
        logger.error('Something went wrong trying to generate the previous quarter...')
        raise BusinessLogicException


def get_currency_data():
    """
    Retrieves conversion rate data response from the DAL
    :return: currency_dict, the result of parse_treasury_response()
    """
    try:
        # all of these calls should be logged elsewhere
        response = dal.fetch_treasury_data()
        currency_dict = parse_treasury_response(response)
        return currency_dict
    except (DalException, BusinessLogicException):
        # this will already be logged as well
        raise BusinessLogicException


def handle_request_errors(func):
    """
    Wrapper to handle errors for the below method (just wanted to implement one of these...)
    :param func: the function to be wrapped
    :return: either the result of func or one of several errors.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except requests.HTTPError as http_error:
            logger.error(f"Failed HTTP Response: {http_error}")
            raise BusinessLogicException
        except requests.JSONDecodeError as json_error:
            logger.error(f"Invalid format received: {json_error}")
            raise BusinessLogicException
        except (KeyError, IndexError) as dict_error:
            logger.error(f"Expected data not found: {dict_error}")
            raise BusinessLogicException
    return wrapper


@handle_request_errors
def parse_treasury_response(response):
    """
    Parses the conversion rate data from the API response into JSON, then into a dict of Currency objects.
    :param response: response from treasury API call.
    :return: currency_dict, a dictionary of Currency objects.
    """
    logger.info("Attempting to parse response from Treasury API")
    response.raise_for_status()
    response_json = response.json()
    last_quarter_date = find_last_quarter_date()
    currency_dict = {}
    extra_currency_counter = 0  # for testing
    for result in response_json['data']:
        # grab variables
        record_date = datetime.strptime(result['record_date'], '%Y-%m-%d').date()
        country_name = result['country']
        currency_name = result['currency']
        exchange_rate = result['exchange_rate']
        # check if the record date = the last date of the previous quarter (these figures are published quarterly)
        if record_date == last_quarter_date:
            # check if the country is already in the dict (there will be a few countries with multiple currencies)
            if country_name in currency_dict.keys():
                new_currency = models.Currency(country_name, currency_name, exchange_rate)
                # if it is, add the new currency
                extra_currency_counter += 1  # for testing
                currency_dict[country_name].append(new_currency)
            else:
                # if not, create a new dict key and add the Currency object to it.
                new_country = models.Currency(country_name, currency_name, exchange_rate)
                currency_dict[country_name] = [new_country]
    logger.info("Successfully parsed API response into currency_dict")
    logger.info(f"Parsed {(len(currency_dict.values())) + extra_currency_counter} currencies from {len(currency_dict.keys())} countries")
    return currency_dict


