from decimal import Decimal

from ostium_python_sdk.scscript.pairinfos import getTradeLiquidationPrice
from .formulae import (PRECISION_18, PRECISION_2, PRECISION_6, GetCurrentRolloverFee, GetFundingRate,
                       GetTradeFundingFee, GetTradeRolloverFee,
                       GetPriceImpact, CurrentTradeProfitRaw,
                       CurrentTotalProfitRaw, CurrentTotalProfitP)


# TBD - used by SDK
# Gets an open trade metrics: such as the open pnl, rollover, funding, liquidation price, price impact, etc.


def get_trade_metrics(trade_details, price_data, block_number, pair_max_leverage, liq_margin_threshold_p=25, verbose=False):
    """
    Calculate PNL and related metrics for a trade.
    """
    if not trade_details or not price_data or not block_number:
        return {
            'pnl': 0,
            'pnl_percent': 0,
            'rollover': 0,
            'funding': 0,
            'total_profit': 0,
            'net_pnl': 0,
            'net_value': 0,
            'liquidation_price': 0
        }

    pair_info = trade_details['pair']
    # Calculate current rollover fee
    current_rollover_raw = GetCurrentRolloverFee(
        pair_info['accRollover'],
        pair_info['lastRolloverBlock'],
        pair_info['rolloverFeePerBlock'],
        str(block_number)
    )

    if verbose:
        print(f"Current rollover fee: {current_rollover_raw}")

    trade_rollover_fee = GetTradeRolloverFee(
        Decimal(trade_details['rollover']) / PRECISION_18,
        Decimal(current_rollover_raw) / PRECISION_18,
        Decimal(trade_details['collateral']) / PRECISION_6,
        Decimal(trade_details['leverage']) / PRECISION_2
    )

    if verbose:
        print(f"Trade Rollover fee: {trade_rollover_fee}")
        if (trade_rollover_fee != 0):
            print(f"***** Trade Rollover fee is not 0: {trade_rollover_fee}")
    # Get funding rate
    funding_rate_raw = GetFundingRate(
        pair_info['accFundingLong'],
        pair_info['accFundingShort'],
        pair_info['lastFundingRate'],
        pair_info['maxFundingFeePerBlock'],
        pair_info['lastFundingBlock'],
        str(block_number),
        pair_info['longOI'],
        pair_info['shortOI'],
        pair_info['maxOI'],
        pair_info['hillInflectionPoint'],
        pair_info['hillPosScale'],
        pair_info['hillNegScale'],
        pair_info['springFactor'],
        pair_info['sFactorUpScaleP'],
        pair_info['sFactorDownScaleP'],
        verbose
    )

    if verbose:
        print(
            f"*** Funding rate: {funding_rate_raw} based on pair_info: {pair_info}")

    # Calculate funding fee
    trade_funding_fee = GetTradeFundingFee(
        # initial funding fee (accFundingFeesPerOi)
        Decimal(trade_details['funding']) / PRECISION_18,
        Decimal(funding_rate_raw['accFundingLong']) if trade_details['isBuy'] else Decimal(
            funding_rate_raw['accFundingShort']),
        Decimal(trade_details['collateral']) / PRECISION_6,
        Decimal(trade_details['leverage']) / PRECISION_2
    )

    if verbose:
        print(f"*** trade_funding_fee: {trade_funding_fee}")

    # Calculate liquidation price
    trade_liquidation_price = getTradeLiquidationPrice(
        Decimal(liq_margin_threshold_p) / PRECISION_2,
        Decimal(trade_details['openPrice']) / PRECISION_18,
        trade_details['isBuy'],
        Decimal(trade_details['collateral']) / PRECISION_6,
        Decimal(trade_details['leverage']) / PRECISION_2,
        Decimal(trade_rollover_fee),
        Decimal(trade_funding_fee),
        Decimal(pair_max_leverage)
    )

    if verbose:
        print(f"trade_liquidation_price: {trade_liquidation_price}")

    # Calculate price impact
    is_open = False  # Get the price assuming a close

    price_impact_raw = GetPriceImpact(
        str(int(Decimal(str(price_data['mid'])) * PRECISION_18)),
        str(int(Decimal(str(price_data['bid'])) * PRECISION_18)),
        str(int(Decimal(str(price_data['ask'])) * PRECISION_18)),
        is_open,
        trade_details['isBuy']
    )
    price_after_impact = price_impact_raw['priceAfterImpact']

    # Calculate PNL (abs)
    pnl_raw = CurrentTradeProfitRaw(
        Decimal(trade_details['openPrice']) / PRECISION_18,
        Decimal(price_after_impact) / PRECISION_18,
        Decimal(trade_details['isBuy']),
        Decimal(trade_details['leverage']) / PRECISION_2,
        Decimal(trade_details['highestLeverage']) / PRECISION_2,
        Decimal(trade_details['collateral']) / PRECISION_6
    )

    # Calculate total profit
    total_profit_raw = CurrentTotalProfitRaw(
        Decimal(trade_details['openPrice']) / PRECISION_18,
        Decimal(price_after_impact) / PRECISION_18,
        Decimal(trade_details['isBuy']),
        Decimal(trade_details['leverage']) / PRECISION_2,
        Decimal(trade_details['highestLeverage']) / PRECISION_2,
        Decimal(trade_details['collateral']) / PRECISION_6,
        Decimal(trade_rollover_fee),
        Decimal(trade_funding_fee)
    )

    # Calculate PNL percentage
    pnl_percent_raw = CurrentTotalProfitP(
        Decimal(total_profit_raw), Decimal(trade_details['collateral']) / PRECISION_6)

    # Convert values to proper decimals
    pnl = Decimal(pnl_raw)
    pnl_percent = Decimal(pnl_percent_raw)
    net_pnl = Decimal(total_profit_raw)

    funding = Decimal(trade_funding_fee)
    rollover = Decimal(trade_rollover_fee)
    net_value = net_pnl + (Decimal(trade_details['collateral']) / PRECISION_6)
    price_impact = Decimal(price_after_impact) / PRECISION_18

    return {
        'pnl': float(pnl),
        'pnl_percent': float(pnl_percent),
        'rollover': float(rollover),
        'funding': float(funding),
        'net_pnl': float(net_pnl),  # pnl without ff, if any
        'net_value': float(net_value),
        'liquidation_price': float(trade_liquidation_price),
        'price_impact': float(price_impact),
        'is_market_open': price_data['isMarketOpen'],
        'bid': price_data['bid'],
        'mid': price_data['mid'],
        'ask': price_data['ask'],
    }
