import json
import time
import requests
import hmac
import hashlib
import os
from datetime import datetime
from ta.trend import EMAIndicator, SMAIndicator
import ccxt
import pandas as pd

def PLACE_BRACKET_ORDER(api_key, api_secret, price, SL, TP, LOT, side, product_symbol, product_id, base_url ):
    if api_key is None:
        print(f"api_key is missing ")
    if  api_secret is None:
        print(f"api_key is missing ")
    if price is None:
        print(f"Price is empty, oder is place on market price")
        price = "market_order"
    else:
        print(f"Emtry is {price}")
    if SL is None:
        print(f"STOPLOSS is not provided")
    if TP is None:
        print(f"Traget is missing")
    if LOT is None:
        print(f"LOT size is empty")
    if side is None:
        print(f"Order type (BUY/SELL) is missing")
    if product_symbol is None:
        print(f"Coin name  is missing")
    if product_id is None:
        print(f"Coin ID is missing")
    if base_url is None:
        print(f"API URL is missing")        
    #base_url = 'https://api.india.delta.exchange'  # Δ India production
    endpoint = '/v2/orders'
    url = base_url + endpoint
    method = 'POST'
    
    # === Helper to generate HMAC signature ===
    def generate_signature(secret, message):
        message = bytes(message, 'utf-8')
        secret = bytes(secret, 'utf-8')
        return hmac.new(secret, message, hashlib.sha256).hexdigest()
    
    
    timestamp = str(int(time.time()))
    # === Bracket Order Payload ===
    order = {
        "product_id": f"{product_id}",
        "product_symbol": f"{product_symbol}",
        "side": f"{side}",
        "size": f"{LOT}",
        "order_type": f"{price}",
        "time_in_force": "gtc",

        # Bracket params
        "bracket_stop_loss_price": f"{SL}",
        "bracket_stop_loss_limit_price": f"{SL}",
        "bracket_take_profit_price": f"{TP}",
        "bracket_take_profit_limit_price": f"{TP}",
        "stop_trigger_method": "last_traded_price"
    }
    query_string = ''
    # === Prepare body and signature ===
    body = json.dumps(order, separators=(',', ':'))
    signature_data = method + timestamp + endpoint + query_string + body
    #print("signature_data", signature_data)
    sig = generate_signature(api_secret,signature_data)
    headers = {
        "api-key": api_key,
        "timestamp": str(timestamp),
        "signature": sig,
        "Content-Type": "application/json"
    }
    
    # === Send the request ===
    response = requests.post(url, headers=headers, data=body)    
    confirm = response.json()
    if confirm:
        success = confirm.get("success")
        if success:
            print(f"{json.dumps(response.json(), indent=2)}")
            print(f"Order has been created sucessfully")
        else:
            print(f"Unable to place order")
            print(f"{json.dumps(response.json(), indent=2)}")
def PLACE_ORDER(api_key, api_secret, price, LOT, side, product_id, base_url ):          
    if api_key is None:
        print(f"api_key is missing ")
    if  api_secret is None:
        print(f"api_key is missing ")
    if price is None:
        print(f"Price is empty, oder is place on market price")
        price = "market_order"

    else:
        print(f"Emtry is {price}")
    if LOT is None:
        print(f"LOT size is empty")
        return None
    if side is None:
        print(f"Order type (BUY/SELL) is missing")
        return None
    if product_id is None:
        print(f"Coin ID is missing")
        return None
    if base_url is None:
        print(f"API URL is missing")
        return None
    endpoint = '/v2/orders'
    url = base_url + endpoint
    method = 'POST'
    def generate_signature(secret, message):
        message = bytes(message, 'utf-8')
        secret = bytes(secret, 'utf-8')
        return hmac.new(secret, message, hashlib.sha256).hexdigest()
    timestamp = str(int(time.time()))
    order = {
        "product_id": f"{product_id}",       # ETHUSD
        "size": f"{LOT}",               # contract size
        "side": f"{side}",           # 'buy' or 'sell'
        "order_type": f"{price}",  # or "limit_order"
        "time_in_force": "gtc"    # good till cancel
    }
    query_string = ''
    # === Prepare body and signature ===
    body = json.dumps(order, separators=(',', ':'))
    signature_data = method + timestamp + endpoint + query_string + body
    #print("signature_data", signature_data)
    sig = generate_signature(api_secret,signature_data)
    headers = {
        "api-key": api_key,
        "timestamp": str(timestamp),
        "signature": sig,
        "Content-Type": "application/json"
    }
    
    # === Send the request ===
    response = requests.post(url, headers=headers, data=body)

    # === Send the request ===
    response = requests.post(url, headers=headers, data=body)    
    confirm = response.json()
    if confirm:
        success = confirm.get("success")
        if success:
            print(f"{json.dumps(response.json(), indent=2)}")
            print(f"Order has been created sucessfully")
        else:
            print(f"Unable to place order")
            print(f"{json.dumps(response.json(), indent=2)}")
