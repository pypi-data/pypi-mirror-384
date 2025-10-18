from abc import ABC, abstractmethod


class Marketplace(ABC):
    @abstractmethod
    def refresh_stock(self, ms_id, value):
        pass

    @abstractmethod
    def refresh_price(self, ms_id, value):
        pass

    @abstractmethod
    def refresh_status(self, ms_id, value):
        pass

    @abstractmethod
    def refresh_stocks(self, products_data: list[dict]):
        pass

    @abstractmethod
    def refresh_prices(self, products_data: dict):
        pass

    @abstractmethod
    def refresh_statuses(self, ids: list[int], values: list[str]):
        pass
