from datetime import datetime,timedelta
import numpy as np
import pandas as pd
import talib
import math
import requests
import time

def supertrend(coin,df, period, atr_multiplier,pivot_period):
    pivot_period=pivot_period
    trend_atr=atr_multiplier
    trend_period=period
        
    df['OpenTime']=pd.to_datetime(df['OpenTime'])
    
    
    df['ma_40']=talib.MA(df['close'], timeperiod=40)
    df['ma_55']=talib.MA(df['close'], timeperiod=55)
    df['ma_99']=talib.MA(df['close'], timeperiod=99)
    df['ma_100']=talib.MA(df['close'], timeperiod=100)
    df['ma_200']=talib.MA(df['close'], timeperiod=200)

    
    df['ema_5']=talib.EMA(df['close'], timeperiod=5)

    df['ema_55']=talib.EMA(df['close'],55)
    df['ema_100']=talib.EMA(df['close'],100)
    df['ema_200']=talib.EMA(df['close'],200)
    

    
    df['prev_close']=df['close'].shift(1)
    df['prev_open']=df['open'].shift(1)

    
    df['pivot_high'] = pivot(df['high'], pivot_period, pivot_period, 'high')
    df['pivot_low'] = pivot(df['low'], pivot_period, pivot_period, 'low')
    df['atr']=talib.ATR(df['high'], df['low'], df['close'], timeperiod=trend_period)
        
    df['pivot_high']=df['pivot_high'].shift(pivot_period)
    df['pivot_low']=df['pivot_low'].shift(pivot_period)
    
    center = np.NaN
    lastpp=np.NaN
    centers=[np.NaN]
    for idx,row in df.iterrows():
        ph=row['pivot_high']
        pl=row['pivot_low']
        
        if ph:
            lastpp = ph
        elif pl:
            lastpp = pl
        else:
            lastpp=np.NaN
            
            
        if not math.isnan(lastpp):
            if math.isnan(centers[-1]): 
                centers.append(lastpp)
            else:         
                center = round(((centers[-1] * 2) + lastpp)/3,3)
                centers.append(center)
        df.at[idx,'center']=center
    
    df.ffill(axis=0,inplace=True) 
    df['up']=df['center']-(trend_atr*df['atr'])
    df['down']=df['center']+(trend_atr*df['atr'])
    
    Tup=[np.NaN]
    Tdown=[np.NaN]
    Trend=[0]
    df['prev_close']=df['close'].shift(1)
    for idx,row in df.iterrows():
        if row['prev_close'] > Tup[-1]:
            Tup.append(max(row['up'],Tup[-1]))
        else:
            Tup.append(row['up'])
            
        if row['prev_close'] < Tdown[-1]:
            Tdown.append(min(row['down'],Tdown[-1]))
        else:
            Tdown.append(row['down'])
            
        if row['close'] > Tdown[-1]:
            df.at[idx,'in_uptrend']=True
            Trend.append(True)
        elif row['close'] < Tup[-1]:
            df.at[idx,'in_uptrend']=False
            Trend.append(False)
        else:
            if math.isnan(Trend[-1]):
                df.at[idx,'in_uptrend']=True
                Trend.append(True)
            else:
                df.at[idx,'in_uptrend']=Trend[-1]
                Trend.append(Trend[-1])
                
    Tup.pop(0)
    Tdown.pop(0)
    df['up']=Tup
    df['down']=Tdown
    return df


def pivot(osc, LBL, LBR, highlow):
    left = []
    right = []
    pivots=[]
    for i in range(len(osc)):
        pivots.append(0.0)
        if i < LBL + 1:
            left.append(osc[i])
        if i > LBL:
            right.append(osc[i])
        if i > LBL + LBR:
            left.append(right[0])
            left.pop(0)
            right.pop(0)
            if checkhl(left, right, highlow):
                pivots[i - LBR] = osc[i - LBR]
    return pivots