def BALANCE_CHECK(api_key, api_secret, base_url ):
    if api_key is None:
        print("API KEY is missing .. !!")
        return None
    if api_secret is None:
        print("api_secret is missing")
        return None
    if base_url is None:
        print("base_url is missing")
        return None
    endpoint = "/v2/wallet/balances"
    method = "GET"
    timestamp = str(int(time.time()))
    def generate_signature(secret, message):
        message = bytes(message, 'utf-8')
        secret = bytes(secret, 'utf-8')
        return hmac.new(secret, message, hashlib.sha256).hexdigest()
    signature_data = method + timestamp + endpoint
    sig = generate_signature(api_secret,signature_data)
    headers = {
        "api-key": api_key,
        "timestamp": timestamp,
        "signature": sig,
    }
    response = requests.get(base_url + endpoint, headers=headers)
    data = response.json()
    balance = data['result'][0]['available_balance_inr']
    print(f"CURRENT BALANCE {balance}")         

def EMA(symbol, timeframe, lookback=None,  ema_value=None):
    if symbol.isupper():
        exchange = ccxt.binance()
        if lookback is None:
            lookback = 500
        if ema_value is None:
            ema_value = 9      
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=lookback)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        # === INDICATORS ===
        ema = EMAIndicator(close=df['close'], window=ema_value).ema_indicator()
        df['EMA'] = ema
        latest_ema = df['EMA'].iloc[-1]
        print(f"{symbol} latest EMA average price is {latest_ema:.2f}")
        #return latest_ema:.2f
    else:
        print("The symbol is not uppercase ❌")

def MOVING_AVG(symbol, timeframe, lookback=None,  ma_value=None):
    if symbol.isupper():
        exchange = ccxt.binance()
        if lookback is None:
            lookback = 500
        if ma_value is None:
            ma_value = 20
    
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=lookback)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        ma = SMAIndicator(close=df['close'], window=ma_value).sma_indicator()
        df['MA'] = ma
        latest_ma = df['MA'].iloc[-1]
        print(f"{symbol} latest moving average price is {latest_ma:.2f}")
        #return latest_ma
    else:
        print("The symbol is not uppercase ❌")
def get_support_resistance(symbol, timeframe, lookback=None, swing_lookback=None):
    if swing_lookback is None:
        swing_lookback = 50
    if lookback is None:
        lookback = 500    
    
    if symbol.isupper():
        exchange = ccxt.binance()
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=lookback)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        # === Format Timestamp ===
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        # === Function to Get Swing Support/Resistance ===
        def get_support_resistance(df, lookback=lookback):
            recent_highs = df['high'].tail(lookback)
            recent_lows = df['low'].tail(lookback)
            resistance = recent_highs.max()
            support = recent_lows.min()
            return round(support, 2), round(resistance, 2)    
        support, resistance = get_support_resistance(df, lookback=swing_lookback)
        gap = abs(resistance - support)
    
        # === Current Price ===
        current_price = df['close'].iloc[-1]
        gap_pct = gap / current_price
    
        # === Market Status ===
        if gap_pct < 0.015:             #OLD 0.015
            market_status = "Sideways"
            #return market_status
        else:
            market_status = "Trending"
            #return market_status    
        # === Output ===
        print(f"Support: {support:.2f}")
        print(f"Resistance: {resistance:.2f}")
        print(f"Range: {gap} ({gap_pct*100:.2f}%)")
        print(f"Market Status: {market_status}")
    
        return market_status
    else:
        print("The symbol is not uppercase ❌")    
