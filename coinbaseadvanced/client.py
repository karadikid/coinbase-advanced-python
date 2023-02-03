import hmac
import hashlib
import time
import requests
import json

from typing import List
from enum import Enum
from datetime import datetime
from coinbaseadvanced.models.products import ProductsPage, Product, CandlesPage
from coinbaseadvanced.models.accounts import AccountsPage, Account
from coinbaseadvanced.models.orders import OrdersPage, Order, OrderBatchCancellation, FillsPage


class SIDE(Enum):
    BUY = "BUY"
    SELL = "SELL"


class STOP_DIRECTION(Enum):
    UNKNOWN = "UNKNOWN_STOP_DIRECTION"
    UP = "STOP_DIRECTION_STOP_UP"
    DOWN = "STOP_DIRECTION_STOP_DOWN"


class ORDER_TYPE(Enum):
    UNKNOWN_ORDER_TYPE = "UNKNOWN_ORDER_TYPE"
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class PRODUCT_TYPE(Enum):
    SPOT = "SPOT"


class GRANULARITY(Enum):
    UNKNOWN = "UNKNOWN_GRANULARITY"
    ONE_MINUTE = "ONE_MINUTE"
    FIVE_MINUTE = "FIVE_MINUTE"
    FIFTEEN_MINUTE = "FIFTEEN_MINUTE"
    THIRTY_MINUTE = "THIRTY_MINUTE"
    ONE_HOUR = "ONE_HOUR"
    TWO_HOUR = "TWO_HOUR"
    SIX_HOUR = "SIX_HOUR"
    ONE_DAY = "ONE_DAY"


