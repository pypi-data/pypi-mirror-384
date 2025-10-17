"""
Parser for convert Bitfinex REST API/WSS response to Binance like result
"""
import time
from decimal import Decimal
import logging
from typing import Dict, List, Union

logger = logging.getLogger(__name__)


class OrderBook:
    def __init__(self, _order_book, symbol) -> None:
        self.symbol = symbol[1:].replace(':', '').lower()
        self.last_update_id = 1
        self.asks = {}
        self.bids = {}
        for i in _order_book:
            if i[2] > 0:
                self.bids[str(i[0])] = str(i[2])
            else:
                self.asks[str(i[0])] = str(abs(i[2]))

    def get_book(self) -> dict:
        bids = [list(item) for item in self.bids.items()]
        bids.sort(key=lambda x: float(x[0]), reverse=True)
        asks = [list(item) for item in self.asks.items()]
        asks.sort(key=lambda x: float(x[0]), reverse=False)
        return {
            'stream': f"{self.symbol}@depth5",
            'data': {
                'lastUpdateId': self.last_update_id,
                'bids': bids[:5],
                'asks': asks[:5],
            },
        }

    def update_book(self, _update):
        self.last_update_id += 1
        if _update[1]:
            if _update[2] > 0:
                self.bids[str(_update[0])] = str(_update[2])
            else:
                self.asks[str(_update[0])] = str(abs(_update[2]))
        elif _update[2] > 0:
            self.bids.pop(str(_update[0]), None)
        else:
            self.asks.pop(str(_update[0]), None)

    def __call__(self):
        return self


def get_symbols(symbols_details: list, symbol) -> str:
    symbols = []
    res = ",t"
    for symbol_details in symbols_details:
        _symbol = symbol_details['pair']
        if 'f0' not in _symbol and _symbol.replace(":", "").upper() == symbol:
            symbols.append(_symbol.upper())
    return f"t{res.join(symbols)}"


def tick_size(precision, _price):
    x = int(_price)
    _price = str(_price)
    if '.' not in _price:
        _price += ".0"
    k = len(_price.split('.')[1])
    x = len(_price.split('.')[0]) if k and x else 0
    if k + x - precision > 0:
        k = precision - x
    elif k + x - precision < 0:
        k += precision - x - k
    return (1 / 10 ** k) if k else 1


def symbol_name(_pair: str) -> ():
    if ':' in _pair:
        pair = _pair.replace(':', '').upper()
        base_asset = _pair.split(':')[0].upper()
        quote_asset = _pair.split(':')[1].upper()
    else:
        pair = _pair.upper()
        base_asset = _pair[:3].upper()
        quote_asset = _pair[3:].upper()
    return pair, base_asset, quote_asset


