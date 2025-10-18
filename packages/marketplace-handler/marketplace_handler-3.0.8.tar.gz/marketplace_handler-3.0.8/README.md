# marketplace_handler

Package to interact with marketplaces.

## Installation

### pip
```bash
pip install marketplace_handler
```

### poetry
```bash
poetry add marketplace_handler
```

## Usage
### Wildberries

```python
from marketplace_handler import Wildberries, WbAccount

wb = Wildberries(
    account_data=WbAccount(
        name="name",
        common_token="common_token",
        statistic_token="statistic_token",
        warehouse_id="warehouse_id",
        x_supplier_id="x_supplier_id",
    ),
    mapping_url="mapping_url",
    mapping_token="mapping_token",
)
```        
### Ozon

```python
from marketplace_handler import Ozon, OzonAccount

ozon = Ozon(
    account_data=OzonAccount(
        name="name",
        api_key="api_key",
        client_id="client_id",
        warehouse_id="warehouse_id",
    ),
    mapping_url="mapping_url",
    mapping_token="mapping_token",
)
```
### Yandex

```python
from marketplace_handler import Yandex, YandexAccount

yandex = Yandex(
    account_data=YandexAccount(
        name="name",
        token="token",
        business_id="business_id",
        campaign_id="campaign_id",
    ),
    mapping_url="mapping_url",
    mapping_token="mapping_token",
)
```


TEST