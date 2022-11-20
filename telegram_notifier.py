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
from multiprocessing import Process

telegram_auth_token='5515290544:AAG9T15VaY6BIxX2VYX8x2qr34aC-zVEYMo'
telegram_group_id='notifier2_scanner_bot_link'


        
exchange = ccxt.binanceus({
    "apiKey": config.api_key,
    "secret": config.secret_key,
    'options': {
    'defaultType': 'future',
    },
})

timeframes_dict={
'5m':5,
'15m':15,
'30m':30,
'1h':60,
'2h':120,
'4h':240,
'1d':1440
}


coin='ETH'
timeframe_1='15m'  #dont forget to change sleep time accordingly
period_1=56
atr1_1=3
pivot_period_1=3
ma_condition_1='ema_200'
time_1=timeframes_dict[timeframe_1]

client=Client(config.api_key,config.secret_key)

client.futures_change_leverage(symbol=f'{coin}USDT', leverage=1)
client.futures_change_leverage(symbol=f'{coin}BUSD', leverage=1)

timeframe_busd='1d'  #dont forget to change sleep time accordingly
period_busd=56
atr1_busd=3
pivot_period_busd=3
ma_condition_busd='ema_200'
time_2=timeframes_dict[timeframe_busd]



p1=Process(target=condition_usdt,args=[timeframe_1,pivot_period_1,atr1_1,period_1,ma_condition_1,exchange,client,coin,time_1])
p2=Process(target=condition_busdt,args=[timeframe_busd,pivot_period_busd,atr1_busd,period_busd,ma_condition_busd,exchange,client,coin,time_2])    
    

if __name__=='__main__':
    p1.start()
    p2.start()
            