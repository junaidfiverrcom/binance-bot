import ccxt
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from zoneinfo import ZoneInfo
import asyncio
import platform
import logging
from colorama import init, Fore, Style
import requests
import os

# Initialize colorama for colored terminal output
init()

# Setup logging
logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
SYMBOLS = [
    '1000LUNC/USDT:USDT', '1000SHIB/USDT:USDT', '1000XEC/USDT:USDT',
    '1INCH/USDT:USDT', 'AAVE/USDT:USDT', 'ADA/USDT:USDT', 'ALGO/USDT:USDT',
    'ALPHA/USDT:USDT', 'ANKR/USDT:USDT', 'APT/USDT:USDT', 'AR/USDT:USDT',
    'ARB/USDT:USDT', 'ARPA/USDT:USDT', 'ATA/USDT:USDT', 'AVAX/USDT:USDT',
    'AXS/USDT:USDT', 'BAKE/USDT:USDT', 'BAND/USDT:USDT', 'BEL/USDT:USDT',
    'BCH/USDT:USDT', 'BNB/USDT:USDT', 'BSV/USDT:USDT', 'BTCDOM/USDT:USDT',
    'BTC/USDT:USDT', 'CAKE/USDT:USDT', 'C98/USDT:USDT', 'CELO/USDT:USDT',
    'CHZ/USDT:USDT', 'COMP/USDT:USDT', 'CRV/USDT:USDT', 'CRO/USDT:USDT',
    'CTSI/USDT:USDT', 'DEFI/USDT:USDT', 'DOGE/USDT:USDT', 'DOT/USDT:USDT',
    'DYDX/USDT:USDT', 'EGLD/USDT:USDT', 'ENS/USDT:USDT', 'ETC/USDT:USDT',
    'ETH/USDT:USDT', 'FET/USDT:USDT', 'FIL/USDT:USDT', 'FLOW/USDT:USDT',
    'FTM/USDT:USDT', 'FXS/USDT:USDT', 'GALA/USDT:USDT', 'GRT/USDT:USDT',
    'GTC/USDT:USDT', 'HBAR/USDT:USDT', 'HNT/USDT:USDT', 'IMX/USDT:USDT',
    'INJ/USDT:USDT', 'IOST/USDT:USDT', 'IOTX/USDT:USDT', 'KAVA/USDT:USDT',
    'KNC/USDT:USDT', 'KSM/USDT:USDT', 'LDO/USDT:USDT', 'LRC/USDT:USDT',
    'LTC/USDT:USDT', 'LPT/USDT:USDT', 'LUNA2/USDT:USDT', 'MASK/USDT:USDT',
    'MATIC/USDT:USDT', 'MKR/USDT:USDT', 'NEAR/USDT:USDT', 'NEO/USDT:USDT',
    'OP/USDT:USDT', 'QNT/USDT:USDT', 'QTUM/USDT:USDT', 'RLC/USDT:USDT',
    'RSR/USDT:USDT', 'RUNE/USDT:USDT', 'RVN/USDT:USDT', 'SAND/USDT:USDT',
    'SKL/USDT:USDT', 'SNX/USDT:USDT', 'SOL/USDT:USDT', 'SPELL/USDT:USDT',
    'STG/USDT:USDT', 'STX/USDT:USDT', 'SUI/USDT:USDT', 'SXP/USDT:USDT',
    'TRX/USDT:USDT', 'THETA/USDT:USDT', 'UNI/USDT:USDT', 'USDC/USDT:USDT',
    'VET/USDT:USDT', 'WAVES/USDT:USDT', 'XEC/USDT:USDT', 'XLM/USDT:USDT',
    'XMR/USDT:USDT', 'XRP/USDT:USDT', 'XTZ/USDT:USDT', 'ZEC/USDT:USDT',
    'ZIL/USDT:USDT', 'ZRX/USDT:USDT'
]

TIMEFRAMES = {
    '2h': 2 * 60 * 60,
    '4h': 4 * 60 * 60,
    '8h': 8 * 60 * 60,
    '12h': 12 * 60 * 60,
    '1d': 24 * 60 * 60,
    '2d': 2 * 24 * 60 * 60,
    '3d': 3 * 24 * 60 * 60,
    '1w': 7 * 24 * 60 * 60
}
WICK_THRESHOLD = 2
CHECK_WINDOW = 3 * 60
UPDATE_INTERVAL = 60

# Initialize ccxt for Binance futures
exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

# Load markets and filter valid symbols at startup
exchange.load_markets()
VALID_SYMBOLS = [symbol for symbol in SYMBOLS if symbol in exchange.symbols]
INVALID_COINS = [symbol for symbol in SYMBOLS if symbol not in exchange.symbols]

# Print and log invalid coins at startup
if INVALID_COINS:
    message = f"Yo, these coins ain't on Binance futures: {', '.join(INVALID_COINS)}"
    print(f"{Fore.RED}{message}{Style.RESET_ALL}")
    logging.warning(message)
else:
    message = "All coins good to go on Binance futures!"
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")
    logging.info(message)