class CoinbaseAdvancedTradeAPIClient(object):
    def __init__(self, api_key: str, secret_key: str, base_url: str = 'https://api.coinbase.com') -> None:
        self._base_url = base_url
        self._api_key = api_key
        self._secret_key = secret_key

    # Accounts #

    def list_accounts(self, limit: int = 49, cursor: str = None) -> AccountsPage:
        request_path = '/api/v3/brokerage/accounts'
        method = "GET"
        query_params = '?limit='+str(limit)

        if cursor is not None:
            query_params = query_params + '&cursor='+cursor

        headers = self._build_request_headers(method, request_path)

        response = requests.get(self._base_url+request_path+query_params, headers=headers)

        page = AccountsPage.from_response(response)
        return page

    def get_account(self, account_id: str) -> Account:
        request_path = f"/api/v3/brokerage/accounts/{account_id}"
        method = "GET"

        headers = self._build_request_headers(method, request_path)

        response = requests.get(self._base_url+request_path, headers=headers)

        account = Account.from_response(response)
        return account

    # Orders #

    def create_buy_market_order(self, client_order_id: str, product_id: str, quote_size: float):
        order_configuration = {
            "market_market_ioc": {
                "quote_size": str(quote_size),
            }
        }

        return self.create_order(client_order_id, product_id, SIDE.BUY, order_configuration)

    def create_sell_market_order(self, client_order_id: str, product_id: str, base_size: float):
        order_configuration = {
            "market_market_ioc": {
                "base_size": str(base_size),
            }
        }

        return self.create_order(client_order_id, product_id, SIDE.SELL, order_configuration)

    def create_limit_order(
            self, client_order_id: str, product_id: str, side: SIDE, limit_price: float, base_size: float,
            cancel_time: datetime = None, post_only: bool = None):

        order_configuration = {}

        limit_order_configuration = {
            "limit_price": str(limit_price),
            "base_size": str(base_size),
        }

        if post_only is not None:
            limit_order_configuration['post_only'] = post_only

        if cancel_time is not None:
            limit_order_configuration['end_time'] = cancel_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            order_configuration['limit_limit_gtd'] = limit_order_configuration
        else:
            order_configuration['limit_limit_gtc'] = limit_order_configuration

        return self.create_order(client_order_id, product_id, side, order_configuration)

    def create_stop_limit_order(
            self, client_order_id: str, product_id: str, side: SIDE, stop_price: float, stop_direction: STOP_DIRECTION,
            limit_price: float, base_size: float, cancel_time: datetime = None):

        order_configuration = {}

        stop_limit_order_configuration = {
            "stop_price": str(stop_price),
            "limit_price": str(limit_price),
            "base_size": str(base_size),
            "stop_direction": stop_direction.value,
        }

        if cancel_time is not None:
            stop_limit_order_configuration['end_time'] = cancel_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            order_configuration['stop_limit_stop_limit_gtd'] = stop_limit_order_configuration
        else:
            order_configuration['stop_limit_stop_limit_gtc'] = stop_limit_order_configuration

        return self.create_order(client_order_id, product_id, side, order_configuration)

    def create_order(self, client_order_id: str, product_id: str, side: SIDE, order_configuration: dict) -> Order:
        request_path = "/api/v3/brokerage/orders"
        method = "POST"

        payload = {
            'client_order_id': client_order_id,
            'product_id': product_id,
            'side': side.value,
            'order_configuration': order_configuration
        }

        headers = self._build_request_headers(method, request_path, json.dumps(payload))
        response = requests.post(self._base_url+request_path, json=payload, headers=headers)

        order = Order.from_create_order_response(response)
        return order

    def cancel_orders(self, order_ids: list) -> OrderBatchCancellation:
        request_path = "/api/v3/brokerage/orders/batch_cancel/"
        method = "POST"

        payload = {
            'order_ids': order_ids,
        }

        headers = self._build_request_headers(method, request_path, json.dumps(payload))
        response = requests.post(self._base_url+request_path, json=payload, headers=headers)

        cancellation_result = OrderBatchCancellation.from_response(response)
        return cancellation_result

    def list_orders(
            self, product_id: str = None, order_status: List[str] = None, limit: int = 999, start_date: datetime = None,
            end_date: datetime = None, user_native_currency: str = None, order_type: ORDER_TYPE = None, order_side: SIDE = None,
            cursor: str = None, product_type: PRODUCT_TYPE = None) -> OrdersPage:
        request_path = '/api/v3/brokerage/orders/historical/batch'
        method = "GET"

        query_params = ''

        if product_id is not None:
            query_params = self._next_param(query_params) + 'product_id='+product_id

        if order_status is not None:
            query_params = self._next_param(query_params) + 'order_status='+','.join(order_status)

        if limit is not None:
            query_params = self._next_param(query_params) + 'limit='+str(limit)

        if start_date is not None:
            query_params = self._next_param(query_params) + 'start_date=' + start_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        if end_date is not None:
            query_params = self._next_param(query_params) + 'end_date=' + end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        if user_native_currency is not None:
            query_params = self._next_param(query_params) + 'user_native_currency=' + user_native_currency

        if order_type is not None:
            query_params = self._next_param(query_params) + 'order_type=' + order_type.value

        if order_side is not None:
            query_params = self._next_param(query_params) + 'order_side=' + order_side.value

        if cursor is not None:
            query_params = self._next_param(query_params) + 'cursor=' + cursor

        if product_type is not None:
            query_params = self._next_param(query_params) + 'product_type=' + product_type.value

        headers = self._build_request_headers(method, request_path)

        response = requests.get(self._base_url+request_path+query_params, headers=headers)

        page = OrdersPage.from_response(response)
        return page

    def list_fills(self, order_id: str = None, product_id: str = None, start_date: datetime = None,
                   end_date: datetime = None, cursor: str = None, limit: int = 100):
        request_path = '/api/v3/brokerage/orders/historical/fills'
        method = "GET"

        query_params = ''

        if order_id is not None:
            query_params = self._next_param(query_params) + 'order_id='+order_id

        if product_id is not None:
            query_params = self._next_param(query_params) + 'product_id='+product_id

        if limit is not None:
            query_params = self._next_param(query_params) + 'limit='+str(limit)

        if start_date is not None:
            query_params = self._next_param(query_params) + 'start_date=' + start_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        if end_date is not None:
            query_params = self._next_param(query_params) + 'end_date=' + end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        if cursor is not None:
            query_params = self._next_param(query_params) + 'cursor=' + cursor

        headers = self._build_request_headers(method, request_path)

        response = requests.get(self._base_url+request_path+query_params, headers=headers)

        page = FillsPage.from_response(response)
        return page

    def get_order(self, order_id: str) -> Order:
        request_path = f"/api/v3/brokerage/orders/historical/{order_id}"
        method = "GET"

        headers = self._build_request_headers(method, request_path)

        response = requests.get(self._base_url+request_path, headers=headers)

        order = Order.from_get_order_response(response)
        return order

    # Products #

    def list_products(self, limit: int = None, offset: int = None, product_type: PRODUCT_TYPE = None) -> ProductsPage:
        request_path = '/api/v3/brokerage/products'
        method = "GET"

        query_params = ''

        if limit is not None:
            query_params = self._next_param(query_params) + 'limit='+str(limit)

        if offset is not None:
            query_params = self._next_param(query_params) + 'offset='+str(offset)

        if product_type is not None:
            query_params = self._next_param(query_params) + 'product_type=' + product_type.value

        headers = self._build_request_headers(method, request_path)

        response = requests.get(self._base_url+request_path+query_params, headers=headers)

        page = ProductsPage.from_response(response)
        return page

    def get_product(self, product_id: str) -> Product:
        request_path = f"/api/v3/brokerage/products/{product_id}"
        method = "GET"

        headers = self._build_request_headers(method, request_path)

        response = requests.get(self._base_url+request_path, headers=headers)

        product = Product.from_response(response)
        return product

    def get_product_candles(
            self, product_id: str, start_date: datetime, end_date: datetime, granularity: GRANULARITY) -> CandlesPage:
        request_path = f"/api/v3/brokerage/products/{product_id}/candles"
        method = "GET"

        query_params = ''

        query_params = self._next_param(query_params) + 'start=' + str(int(start_date.timestamp()))
        query_params = self._next_param(query_params) + 'end=' + str(int(end_date.timestamp()))
        query_params = self._next_param(query_params) + 'granularity=' + granularity.value

        headers = self._build_request_headers(method, request_path)

        response = requests.get(self._base_url+request_path+query_params, headers=headers)

        product_candles = CandlesPage.from_response(response)
        return product_candles

    # Helpers #

    def _build_request_headers(self, method, request_path, body=''):
        timestamp = str(int(time.time()))

        message = timestamp+method+request_path+body
        signature = self._create_signature(message)

        return {
            "accept": "application/json",
            'CB-ACCESS-KEY': self._api_key,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-SIGN': signature,
        }

    def _create_signature(self, message):
        signature = hmac.new(
            self._secret_key.encode('utf-8'),
            message.encode('utf-8'),
            digestmod=hashlib.sha256).digest().hex()

        return signature

    def _next_param(self, query_params: str) -> str:
        return query_params + ('?' if query_params == '' else '&')