def checkhl(data_back, data_forward, hl):
    if hl == 'high' or hl == 'High':
        ref = data_back[len(data_back)-1]
        for i in range(len(data_back)-1):
            if ref < data_back[i]:
                return 0
        for i in range(len(data_forward)):
            if ref <= data_forward[i]:
                return 0
        return 1
    if hl == 'low' or hl == 'Low':
        ref = data_back[len(data_back)-1]
        for i in range(len(data_back)-1):
            if ref > data_back[i]:
                return 0
        for i in range(len(data_forward)):
            if ref >= data_forward[i]:
                return 0
        return 1
    
def ema_pos(x,col_name):
    if x['close'] > x[col_name]:
        return 1
    else:
        return -1
    
def close_position(client,coin,signal):
    if signal == 'Buy':
        client.futures_create_order(symbol=f'{coin}USDT', side='SELL', type='MARKET', quantity=1000,dualSidePosition=True,positionSide='LONG')
    else:
        client.futures_create_order(symbol=f'{coin}USDT', side='BUY', type='MARKET', quantity=1000,dualSidePosition=True,positionSide='SHORT')
        
def close_position_busd(client,coin,signal):
    if signal == 'Buy':
        client.futures_create_order(symbol=f'{coin}BUSD', side='SELL', type='MARKET', quantity=1000,dualSidePosition=True,positionSide='LONG')
    else:
        client.futures_create_order(symbol=f'{coin}BUSD', side='BUY', type='MARKET', quantity=1000,dualSidePosition=True,positionSide='SHORT')
        
        
telegram_auth_token='5515290544:AAG9T15VaY6BIxX2VYX8x2qr34aC-zVEYMo'
telegram_group_id='notifier2_scanner_bot_link'        
        
def notifier(message):
    telegram_api_url=f'https://api.telegram.org/bot{telegram_auth_token}/sendMessage?chat_id=@{telegram_group_id}&text={message}'
    tel_resp=requests.get(telegram_api_url)
    if tel_resp.status_code==200:
        pass
    else:
        notifier(message)
        
def condition_usdt(timeframe,pivot_period,atr1,period,ma_condition,exchange,client,coin,sleep_time):
    while(True):
        bars = exchange.fetch_ohlcv(f'{coin}/USDT', timeframe=timeframe, limit=300)
        df = pd.DataFrame(bars[:-1], columns=['OpenTime', 'open', 'high', 'low', 'close', 'volume'])
        df['OpenTime'] = pd.to_datetime(df['OpenTime'], unit='ms')+ pd.DateOffset(hours=5, minutes=30)
        super_df=supertrend(coin,df, period, atr1,pivot_period)
        super_df[f'{ma_condition}_pos']=super_df[[ma_condition,'close']].apply(ema_pos,col_name=ma_condition,axis=1)
        ma_pos=super_df.iloc[-1][f'{ma_condition}_pos']
        if super_df.iloc[-1]['in_uptrend'] != super_df.iloc[-2]['in_uptrend']:
            print(f'scanning USDT {super_df.iloc[-1][f"OpenTime"]} trade not found, ma_pos :{super_df.iloc[-1][f"{ma_condition}_pos"]} and uptrend :{super_df.iloc[-1]["in_uptrend"]},sleeping for {sleep_time*60} seconds')
            acc_balance = round(float(client.futures_account()['availableBalance']),2)
            stake=(acc_balance*0.10)*1
            
            entry=super_df.iloc[-1]['close']
            quantity=round(stake/entry,3)

            
            
            signal = ['Buy' if super_df.iloc[-1]['in_uptrend'] == True else 'Sell'][0]
            
            try:
                close_position(client,coin,'Sell') #close open position if any
            except Exception as err:
                try:
                    close_position(client,coin,'Buy')
                except Exception as e:
                    notifier(e)
                    
                notifier(err)
            
            
            notifier(f'Trend Changed {signal} and ma condition {ma_condition} is {ma_pos}')
            
            if signal == 'Buy' and ma_pos == 1:
                #buy order
                client.futures_create_order(symbol=f'{coin}USDT', side='BUY', type='MARKET', quantity=quantity,dualSidePosition=True,positionSide='LONG')
                notifier(f'Bought @{entry}, Timeframe : {timeframe} , pivot_period: {pivot_period},atr:{atr1},period : {period},ma :{ma_condition}')
                
            if signal == 'Sell' and ma_pos == -1:
                    
                #sell order
                client.futures_create_order(symbol=f'{coin}USDT', side='SELL', type='MARKET', quantity=quantity,dualSidePosition=True,positionSide='SHORT')
                notifier(f'Sold @{entry},Timeframe : {timeframe} , pivot_period: {pivot_period},atr:{atr1},period : {period},ma :{ma_condition}')
            
            time.sleep(sleep_time*60)
        else:
            print(f'scanning USDT {super_df.iloc[-1][f"OpenTime"]} trade not found, ma_pos :{super_df.iloc[-1][f"{ma_condition}_pos"]} and uptrend :{super_df.iloc[-1]["in_uptrend"]},sleeping for 30 seconds ')

            time.sleep(30)
            
            
