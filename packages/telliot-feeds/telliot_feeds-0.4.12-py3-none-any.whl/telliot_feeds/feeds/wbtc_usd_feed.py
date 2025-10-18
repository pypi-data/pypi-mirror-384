from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.agni import agniFinancePriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.fusionX import fusionXPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price.spot.uniswapV3 import UniswapV3PriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

wbtc_usd_median_feed = DataFeed(
    query=SpotPrice(asset="WBTC", currency="USD"),
    source=PriceAggregator(
        asset="wbtc",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="wbtc", currency="usd"),
            KrakenSpotPriceSource(asset="wbtc", currency="usd"),
            UniswapV3PriceSource(asset="wbtc", currency="usd"),
            agniFinancePriceSource(asset="wbtc", currency="usd"),
            fusionXPriceSource(asset="wbtc", currency="usd"),
        ],
    ),
)
