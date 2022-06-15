import requests
import pandas as pd
import json
import pytz
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

def notifier(message):
    telegram_api_url=f'https://api.telegram.org/bot{telegram_auth_token}/sendMessage?chat_id=@{telegram_group_id}&text={message}'
    tel_resp=requests.get(telegram_api_url)
    if tel_resp.status_code==200:
        pass
    else:
        notifier(message)
        
exchange = ccxt.binanceus({
    "apiKey": config.api_key,
    "secret": config.secret_key,
    'options': {
    'defaultType': 'future',
    },
})
coin='AVAX'
timeframe='5m'
atr,period = 2,31


client=Client(config.api_key,config.secret_key)

while True:
    msg='Scanning for change in trend'
    print(msg)
    bars = exchange.fetch_ohlcv(f'{coin}/USDT', timeframe=timeframe, limit=350)
    df = pd.DataFrame(bars[:-1], columns=['OpenTime', 'open', 'high', 'low', 'close', 'volume'])
    df['OpenTime'] = pd.to_datetime(df['OpenTime'], unit='ms')+ pd.DateOffset(hours=5, minutes=30)

    super_df=supertrend(df,period,atr)

    trade_df=create_signal_df(super_df,df,coin,timeframe,atr,period,100,100)
    trade_df['max']=((trade_df['local_max']-trade_df['entry'])/trade_df['entry'])*100
    trade_df['min']=((trade_df['local_min']-trade_df['entry'])/trade_df['entry'])*100

    super_df['ema_20_pos']=super_df[['ema_20','close']].apply(ema_pos,col_name='ema_20',axis=1)
    super_df['ema_33_pos']=super_df[['ema_33','close']].apply(ema_pos,col_name='ema_33',axis=1)
    super_df['ema_55_pos']=super_df[['ema_55','close']].apply(ema_pos,col_name='ema_55',axis=1)

    if super_df.iloc[-1]['in_uptrend'] != super_df.iloc[-2]['in_uptrend']:
        signal = [1 if super_df.iloc[-1]['in_uptrend'] == True else 0][0]
        ema_55_pos = [1 if super_df.iloc[-1]['ema_55_pos'] == 'above' else 0][0]
        ema_20_pos = [1 if super_df.iloc[-1]['ema_20_pos'] == 'above' else 0][0]
        ema_33_pos = [1 if super_df.iloc[-1]['ema_33_pos'] == 'above' else 0][0]
        rsi = super_df.iloc[-1]['rsi']
        prev_trend_1=trade_df.iloc[-1]['candle_count']
        prev_trend_2=trade_df.iloc[-2]['candle_count']
        prev_local_max_bar=trade_df.iloc[-1]['local_max_bar']
        prev_local_min_bar=trade_df.iloc[-1]['local_min_bar']
        prev_max_per=trade_df.iloc[-1]['max']
        prev_min_per=trade_df.iloc[-1]['min']
        model_max=pickle.load(open('models/log_reg_1.5_max_2_31.sav','rb'))
        max_pred=model_max.predict([[signal,ema_55_pos,ema_20_pos,ema_33_pos,rsi,prev_trend_1,prev_trend_2,
                    prev_local_max_bar,prev_local_min_bar,prev_max_per,prev_min_per]])[0]
        max_percent=model_max.predict_proba([[signal,ema_55_pos,ema_20_pos,ema_33_pos,rsi,prev_trend_1,prev_trend_2,
                    prev_local_max_bar,prev_local_min_bar,prev_max_per,prev_min_per]])
        if max_pred == 0:
            msg=f'In current trend cycle it cannot reach a maximum of 1.5% with {max_percent} prob signal is to {signal}'
            notifier(msg)
        else:
            msg=f'Can reach a maximum of 1.5% with {max_percent} prob signal is to {signal}'
            notifier(msg)
        
        model_min=pickle.load(open('models/log_reg_1.5_min_2_31.sav','rb'))
        min_pred=model_min.predict([[signal,ema_55_pos,ema_20_pos,ema_33_pos,rsi,prev_trend_1,prev_trend_2,
                    prev_local_max_bar,prev_local_min_bar,prev_max_per,prev_min_per]])[0]
        min_percent=model_min.predict_proba([[signal,ema_55_pos,ema_20_pos,ema_33_pos,rsi,prev_trend_1,prev_trend_2,
                    prev_local_max_bar,prev_local_min_bar,prev_max_per,prev_min_per]])
        if min_pred == 0:
            msg=f'In current trend cycle it cannot fall to 1.5% with {min_percent} prob signal is to {signal}'
            notifier(msg)
        else:
            msg=f'Can fall to a minimum of 1.5% with {min_percent} prob signal is to {signal}'
            notifier(msg)
        time.sleep(500)
        
        
        
    else:
        pass
    
    time.sleep(30)
    
        
