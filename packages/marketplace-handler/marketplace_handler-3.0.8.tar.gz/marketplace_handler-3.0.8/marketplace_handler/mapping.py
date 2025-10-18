from typing import List, Dict, TypeVar, Type

from pydantic import BaseModel
from requests import Session

from marketplace_handler.config import settings
from marketplace_handler.logger import logger
from marketplace_handler.schemas import MsItem, WbItem, OzonItem, YandexItem
from marketplace_handler.validators import validate_ids_and_values


NameItem = TypeVar('NameItem', bound=BaseModel)


class Mapping:

    def __init__(self, url: str, mapping_token: str):
        self._logger = logger
        self.session = Session()
        self.session.headers.update(
            {
                "Authorization": mapping_token,
            }
        )
        self.mapping_url = url + "/collector/v1/mapping"
        self.product_url = url + "/collector/v1/products/additional/cmd_list"

    @validate_ids_and_values
    def get_mapped_data(self, ms_ids: List[str], values: List[int], name_market_barcode) -> List[MsItem]:
        if len(ms_ids) == 1:
            ms_items = self.session.get(
                f"{self.mapping_url}", params={"ms_id": ms_ids[0]}
            )
            ms_items = ms_items.json()[0]
            ms_items["barcodes"] = ms_items[name_market_barcode]
            return [MsItem(**ms_items, value=values[0])]

        mapped_data = []
        for i in range(0, len(ms_ids), settings.MAPPING_LIMIT):
            ms_ids_chunk = ms_ids[i: i + settings.MAPPING_LIMIT]
            values_chunk = values[i: i + settings.MAPPING_LIMIT]
            ms_items = self.session.get(
                f"{self.mapping_url}", params={"ms_id": ",".join(ms_ids_chunk)}
            )

            id_value_map = dict(zip(ms_ids_chunk, values_chunk))

            for item in ms_items.json():
                value = id_value_map.get(item["ms_id"])
                item["value"] = value
                item["barcode"] = item[name_market_barcode]
                mapped_data.append(MsItem(**item))

        return mapped_data

    def get_mapped_data_by_nm_ids(self, stocks_data: Dict) -> List[Dict]:
        mapped_data = []
        response = []
        nm_ids = list(stocks_data.keys())
        for i in range(0, len(nm_ids), settings.MAPPING_LIMIT):
            nm_ids_chunk = nm_ids[i: i + settings.MAPPING_LIMIT]
            mapped_data.extend(
                self.session.get(
                    f"{self.mapping_url}", params={"nm_id": ",".join(nm_ids_chunk)}
                ).json()
            )

        for elem in mapped_data:
            if stocks_data.get(elem.get("nm_id")):
                response.append(
                    {
                        "ms_id": elem.get("ms_id"),
                        "nm_id": elem.get("nm_id"),
                        "barcode": stocks_data.get(elem.get("nm_id")).get("barcode"),
                        "quantity": stocks_data.get(elem.get("nm_id")).get("quantity"),
                    }
                )
        return response

    def get_product_data(self, ms_ids: list[str], name_base_item: Type[NameItem]) -> List[NameItem]:

        mapped_data = self.session.post(self.product_url, json={"ms_id": ms_ids}).json()
        return [name_base_item(**item) for item in mapped_data]

    @staticmethod
    def _get_from_market_products(keys_product, ms_products):

        for key in keys_product:
            product_ms = ms_products['single_key'].get(key)
            if product_ms:
                return product_ms

        for key_product in keys_product:
            for keys_in_ms in ms_products['multy_key']:
                if key_product in keys_in_ms:
                    return ms_products['multy_key'].get(keys_in_ms)

        return None

    def mapped_data(self, ms_products: dict, market_products: dict, name_base_item: Type[NameItem]) -> List[NameItem]:

        mapped_data = []

        for keys_product, price_product in market_products.items():

            product_ms = self._get_from_market_products(keys_product, ms_products)

            if not product_ms:
                logger.warning(f'Cannot mapped product. Not found barcodes from market - {keys_product} in MS data. Skipped')
                continue

            instance = name_base_item(**product_ms)

            if name_base_item == WbItem and not instance.nm_id:
                self._logger.error(f"Product {instance.ms_id} does not have nm_id")
                continue
            elif name_base_item == OzonItem and not instance.code:
                self._logger.error(f"Product {instance.ms_id} does not have ozon_sku")
                continue

            if name_base_item == WbItem:
                instance.market_price = price_product[0] - (price_product[0] * price_product[1]) / 100
                instance.market_discount = price_product[1]
            elif name_base_item == YandexItem:
                instance.offer_id = price_product[0]
                instance.market_price = price_product[1]
            else:
                instance.market_price = price_product

            if not instance.market_price:
                self._logger.warning(f"For {instance.ms_id} not price in market {name_base_item.__name__}")
                continue

            mapped_data.append(instance)

        return mapped_data
