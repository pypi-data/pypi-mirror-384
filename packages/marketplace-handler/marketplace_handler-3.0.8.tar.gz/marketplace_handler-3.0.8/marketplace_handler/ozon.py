from collections import namedtuple
from more_itertools import batched
from typing import AsyncGenerator, Union

from pydantic import BaseModel
from aiohttp import ClientSession, ClientResponseError

from marketplace_handler.logger import logger
from marketplace_handler.config import settings
from marketplace_handler.schemas import OzonAccount
from marketplace_handler.marketplace import Marketplace
from marketplace_handler.exceptions import InitialisationException
from marketplace_handler.validators import validate_required_fields


class Ozon(Marketplace):
    def __init__(self, account_data: OzonAccount, session: ClientSession | None = None):
        self._LIMIT_REQUEST_PRODUCTS = settings.OZON_LIMIT_REQUEST_PRODUCTS
        self._LIMIT_REQUEST_PRODUCTS_PRICE = settings.OZON_LIMIT_REQUEST_PRODUCTS_PRICE
        self._SEND_PRICE_REFRESH_ITEM_LIMIT = settings.OZON_SEND_PRICE_REFRESH_ITEM_LIMIT
        self._SEND_LIMIT_STOCKS = settings.OZON_SEND_LIMIT_STOCKS

        self._name = account_data.name
        self.warehouse_id = account_data.warehouse_id
        self._logger = logger
        self._session = session
        self._account_data = account_data

        if not hasattr(self, "warehouse_id"):
            self._logger.error(f"Warehouse ID not found for account name: {self._name}")
            raise InitialisationException(f"Warehouse ID not found for account name: {self._name}")

        self._logger.info(f"Ozon account for {self._name} is initialized")

    async def __aenter__(self):
        self._logger.info('Session is open')
        self._session = ClientSession()
        self._session.headers.update({
            "Client-Id": self._account_data.client_id,
            "Api-Key": self._account_data.api_key,
        })
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._logger.info('Closing session')
        await self._session.close()

    async def __request(self, url, method, params=None, json=None, retries=3, **kwargs):
        for attempt in range(retries):
            try:
                async with self._session.request(method=method, url=url, params=params, json=json, **kwargs) as response:
                    response.raise_for_status()
                    return await response.json()

            except ClientResponseError as e:
                if e.status == 400:
                    self._logger.error("Bad request: Invalid data sent.")
                else:
                    self._logger.error(f"Request failed for {url} with status {e.status}")

            except Exception as e:
                self._logger.error(f"An error occurred for {url}: {e}")

            if attempt < retries - 1:
                self._logger.info(f"Retrying... {attempt + 1}/{retries} for {url}")

        self._logger.error(f"Failed to send data to {url} after all retries.")
        return False

    async def get_prices_from_market(self) -> AsyncGenerator:
        url = f"{settings.ozon_api_url}/v5/product/info/prices"
        body = {
            "filter": {"visibility": "ALL"},
            "limit": self._LIMIT_REQUEST_PRODUCTS_PRICE,
            "cursor": ''
        }

        while True:
            response = await self.__request(url=url, method='POST', json=body)

            if not response['items']:
                break

            yield {
                item['offer_id']: {'basic_price': item['price'], 'price_indexes': item['price_indexes']}
                for item in response.get('items')
            }

            cursor = response.get('cursor')
            if not cursor:
                break

            body['cursor'] = cursor

    @validate_required_fields(('code', 'ozon_after_discount', 'old_price'))
    async def refresh_prices(self, products_data: list[Union[dict, BaseModel, namedtuple]]):
        url = f"{settings.ozon_api_url}/v1/product/import/prices"

        for batch in batched(products_data, self._SEND_PRICE_REFRESH_ITEM_LIMIT):

            body = {
                "prices": [{
                    "offer_id": item["code"] if isinstance(item, dict) else item.code,
                    "price": str(item['ozon_after_discount'] if isinstance(item, dict) else item.ozon_after_discount),
                    "min_price": str(item['ozon_after_discount'] if isinstance(item, dict) else item.ozon_after_discount),
                    "old_price": str(item['old_price'] if isinstance(item, dict) else item.old_price)
                } for item in batch]
            }

            await self.__request(url=url, method='POST', json=body)

    @validate_required_fields(('code', 'stock'))
    async def refresh_stocks(self, products_data: list[Union[dict, BaseModel, namedtuple]]):

        for batch in batched(products_data, self._SEND_LIMIT_STOCKS):
            body = {
                "stocks": [{
                    "offer_id": product["code"] if isinstance(product, dict) else product.code,
                    "stock": product["stock"] if isinstance(product, dict) else product.stock,
                } for product in batch]
            }

            await self.__request(
                url=f'{settings.ozon_api_url}/v2/products/stocks',
                method='POST',
                json=body
            )

    @validate_required_fields(('code', 'stock'))
    async def refresh_stocks_by_warehouse_id(self, products_data: list[Union[dict, BaseModel, namedtuple]], warehouse):
        for batch in batched(products_data, self._SEND_LIMIT_STOCKS):
            body = {
                "stocks": [{
                    "offer_id": product["code"] if isinstance(product, dict) else product.code,
                    "stock": product["stock"] if isinstance(product, dict) else product.stock,
                    "warehouse_id": warehouse
                } for product in batch]
            }

            await self.__request(
                url=f'{settings.ozon_api_url}/v2/products/stocks',
                method='POST',
                json=body
            )

    async def get_all_products(self):
        url = f"{settings.ozon_api_url}/v3/product/list"
        json = {
            "filter": {"visibility": "ALL"},
            "limit": self._LIMIT_REQUEST_PRODUCTS,
            "last_id": ''
        }

        while True:

            response = await self.__request(url=url, method='POST', json=json)

            result = response.get('result')

            if not result.get('items'):
                break

            yield result.get('items')

            json['last_id'] = result.get('last_id', '')

            if not json['last_id']:
                break

    def refresh_price(self, ms_id, value):
        raise NotImplementedError

    def refresh_stock(self, ms_id, value):
        raise NotImplementedError

    def refresh_status(self, wb_order_id, status):
        raise NotImplementedError

    def refresh_statuses(self, wb_order_ids, statuses):
        raise NotImplementedError
