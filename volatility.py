"""
This algorithm trades Volatility.
"""
import talib


def initialize(context):
    """
    Called once at the start of the algorithm.
    """
    # Set Commision
    set_commission(commission.PerTrade(cost=0.00))

    # Record tracking variables at the end of each day.
    schedule_function(my_record_vars, date_rules.every_day(), time_rules.market_close())

    # Rebalance Portfolio executes at the start of every trading day.
    schedule_function(my_rebalance, date_rules.every_day(), time_rules.market_open())

    """
    Volatility Stock
    """
    # Define Volatility tool
    context.stocks = [sid(41968)]

    # Keep tracks of starting balance
    context.starting_balance = context.portfolio.portfolio_value

    """
    RSI levels

    """
    # Define RSI intensities
    context.rsi_lower = 33
    context.rsi_low = 50
    context.rsi_high = 55
    context.rsi_higher = 70

    """
    MACD Levels

    """
    context.macd_low = -0.05
    context.macd_high = 0.05

    """
    Global Variables

    """
    # Global RSIs
    context.rsis = []
    # Global BollingerBands
    context.bands = []
    context.bands_weight = 0.00

    # Timer is updated daily depending on when a transaction is executed.
    # Timer is reset in rebalance and updated every morning
    context.timer = 0
    # Global Last Prices
    context.prices = []
    # Global Weights
    context.weights = []
    context.rsi_weight = 0.00
    # Global Simple Moving Averages
    context.smas = []
    # Global MACDs
    context.macds = []
    context.macd_weight = 0.00
    # Global starting weight
    context.weight = 0

    pass


def before_trading_start(context, data):
    """
    Called every day before market open.

    """
    update_timer(context)

    # Update context
    update_context(context, data)
    pass


def update_timer(context):
    if (context.timer > 0):
        context.timer = context.timer - 1


def my_assign_weights(context, data):
    """
    Assign weights to securities that we want to order.
    """
    block = 0.10
    weight = context.weight
    bands = context.bands
    rsis = context.rsis
    prices = context.prices
    smas = context.smas

    for stock in context.stocks:
        if (data.can_trade(stock)):
            # If price is above or below the 100 day moving average
            if (prices[stock] > smas[stock][2]):
                if ((prices[stock] <= bands[stock][2]) &
                        (rsis[stock] < context.rsi_high) &
                        (context.weight < 0.90)):
                    context.weight = weight + block
                    log.info('\n BUY high')
                elif ((prices[stock] >= bands[stock][0]) &
                          (rsis[stock] > context.rsi_higher) &
                          (context.weight > 0.10)):
                    context.weight = weight - block
                    log.info('\n  SELL high ')
            elif (prices[stock] < smas[stock][2]):
                if ((prices[stock] <= bands[stock][2]) &
                        (rsis[stock] < context.rsi_lower) &
                        (context.weight < 0.90)):
                    context.weight = weight + block
                    log.info('\n BUY low ')
                elif ((prices[stock] >= bands[stock][0]) &
                          (rsis[stock] > context.rsi_low) &
                          (context.weight > 0.10)):
                    context.weight = weight - block
                    log.info('\n SELL low ')
    pass


def my_rebalance(context, data):
    """
    Execute orders according to our schedule_function() timing. 

    """
    if (context.weight <= 0):
        context.weight = 0
    elif (context.weight >= 1):
        context.weight = 1
    for stock in context.stocks:
        if (data.can_trade(stock) & (context.timer == 0)):
            if ((context.account.buying_power > 0)):
                order_target_percent(stock, context.weight)
                context.timer = 2
    pass


def my_record_vars(context, data):
    """
    Plot variables at the end of each day.

    """
    # Get Total Weight
    total_weight = context.rsi_weight + context.macd_weight + context.rsi_weight

    record(total_weight=total_weight)
    pass


def handle_data(context, data):
    """
    Called every minute.

    """
    pass


def calculate_rsis(context, data):
    """
    Calculates the rsis for context.stocks

    """
    rsis = {}
    for stock in context.stocks:
        prices = data.history(stock, 'low', 20, '1d')
        rsi = talib.RSI(prices, timeperiod=15)[-1]
        rsis[stock] = rsi
    return rsis


def calculate_bbands(context, data):
    """
    Calculates the BollingerBands for each stock.

    """
    bands = {}
    for stock in context.stocks:
        prices = data.history(stock, 'price', 40, '1d')
        upper, middle, lower = talib.BBANDS(
            prices,
            timeperiod=20,
            nbdevup=2,
            nbdevdn=2,
            matype=0)
        bands[stock] = [upper[-1], middle[-1], lower[-1]]
    return bands


def get_latest_prices(context, data):
    prices = {}
    for stock in context.stocks:
        price = data.current(stock, 'price')
        prices[stock] = price
    return prices


def get_smas(context, data):
    smas = {}
    for stock in context.stocks:
        price_26 = data.history(stock, 'price', 26, '1d').mean()
        price_50 = data.history(stock, 'price', 50, '1d').mean()
        price_100 = data.history(stock, 'price', 100, '1d').mean()
        smas[stock] = [price_26, price_50, price_100]
    return smas


def above_all_smas(context, stock):
    price = context.prices[stock]
    if ((price > context.smas[stock][0]) & (price > context.smas[stock][1]) & (price > context.smas[stock][2])):
        return True
    else:
        return False


def below_all_smas(context, stock):
    price = context.prices[stock]
    if ((price < context.smas[stock][0]) & (price < context.smas[stock][1]) & (price < context.smas[stock][2])):
        return True
    else:
        return False


def get_macd_signals(context, data):
    macds = {}
    for stock in context.stocks:
        prices = data.history(stock, 'price', 40, '1d')
        macd_raw, signal, hist = talib.MACD(prices, fastperiod=12, slowperiod=26, signalperiod=9)
        macds[stock] = macd_raw[-1] - signal[-1]
    return macds


def update_context(context, data):
    # Get Latest Prices
    context.prices = get_latest_prices(context, data)
    # Calculate RSIs for each stock
    context.rsis = calculate_rsis(context, data)
    # Calculate Bollinger Bands for each stock
    context.bands = calculate_bbands(context, data)
    # Get Simple Moving Averages
    context.smas = get_smas(context, data)
    # Get MACD signals
    context.macds = get_macd_signals(context, data)
    # Get Weights
    context.weights = my_assign_weights(context, data)
    pass