def identify_candlestick_pattern(open_price, high_price, low_price, current_price):
    body = abs(current_price - open_price)
    upper_wick = max(high_price - max(open_price, current_price), 0)
    lower_wick = max(min(open_price, current_price) - low_price, 0)
    total_range = high_price - low_price

    if total_range == 0:
        return 'None', 'No Range'

    body_percent = body / total_range
    upper_wick_percent = upper_wick / total_range
    lower_wick_percent = lower_wick / total_range

    # Wick Side
    if lower_wick > upper_wick and lower_wick >= WICK_THRESHOLD * body:
        wick_side = 'Longer Lower Wick'
    elif upper_wick > lower_wick and upper_wick >= WICK_THRESHOLD * body:
        wick_side = 'Longer Upper Wick'
    elif upper_wick > 0 and lower_wick > 0 and abs(upper_wick - lower_wick) < 0.1 * total_range:
        wick_side = 'Equal Wicks'
    else:
        wick_side = 'No Significant Wick'

    # Candlestick Pattern Detection (prioritized)
    if body_percent <= 0.05:
        if upper_wick_percent >= 0.8 and lower_wick_percent < 0.05:
            pattern = 'Gravestone Doji'
        elif lower_wick_percent >= 0.8 and upper_wick_percent < 0.05:
            pattern = 'Dragonfly Doji'
        elif upper_wick_percent >= 0.4 and lower_wick_percent >= 0.4 and abs(upper_wick - lower_wick) < 0.1 * total_range:
            pattern = 'Rickshaw Man'
        elif upper_wick_percent >= 0.4 and lower_wick_percent >= 0.4:
            pattern = 'Long-legged Doji'
        elif upper_wick_percent >= 0.3 and lower_wick_percent >= 0.3:
            pattern = 'Spinning Top'
        elif upper_wick_percent >= 0.2 and lower_wick_percent >= 0.2:
            pattern = 'High Wave Candle'
        else:
            pattern = 'Doji'
    elif body_percent <= 0.2:
        if upper_wick >= WICK_THRESHOLD * body and lower_wick_percent < 0.1:
            pattern = 'Pin Bar'
        elif lower_wick >= WICK_THRESHOLD * body and upper_wick_percent < 0.1:
            pattern = 'Pin Bar'
        elif lower_wick_percent >= 0.6 and body_percent <= 0.2:
            pattern = 'Hammer' if current_price > open_price else 'Hanging Man'
        elif upper_wick_percent >= 0.6 and body_percent <= 0.2:
            pattern = 'Shooting Star' if current_price < open_price else 'Inverted Hammer'
        else:
            pattern = 'None'
    else:
        pattern = 'None'

    return pattern, wick_side

async def check_upcoming_closes(now):
    pkt = now.astimezone(ZoneInfo('Asia/Karachi'))
    upcoming = []
    for timeframe, interval_seconds in TIMEFRAMES.items():
        current_time_seconds = now.timestamp()
        seconds_since_last_candle = current_time_seconds % interval_seconds
        time_to_next_candle = interval_seconds - seconds_since_last_candle
        if CHECK_WINDOW - 30 <= time_to_next_candle <= CHECK_WINDOW + 60:
            message = f"Yo, {timeframe} candles closing in ~{int(time_to_next_candle/60)} minutes!"
            upcoming.append(message)
    if upcoming:
        if platform.system() == 'Windows':
            try:
                import winsound
                winsound.Beep(1000, 500)
            except:
                print(f"{Fore.YELLOW}Beep not supported; check upcoming closes!{Style.RESET_ALL}")
                logging.warning("Audio beep not supported")
        else:
            print(f"{Fore.YELLOW}Audio alerts not supported on {platform.system()}{Style.RESET_ALL}")
            logging.warning(f"Audio alerts not supported on {platform.system()}")
        print(f"{Fore.YELLOW}{' | '.join(upcoming)}{Style.RESET_ALL}")
        logging.info(' | '.join(upcoming))
        # Send Telegram notification for upcoming closes
        for message in upcoming:
            send_telegram_message(f"⏰ <b>{message}</b>")
    return upcoming, min([interval_seconds - (now.timestamp() % interval_seconds) for interval_seconds in TIMEFRAMES.values()] + [UPDATE_INTERVAL])

# Telegram configuration (use environment variables)
BOT_TOKEN = os.getenv('BOT_TOKEN', '8070648958:AAEZCwZPElsRmHweoq-X5rIp0f-GPfkLtCg')
CHAT_ID = os.getenv('CHAT_ID', '6665886955')

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    for attempt in range(3):  # Retry up to 3 times
        try:
            response = requests.post(url, data=payload, timeout=5)
            if response.status_code == 200:
                print("✅ Telegram message sent!")
                logging.info("Telegram message sent successfully")
                return
            else:
                print(f"❌ Failed to send message: {response.text}")
                logging.warning(f"Failed to send Telegram message: {response.text}")
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            logging.error(f"Error sending Telegram message: {e}")
        time.sleep(2 ** attempt)  # Exponential backoff
    logging.error("Failed to send Telegram message after retries")