def pivot_support_resistance(symbol, timeframe, swing_lookback=None):
    if swing_lookback is None:
        swing_lookback = 50
    if symbol.isupper():
        exchange = ccxt.binance()
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=swing_lookback)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['pivot'] = (df['high'] + df['low'] + df['close']) / 3
        df['support1'] = (2 * df['pivot']) - df['high']
        df['support2'] = df['pivot'] - (df['high'] - df['low'])
        df['resistance1'] = (2 * df['pivot']) - df['low']
        df['resistance2'] = df['pivot'] + (df['high'] - df['low'])
        latest = df.iloc[-1]
        support = round(min(latest['support1'], latest['support2']), 2)
        resistance = round(max(latest['resistance1'], latest['resistance2']), 2)
        support = round(support, 2)
        resistance = round(resistance, 2)
        print(f"{symbol} PIVOT base support {support:.2f}")
        print(f"{symbol} PIVOT base resistance {resistance:.2f}")
        #return support, resistance 
    else:
        print("The symbol is not uppercase ❌")

def CURRENT_PRICE(symbol):

    if not symbol:
        print("Coin name is missing..")
        return None

    if symbol.isupper():
        exchange = ccxt.binance()
        exchange.load_markets()  # Important: load markets first
    
        if symbol not in exchange.symbols:
            print(f"{symbol} is not available on Binance.")
            return None
        try:
            ticker = exchange.fetch_ticker(symbol)
            price = ticker['last']
            print(f"{symbol} current price is {price:.2f}")
            #return f"{price:.2f}"
        except Exception as e:
            print(f"Error fetching price: {e}")
            return None        
    else:
        print("The symbol is not uppercase ❌")

def EMA_MA_CROSSOVER(symbol, timeframe, lookback=None,  ma_value=None, ema_value=None):
    if symbol.isupper():
        exchange = ccxt.binance()
        if lookback is None:
            lookback = 500
        if ma_value is None:
            ma_value = 22
        if ema_value is None:
            ema_value = 9
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=lookback)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            ma = SMAIndicator(close=df['close'], window=ma_value).sma_indicator()
            ema = EMAIndicator(close=df['close'], window=ema_value).ema_indicator()
            df['EMA'] = ema
            df['MA'] = ma
            df['prev_EMA'] = df['EMA'].shift(1)
            df['prev_MA'] = df['MA'].shift(1)
            latest_ma = df['MA'].iloc[-1]
            latest_ema = df['EMA'].iloc[-1]
            if (df.iloc[-2]['EMA'] < df.iloc[-2]['MA']) and (df.iloc[-1]['EMA'] > df.iloc[-1]['MA']):
                status = f"EMA_{ema_value} CROSSED ABOVE TO MOVING AVERAGE {ma_value}"
            elif (df.iloc[-2]['EMA'] > df.iloc[-2]['MA']) and (df.iloc[-1]['EMA'] < df.iloc[-1]['MA']):
                status = f"EMA_{ema_value} CROSS BELOW TO MOVING AVERAGE {ma_value}"
            else:
                if latest_ema > latest_ma:
                    market = "EMA is above MA → Bullish trend"
                elif latest_ema < latest_ma:
                    market = "EMA is below SMA → Bearish trend"
                else:
                    market = "EMA equals MA → Neutral trend"            
                status = f" {symbol} -> {market},  CROSSOVER IS NOT YET"
            return status
        except Exception as e:
            print(f"Error fetching price: {e}")
    else:
        print("The symbol is not uppercase ❌")
def is_reversal_candle(open_, close, high, low):
    body = abs(close - open_)
    candle_range = high - low
    upper_wick = high - max(open_, close)
    lower_wick = min(open_, close) - low
    if body < candle_range * 0.3:
        if close > open_ and lower_wick > 2 * body and upper_wick < body:
            return "Bullish Reversal"
        elif close < open_ and upper_wick > 2 * body and lower_wick < body:
            return "Bearish Reversal"
    if close > open_ and lower_wick > upper_wick and lower_wick > body:
        return "Bullish Hammer"
    if close < open_ and upper_wick > lower_wick and upper_wick > body:
        return "Bearish Hammer"
    if close > open_ and upper_wick < body * 0.3 and lower_wick < body * 0.3:
        return "Bullish Marubozu"
    if close < open_ and upper_wick < body * 0.3 and lower_wick < body * 0.3:
        return "Bearish Marubozu"
    return None        