#################### TESTING ####################


# For Reading
# client = CoinbaseAdvancedTradeAPIClient(api_key='hOOnWpN0x2zsu12i', secret_key='86s3z4DLYrFCw4QonF54u4CdirrbBSnw')

# page = client.list_accounts(limit=89898)  # Accounts: List Accounts

# account = client.get_account('b044449a-38a3-5b8f-a506-4a65c9853222')


# Full Access to ALGO Wallet
client = CoinbaseAdvancedTradeAPIClient(api_key='Jk31IAjyWQEG3BfP', secret_key='HUbLt2GsnPOTTkl0t2wkFWn4RrznDJRM')


# if page.error:
#    print(page.error)
# else:
#    accounts = page.accounts
#    for a in accounts:
#        if a.name == 'BTC Wallet':
#            print(a.hold)


############

# a = 5

# if account.error:
#    print(account.error)
# else:
#    print(account.name)

############

# order = client.create_order("nkjsdfnw23", "ALGO-USD", "SELL", order_configuration)

#order = client.create_limit_order("nlksdbnfgjd8y9mn,m234", "ALGO-USD", SIDE.BUY, ".19", 10)

# order = client.create_stop_limit_order("mklansdu8wehr", "ALGO-USD", SIDE.BUY, .18,
#                                       STOP_DIRECTION.DOWN, .16, 7, datetime(2023, 5, 9, 15))

# order = client.create_buy_market_order("asdasd", "ALGO-USD", 1)
# order = client.create_sell_market_order("njkasdh7", "ALGO-USD", 5)

#order1 = client.create_limit_order("k7999902", "ALGO-USD", SIDE.SELL, ".9", 5)
#order2 = client.create_limit_order("j876789ks", "ALGO-USD", SIDE.SELL, ".9", 5)

#a = 5
#cancellation_receipt = client.cancel_orders(['a', 'b'])

#cancellation_receipt = client.cancel_orders([order2.order_id])

#orders_page = client.list_orders(start_date=datetime(2023, 1, 25), end_date=datetime(2023, 1, 30), limit=10, )
#fills_page = client.list_fills(limit=5, start_date=datetime(2023, 1, 20), end_date=datetime(2023, 1, 30))

#order = client.get_order("5fffa9e8-73db-4a2c-8b3f-08509203ac04")

#product_page = client.list_products(limit=5)

#product = client.get_product('BTC-USD')

# candles = client.get_product_candles(
#     "ALGO-USD", start_date=datetime(2023, 1, 1),
#     end_date=datetime(2023, 1, 31),
#     granularity=GRANULARITY.ONE_DAY)

a = 5
