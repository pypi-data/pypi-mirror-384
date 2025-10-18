from .config import settings


def get_chunks(ids, values, limit=settings.WB_ITEMS_REFRESH_LIMIT):
    chunks_ids = [ids[i: i + limit] for i in range(0, len(ids), limit)]
    chunks_values = [values[i: i + limit] for i in range(0, len(values), limit)]
    return chunks_ids, chunks_values


def is_too_small_price(price_from_ms: int | float, price_from_market: int | float, percent: float = settings.LOWER_LIMIT) -> bool:
    return price_from_ms <= price_from_market * percent


def is_too_high_price(price_from_ms: int | float, price_from_market: int | float, percent: float = settings.UPPER_LIMIT) -> bool:
    return price_from_ms >= price_from_market * percent
