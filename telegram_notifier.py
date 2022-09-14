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


coin='LUNA2'
timeframe='1m'
atr_trend,period = 1,56
stake=100

client=Client(config.api_key,config.secret_key)

client.futures_change_leverage(symbol=f'{coin}BUSD', leverage=10)

precision=0
pricePrecision=2
trade=None
change_in_tp=0
entry_2=0
quantity =0
tp_order_id=0
predict_order_type,signal=None,None

def close_position(client,coin,signal):
    if signal == 'Buy':
        client.futures_create_order(symbol=f'{coin}BUSD', side='SELL', type='MARKET', quantity=quantity,dualSidePosition=True,positionSide='LONG')
    else:
        client.futures_create_order(symbol=f'{coin}BUSD', side='BUY', type='MARKET', quantity=quantity,dualSidePosition=True,positionSide='SHORT')

while True:
    super_df=fetch_data(exchange,coin,timeframe,period,atr_trend)
    entry=super_df.iloc[-1]['close']
    quantity=round(stake/entry)
    if super_df.iloc[-1]['in_uptrend'] != super_df.iloc[-2]['in_uptrend']:
        print(super_df.iloc[-1]['in_uptrend'])
        trade=1
        if signal =='Buy':
            client.futures_create_order(symbol=f'{coin}BUSD', side='SELL', type='MARKET', quantity=quantity,dualSidePosition=True,positionSide='LONG')
        elif signal =='Sell':
            client.futures_create_order(symbol=f'{coin}BUSD', side='BUY', type='MARKET', quantity=quantity,dualSidePosition=True,positionSide='SHORT')     

        if str(super_df.iloc[-1]['in_uptrend']) == 'False':
            client.futures_create_order(symbol=f'{coin}BUSD', side='BUY', type='MARKET', quantity=quantity,dualSidePosition=True,positionSide='LONG')
            curr_trade='Buy'
            signal=curr_trade
        elif str(super_df.iloc[-1]['in_uptrend']) == 'True':
            client.futures_create_order(symbol=f'{coin}BUSD', side='SELL', type='MARKET', quantity=quantity,dualSidePosition=True,positionSide='SHORT')
            curr_trade='Sell'
            signal=curr_trade
        time.sleep(59)
    elif trade==1:
        if curr_trade=='Buy' and super_df.iloc[-2]['in_uptrend']=='False' and super_df['color']==-1:
            close_position(client,coin,curr_trade)
            trade=0
        elif curr_trade=='Sell' and super_df.iloc[-2]['in_uptrend']=='True' and super_df['color']==1:
            close_position(client,coin,curr_trade)
            trade=0