import asyncio

from datetime import datetime
from more_itertools import batched
from collections import namedtuple
from typing import AsyncGenerator, Union, Optional


from pydantic import BaseModel
from aiohttp import ClientSession, ClientResponseError

from marketplace_handler.config import settings
from marketplace_handler.logger import logger
from marketplace_handler.schemas import YandexAccount
from marketplace_handler.marketplace import Marketplace
from marketplace_handler.exceptions import InitialisationException
from marketplace_handler.validators import validate_required_fields


class Yandex(Marketplace):

    def __init__(self, account_data: YandexAccount, session: ClientSession | None = None):

        self._SEND_STOCKS_LIMIT = settings.YANDEX_STOCK_LIMIT
        self._LIMIT_REQUEST_STOCKS = settings.YANDEX_LIMIT_REQUEST_STOCKS
        self._SEND_PRICE_REFRESH_ITEM_LIMIT = settings.YANDEX_PRICE_REFRESH_ITEM_LIMIT
        self._LIMIT_REQUEST_PRODUCTS = settings.YANDEX_LIMIT_REQUEST_PRODUCTS

        self._name = account_data.name
        self._campaign_id = account_data.campaign_id
        self._business_id = account_data.business_id
        self._logger = logger
        self.__token = account_data.token
        self._session = session

        self.request_limits = {}

        if not hasattr(self, "_campaign_id") or not hasattr(self, "_business_id"):
            self._logger.error(f"Campaing or Business id not found for account name: {self._name}")
            raise InitialisationException(f"Campaing or Business id not found for account name: {self._name}")

        self._logger.info(f"Yandex account for {self._name} is initialized.")

    async def _initialize_limits(self, url, method):
        try:
            async with self._session.request(url=url, method=method) as response:

                rate_limit = int(response.headers.get('X-RateLimit-Resource-Limit', 0))
                remaining = int(response.headers.get('X-RateLimit-Resource-Remaining', 0))
                reset_time = response.headers.get('X-RateLimit-Resource-Until', None)

                self._logger.info(f"Rate Limit: {rate_limit}, Remaining: {remaining}, Reset Time: {reset_time}")

                self.request_limits[url] = {
                    'rate_limit': rate_limit,
                    'remaining': remaining,
                    'reset_time': reset_time
                }
        except Exception as e:
            self._logger.error(f"Error while initializing rate limits for {url}: {e}")

    async def __aenter__(self):
        self._logger.info("Session is open")
        self._session = ClientSession()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self.__token}"
            }
        )
        return self

    def add_headers(self):
        self._session.headers.update({
            "Authorization": f"Bearer {self.__token}"
        })

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._logger.info('Closing session')
        await self._session.close()

    async def __request(self, url, method, params=None, json=None, retries=3, **kwargs):
        limit_info = self.request_limits.get(url)

        if limit_info is None:
            await self._initialize_limits(url=url, method=method)
            limit_info = self.request_limits.get(url)

        for attempt in range(retries):
            try:
                remaining = limit_info['remaining']
                reset_time = limit_info['reset_time']

                if remaining == 0 and reset_time:
                    reset_time_obj = datetime.strptime(reset_time, "%a, %d %b %Y %H:%M:%S GMT")
                    wait_time = int((reset_time_obj - datetime.utcnow()).total_seconds())

                    if wait_time > 0:
                        self._logger.warning(f"Rate limit exceeded for {url}. Waiting for {wait_time} seconds until {reset_time_obj}.")
                        await asyncio.sleep(wait_time)

                async with self._session.request(method=method, url=url, params=params, json=json, **kwargs) as response:
                    response.raise_for_status()

                    rate_limit = int(response.headers.get('X-RateLimit-Resource-Limit', 0))
                    remaining = int(response.headers.get('X-RateLimit-Resource-Remaining', 0))
                    reset_time = response.headers.get('X-RateLimit-Resource-Until', None)

                    self._logger.info(f"Rate Limit: {rate_limit}, Remaining: {remaining}, Reset Time: {reset_time}")

                    self.request_limits[url] = {
                        'rate_limit': rate_limit,
                        'remaining': remaining,
                        'reset_time': reset_time
                    }

                    return await response.json()

            except ClientResponseError as e:
                if e.status == 400:
                    self._logger.error("Bad request: Invalid data sent.")
                elif e.status == 420:
                    self._logger.warning(f"Too many requests to {url}: Rate limit exceeded.")
                    await asyncio.sleep(30)
                else:
                    self._logger.error(f"Request failed for {url} with status {e.status}")

            except Exception as e:
                self._logger.error(f"An error occurred for {url}: {e}")

            if attempt < retries - 1:
                self._logger.info(f"Retrying... {attempt + 1}/{retries} for {url}")

        self._logger.error(f"Failed to send data to {url} after all retries.")
        return False

    async def get_products_by_campaign_id(self, statuses: Optional[list[str]] = None) -> AsyncGenerator:
        request_params = {
            'url': f'{settings.yandex_api_url}/campaigns/{self._campaign_id}/offers',
            'method': 'POST',
            'params': {'page_token': '', 'limit': self._LIMIT_REQUEST_PRODUCTS},
            'json':  {
                'statuses': [
                    'PUBLISHED', 'CHECKING', 'DISABLED_BY_PARTNER', 'REJECTED_BY_MARKET',
                    'DISABLED_AUTOMATICALLY', 'CREATING_CARD', 'NO_CARD', 'NO_STOCKS'
                ] if not statuses else statuses
            }
        }

        while True:
            response = await self.__request(**request_params)

            if not response['result']['offers']:
                break

            yield response['result']['offers']

            request_params['params']['page_token'] = response['result'].get('paging', {}).get('nextPageToken', None)
            if not request_params['params']['page_token']:
                break

    async def get_products_by_business_id(self) -> AsyncGenerator:

        url = f'{settings.yandex_api_url}/businesses/{self._business_id}/offer-mappings'
        params = {
            'page_token': '',
            'limit': self._LIMIT_REQUEST_PRODUCTS
        }

        while True:
            products = await self.__request(url=url, method='POST', params=params)

            if not products:
                self._logger.error(f'Could not get price by business_id: {self._business_id}')
                break

            yield products.get("result").get("offerMappings")

            paging = products.get("result").get("paging")
            page_token = paging.get("nextPageToken") if paging else None

            if not page_token:
                break

            params['page_token'] = page_token

    async def get_prices_by_business_id(self) -> AsyncGenerator:

        async for products in self.get_products_by_business_id():

            clean_products = {}

            for product in products:
                offer = product.get("offer")
                offer_id = offer.get("offerId")

                if offer_id not in clean_products:
                    clean_products[offer_id] = {}

                clean_products[offer_id] = {
                    'basic_price': offer.get('basicPrice'),
                    'purchase_price': offer.get('purchasePrice'),
                    'additional_expenses': offer.get('additionalExpenses'),
                    'cofinance_price': offer.get('cofinancePrice'),
                }
            yield clean_products

    async def get_prices_by_campaign_id(self) -> AsyncGenerator:

        async for products in self.get_products_by_campaign_id():

            if not products:
                self._logger.error(f'Could not get price by campaign_id {self._campaign_id}')
                break

            yield {
                product.get("offerId"): {
                    'basic_price': product.get('basicPrice'),
                    'campaign_price': product.get('campaignPrice')
                }
                for product in products
            }

    @validate_required_fields(('offer_id', 'price', 'discount_base'))
    async def refresh_prices_by_business_id(self, products_data: list[Union[dict, BaseModel, namedtuple]]) -> None:
        url = f"{settings.yandex_api_url}/businesses/{self._business_id}/offer-prices/updates"

        for batch in batched(products_data, self._SEND_PRICE_REFRESH_ITEM_LIMIT):
            body = {
                "offers": [
                    {
                        "offerId": item["offer_id"] if isinstance(item, dict) else item.offer_id,
                        "price": {
                            "value": int(item['price'] if isinstance(item, dict) else item.price),
                            "currencyId": "RUR",
                            "discountBase": int(item['discount_base'] if isinstance(item, dict) else item.discount_base)
                        }
                    } for item in batch
                ]
            }

            await self.__request(url=url, method='POST', json=body)

    @validate_required_fields(('offer_id', 'price', 'discount_base'))
    async def refresh_prices_by_campaign_id(self, products_data: list[Union[dict, BaseModel, namedtuple]]) -> None:
        url = f"{settings.yandex_api_url}/campaigns/{self._business_id}/offer-prices/updates"

        for batch in batched(products_data, self._SEND_PRICE_REFRESH_ITEM_LIMIT):
            body = {
                "offers": [
                    {
                        "offerId": item["offer_id"] if isinstance(item, dict) else item.offer_id,
                        "price": {
                            "value": int(item['price'] if isinstance(item, dict) else item.price),
                            "currencyId": "RUR",
                            "discountBase": int(item['discount_base'] if isinstance(item, dict) else item.discount_base)
                        }
                    } for item in batch
                ]
            }

            await self.__request(url=url, method='POST', json=body)

    @validate_required_fields(('code', 'stock'))
    async def refresh_stocks(self, products_data: list[Union[dict, BaseModel, namedtuple]]) -> None:
        for batch in batched(products_data, self._SEND_STOCKS_LIMIT):
            body = {
                "skus": [
                    {
                        "sku": item["code"] if isinstance(item, dict) else item.code,
                        "items": [{"count": item["stock"] if isinstance(item, dict) else item.stock}]
                    }
                    for item in batch
                ]
            }

            await self.__request(
                url=f'{settings.yandex_api_url}/campaigns/{self._campaign_id}/offers/stocks',
                method='PUT',
                json=body
            )

    @validate_required_fields(('code', 'stock'))
    async def refresh_stocks_by_warehouse_id(self, products_data: list[Union[dict, BaseModel, namedtuple]], warehouse):
        for batch in batched(products_data, self._SEND_STOCKS_LIMIT):
            body = {
                "skus": [
                    {
                        "sku": item["code"] if isinstance(item, dict) else item.code,
                        "items": [{"count": item["stock"] if isinstance(item, dict) else item.stock}]
                    }
                    for item in batch
                ]
            }

            await self.__request(
                url=f'{settings.yandex_api_url}/campaigns/{warehouse}/offers/stocks',
                method='PUT',
                json=body
            )

    def refresh_prices(self, products_data: dict):
        raise NotImplementedError

    def refresh_price(self, ms_id, value):
        raise NotImplementedError

    def refresh_stock(self, ms_id, value):
        raise NotImplementedError

    def refresh_status(self, ms_id, value):
        raise NotImplementedError

    def refresh_statuses(self, ids: list[int], values: list[str]):
        raise NotImplementedError

    def __getattr__(self, name):
        if name == "get_all_products":
            return self.get_products_by_campaign_id
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
