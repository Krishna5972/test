import requests
import pandas as pd
from datetime import datetime
import time
import ccxt
import config
from binance.client import Client
import pandas as pd
from bot_funtions import *
import warnings
warnings.filterwarnings('ignore')
import pickle

telegram_auth_token='5515290544:AAG9T15VaY6BIxX2VYX8x2qr34aC-zVEYMo'
telegram_group_id='notifier2_scanner_bot_link'


        
exchange = ccxt.binanceus({
    "apiKey": config.api_key,
    "secret": config.secret_key,
    'options': {
    'defaultType': 'future',
    },
})

coin='ETH'
timeframe='1m'
period=7
atr1=1
pivot_period=1
ma_condition='ema_5'

client=Client(config.api_key,config.secret_key)

client.futures_change_leverage(symbol=f'{coin}USDT', leverage=2)

acc_balance = round(float(client.futures_account()['totalWalletBalance']),2)
stake=(acc_balance*0.70)*2


while(True):
    print('scanning')
    bars = exchange.fetch_ohlcv(f'{coin}/USDT', timeframe=timeframe, limit=300)
    df = pd.DataFrame(bars[:-1], columns=['OpenTime', 'open', 'high', 'low', 'close', 'volume'])
    df['OpenTime'] = pd.to_datetime(df['OpenTime'], unit='ms')+ pd.DateOffset(hours=5, minutes=30)
    super_df=supertrend(coin,df, period, atr1,pivot_period)
    super_df[f'{ma_condition}_pos']=super_df[[ma_condition,'close']].apply(ema_pos,col_name=ma_condition,axis=1)
    if super_df.iloc[-1]['in_uptrend'] != super_df.iloc[-2]['in_uptrend']:
        
        entry=super_df.iloc[-1]['close']
        quantity=round(stake/entry,3)

        ma_pos=super_df.iloc[-1][ma_condition]
        
        signal = ['Buy' if super_df.iloc[-1]['in_uptrend'] == True else 'Sell']
        
        notifier(f'Trend Changed {signal} and ma condition {ma_condition} is {ma_pos}')
        
        if signal == 'Buy' and ma_pos == 1:
            
            try:
                close_position(client,coin,signal) #close open position if any
            except Exception as e:
                pass
                
            #buy order
            client.futures_create_order(symbol=f'{coin}USDT', side='BUY', type='MARKET', quantity=quantity,dualSidePosition=True,positionSide='LONG')
            notifier(f'Bought @{entry}')
            
        if signal == 'Sell' and ma_pos == -1:
            
            try:
                close_position(client,coin,signal)
            except Exception as e:
                pass
            #sell order
            client.futures_create_order(symbol=f'{coin}USDT', side='SELL', type='MARKET', quantity=quantity,dualSidePosition=True,positionSide='SHORT')
            notifier(f'Sold @{entry}')
        
        time.sleep(60)
    else:
        ma=super_df[ma_condition].iloc[-1]
        close=super_df['close'].iloc[-1]
        
        print(f'scanning at {super_df.iloc[-1][f"OpenTime"]} trade not found {super_df.iloc[-1][f"{ma_condition}_pos"]} and signal is {super_df.iloc[-1]["in_uptrend"]}')
        time.sleep(35)