def exchange_info(symbols_details: list, tickers: list, symbol_t) -> dict:
    symbols = []
    symbols_price = {
        pair[0].replace(':', '').upper()[1:]: pair[7] for pair in tickers
    }
    for market in symbols_details:
        if 'f0' not in market.get("pair"):
            _symbol, _base_asset, _quote_asset = symbol_name(market.get("pair"))
            if _symbol == symbol_t:
                _base_asset_precision = len(str(market.get('minimum_order_size'))) - 2
                # Filters var
                _price = symbols_price.get(_symbol, 0.0)
                _tick_size = tick_size(market.get('price_precision'), _price)
                _min_qty = float(market.get('minimum_order_size'))
                _max_qty = float(market.get('maximum_order_size'))
                _min_notional = _min_qty * _price

                _price_filter = {
                    "filterType": "PRICE_FILTER",
                    "minPrice": str(_tick_size),
                    "maxPrice": "1000000",
                    "tickSize": str(_tick_size)
                }
                _lot_size = {
                    "filterType": "LOT_SIZE",
                    "minQty": str(_min_qty),
                    "maxQty": str(_max_qty),
                    "stepSize": str(10**(-_base_asset_precision))
                }
                _min_notional = {
                    "filterType": "MIN_NOTIONAL",
                    "minNotional": str(_min_notional),
                    "applyToMarket": True,
                    "avgPriceMins": 0
                }
                _percent_price = {
                    "filterType": "PERCENT_PRICE",
                    "multiplierUp": "5",
                    "multiplierDown": "0.2",
                    "avgPriceMins": 5
                }

                symbol = {
                    "symbol": _symbol,
                    "status": "TRADING",
                    "baseAsset": _base_asset,
                    "baseAssetPrecision": _base_asset_precision,
                    "quoteAsset": _quote_asset,
                    "quoteAssetPrecision": _base_asset_precision,
                    "baseCommissionPrecision": 8,
                    "quoteCommissionPrecision": 8,
                    "orderTypes": ["LIMIT", "MARKET"],
                    "icebergAllowed": False,
                    "ocoAllowed": False,
                    "quoteOrderQtyMarketAllowed": False,
                    "allowTrailingStop": False,
                    "cancelReplaceAllowed": False,
                    "isSpotTradingAllowed": True,
                    "isMarginTradingAllowed": False,
                    "filters": [_price_filter, _lot_size, _min_notional, _percent_price],
                    "permissions": ["SPOT"],
                }
                symbols.append(symbol)

    return {
        "timezone": "UTC",
        "serverTime": int(time.time() * 1000) if symbols else None,
        "rateLimits": [],
        "exchangeFilters": [],
        "symbols": symbols,
    }


def account_balances(res: list) -> dict:
    balances = []
    for balance in res:
        if balance[0] == 'exchange':
            total = str(balance[2] or 0.0)
            free = str(balance[4] or 0.0)
            locked = str(Decimal(total) - Decimal(free))
            _binance_res = {
                "asset": balance[1],
                "free": free,
                "locked": locked,
            }
            balances.append(_binance_res)
    return {"balances": balances}


def order(res: list, response_type=None, cancelled=False) -> dict:
    # print(f"order.order: {res}")
    symbol = res[3][1:].replace(':', '')
    order_id = res[0]
    order_list_id = -1
    client_order_id = str(res[2]) or str()
    price = str(res[16] or 0.0)
    orig_qty = str(abs(res[7]) or 0.0)
    executed_qty = str(Decimal(orig_qty) - Decimal(str(abs(res[6]))))
    avg_fill_price = str(res[17] or 0.0)
    cummulative_quote_qty = str(Decimal(executed_qty) * Decimal(avg_fill_price))
    orig_quote_order_qty = str(Decimal(orig_qty) * Decimal(price))
    #
    if 'CANCELED' in res[13] or cancelled:
        status = 'CANCELED'
    elif Decimal(orig_qty) > Decimal(executed_qty) > 0:
        status = 'PARTIALLY_FILLED'
    elif Decimal(executed_qty) >= Decimal(orig_qty):
        status = 'FILLED'
    else:
        status = 'NEW'
    #
    _type = "LIMIT"

    time_in_force = "GTC"
    side = 'BUY' if res[7] > 0 else 'SELL'
    stop_price = '0.0'
    iceberg_qty = '0.0'
    _time = res[4]
    update_time = res[5]
    is_working = True
    #
    if response_type:
        return {
            "symbol": symbol,
            "origClientOrderId": client_order_id,
            "orderId": order_id,
            "orderListId": order_list_id,
            "clientOrderId": client_order_id,
            "transactTime": _time,
            "price": price,
            "origQty": orig_qty,
            "executedQty": executed_qty,
            "cummulativeQuoteQty": cummulative_quote_qty,
            "status": status,
            "timeInForce": time_in_force,
            "type": _type,
            "side": side,
        }
    elif response_type is None:
        return {
            "symbol": symbol,
            "orderId": order_id,
            "orderListId": order_list_id,
            "clientOrderId": client_order_id,
            "price": price,
            "origQty": orig_qty,
            "executedQty": executed_qty,
            "cummulativeQuoteQty": cummulative_quote_qty,
            "status": status,
            "timeInForce": time_in_force,
            "type": _type,
            "side": side,
            "stopPrice": stop_price,
            "icebergQty": iceberg_qty,
            "time": _time,
            "updateTime": update_time,
            "isWorking": is_working,
            "origQuoteOrderQty": orig_quote_order_qty,
        }
    else:
        return {
            "symbol": symbol,
            "orderId": order_id,
            "orderListId": order_list_id,
            "clientOrderId": client_order_id,
            "price": price,
            "origQty": orig_qty,
            "executedQty": executed_qty,
            "cummulativeQuoteQty": cummulative_quote_qty,
            "status": status,
            "timeInForce": time_in_force,
            "type": _type,
            "side": side,
        }


