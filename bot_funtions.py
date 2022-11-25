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
    df['lower_band']=Tup
    df['upper_band']=Tdown
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
        
def notifier(message,tries=0):
    telegram_api_url=f'https://api.telegram.org/bot{telegram_auth_token}/sendMessage?chat_id=@{telegram_group_id}&text={message}'
    #https://api.telegram.org/bot5515290544:AAG9T15VaY6BIxX2VYX8x2qr34aC-zVEYMo/sendMessage?chat_id=@notifier2_scanner_bot_link&text=hii
    tel_resp=requests.get(telegram_api_url)
    if tel_resp.status_code==200:
        pass
    else:
        while(tries < 25):
            print(f'Telegram notifier problem retrying {tries}')
            tries+=1
            time.sleep(0.5)
            notifier(message,tries)
            
        
def condition_usdt(timeframe,pivot_period,atr1,period,ma_condition,exchange,client,coin,sleep_time,in_trade_usdt,in_trade_busd,lock):
    notifier(f'Starting USDT function,SARAVANA BHAVA')
    while(True):
        try:
            risk=0.02
            bars = exchange.fetch_ohlcv(f'{coin}/USDT', timeframe=timeframe, limit=300)                        
            df = pd.DataFrame(bars[:-1], columns=['OpenTime', 'open', 'high', 'low', 'close', 'volume'])
            df['OpenTime'] = pd.to_datetime(df['OpenTime'], unit='ms')+ pd.DateOffset(hours=5, minutes=30)
            super_df=supertrend(coin,df, period, atr1,pivot_period)
            super_df[f'{ma_condition}_pos']=super_df[[ma_condition,'close']].apply(ema_pos,col_name=ma_condition,axis=1)
            ma_pos=super_df.iloc[-1][f'{ma_condition}_pos']
            if super_df.iloc[-1]['in_uptrend'] != super_df.iloc[-2]['in_uptrend']: 
                lock.acquire()
                
                try:
                    close_position(client,coin,'Sell') #close open position if any
                    in_trade_usdt.value=in_trade_usdt.value-1
                except Exception as err:
                    try:
                        close_position(client,coin,'Buy')
                        in_trade_usdt.value=in_trade_usdt.value-1
                    except Exception as e:
                        notifier(e)
                        
                    notifier(err)

                print(f'scanning USDT {super_df.iloc[-1][f"OpenTime"]} trade found, ma_pos :{super_df.iloc[-1][f"{ma_condition}_pos"]} and uptrend :{super_df.iloc[-1]["in_uptrend"]},bsud_poisiton :{in_trade_busd.value},usdt_position :{in_trade_usdt.value},sleeping for {sleep_time*60} seconds')
                acc_balance = round(float(client.futures_account()['availableBalance']),2)
                if in_trade_busd.value == 0:
                    stake=(acc_balance*0.68)
                else:
                    stake=acc_balance
                    
                

                
                signal = ['Buy' if super_df.iloc[-1]['in_uptrend'] == True else 'Sell'][0]
                entry=super_df.iloc[-1]['close']
                
                if signal == 'Buy':
                    sl=super_df.iloc[-1]['lower_band']
                    sl_perc=(entry-sl)/entry
                else:
                    sl=super_df.iloc[-1]['upper_band']
                    sl_perc=(sl-entry)/entry
                    
                print(f'initial stake:{stake}')
                stake=(stake*risk)/sl_perc
                quantity=round(stake/entry,3)

                
                print(f'risk adjusted stake:{stake},entry:{entry},sl_perc: {sl_perc}')
                notifier(f'risk adjusted stake:{stake},entry:{entry},sl_perc: {sl_perc}')
                
                rr=3
                notifier(f'Trend Changed {signal} and ma condition {ma_condition} is {ma_pos}')
                
                if signal == 'Buy' and ma_pos == 1:
                    #buy order
                    client.futures_create_order(symbol=f'{coin}USDT', side='BUY', type='MARKET', quantity=quantity,dualSidePosition=True,positionSide='LONG')
                    notifier(f'Bought @{entry}, Timeframe : {timeframe} , pivot_period: {pivot_period},atr:{atr1},period : {period},ma :{ma_condition}')
                    take_profit=entry+((entry-sl)*rr)
                    client.futures_create_order(
                            symbol=f'{coin}USDT',
                            price=round(take_profit,2),
                            side='SELL',
                            positionSide='LONG',
                            quantity=quantity,
                            timeInForce='GTC',
                            type='LIMIT',
                            # reduceOnly=True,
                            closePosition=False,
                            # stopPrice=round(take_profit,2),
                            workingType='MARK_PRICE',
                            priceProtect=True  
                            )
                    in_trade_usdt.value=1
                    
                if signal == 'Sell' and ma_pos == -1:
                        
                    #sell order
                    client.futures_create_order(symbol=f'{coin}USDT', side='SELL', type='MARKET', quantity=quantity,dualSidePosition=True,positionSide='SHORT')
                    notifier(f'Sold @{entry},Timeframe : {timeframe} , pivot_period: {pivot_period},atr:{atr1},period : {period},ma :{ma_condition}')
                    take_profit=entry-((sl-entry)*rr)
                    client.futures_create_order(
                                            symbol=f'{coin}USDT',
                                            price=round(take_profit,2),
                                            side='BUY',
                                            positionSide='SHORT',
                                            quantity=quantity,
                                            timeInForce='GTC',
                                            type='LIMIT',
                                            # reduceOnly=True,
                                            closePosition=False,
                                            # stopPrice=round(take_profit,2),
                                            workingType='MARK_PRICE',
                                            priceProtect=True  
                                            )
                    in_trade_usdt.value=1
                lock.release()
                time.sleep(sleep_time*60)
            else:
                print(f'Scanning USDT {super_df.iloc[-1][f"OpenTime"]} trade not found, ma_pos :{super_df.iloc[-1][f"{ma_condition}_pos"]} and uptrend :{super_df.iloc[-1]["in_uptrend"]}, bsud_poisiton :{in_trade_busd.value},usdt_position :{in_trade_usdt.value}')
                if in_trade_usdt.value==1:
                    open_orders=client.futures_get_open_orders(symbol=f'{coin}USDT')
                    if len(open_orders)==0:
                        lock.acquire()
                        in_trade_usdt.value=0
                        lock.release()
                time.sleep(2)
        except Exception as err:
            notifier(err)
            notifier(f'Restarting USDT function in 50 seconds')
            time.sleep(50)


            
            
