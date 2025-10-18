import asyncio
from collections import namedtuple
from typing import Union
from more_itertools import batched

from aiohttp import ClientSession, ClientResponseError
from pydantic import BaseModel

from marketplace_handler.exceptions import InitialisationException
from marketplace_handler.logger import logger
from marketplace_handler.config import settings
from marketplace_handler.marketplace import Marketplace
from marketplace_handler.schemas import WbAccount
from marketplace_handler.validators import validate_required_fields


class Wildberries(Marketplace):
    def __init__(self, account_data: WbAccount, session: ClientSession | None = None):
        self._LIMIT_REQUEST_PRODUCTS = settings.WB_LIMIT_REQUEST_PRODUCTS
        self._SEND_STOCKS_LIMIT = settings.WB_SEND_STOCKS_LIMIT
        self._SEND_PRICE_REFRESH_ITEM_LIMIT = settings.WB_SEND_PRICE_REFRESH_ITEM_LIMIT

        self._logger = logger
        self._session = session
        self._name = account_data.name
        self.__common_token = account_data.common_token
        self.__statistic_token = account_data.statistic_token

        self._warehouse_id = account_data.warehouse_id

        if not hasattr(self, '_warehouse_id'):
            self._logger.error('Warehouse id is not found')
            raise InitialisationException('Warehouse id is not found')

        self._logger.debug(f'Wildberries account for {self._name} is initialized.')

    async def __aenter__(self):
        self._logger.info("Session is open")
        self._session = ClientSession()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self.__common_token}"
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._logger.info('Closing session')
        await self._session.close()

    def add_headers(self):
        self._session.headers.update({
            "Authorization": f"Bearer {self.__common_token}"
        })

    async def __request(self, url, method, params=None, json=None, retries=3, **kwargs):

        for attempt in range(retries):
            try:
                async with self._session.request(method=method, url=url, params=params, json=json, **kwargs) as response:
                    if response.status == 204:
                        self._logger.warning('Stocks was sent, but WB return 204 status. It is okay.')
                        return None

                    response.raise_for_status()
                    return await response.json()

            except ClientResponseError as e:
                if e.status == 400:
                    self._logger.error("Bad request: Invalid data sent.")
                elif e.status == 429:
                    self._logger.warning(f"Too many requests to {url}")
                    await asyncio.sleep(30)
                else:
                    self._logger.error(f"Request failed for {url} with status {e.status}")

            except Exception as e:
                self._logger.error(f"An error occurred for {url}: {e}")

            if attempt < retries - 1:
                self._logger.info(f"Retrying... {attempt + 1}/{retries} for {url}")

        self._logger.error(f"Failed to send data to {url} after all retries.")
        return None

    async def get_all_products(self):
        url = f"{settings.wb_price_url}/api/v2/list/goods/filter"
        params = {
            "limit": self._LIMIT_REQUEST_PRODUCTS,
            "offset": 0
        }

        while True:
            response = await self.__request(url=url, method='GET', params=params)
            list_goods = response.get('data').get('listGoods')

            if not list_goods:
                break

            yield list_goods

            params['offset'] += self._LIMIT_REQUEST_PRODUCTS

    async def __setup_xpow_token(self) -> str:
        async with ClientSession() as local_session:
            x_pow_token = ""
            try:
                async with local_session.get(url=settings.xpow_solver_url) as response:
                    if response.ok:
                        response_payload = await response.json()
                        x_pow_token = response_payload.get("x-pow", "")
                    else:
                        self._logger.warning(f"Couldn't get the x-pow token: {response}")
            finally:
                return x_pow_token
        
    async def get_prices_from_market(self):
        async for products in self.get_all_products():
            price_products = {}

            for product in products:
                    price = product['sizes'][0]['price']
                    discount = product["discount"]

                    price_products.update({product["nmID"]: (price, discount)})

            yield products

    async def get_stock_by_alter_api(self, nms_id: list[str]):

        async with ClientSession() as local_session:
            for batch in batched(nms_id, self._LIMIT_REQUEST_PRODUCTS):

                params = {
                    'appType': 1,
                    'regions': '80,38,4,64,83,33,68,70,69,30,86,75,40,1,66,110,22,31,48,71,114',
                    'dest': -2133464,
                    'nm': ';'.join(batch),
                    'curr': 'rub',
                    'spp': 30
                }

                headers = {
                    "x-pow": await self.__setup_xpow_token()
                }

                async with local_session.get(url=settings.wb_shadow_url, params=params, headers=headers) as response:

                    products = (await response.json()).get('products', {})

                    if not products:
                        continue

                    yield {
                        str(item.get('id')): size.get('stocks')
                        for item in products
                        for size in item.get('sizes')
                    }

    @validate_required_fields(('wb_barcodes', 'stock'))
    async def refresh_stocks_by_warehouse_id(self, products_data: list[Union[dict, BaseModel, namedtuple]], warehouse) -> None:
        url = f"{settings.wb_api_url}/api/v3/stocks/{warehouse}"
        for batch in batched(products_data, self._SEND_STOCKS_LIMIT):

            body = {
                "stocks": [
                    {
                        "sku": product["wb_barcodes"] if isinstance(product, dict) else product.wb_barcodes,
                        "amount": product["stock"] if isinstance(product, dict) else product.stock
                    }
                    for product in batch
                ]
            }
            await self.__request(url=url, method='PUT', json=body)

    @validate_required_fields(('nm_id', 'origin_price', 'market_discount'))
    async def refresh_prices(self, products_data: list[Union[dict, BaseModel, namedtuple]]) -> None:
        url = f"{settings.wb_price_url}/api/v2/upload/task"

        for batch in batched(products_data, self._SEND_PRICE_REFRESH_ITEM_LIMIT):

            self.validate_discount(batch)

            body = {"data": [
                {
                    'nmID': item["nm_id"] if isinstance(item, dict) else item.nm_id,
                    'price': item["origin_price"] if isinstance(item, dict) else item.origin_price,
                    'discount': item["market_discount"] if isinstance(item, dict) else item.market_discount,
                } for item in batch
            ]}

            await self.__request(url=url, method='POST', json=body)


    @staticmethod
    def validate_discount(products):
        for product in products:
            if isinstance(product, dict):
                if product.get('market_discount') != settings.WB_DISCOUNT:
                    product['market_discount'] = settings.WB_DISCOUNT
            else:
                if product.market_discount != settings.WB_DISCOUNT:
                    product.market_discount = settings.WB_DISCOUNT


    def refresh_price(self, ms_id, value):
        raise NotImplementedError

    def refresh_stock(self, ms_id, value):
        raise NotImplementedError

    def refresh_stocks(self, products_data: list[dict]):
        raise NotImplementedError

    def refresh_status(self, ms_id, value):
        raise NotImplementedError

    def refresh_statuses(self, ids: list[int], values: list[str]):
        raise NotImplementedError

    def get_stocks(self):
        raise NotImplementedError
