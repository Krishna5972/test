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
stake=1000

client=Client(config.api_key,config.secret_key)

client.futures_change_leverage(symbol=f'{coin}USDT', leverage=10)

precision=0
pricePrecision=2
trade=None
change_in_tp=0
entry_2=0
quantity =0
tp_order_id=0
predict_order_type,signal=None,None
high,low = 0,10000

model_max=pickle.load(open('models/logreg_max_1.8.sav','rb'))

model_min=pickle.load(open('models/logreg_min_1.5.sav','rb'))



while True:
    msg='Scanning for change in trend'
    print(msg)
    super_df,trade_df,df_1m=fetch_data(exchange,coin,timeframe,period,atr_trend)
    
    openorders=client.futures_get_open_orders(symbol=f'{coin}USDT')
    
    if high <= df_1m.iloc[-1]['high']:
            high=df_1m.iloc[-1]['high']
    if low >= df_1m.iloc[-1]['low']:
        low=df_1m.iloc[-1]['low']

    if predict_order_type == 'ENTRY_LIMIT':
        
        if (signal == 'SELL') & (high >= entry) & (len(openorders)==0):
            try:
                tp_order_id=create_limit_tpsl(client,coin,signal,quantity,stop_price,take_profit) 
                msg='TP and SL placed'
                notifier(msg)
                entry=10000
                predict_order_type=None
            except Exception as e:
                msg=f'BUG in placing tp and sl when order got filled : {e}'
                notifier(msg)
                msg=f'singal :{signal},quantity : {quantity},stopprice: {stop_price},takeprofit :{take_profit} : {e}'
                notifier(msg)
        
                
        elif (signal == 'BUY') & (low <= entry) & ((len(openorders)==0)):
            try:
                tp_order_id=create_limit_tpsl(client,coin,signal,quantity,stop_price,take_profit)
                msg='TP and SL placed'
                predict_order_type=None
                entry=-1
            except Exception as e:
                msg=f'BUG in placing tp and sl when order got filled : {e}'
                notifier(msg)
                msg=f'singal :{signal},quantity : {quantity},stopprice: {stop_price},takeprofit :{take_profit} : {e}'
                notifier(msg)
                
    elif predict_order_type == 'RE-ENTRY':
        tp_order_id,change_in_tp=handle_barrier(coin,exchange,client,df_1m,trade,entry_2,openorders,change_in_tp,quantity,tp_order_id,notifier)
        
        

    if super_df.iloc[-1]['in_uptrend'] != super_df.iloc[-2]['in_uptrend']:
        
        high,low = 0,10000
        
        try:
            close_position(client,coin,signal)
        except Exception as e:
            msg=f'Tried to close but no positions are open : {e}'
            notifier(msg)
            
        exchange.cancel_all_orders(f'{coin}USDT')
            
        feature_values,signal=features(super_df,trade_df)
    
        max_pred=model_max.predict([feature_values])[0]
        max_percent=model_max.predict_proba([feature_values])
        
        
        min_pred=model_min.predict([feature_values])[0]
        min_percent=model_min.predict_proba([feature_values])
        
        notifier(f'max pred : {max_pred}')
        notifier(f'min pred : {min_pred}')
        
        if (max_pred ==0) & (min_pred == 0) & (signal == 1):
            msg=f'LIMIT TYPE TRADE,SELLING'
            notifier(msg)
            
            trade='SELL'
            signal='SELL'
            
            entry=super_df.iloc[-1]['close']
            stop_price=entry+(entry*0.0188) 
            entry = round(entry + (entry*0.011),2) #2nd_entry_uptrend
              #stop_loss_uptrend  
            take_profit=entry-(entry*0.0135)   #tp_uptrend
            
            quantity=stake/entry
            quantity = int(round(quantity, precision))
            stop_price=float(round(stop_price, pricePrecision))
            take_profit=float(round(take_profit, pricePrecision))
            change_in_tp=0
            predict_order_type='ENTRY_LIMIT'
            notifier(predict_order_type)
            create_limit_order(client,coin,signal,entry,quantity)
            time.sleep(300)
            
        elif (max_pred ==0) & (min_pred == 1) & (signal == 0):
            msg=f'LIMIT TYPE TRADE,SELLING'
            notifier(msg)
            
            trade='SELL'
            signal='SELL'
            
            entry=super_df.iloc[-1]['close']
            stop_price=entry+(entry*0.0188)
            entry = round(entry + (entry*0.0068),2) #2nd_entry_uptrend
               #stop_loss_uptrend  
            take_profit=entry-(entry*0.01)   #tp_uptrend
            
            quantity=stake/entry
            quantity = int(round(quantity, precision))
            stop_price=float(round(stop_price, pricePrecision))
            take_profit=float(round(take_profit, pricePrecision))
            change_in_tp=0
            predict_order_type='ENTRY_LIMIT'
            notifier(predict_order_type)
            create_limit_order(client,coin,signal,entry,quantity)
            time.sleep(300)
            
            
            
        elif (max_pred ==0) & (min_pred == 1) & (signal == 1):
            msg=f'MARKET TYPE TRADE,SELLING'
            notifier(msg)
            
            trade='SELL'
            signal='SELL'
            
            entry=super_df.iloc[-1]['close']
            
            stop_price=entry+(entry*0.0188)  #stop_loss_uptrend     
            entry_2 = round(entry + (entry*0.011),2) #2nd_entry_uptrend
            take_profit=entry-(entry*0.0135)   #tp_uptrend
            
            quantity=stake/entry
            quantity = int(round(quantity, precision))
            stop_price=float(round(stop_price, pricePrecision))
            take_profit=float(round(take_profit, pricePrecision))
            change_in_tp=0 
            predict_order_type = 'RE-ENTRY'
            notifier(predict_order_type)   
            tp_order_id,barier_order_id=create_order(client,coin,signal,quantity,entry_2,stop_price,take_profit)
            time.sleep(300)
            
        elif (max_pred ==1) & (min_pred == 0) & (signal == 0):
            msg=f'MARKET TYPE TRADE,SELLING'
            notifier(msg)
            
            trade='BUY'
            signal='BUY'
            
            entry=super_df.iloc[-1]['close']
            
            stop_price=entry-(entry*0.0155)  #stop_loss_uptrend     
            entry_2 = round(entry - (entry*0.011),2) #2nd_entry_uptrend
            take_profit=entry+(entry*0.0135)   #tp_uptrend
            
            quantity=stake/entry
            quantity = int(round(quantity, precision))
            stop_price=float(round(stop_price, pricePrecision))
            take_profit=float(round(take_profit, pricePrecision))
            change_in_tp=0 
            predict_order_type = 'RE-ENTRY'
            notifier(predict_order_type)   
            tp_order_id,barier_order_id=create_order(client,coin,signal,quantity,entry_2,stop_price,take_profit)
            time.sleep(300)
        
        elif (max_pred ==1) & (min_pred == 0) & (signal == 1):
            msg=f'LIMIT TYPE TRADE,BUYING'
            notifier(msg)
            
            trade='BUY'
            signal='BUY'
            
            entry=super_df.iloc[-1]['close']

             #2nd_entry_uptrend  
            stop_price=entry-(entry*0.0155)
            entry = round(entry - (entry*0.0068),2)
            take_profit=entry+(entry*0.01)   #tp_uptrend  
            quantity=stake/entry
            quantity = int(round(quantity, precision))
            stop_price=float(round(stop_price, pricePrecision))
            take_profit=float(round(take_profit, pricePrecision))
            change_in_tp=0
            predict_order_type='ENTRY_LIMIT'
            notifier(predict_order_type)
            create_limit_order(client,coin,signal,entry,quantity)
            time.sleep(300)
            
        elif (max_pred ==1) & (min_pred == 1) & (signal == 0):
            msg=f'LIMIT TYPE TRADE,BUYING'
            notifier(msg)
            
            trade='BUY'
            signal='BUY'
            
            entry=super_df.iloc[-1]['close']

             #2nd_entry_uptrend  
            stop_price=entry-(entry*0.0155)
            entry = round(entry - (entry*0.011),2)
            take_profit=entry+(entry*0.0135)   #tp_uptrend  
            quantity=stake/entry
            quantity = int(round(quantity, precision))
            stop_price=float(round(stop_price, pricePrecision))
            take_profit=float(round(take_profit, pricePrecision))
            change_in_tp=0
            predict_order_type='ENTRY_LIMIT'
            notifier(predict_order_type)
            create_limit_order(client,coin,signal,entry,quantity)
            time.sleep(300)
            
        else:
            msg=f'Exception case {max_pred},{min_pred},{signal}'
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
                    
            if predict_order_type =='RE-ENTRY':        
                if stop_market_orders == 0: #implies tp order is hit and entry_2 is open
                    exchange.cancel_all_orders(f'{coin}USDT')
                    notifier('No stop market orders, canceling all open orders')
                    predict_order_type=None
                if tp_order_id not in open_order_ids:
                    exchange.cancel_all_orders(f'{coin}USDT')
                    change_in_tp=0
                    notifier('No TP, canceling all open orders')
                    predict_order_type=None
                
        else:
            predict_order_type=None
            change_in_tp=0
            
        
    
    
    time.sleep(45)