def condition_busdt(timeframe,pivot_period,atr1,period,ma_condition,exchange,client,coin,sleep_time,in_trade_usdt,in_trade_busd,lock):
    notifier(f'Starting BUSD function,SARAVANA BHAVA')
    while(True):
        try:
            risk=0.02
            bars = exchange.fetch_ohlcv(f'{coin}/USDT', timeframe=timeframe, limit=300)
            df = pd.DataFrame(bars[:-1], columns=['OpenTime', 'open', 'high', 'low', 'close', 'volume'])
            df['OpenTime'] = pd.to_datetime(df['OpenTime'], unit='ms')+ pd.DateOffset(hours=5, minutes=30)
            super_df=supertrend(coin,df, period, atr1,pivot_period)
            super_df[f'{ma_condition}_pos']=super_df[[ma_condition,'close']].apply(ema_pos,col_name=ma_condition,axis=1)
            ma_pos=super_df.iloc[-1][f'{ma_condition}_pos']
            if super_df.iloc[-1]['in_uptrend'] != super_df.iloc[-2]['in_uptrend']:
                lock.acquire()
                
                try:
                    close_position_busd(client,coin,'Sell') #close open position if any
                    in_trade_busd.value=0
                except Exception as err:
                    try:
                        close_position_busd(client,coin,'Buy')
                        in_trade_busd.value=0
                    except Exception as e:
                        
                        notifier(e)
                        
                    notifier(err)
                
                
                
                
                
                print(f'scanning busd {super_df.iloc[-1][f"OpenTime"]} trade found, ma_pos :{super_df.iloc[-1][f"{ma_condition}_pos"]} and uptrend :{super_df.iloc[-1]["in_uptrend"]}, bsud_poisiton :{in_trade_busd.value},usdt_position :{in_trade_usdt.value} , sleeping for {sleep_time*60} seconds')
                acc_balance = round(float(client.futures_account()['availableBalance']),2)
                
                
                if in_trade_usdt.value==0:
                    stake=(acc_balance*0.68)
                else:
                    stake=acc_balance

                
                
                
                signal = ['Buy' if super_df.iloc[-1]['in_uptrend'] == True else 'Sell'][0]
                entry=super_df.iloc[-1]['close']
                
                if signal == 'Buy':
                    sl=super_df.iloc[-1]['lower_band']
                    sl_perc=(entry-sl)/entry
                else:
                    sl=super_df.iloc[-1]['upper_band']
                    sl_perc=(sl-entry)/entry
                    
                print(f'initial stake:{stake}')
                stake=(stake*risk)/sl_perc
                quantity=round(stake/entry,3)

                
                print(f'risk adjusted stake:{stake},entry:{entry},sl_perc: {sl_perc}')

                notifier(f'risk adjusted stake:{stake},entry:{entry},sl_perc: {sl_perc}')
                                
                
                notifier(f'Trend Changed {signal} and ma condition {ma_condition} is {ma_pos}')
                
                
                if signal == 'Buy' and ma_pos == 1:
                    #buy order
                    client.futures_create_order(symbol=f'{coin}BUSD', side='BUY', type='MARKET', quantity=quantity,dualSidePosition=True,positionSide='LONG')
                    notifier(f'Bought BUSD @{entry} , Timeframe : {timeframe} , pivot_period: {pivot_period},atr:{atr1},period : {period},ma :{ma_condition}')
                    in_trade_busd.value=1
                    
                if signal == 'Sell' and ma_pos == -1:
                        
                    #sell order
                    client.futures_create_order(symbol=f'{coin}BUSD', side='SELL', type='MARKET', quantity=quantity,dualSidePosition=True,positionSide='SHORT')
                    notifier(f'Sold BUSD @{entry},Timeframe : {timeframe} , pivot_period: {pivot_period},atr:{atr1},period : {period},ma :{ma_condition}')
                    in_trade_busd.value=1
                lock.release()
                time.sleep(sleep_time*60)
            else:       
                print(f'Scanning BUSD {super_df.iloc[-1][f"OpenTime"]} trade not found, ma_pos :{super_df.iloc[-1][f"{ma_condition}_pos"]} and uptrend :{super_df.iloc[-1]["in_uptrend"]}, bsud_poisiton :{in_trade_busd.value},usdt_position :{in_trade_usdt.value}')
                
                time.sleep(2)
        except Exception as e:
            notifier(e)
            notifier(f'Restarting BUSD function in 50 seconds')
            time.sleep(50)