def orders(res: list, response_type=None, cancelled=False) -> list:
    binance_orders = []
    for _order in res:
        i_order = order(_order, response_type=response_type, cancelled=cancelled)
        binance_orders.append(i_order)
    return binance_orders


def order_book(res: List[List[float]]) -> Dict[str, Union[int, List[List[str]]]]:
    """
    Processes a list of raw order book entries into a structured dictionary.

    Args:
        res: A list of order entries, where each entry is a list like
             [price (float), quantity (float), side_indicator (float)].
             side_indicator > 0 for bids, < 0 for asks.

    Returns:
        A dictionary representing the order book with 'lastUpdateId', 'bids', and 'asks'.
    """
    binance_order_book: Dict[str, Union[int, List[List[str]]]] = {
        "lastUpdateId": int(time.time() * 1000)
    }

    bids: List[List[str]] = []
    asks: List[List[str]] = []

    for i in res:
        # Assuming i[2] determines bid/ask side and its absolute value is the quantity
        if i[2] > 0: # This means it's a bid (positive quantity indicator)
            bids.append([str(i[0]), str(i[2])]) # price, quantity
        else: # This means it's an ask (negative quantity indicator or zero)
            asks.append([str(i[0]), str(abs(i[2]))]) # price, absolute quantity

    binance_order_book['bids'] = bids
    binance_order_book['asks'] = asks
    return binance_order_book


def ticker_price_change_statistics(res: list, symbol):
    return {
        "symbol": symbol,
        "priceChange": str(res[4]),
        "priceChangePercent": str(res[5]),
        "weightedAvgPrice": "0.0",
        "prevClosePrice": str(res[6] - res[4]),
        "lastPrice": str(res[6]),
        "lastQty": "0.0",
        "bidPrice": str(res[0]),
        "bidQty": "0.0",
        "askPrice": str(res[2]),
        "askQty": "0.00",
        "openPrice": str(res[6] - res[4]),
        "highPrice": str(res[8]),
        "lowPrice": str(res[9]),
        "volume": str(res[7]),
        "quoteVolume": "0.0",
        "openTime": int(time.time() * 1000) - 60 * 60 * 24,
        "closeTime": int(time.time() * 1000),
        "firstId": 0,
        "lastId": 1,
        "count": 1,
    }


def fetch_symbol_price_ticker(res: list, symbol) -> dict:
    return {
        "symbol": symbol,
        "price": str(res[6]),
    }


def interval(_interval: str) -> int:
    resolution = {
        '1m': 60,
        '5m': 5 * 60,
        '15m': 15 * 60,
        '30m': 30 * 60,
        '1h': 60 * 60,
        '3h': 3 * 60 * 60,
        '6h': 6 * 60 * 60,
        '12h': 12 * 60 * 60,
        '1D': 24 * 60 * 60,
        '1W': 7 * 24 * 60 * 60,
        '14D': 14 * 24 * 60 * 60,
        '1M': 31 * 24 * 60 * 60
    }
    return resolution.get(_interval, 0)


def klines(res: list, _interval: str) -> list:
    binance_klines = []
    for i in res:
        start_time = i[0]
        _candle = [
            start_time,
            str(i[1]),
            str(i[3]),
            str(i[4]),
            str(i[2]),
            str(i[5]),
            start_time + interval(_interval) * 1000 - 1,
            '0.0',
            0,
            '0.0',
            '0.0',
            '0.0',
        ]
        binance_klines.append(_candle)
    return binance_klines


