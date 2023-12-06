from exceptions import DalException
from logging_config import get_logger
import requests

"""
This module contains a single method to fetch conversion data from the Treasury API

Methods:
--------
    fetch_treasury_data():
        Makes HTTP request to the Treasury api and returns the response, also checks for several errors.
        
Constants:
----------
    BASE_URL: the base url for the treasury API
    ENDPOINT: the endpoint for rates of exchange
    DESIRED_PAGE_NUMBER: the page number I want from the treasury API (1)
    DESIRED_PAGE_SIZE: the amount of results I want on my one page 
    
"""

BASE_URL = 'https://api.fiscaldata.treasury.gov/services/api/fiscal_service'
ENDPOINT = '/v1/accounting/od/rates_of_exchange'
DESIRED_PAGE_NUMBER = 1
DESIRED_PAGE_SIZE = 200
logger = get_logger(__name__)


def fetch_treasury_data():
    """
    Makes HTTP request to the Treasury api and returns the response, also checks for several errors.
    :return: response from the treasury api
    """
    logger.info('Fetching currency data from the treasury API')
    url = f"{BASE_URL}{ENDPOINT}"
    params = {'sort': '-record_date',
              'format': 'json',
              'page[number]': DESIRED_PAGE_NUMBER,
              'page[size]': DESIRED_PAGE_SIZE}
    try:
        response = requests.get(url, params=params)
        logger.info('Successfully fetched currency data in DAL')
        return response
    except requests.Timeout as time_out:
        logger.error(f"Request timed out: {time_out}")
        raise DalException
    except requests.ConnectionError as connection_error:
        logger.error(f"Connection failed: {connection_error}")
        raise DalException
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise DalException