def condition_busdt(timeframe,pivot_period,atr1,period,ma_condition,exchange,client,coin,sleep_time):
    while(True):
        
        bars = exchange.fetch_ohlcv(f'{coin}/USDT', timeframe=timeframe, limit=300)
        df = pd.DataFrame(bars[:-1], columns=['OpenTime', 'open', 'high', 'low', 'close', 'volume'])
        df['OpenTime'] = pd.to_datetime(df['OpenTime'], unit='ms')+ pd.DateOffset(hours=5, minutes=30)
        super_df=supertrend(coin,df, period, atr1,pivot_period)
        super_df[f'{ma_condition}_pos']=super_df[[ma_condition,'close']].apply(ema_pos,col_name=ma_condition,axis=1)
        ma_pos=super_df.iloc[-1][f'{ma_condition}_pos']
        if super_df.iloc[-1]['in_uptrend'] != super_df.iloc[-2]['in_uptrend']:
            print(f'scanning busd {super_df.iloc[-1][f"OpenTime"]} trade found, ma_pos :{super_df.iloc[-1][f"{ma_condition}_pos"]} and uptrend :{super_df.iloc[-1]["in_uptrend"]},sleeping for {sleep_time*60} seconds ')
            acc_balance = round(float(client.futures_account()['availableBalance']),2)
            stake=(acc_balance*0.10)*1
            
            entry=super_df.iloc[-1]['close']
            quantity=round(stake/entry,3)

            
            
            signal = ['Buy' if super_df.iloc[-1]['in_uptrend'] == True else 'Sell'][0]
            
            
            notifier(f'Trend Changed {signal} and ma condition {ma_condition} is {ma_pos}')
            
                           
            try:
                close_position_busd(client,coin,'Sell') #close open position if any
            except Exception as err:
                try:
                    close_position_busd(client,coin,'Buy')
                except Exception as e:
                    notifier(e)
                notifier(err)
            
            if signal == 'Buy' and ma_pos == 1:
                #buy order
                client.futures_create_order(symbol=f'{coin}BUSD', side='BUY', type='MARKET', quantity=quantity,dualSidePosition=True,positionSide='LONG')
                notifier(f'Bought BUSD @{entry} , Timeframe : {timeframe} , pivot_period: {pivot_period},atr:{atr1},period : {period},ma :{ma_condition}')
                
            if signal == 'Sell' and ma_pos == -1:
                    
                #sell order
                client.futures_create_order(symbol=f'{coin}BUSD', side='SELL', type='MARKET', quantity=quantity,dualSidePosition=True,positionSide='SHORT')
                notifier(f'Sold BUSD @{entry},Timeframe : {timeframe} , pivot_period: {pivot_period},atr:{atr1},period : {period},ma :{ma_condition}')
            
            time.sleep(sleep_time*60)
        else:       
            print(f'scanning busd {super_df.iloc[-1][f"OpenTime"]} trade not found, ma_pos :{super_df.iloc[-1][f"{ma_condition}_pos"]} and uptrend :{super_df.iloc[-1]["in_uptrend"]},sleeping for 30 seconds ')
            
            time.sleep(30)