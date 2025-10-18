class Settings:
    # WB
    wb_api_url: str = "https://marketplace-api.wildberries.ru"
    wb_price_url: str = "https://discounts-prices-api.wildberries.ru"
    wb_statistic_url: str = "https://statistics-api.wildberries.ru"
    wb_commission_url: str = "https://common-api.wildberries.ru"
    wb_shadow_url: str = 'https://card.wb.ru/cards/v4/detail'
    WB_LIMIT_REQUEST_PRODUCTS: int = 200
    WB_SEND_STOCKS_LIMIT: int = 200
    WB_SEND_PRICE_REFRESH_ITEM_LIMIT: int = 200
    WB_DISCOUNT = 50

    # OZON
    ozon_api_url: str = "https://api-seller.ozon.ru"
    OZON_LIMIT_REQUEST_PRODUCTS: int = 200
    OZON_LIMIT_REQUEST_PRODUCTS_PRICE: int = 200
    OZON_SEND_PRICE_REFRESH_ITEM_LIMIT: int = 1000
    OZON_SEND_LIMIT_STOCKS: int = 100

    # YANDEX
    yandex_api_url: str = "https://api.partner.market.yandex.ru"
    YANDEX_STOCK_LIMIT = 1000
    YANDEX_LIMIT_REQUEST_STOCKS = 1000
    YANDEX_PRICE_REFRESH_ITEM_LIMIT = 500
    YANDEX_LIMIT_REQUEST_PRODUCTS = 200

    # Limiting upper and lower price
    UPPER_LIMIT: float = 1.75
    LOWER_LIMIT: float = 0.70
    
    # Common
    xpow_solver_url: str = "http://82.97.250.99:8018/x-pow"


settings = Settings()