def CANDLE_PATTERNE(symbol,timeframe):
    exchange = ccxt.binance()
    df = pd.DataFrame(exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=6),
                      columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True).dt.tz_convert('Asia/Kolkata')

    highs = df['high'].tolist()[-3:]
    closes = df['close'].tolist()[-3:]
    last_candle = df.iloc[-2]
    reversal = is_reversal_candle(last_candle['open'], last_candle['close'], last_candle['high'], last_candle['low'])

    if reversal is None:
        print ("CANDLE PATTERNE NOT FOUND")
    else:
        return reversal
        print(reversal)
def FVG(symbol, timeframe, FVGlimit=None):
    if FVGlimit is None:
        FVGlimit = 500

    exchange = ccxt.binance() 
    # ======= FETCH DATA =======
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=FVGlimit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # ======= FVG DETECTION =======
    fvg_list = []
    
    for i in range(2, len(df)):
     c1, c2, c3 = df.iloc[i-2], df.iloc[i-1], df.iloc[i]
     
     # Bullish FVG: Gap between c1 high and c3 low
     if c3['low'] > c1['high']:
         fvg_list.append({
             'type': 'bullish',
             'start_index': i-2,
             'end_index': i,
             'gap_low': c1['high'],
             'gap_high': c3['low'],
             'timestamp': c3['timestamp']
         })
     
     # Bearish FVG: Gap between c1 low and c3 high
     elif c3['high'] < c1['low']:
         fvg_list.append({
             'type': 'bearish',
             'start_index': i-2,
             'end_index': i,
             'gap_low': c3['high'],
             'gap_high': c1['low'],
             'timestamp': c3['timestamp']
         })
    
    # ======= OUTPUT LAST TWO FVGs =======
    if fvg_list:
     print(f"Showing the last {min(2, len(fvg_list))} FVG(s):\n")
     for fvg in fvg_list[-2:]:  # Only last two
         print(f"{fvg['timestamp']} | {fvg['type'].upper()} | Gap Low: {fvg['gap_low']} | Gap High: {fvg['gap_high']}")
         return f"{fvg['timestamp']} | {fvg['type'].upper()} | Gap Low: {fvg['gap_low']} | Gap High: {fvg['gap_high']}"
    else:
     print("No FVG found.")
