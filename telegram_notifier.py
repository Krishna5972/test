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
atr_trend,period = 2,76
stake=40

client=Client(config.api_key,config.secret_key)

client.futures_change_leverage(symbol=f'{coin}USDT', leverage=1)

precision=0
pricePrecision=2
trade=None
change_in_tp=0

model_max=pickle.load(open('models/logreg_buy_new.sav','rb'))

model_min=pickle.load(open('models/logreg_sell_new.sav','rb'))



while True:
    msg='Scanning for change in trend'
    print(msg)
    

    super_df,trade_df,df_1m=fetch_data(exchange,coin,timeframe,period,atr_trend,change_in_tp)
    
    openorders=client.futures_get_open_orders(symbol=f'{coin}USDT')

    tp_order_id,change_in_tp=handle_barrier(coin,exchange,client,df_1m,trade,entry_2,openorders,change_in_tp,quantity,tp_order_id,notifier)



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
                change_in_tp=0
                
                tp_order_id,barier_order_id=create_order(client,coin,signal,quantity,entry_2,stop_price,take_profit)
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
                
                trade='SELL'
                signal='BUY'
                entry=super_df.iloc[-1]['close']
                stop_price=entry-(entry*0.016)  #stop_loss_uptrend  
                entry_2 = round(entry - (entry*0.011),2) #2nd_entry_uptrend
                take_profit=entry+(entry*0.0135)   #tp_uptrend
                
                quantity=stake/entry
                quantity = int(round(quantity, precision))
                stop_price=float(round(stop_price, pricePrecision))
                take_profit=float(round(take_profit, pricePrecision))
                change_in_tp=0
                
                tp_order_id,barier_order_id=create_order(client,coin,signal,quantity,entry_2,stop_price,take_profit)
                time.sleep(300)
                
            else:
                msg=f'Skipping the trade'
                notifier(msg)    
                time.sleep(300)      
    else:
        openorders=client.futures_get_open_orders(symbol=f'{coin}USDT')
        if len(openorders) > 0:  #if tp is hit,close based on open order type
            stop_market_orders=0
            limit_orders=0
            open_order_ids=[]
            for order in openorders:
                open_order_ids.append(order['orderId'])
                if order['type'] == 'STOP_MARKET':
                    stop_market_orders+=1
                if order['type'] == 'LIMIT':
                    limit_orders+=1
                    
            if stop_market_orders == 0: #implies tp order is hit and entry_2 is open
                exchange.cancel_all_orders(f'{coin}USDT')
                notifier('No stop market orders, canceling all open orders')
            if tp_order_id not in open_order_ids:
                exchange.cancel_all_orders(f'{coin}USDT')
                change_in_tp=0
                notifier('No TP, canceling all open orders')
                
            
    

        else:
            change_in_tp=0
            
        
    
    
    time.sleep(20)
    
        