def candle(res: list, symbol: str = None, ch_type: str = None) -> dict:
    symbol = symbol[1:].replace(':', '')
    start_time = res[0]
    _interval = ch_type.split('_')[1]
    return {
        'stream': f"{symbol.lower()}@{ch_type.replace('candles', 'kline')}",
        'data': {
            'e': 'kline',
            'E': int(time.time()),
            's': symbol,
            'k': {
                't': start_time,
                'T': start_time + interval(_interval) * 1000 - 1,
                's': symbol,
                'i': _interval,
                'f': 100,
                'L': 200,
                'o': str(res[1]),
                'c': str(res[2]),
                'h': str(res[3]),
                'l': str(res[4]),
                'v': str(res[5]),
                'n': 100,
                'x': False,
                'q': '0.0',
                'V': '0.0',
                'Q': '0.0',
                'B': '0',
            },
        },
    }


def account_trade_list(res: list, order_id=None) -> list:
    binance_trade_list = []
    for trade in res:
        if order_id is None or order_id == trade[3]:
            price = str(trade[5])
            qty = str(abs(trade[4]))
            quote_qty = str(Decimal(price) * Decimal(qty))
            binance_trade = {
                "symbol": trade[1][1:].replace(':', ''),
                "id": trade[0],
                "orderId": trade[3],
                "orderListId": -1,
                "price": price,
                "qty": qty,
                "quoteQty": quote_qty,
                "commission": str(abs(trade[9])),
                "commissionAsset": trade[10],
                "time": trade[2],
                "isBuyer": trade[4] > 0,
                "isMaker": trade[8] == 1,
                "isBestMatch": True,
            }
            binance_trade_list.append(binance_trade)
    return binance_trade_list


def ticker(res: list, symbol: str = None) -> dict:
    _symbol = symbol[1:].replace(':', '').lower()
    return {
        'stream': f"{_symbol}@miniTicker",
        'data': {
            "e": "24hrMiniTicker",
            "E": int(time.time()),
            "s": _symbol.upper(),
            "c": str(res[6]),
            "o": str(res[6] - res[4]),
            "h": str(res[8]),
            "l": str(res[9]),
            "v": str(res[7]),
            "q": "0",
        },
    }


def on_funds_update(res: list) -> dict:
    binance_funds: Dict[str, Union[str, int, List]] = {
        'e': 'outboundAccountPosition',
        'E': int(time.time() * 1000),
        'u': int(time.time() * 1000),
    }
    funds = []
    if not isinstance(res[0], list):
        res = [res]
    for i in res:
        if i[0] == 'exchange':
            total = str(i[2])
            free = str(i[4] or total)
            locked = str(Decimal(total) - Decimal(free))
            balance = {
                'a': i[1],
                'f': free,
                'l': locked
            }
            funds.append(balance)
    binance_funds['B'] = funds
    return binance_funds


def on_balance_update(res: list) -> dict:
    return {
        'e': 'balanceUpdate',
        'E': res[3],
        'a': res[1],
        'd': res[5],
        'T': int(time.time() * 1000),
    }