def RSI(symbol, timeframe, RSIlimit=None, rsi_period=None, overbought=None, oversold=None):
    exchange = ccxt.binance()
    if RSIlimit is None:
        RSIlimit = 500
    if rsi_period is None:
        rsi_period = 14
    if overbought is None:
        overbought = 70
    if oversold is None:
        oversold = 30

    def fetch_ohlcv():
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=RSIlimit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    
    def calculate_rsi(df, period):
        delta = df['close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
    
        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()
    
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df
    
    print(f"Starting live RSI monitoring for {symbol} ({timeframe})...")
    last_timestamp = None
    
    try:
        df = fetch_ohlcv()
        df = calculate_rsi(df, rsi_period)
        latest = df.iloc[-1]
        if latest['timestamp'] != last_timestamp:
            last_timestamp = latest['timestamp']
            print(f"{latest['timestamp']} | Close: {latest['close']} | RSI: {latest['RSI']:.2f}", end='')
            if latest['RSI'] > overbought:
                print(" ⚠️ Overbought!")
                return "Overbought"
            elif latest['RSI'] < oversold:
                print(" ⚠️ Oversold!")
                return "Oversold"
            else:
                return "Normal"
    except Exception as e:
        print("Error:", e)

def MARKET_MOOD(symbol, timeframeT1=None, timeframeT2=None, timeframeT3=None, timeframeT4=None, lookback=None, swing_lookback=None, FVGlimit=None, RSIlimit=None, rsi_period=None, overbought=None, oversold=None):
    print(f"It will take some time to analysis {symbol}...")
    print(f"COIN NAME :-  {symbol}")
    CURRENT_PRICE(symbol)
    if timeframeT1 is None:
        timeframeT1 = '15m'
    if timeframeT2 is None:
        timeframeT2 = '1h'
    if timeframeT3 is None:
        timeframeT3 = '4h'
    if timeframeT4 is None:
        timeframeT4 = '1d'
    RSIstatus_dict = {}
    CPATTERNE_dict = {}
    SR_dict = {}   
    for t in timeframeT1, timeframeT2, timeframeT3, timeframeT4:
        print(f"Analysis {symbol} chart on timeframe {t}")
        RSIstatus = RSI(symbol, t, RSIlimit=None, rsi_period=None, overbought=None, oversold=None)
        RSIstatus_dict[f"{t}"] = RSIstatus
        C_PATTERNE = CANDLE_PATTERNE(symbol,t)
        if C_PATTERNE is None:
            C_PATTERNE = 'Normal'

        CPATTERNE_dict[f"{t}"] = C_PATTERNE
        SRSTATUS = get_support_resistance(symbol, t, lookback=None, swing_lookback=None)
        SR_dict[f"{t}"] = SRSTATUS
        print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ \n \n")  
    print()      
    print ("**********FINAL REPORTS************\n")
    print(f"RSI REPORTS: \n| Timeframe  | RSI STATUS |")
    for timeframe, rsi_value in RSIstatus_dict.items():
        print(f"| {timeframe}          |    {rsi_value}   |")
    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ \n \n")    
    print(f"CANDLE PATTERNE Detection: \n | Timeframe  | PATTERNE |")            
    for timeframe, cpatterne in CPATTERNE_dict.items():
        print(f"| {timeframe}          |    {cpatterne}   |")
    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ \n \n")    
    print(f"SUPPORT RESISTAMCE Detection: \n | Timeframe  | PATTERNE |")            
    for timeframe, SR in SR_dict.items():
        print(f"| {timeframe}          |    {SR}   |")
    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ \n \n")    
    for i in timeframeT1, timeframeT2:
        print(f"Finding fair value gap on timeframe {i}")
        FVG(symbol, i, FVGlimit=None)
    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ \n \n")    

    rsikey = "" 
    RSIstatus_confirm = "" 
    count_bearish = 0
    count_bullish = 0
    RSIstatus_oversold = 0
    RSIstatus_Overbought = 0
    SR_STATUS_Count = 0
    for key in [k for k in RSIstatus_dict]:
        if RSIstatus_dict[key].lower().startswith("oversold"):
            RSIstatus_oversold += 1
            RSIstatus_dict[key] == rsikey

        if RSIstatus_dict[key].lower().startswith("Overbought"):
            RSIstatus_Overbought += 1
            RSIstatus_dict[key] == rsikey

    for ckey in [c for c in CPATTERNE_dict]:
        if CPATTERNE_dict[key].lower().startswith("bearish"):
            count_bearish += 1
        if CPATTERNE_dict[key].lower().startswith("bullish"):
            count_bullish += 1
    for SR_key in [sr for sr in SR_dict]:
        if SR_dict[key].lower().startswith("sideways"):
            SR_STATUS_Count += 1
    if count_bearish >= 2 and RSIstatus_oversold >= 2 and SR_STATUS_Count == 0:
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ \n \n")
        print(f"{symbol} IS SHOWING STRONG BEARISH BUT RSI IS Oversold ...!!! \n")
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ \n \n")
    elif count_bullish >=2 and RSIstatus_Overbought >= 2 and SR_STATUS_Count == 0:
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ \n \n")
        print(f"{symbol} IS SHOWING STRONG BULLISH BUT RSI is Overbought ...!!!  \n")
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ \n \n")
    elif count_bearish >= 1 and count_bullish >=1 and rsikey is None and SR_STATUS_Count >= 1:
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ \n \n")
        print(f"{symbol} MARKET IS LOOKING SIDEWAYS  \n")
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ \n \n")
    elif count_bearish >= 2 and rsikey is None and SR_STATUS_Count == 0:
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ \n \n")
        print(f"{symbols} IS LOOKING BEARISH ...  \n")
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ \n \n")
    elif  count_bullish >=2  and rsikey is None and SR_STATUS_Count == 0:
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ \n \n")
        print(f"{symbols} IS LOOKING BULLISH...  \n")
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ \n \n")
    else:
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ \n \n")
        print(f"{symbols} IS CHOPPY OR SIDEWAYS ")
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ \n \n")
        