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
'1m':1,
'5m':5,
'15m':15,
'30m':30,
'1h':60,
'2h':120,
'4h':240,
'1d':1440
}

print('Started running')

coin='ETH'
timeframe_usdt='1m' 
period_usdt=5
atr1_usdt=1
pivot_period_usdt=1
ma_condition_usdt='ema_5'
time_usdt=timeframes_dict[timeframe_usdt]

client=Client(config.api_key,config.secret_key)

client.futures_change_leverage(symbol=f'{coin}USDT', leverage=10)
notifier('Heroku Dyno Cycle')
client.futures_change_leverage(symbol=f'{coin}BUSD', leverage=10)


timeframe_busd='15m'  
period_busd=28
atr1_busd=1
pivot_period_busd=5
ma_condition_busd='ema_200'
time_busd=timeframes_dict[timeframe_busd]



p1=Process(target=condition_usdt,args=[timeframe_usdt,pivot_period_usdt,atr1_usdt,period_usdt,ma_condition_usdt,exchange,client,coin,time_usdt])
p2=Process(target=condition_busdt,args=[timeframe_busd,pivot_period_busd,atr1_busd,period_busd,ma_condition_busd,exchange,client,coin,time_busd])    
    

if __name__=='__main__':
    p1.start()
    p2.start()
            