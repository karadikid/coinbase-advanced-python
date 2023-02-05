import json
import requests


class FeeTier:
    pricing_tier: str
    usd_from: int
    usd_to: str
    taker_fee_rate: str
    maker_fee_rate: str

    def __init__(self, pricing_tier: str, usd_from: int, usd_to: str, taker_fee_rate: str, maker_fee_rate: str) -> None:
        self.pricing_tier = pricing_tier
        self.usd_from = usd_from
        self.usd_to = usd_to
        self.taker_fee_rate = taker_fee_rate
        self.maker_fee_rate = maker_fee_rate


class GoodsAndServicesTax:
    rate: str
    type: str

    def __init__(self, rate: str, type: str) -> None:
        self.rate = rate
        self.type = type


class MarginRate:
    value: str

    def __init__(self, value: str) -> None:
        self.value = value


class TransactionsSummary:
    total_volume: int
    total_fees: int
    fee_tier: FeeTier
    margin_rate: MarginRate
    goods_and_services_tax: GoodsAndServicesTax
    advanced_trade_only_volume: int
    advanced_trade_only_fees: int
    coinbase_pro_volume: int
    coinbase_pro_fees: int

    error: dict

    def __init__(self, total_volume: int, total_fees: int, fee_tier: dict, margin_rate: dict,
                 goods_and_services_tax: dict, advanced_trade_only_volume: int,
                 advanced_trade_only_fees: int, coinbase_pro_volume: int, coinbase_pro_fees: int, error=None) -> None:
        self.total_volume = total_volume
        self.total_fees = total_fees
        self.fee_tier = FeeTier(**fee_tier) if fee_tier is not None else None
        self.margin_rate = MarginRate(**margin_rate) if margin_rate is not None else None
        self.goods_and_services_tax = GoodsAndServicesTax(
            **goods_and_services_tax) if goods_and_services_tax is not None else None
        self.advanced_trade_only_volume = advanced_trade_only_volume
        self.advanced_trade_only_fees = advanced_trade_only_fees
        self.coinbase_pro_volume = coinbase_pro_volume
        self.coinbase_pro_fees = coinbase_pro_fees

        self.error = error

    @classmethod
    def from_response(cls, response: requests.Response) -> 'TransactionsSummary':

        if not response.ok:
            error_result = json.loads(response.text)
            return cls(None, None, None, None, None, None, None, None, None, error=error_result)

        result = json.loads(response.text)
        return cls(**result)