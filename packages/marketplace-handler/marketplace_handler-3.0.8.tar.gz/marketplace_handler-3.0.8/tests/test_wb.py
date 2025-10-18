from datetime import datetime

import pytest
from pydantic import ValidationError
from requests import HTTPError

from marketplace_handler.config import settings
from marketplace_handler.exceptions import InvalidStatusException


class TestWildberries:
    def test_refresh_stock(self, mock_api, wildberries):
        mock_api.put(
            f"{settings.wb_api_url}api/v3/stocks/{wildberries.warehouse_id}",
            status_code=204,
        )
        assert wildberries.refresh_stock("1", 0)

    @pytest.mark.parametrize(
        "ms_id, value",
        [
            ("1", "0"),
            (2, 2),
        ],
    )
    def test_refresh_stock_with_invalid_parameters(
        self, mock_api, wildberries, ms_id, value
    ):
        mock_api.put(
            f"{settings.wb_api_url}api/v3/stocks/{wildberries.warehouse_id}",
            status_code=204,
        )
        with pytest.raises(AssertionError):
            assert wildberries.refresh_stock(ms_id, value)

    def test_refresh_stocks(self, mock_api, wildberries):
        mock_api.put(
            f"{settings.wb_api_url}api/v3/stocks/{wildberries.warehouse_id}",
            status_code=204,
        )
        assert wildberries.refresh_stocks(["1", "2"], [1, 3])

    def test_refresh_stocks_with_invalid_id(self, mock_api, wildberries):
        mock_api.put(
            f"{settings.wb_api_url}api/v3/stocks/{wildberries.warehouse_id}",
            status_code=204,
        )
        with pytest.raises(ValidationError):
            wildberries.refresh_stocks(["1", "3"], [1, 3])

    @pytest.mark.parametrize(
        "ms_ids, values",
        [
            (["1", 2], [2, 3]),
            (["1", "2"], ["str", 3]),
        ],
    )
    def test_refresh_stocks_with_invalid_parameters(
        self, mock_api, wildberries, ms_ids, values
    ):
        mock_api.put(
            f"{settings.wb_api_url}api/v3/stocks/{wildberries.warehouse_id}",
            status_code=204,
        )
        with pytest.raises(ValidationError):
            wildberries.refresh_stocks(ms_ids, values)

    def test_refresh_stocks_with_invalid_length(self, mock_api, wildberries):
        mock_api.put(
            f"{settings.wb_api_url}api/v3/stocks/{wildberries.warehouse_id}",
            status_code=204,
        )
        with pytest.raises(AssertionError):
            wildberries.refresh_stocks(["1", "2"], [1, 2, 3])

    def test_refresh_stocks_with_invalid_warehouse_id(self, mock_api, wildberries):
        wildberries.warehouse_id = wildberries.warehouse_id + 1
        mock_api.put(
            f"{settings.wb_api_url}api/v3/stocks/{wildberries.warehouse_id}",
            status_code=404,
        )
        with pytest.raises(HTTPError):
            wildberries.refresh_stocks(["1", "2"], [1, 2])

    def test_refresh_price(self, mock_api, wildberries, wb_prices):
        assert wildberries.refresh_price("1", 0)

    @pytest.mark.parametrize(
        "ms_id, value",
        [
            ("1", "0"),
            (2, 2),
        ],
    )
    def test_refresh_price_with_invalid_parameters(
        self, mock_api, wildberries, wb_prices, ms_id, value
    ):
        with pytest.raises(AssertionError):
            wildberries.refresh_price(ms_id, value)

    def test_refresh_prices(self, mock_api, wildberries, wb_prices):
        assert wildberries.refresh_prices(["1", "2"], [0, 1])

    @pytest.mark.parametrize(
        "ms_ids, values",
        [
            (["1", 2], [2, 3]),
            (["1", "2"], ["str", 3]),
        ],
    )
    def test_refresh_prices_with_invalid_parameters(
        self, mock_api, wildberries, wb_prices, ms_ids, values
    ):
        with pytest.raises(ValidationError):
            wildberries.refresh_prices(ms_ids, values)

    def test_refresh_prices_with_invalid_length(self, mock_api, wildberries, wb_prices):
        with pytest.raises(AssertionError):
            wildberries.refresh_prices(["1", "2"], [1, 2, 3])

    @pytest.mark.parametrize("status", ["confirm", "cancel"])
    def test_refresh_status(self, wildberries, wb_statuses, status):
        assert wildberries.refresh_status(1234567, status)

    def test_refresh_invalid_status(self, wildberries, wb_statuses):
        with pytest.raises(InvalidStatusException):
            wildberries.refresh_status(1234567, "killmeplease")

    def test_refresh_statuses(self, wildberries, wb_statuses):
        assert wildberries.refresh_statuses([1234567, 1234568], ["confirm", "cancel"])

    def test_refresh_statuses_with_invalid_length(self, wildberries, wb_statuses):
        with pytest.raises(AssertionError):
            wildberries.refresh_statuses(
                [1234567, 1234568], ["confirm", "cancel", "confirm"]
            )

    def test_refresh_statuses_with_invalid_status(self, wildberries, wb_statuses):
        with pytest.raises(InvalidStatusException):
            wildberries.refresh_statuses(
                [1234567, 1234568], ["confirm", "killmeplease"]
            )

    def test_refresh_discount(self, mock_api, wildberries, wb_prices):
        assert wildberries.refresh_price("1", 0)

    @pytest.mark.parametrize(
        "ms_id, value",
        [
            ("1", "0"),
            (2, 2),
        ],
    )
    def test_refresh_discount_with_invalid_parameters(
        self, mock_api, wildberries, wb_prices, ms_id, value
    ):
        with pytest.raises(AssertionError):
            wildberries.refresh_discount(ms_id, value)

    def test_refresh_discounts(self, mock_api, wildberries, wb_prices):
        assert wildberries.refresh_discounts(["1", "2"], [0, 1])

    @pytest.mark.parametrize(
        "ms_ids, values",
        [
            (["1", 2], [2, 3]),
            (["1", "2"], ["str", 3]),
        ],
    )
    def test_refresh_discounts_with_invalid_parameters(
        self, mock_api, wildberries, wb_prices, ms_ids, values
    ):
        with pytest.raises(ValidationError):
            wildberries.refresh_discounts(ms_ids, values)

    def test_refresh_discounts_with_invalid_length(
        self, mock_api, wildberries, wb_prices
    ):
        with pytest.raises(AssertionError):
            wildberries.refresh_discounts(["1", "2"], [1, 2, 3])

    def test_get_stocks(self, mock_api, wildberries, wb_stocks):
        assert wildberries.get_stocks()

    @pytest.mark.parametrize("date_str", ["2021-01-01", "2021-01-01T00:00:00"])
    def test_get_stocks_with_date_and_datetime(
        self, mock_api, wildberries, wb_stocks, date_str
    ):
        assert wildberries.get_stocks(date_str)

    @pytest.mark.parametrize(
        "date_str", ["20210101", "345345345345", "today", f"{datetime.now()}"]
    )
    def test_get_stocks_with_invalid_date(
        self, mock_api, wildberries, wb_stocks, date_str
    ):
        with pytest.raises(ValueError):
            wildberries.get_stocks(date_str)
