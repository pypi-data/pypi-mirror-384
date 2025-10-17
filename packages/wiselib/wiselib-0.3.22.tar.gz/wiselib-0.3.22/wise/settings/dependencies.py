from pydantic import BaseModel


class DelphinusSettings(BaseModel):
    url: str

    timeout: int = 10  # request timeout in seconds

    candles_by_slug_path: str = "/v1/candles-by-slugs"
    last_candle_by_slug_path: str = "/v1/candles-by-slugs/last"

    candles_by_pair_path: str = "/v2/candles-by-pair"
    last_candle_by_pair_path: str = "/v2/candles-by-pair/last"

    usd_price_by_address_path: str = "/v1/price/usd"
    pair_price_by_address_path: str = "/v1/price/pair"


class DelphiSettings(BaseModel):
    url: str