async def process_symbol(symbol, timeframe, interval_seconds, semaphore):
    async with semaphore:
        try:
            ticker = exchange.fetch_ticker(symbol)
            current_price = float(ticker['last']) if ticker.get('last') is not None else None
            if current_price is None:
                print(f"{Fore.RED}Oops, no valid price for {symbol} {timeframe}{Style.RESET_ALL}")
                logging.warning(f"No valid price for {symbol} {timeframe}")
                return

            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=2)
            if len(ohlcv) < 2:
                print(f"{Fore.YELLOW}Insufficient OHLCV data for {symbol} {timeframe}{Style.RESET_ALL}")
                logging.warning(f"Insufficient OHLCV data for {symbol} {timeframe}")
                return

            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)

            now = datetime.fromtimestamp(exchange.fetch_time() / 1000.0, tz=ZoneInfo('UTC'))
            pkt = now.astimezone(ZoneInfo('Asia/Karachi'))
            current_candle = df.iloc[-1]
            candle_close_time = df['timestamp'].iloc[-1] + timedelta(seconds=interval_seconds)
            time_to_close = (candle_close_time - now).total_seconds()

            if CHECK_WINDOW - 30 <= time_to_close <= CHECK_WINDOW + 30:
                pattern, wick_side = identify_candlestick_pattern(
                    current_candle['open'], current_candle['high'],
                    current_candle['low'], current_price)

                if pattern != 'None':
                    pkt_24hr = pkt.strftime('%Y-%m-%d %H:%M:%S')
                    pkt_12hr = pkt.strftime('%Y-%m-%d %I:%M:%S %p')
                    output = (f"📊 <b>Candle Alert!</b>\n"
                              f"📅 Date: <code>{pkt_24hr}</code>\n"
                              f"🕒 Timeframe: <b>{timeframe}</b>\n"
                              f"💰 Coin: <b>{symbol}</b>\n"
                              f"🧠 Pattern: <b>{pattern}</b>\n"
                              f"💥 Wick: <b>{wick_side}</b>\n")
                    print(output)
                    logging.info(output)
                    send_telegram_message(output)

        except ccxt.RateLimitExceeded:
            print(f"{Fore.RED}Rate limit exceeded for {symbol} {timeframe}. Retrying...{Style.RESET_ALL}")
            logging.warning(f"Rate limit exceeded for {symbol} {timeframe}")
            await asyncio.sleep(10)
            await process_symbol(symbol, timeframe, interval_seconds, semaphore)
        except ccxt.NetworkError as e:
            print(f"{Fore.RED}Network error for {symbol} {timeframe}: {e}{Style.RESET_ALL}")
            logging.error(f"Network error for {symbol} {timeframe}: {e}")
        except ccxt.ExchangeError as e:
            print(f"{Fore.RED}Exchange error for {symbol} {timeframe}: {e}{Style.RESET_ALL}")
            logging.error(f"Exchange error for {symbol} {timeframe}: {e}")
        except Exception as e:
            print(f"{Fore.RED}Unexpected error for {symbol} {timeframe}: {e}{Style.RESET_ALL}")
            logging.error(f"Unexpected error for {symbol} {timeframe}: {e}")

async def refresh_markets():
    while True:
        try:
            exchange.load_markets()
            global VALID_SYMBOLS
            VALID_SYMBOLS = [symbol for symbol in SYMBOLS if symbol in exchange.symbols]
            logging.info(f"Refreshed markets. Valid symbols: {len(VALID_SYMBOLS)}")
        except Exception as e:
            logging.error(f"Failed to refresh markets: {e}")
        await asyncio.sleep(3600)  # Refresh every hour

async def main():
    # Start market refresh task
    asyncio.create_task(refresh_markets())
    
    # Semaphore to limit concurrent API calls
    semaphore = asyncio.Semaphore(10)
    
    while True:
        now = datetime.fromtimestamp(exchange.fetch_time() / 1000.0, tz=ZoneInfo('UTC'))
        print(f"{Fore.CYAN}💓 Yo, I'm alive!{Style.RESET_ALL}", end="", flush=True)
        logging.info("Bot heartbeat")

        upcoming, min_sleep = await check_upcoming_closes(now)

        tasks = []
        for symbol in VALID_SYMBOLS:
            for timeframe, interval_seconds in TIMEFRAMES.items():
                time_to_next = interval_seconds - (now.timestamp() % interval_seconds)
                if CHECK_WINDOW - 30 <= time_to_next <= CHECK_WINDOW + 30:
                    tasks.append(process_symbol(symbol, timeframe, interval_seconds, semaphore))

        if tasks:
            await asyncio.gather(*tasks)

        print(".", flush=True)
        await asyncio.sleep(min(min_sleep, UPDATE_INTERVAL))

if __name__ == "__main__":
    # Test message to confirm Telegram works
    send_telegram_message("✅ Hello from Binance candle bot! Telegram is working.")
    
    # Start main loop
    asyncio.run(main())