def on_order_update(res: list, _order: {}) -> dict:
    # logger.info(f"on_order_update.res: {res}, order: {_order}")
    side = 'BUY' if res[7] > 0 else 'SELL'
    #
    order_quantity = _order["origQty"]
    cumulative_filled_quantity = _order["executedQty"]
    cumulative_quote_asset = str(cumulative_filled_quantity * Decimal(str(res[17])))
    quote_order_qty = str(Decimal(order_quantity) * Decimal(str(res[16])))
    #
    trade_id = -1
    last_executed_quantity = "0"
    last_executed_price = "0"
    is_maker = False
    commission_amount = "0"
    commission_asset = ""
    if _event := _order['lastEvent']:
        trade_id = _event[0]
        last_executed_quantity = str(abs(_event[4]))
        last_executed_price = str(_event[5])
        is_maker = _event[8] == 1
        commission_amount = str(_event[9]) if _event[9] else "0"
        commission_asset = _event[10] or ""
    last_quote_asset_transacted = str(Decimal(last_executed_quantity) * Decimal(last_executed_price))
    if 'CANCELED' in res[13]:
        status = 'CANCELED'
    elif order_quantity > cumulative_filled_quantity > 0:
        status = 'PARTIALLY_FILLED'
    elif cumulative_filled_quantity >= order_quantity:
        status = 'FILLED'
    else:
        status = 'NEW'
    return {
        "e": "executionReport",
        "E": res[5],
        "s": res[3][1:].replace(':', ''),
        "c": str(res[2]),
        "S": side,
        "o": "LIMIT",
        "f": "GTC",
        "q": str(order_quantity),
        "p": str(res[16]),
        "P": "0.00000000",
        "F": "0.00000000",
        "g": -1,
        "C": "",
        "x": "TRADE",
        "X": status,
        "r": "NONE",
        "i": res[0],
        "l": last_executed_quantity,
        "z": str(cumulative_filled_quantity),
        "L": last_executed_price,
        "n": commission_amount,
        "N": commission_asset,
        "T": res[5],
        "t": trade_id,
        "I": 123456789,
        "w": True,
        "m": is_maker,
        "M": False,
        "O": res[4],
        "Z": cumulative_quote_asset,
        "Y": last_quote_asset_transacted,
        "Q": quote_order_qty,
    }


def on_order_trade(_order: dict) -> dict:
    # logger.info(f"on_order_trade._order: {_order}")
    event = _order['lastEvent']
    orig_qty = _order['origQty']
    executed_qty = _order['executedQty']
    #
    order_price = Decimal(str(event[7]))
    quote_order_qty = str(Decimal(executed_qty) * order_price)
    cumulative_quote_asset = str(executed_qty * order_price)
    #
    last_executed_quantity = str(abs(event[4]))
    last_executed_price = str(event[5])
    last_quote_asset = str(Decimal(last_executed_quantity) * Decimal(last_executed_price))
    #
    status = 'NEW'
    if orig_qty > executed_qty > 0:
        status = 'PARTIALLY_FILLED'
    elif executed_qty >= orig_qty:
        status = 'FILLED'

    return {
        "e": "executionReport",
        "E": event[2],
        "s": event[1][1:].replace(':', ''),
        "c": str(event[11]),
        "S": 'BUY' if event[4] > 0 else 'SELL',
        "o": "LIMIT",
        "f": "GTC",
        "q": str(orig_qty),
        "p": str(order_price),
        "P": "0.00000000",
        "F": "0.00000000",
        "g": -1,
        "C": "",
        "x": "TRADE",
        "X": status,
        "r": "NONE",
        "i": event[3],
        "l": last_executed_quantity,
        "z": str(executed_qty),
        "L": last_executed_price,
        "n": str(event[9]) if event[9] else "0",
        "N": event[10],
        "T": event[2],
        "t": event[0],
        "I": 123456789,
        "w": True,
        "m": event[8] == 1,
        "M": False,
        "O": event[2],
        "Z": cumulative_quote_asset,
        "Y": last_quote_asset,
        "Q": quote_order_qty,
    }


def funding_wallet(res: list) -> list:
    balances = []
    for balance in res:
        if balance[0] in ('exchange', 'funding'):
            total = str(balance[2] or 0.0)
            if float(total):
                free = str(balance[4] or 0.0)
                locked = str(Decimal(total) - Decimal(free))
                _binance_res = {
                    "asset": balance[1],
                    "free": free,
                    "locked": locked,
                    "freeze": "0",
                    "withdrawing": "0",
                    "btcValuation": "0.0",
                }
                balances.append(_binance_res)
    return balances


def find_order(_res, order_id, origin_client_order_id):
    res = []
    if _res:
        if order_id:
            res = _res[0]
        else:
            for i in _res:
                if i[2] == int(origin_client_order_id):
                    res = i
                    break
    return res
