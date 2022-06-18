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
coin='AVAX'
timeframe='5m'
atr,period = 2,76
stake=40

client=Client(config.api_key,config.secret_key)

client.futures_change_leverage(symbol=f'{coin}USDT', leverage=1)

precision=0
pricePrecision=2

model_max=pickle.load(open('models/logreg_buy.sav','rb'))

model_min=pickle.load(open('models/logreg_sell.sav','rb'))

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
    
    super_df['upper_perc'],super_df['lower_perc']=zip(*super_df[['upperband','lowerband','close']].apply(atr_perc,axis=1))
    
    openorders=client.futures_get_open_orders(symbol=f'{coin}USDT')

    trade=None
    if trade =='SELL':
        if super_df.iloc[-1]['high'] >= entry_2 & len(openorders) > 0:
            quantity=quantity*2
            take_profit=entry_2-(entry_2*0.0135) 
            change_tp(client,coin,trade,quantity,take_profit)
        else:
            pass
    elif trade == 'BUY':
        if super_df.iloc[-1]['low'] <= entry_2 & len(openorders) > 0:
            take_profit=entry_2+(entry_2*0.0135)
            change_tp(client,coin,trade,quantity,take_profit)
        else:
            pass









    if super_df.iloc[-1]['in_uptrend'] != super_df.iloc[-2]['in_uptrend']:
        
            
        
        signal = [1 if super_df.iloc[-1]['in_uptrend'] == True else 0][0]
        ema_55_pos = [1 if super_df.iloc[-1]['ema_55_pos'] == 'above' else 0][0]
        ema_20_pos = [1 if super_df.iloc[-1]['ema_20_pos'] == 'above' else 0][0]
        ema_33_pos = [1 if super_df.iloc[-1]['ema_33_pos'] == 'above' else 0][0]
        
        size=super_df.iloc[-1]['size']*100
        
        upper_perc=np.abs(super_df.iloc[-1]['upper_perc'])*100
        lower_perc=np.abs(super_df.iloc[-1]['lower_perc'])*100
    
        
        rsi = super_df.iloc[-1]['rsi']
        prev_trend_1=trade_df.iloc[-1]['candle_count']
        prev_trend_2=trade_df.iloc[-2]['candle_count']
        prev_local_max_bar=trade_df.iloc[-1]['local_max_bar']
        prev_local_min_bar=trade_df.iloc[-1]['local_min_bar']
        prev_max_per=trade_df.iloc[-1]['max']
        prev_min_per=trade_df.iloc[-1]['min']
        
        if super_df.iloc[-1]['in_uptrend']==True:
            
            try:
                prev_position='BUY'
                close_position(client,coin,prev_position)
            except Exception as e:
                msg=f'Tried to close but no positions are open'
                notifier(msg)
                
            exchange.cancel_all_orders(f'{coin}USDT')
                

        
            max_pred=model_max.predict([[signal,ema_55_pos,ema_20_pos,ema_33_pos,rsi,prev_trend_1,prev_trend_2,
                        prev_local_max_bar,prev_local_min_bar,prev_max_per,prev_min_per,upper_perc,lower_perc,size]])[0]
            max_percent=model_max.predict_proba([[signal,ema_55_pos,ema_20_pos,ema_33_pos,rsi,prev_trend_1,prev_trend_2,
                        prev_local_max_bar,prev_local_min_bar,prev_max_per,prev_min_per,upper_perc,lower_perc,size]])
            
            if max_pred == 0 or max_pred == 1:
                msg=f'Taking the trade {max_pred}'
                notifier(msg)
                trade='SELL'
                
                signal='SELL'
                entry=super_df.iloc[-1]['close']
                stop_price=entry+(entry*0.0185)  #stop_loss_uptrend     
                entry_2 = round(entry + (entry*0.01),2) #2nd_entry_uptrend
                take_profit=entry-(entry*0.0135)   #tp_uptrend
                
                quantity=stake/entry
                quantity = int(round(quantity, precision))
                stop_price=float(round(stop_price, pricePrecision))
                take_profit=float(round(take_profit, pricePrecision))
                
                create_order(client,coin,signal,quantity,entry_2,stop_price,take_profit)
                time.sleep(300)
                
            else:
                msg=f'Skipping the trade'
                notifier(msg)
                time.sleep(300)
            
                
            
            
        if super_df.iloc[-1]['in_uptrend']==False:
            
            try:
                prev_position='SELL'
                close_position(client,coin,prev_position)
            except Exception as e:
                msg=f'Tried to close but no positions are open'
                notifier(msg)
                
            exchange.cancel_all_orders(f'{coin}USDT')
        
            min_pred=model_min.predict([[signal,ema_55_pos,ema_20_pos,ema_33_pos,rsi,prev_trend_1,prev_trend_2,
                        prev_local_max_bar,prev_local_min_bar,prev_max_per,prev_min_per,upper_perc,lower_perc,size]])[0]
            min_percent=model_min.predict_proba([[signal,ema_55_pos,ema_20_pos,ema_33_pos,rsi,prev_trend_1,prev_trend_2,
                        prev_local_max_bar,prev_local_min_bar,prev_max_per,prev_min_per,upper_perc,lower_perc,size]])
            if min_pred == 0 or  min_pred == 1:
                msg=f'taking the trade {min_pred}'
                notifier(msg)
                
                signal='BUY'
                entry=super_df.iloc[-1]['close']
                stop_price=entry-(entry*0.016)  #stop_loss_uptrend  
                entry_2 = round(entry - (entry*0.011),2) #2nd_entry_uptrend
                take_profit=entry+(entry*0.0135)   #tp_uptrend
                
                quantity=stake/entry
                quantity = int(round(quantity, precision))
                stop_price=float(round(stop_price, pricePrecision))
                take_profit=float(round(take_profit, pricePrecision))
                
                create_order(client,coin,signal,quantity,entry_2,stop_price,take_profit)
                time.sleep(300)
                
            else:
                msg=f'Skipping the trade'
                notifier(msg)    
                time.sleep(300)      
    else:
        if len(openorders) == 2:
            exchange.cancel_all_orders(f'{coin}USDT')
        else:
            pass
            
        
    
    
    time.sleep(20)
    
        
