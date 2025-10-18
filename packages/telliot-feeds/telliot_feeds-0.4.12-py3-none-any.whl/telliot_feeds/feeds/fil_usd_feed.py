from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price.spot.okx import OKXSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

fil_usd_median_feed = DataFeed(
    query=SpotPrice(asset="FIL", currency="USD"),
    source=PriceAggregator(
        asset="fil",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="fil", currency="usd"),
            KrakenSpotPriceSource(asset="fil", currency="usd"),
            OKXSpotPriceSource(asset="fil", currency="usdt"),
        ],
    ),
)
