import pandas as pd
import talib
from datetime import datetime,timedelta
from numba import njit
import numpy as np

def supertrend(df, period, atr_multiplier):
    hl2 = (df['high'] + df['low']) / 2
    df['atr'] = atr(df, period)
    df['upperband'] = hl2 + (atr_multiplier * df['atr'])
    df['lowerband'] = hl2 - (atr_multiplier * df['atr'])
    df['in_uptrend'] = True
    
    df['OpenTime']=pd.to_datetime(df['OpenTime'])
    
    df['size']=df.apply(candle_size,axis=1)


    

    df['ema_55']=talib.EMA(df['close'],55)
    df['ema_20']=talib.EMA(df['close'],20)
    df['ema_33']=talib.EMA(df['close'],33)
    df['rsi'] = talib.RSI(df['close'], timeperiod=14)

    for current in range(1, len(df.index)):
        previous = current - 1

        if df['close'][current] > df['upperband'][previous]:
            df['in_uptrend'][current] = True
        elif df['close'][current] < df['lowerband'][previous]:
            df['in_uptrend'][current] = False
        else:
            df['in_uptrend'][current] = df['in_uptrend'][previous]

            if df['in_uptrend'][current] and df['lowerband'][current] < df['lowerband'][previous]:
                df['lowerband'][current] = df['lowerband'][previous]

            if not df['in_uptrend'][current] and df['upperband'][current] > df['upperband'][previous]:
                df['upperband'][current] = df['upperband'][previous]
        
    return df


def tr(data):
    data['previous_close'] = data['close'].shift(1)
    data['high-low'] = abs(data['high'] - data['low'])
    data['high-pc'] = abs(data['high']- data['previous_close'])
    data['low-pc'] = abs(data['low'] - data['previous_close'])

    tr = data[['high-low', 'high-pc', 'low-pc']].max(axis=1)

    return tr

def candle_size(x,coin):
    return abs(((x['close']-x['open'])/x['open'])*100)


def atr(data, period):
    data['tr'] = tr(data)
    atr = data['tr'].rolling(period).mean()

    return atr


@njit
def cal_numba(opens,highs,lows,closes,in_uptrends,profit_perc,sl_perc,upper_bands,lower_bands):
    entries=np.zeros(len(opens))
    signals=np.zeros(len(opens))  #characters  1--> buy  2--->sell
    tps=np.zeros(len(opens))
    trades=np.zeros(len(opens))  #characters   1--->w  0---->L
    close_prices=np.zeros(len(opens))
    time_index=np.zeros(len(opens))
    candle_count=np.zeros(len(opens))
    local_max=np.zeros(len(opens))
    local_min=np.zeros(len(opens))
    upper=np.zeros(len(opens))
    lower=np.zeros(len(opens))
    
    local_max_bar=np.zeros(len(opens))
    local_min_bar=np.zeros(len(opens))
    
    indication = 0
    buy_search=0
    sell_search=1
    change_index=0
    i=-1
    while(i<len(opens)):
        i=i+1
        
        if (indication == 0) & (sell_search == 1) & (buy_search == 0) & (change_index == i):
            
            sell_search=0
            flag=0
            trade= 5
            while (indication == 0):
                
                entry = closes[i]
                tp = entry - (entry * profit_perc)
                sl = entry + (entry * sl_perc)
                
                upper[i]=upper_bands[i]
                lower[i]=lower_bands[i]
                
                
                entries[i]=entry
                tps[i]=tp
                signals[i]=2
                local_max[i]=highs[i+1]
                local_min[i]=lows[i+1]
                for j in range(i+1,len(opens)):
                    candle_count[i]=candle_count[i]+1
                    if lows[j] < local_min[i]:
                        local_min[i]=lows[j]
                        local_min_bar[i]=candle_count[i]
                    if highs[j]>local_max[i]:
                        local_max[i]=highs[j]
                        local_max_bar[i]=candle_count[i]

                    if lows[j] < tp and flag==0:

                        trades[i] = 1
                        close_prices[i]=tp
                        time_index[i]=i
                        
                        indication=1
                        buy_search=1
                        flag=1
                        
                        
                    elif (highs[j] > sl and flag==0) or (in_uptrends[j] == 'True'):
                        if highs[j] > sl and flag==0:
                            trades[i] = 0
                            close_prices[i]=sl
                            time_index[i]=i

                            indication=1
                            buy_search=1
                            flag=1
                            
                        if in_uptrends[j] == 'True':
                            

                            if trades[i] ==1:
                                change_index=j
                            elif trades[i] == 0 and flag ==1:
                                change_index=j
                            else:
                                trades[i] = 0
                                close_prices[i]=closes[j]
                                time_index[i]=i
                                change_index=j
                            
                            indication=1
                            buy_search=1
                            break
                    else:
                        pass
                break
        elif (indication == 1 ) & (sell_search == 0) & (buy_search == 1) & (change_index==i):
            
            buy_search= 0
            flag=0

            while (indication == 1):


                entry = closes[i]
                tp = entry + (entry * profit_perc)
                sl = entry - (entry * sl_perc)
                
                upper[i]=upper_bands[i]
                lower[i]=lower_bands[i]
                
                entries[i]=entry
                tps[i]=tp
                signals[i]=1
                local_max[i]=highs[i+1]  
                local_min[i]=lows[i+1]
                for j in range(i+1,len(opens)):
                    if lows[j] < local_min[i]:
                        local_min[i]=lows[j]
                        local_min_bar[i]=candle_count[i]
                    if highs[j]>local_max[i]:
                        local_max[i]=highs[j]
                        local_max_bar[i]=candle_count[i]
                        
                    candle_count[i]=candle_count[i]+1
                    if highs[j] > tp and flag==0 :
                        trades[i]  = 1
                        sell_search=1
                        close_prices[i]=tp
                        time_index[i]=i
                        

                        flag=1
                        indication=0
                    elif (lows[j] < sl and flag==0) or (in_uptrends[j] == 'False'):
                        if lows[j] < sl and flag==0:

                            trades[i]= 0
                            close_prices[i]=sl
                            time_index[i]=i
                            indication=0
                            sell_search=1
                            flag=1
                            
                        if in_uptrends[j] == 'False':
                            
                            if trades[i] ==1:
                                change_index=j
                            elif trades[i] == 0 and flag ==1:
                                change_index=j
                            else:
                                trades[i] = 0
                                close_prices[i]=closes[j]
                                time_index[i]=i
                                change_index=j
                            
                            indication=0
                            sell_search=1
                            break

                    
                        
                    else:
                        pass
                break
        else:
            continue
        
    return entries,signals,tps,trades,close_prices,time_index,candle_count,local_max,local_min,local_max_bar,local_min_bar,upper,lower


def create_signal_df(super_df,df,coin,timeframe,atr1,period,profit,sl):
    opens=super_df['open'].to_numpy(dtype='float64')
    highs=super_df['high'].to_numpy(dtype='float64')
    lows=super_df['low'].to_numpy(dtype='float64')
    closes=super_df['close'].to_numpy(dtype='float64')
    in_uptrends=super_df['in_uptrend'].to_numpy(dtype='U5')
    upper_bands=super_df['upperband'].to_numpy(dtype='float64')
    lower_bands=super_df['lowerband'].to_numpy(dtype='float64')
    entries,signals,tps,trades,close_prices,time_index,candle_count,local_max,local_min,local_max_bar,local_min_bar,upper,lower=cal_numba(opens,highs,lows,closes,in_uptrends,profit,sl,upper_bands,lower_bands)
    trade_df=pd.DataFrame({'signal':signals,'entry':entries,'tp':tps,'trade':trades,'close_price':close_prices,'candle_count':candle_count,
                           'local_max':local_max,'local_min':local_min,'local_max_bar':local_max_bar,'local_min_bar':local_min_bar,'upper_band':upper,'lower_band':lower})
    # before_drop=trade_df.shape[0]
    # print(f'Number of columns before drop : {before_drop}')
    
    
    trade_df_index=trade_df[trade_df['entry']!=0]
    
    indexes=trade_df_index.index.to_list()
    
    for i in indexes:
        try:
            trade_df.at[i,'TradeOpenTime']=df[df.index==i+1]['OpenTime'][(i+1)]
        except KeyError:
            trade_df.at[i,'TradeOpenTime']=(df[df.index==i]['OpenTime'][(i)]) 
    for i in indexes:
        try:
            trade_df.at[i,'signalTime']=df[df.index==i]['OpenTime'][(i)]
        except KeyError:
            trade_df.at[i,'signalTime']=(df[df.index==i]['OpenTime'][(i)])
            
    trade_df['signal']=trade_df['signal'].apply(signal_decoding)
    
    trade_df.dropna(inplace=True)
                        
    entries=trade_df['entry'].to_numpy(dtype='float64')
    closes=trade_df['close_price'].to_numpy(dtype='float64')
    # trades=trade_df['trade'].to_numpy(dtype='U1')
    signals=trade_df['signal'].to_numpy(dtype='U5')
    outputs=np.zeros(len(entries))
    percentages=df_perc_cal(entries,closes,signals,outputs)
    trade_df['percentage'] = percentages.tolist()
    trade_df['trade']=trade_df['percentage'].apply(trade_decoding)
    # after_drop=trade_df.shape[0]
    # print(f'Number of columns after drop : {after_drop}')
    trade_df=trade_df.reset_index(drop=True)
    if (trade_df['percentage'][trade_df.shape[0]-1]==-1) | (trade_df['percentage'][trade_df.shape[0]-1]==1):
        trade_df=trade_df[:-1]
    else:
        pass
    trade_df['signalTime']=pd.to_datetime(trade_df['signalTime'])
    super_df['OpenTime']=pd.to_datetime(super_df['OpenTime'])
    
    trade_df=pd.merge(trade_df, super_df, how='left', left_on=['signalTime'], right_on = ['OpenTime'])
    
    trade_df=trade_df[['signal',
    'entry',
    'tp',
    'trade',
    'close_price',
    'TradeOpenTime',
    'percentage',
    'OpenTime',
    'size',
    'ema_55',
    'ema_20',
    'ema_33',
    'rsi',
    'candle_count',
    'local_max','local_min',
    'local_max_bar','local_min_bar',
    'upper_band','lower_band']]
    trade_df=trade_df.dropna()
    trade_df=trade_df[2:]
    
    return trade_df


def signal_decoding(x):
    if x == 1:
        return 'Buy'
    else:
        return 'Sell'
    
def trade_decoding(x):
    if x > 0:
        return 'W'
    else:
        return 'L'
    
@njit
def df_perc_cal(entries,closes,signals,percentages):
    for i in range(0,len(entries)):
        if signals[i]=='Buy':
            percentages[i]=(closes[i]-entries[i])/entries[i]
        else:
            percentages[i]=-(closes[i]-entries[i])/entries[i]
    return percentages

def ema_pos(x,col_name):
    if x['close'] > x[col_name]:
        return 'above'
    else:
        return 'below'
    
def atr_perc(x):
    return (x['upperband']-x['close'])/x['close']*100,(x['lowerband']-x['close'])/x['close']*100


def close_position(client,coin,signal):
    if signal == 'BUY':
        client.futures_create_order(symbol=f'{coin}USDT', side='SELL', type='MARKET', quantity=1000,dualSidePosition=True,positionSide='LONG')
    else:
        client.futures_create_order(symbol=f'{coin}USDT', side='BUY', type='MARKET', quantity=1000,dualSidePosition=True,positionSide='SHORT')
        
def create_limit_order(client,coin,signal,entry,quantity):
    if signal == 'BUY':
        #2nd barrier
        barrier_order=client.futures_create_order(
        symbol=f'{coin}USDT',
        price=entry,
        side='BUY',
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
    else:
        #2nd barrier
        barrier_order=client.futures_create_order(
        symbol=f'{coin}USDT',
        price=entry,
        side='SELL',
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
        
        
        
def change_tp(client,coin,signal,quantity,take_profit):
    if signal == 'SELL':
        #when 2nd_barrier gets hit change in tp
        order=client.futures_create_order(
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
        return order['orderId']
        
    else:
        #tp
        order=client.futures_create_order(
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
        return order['orderId']

def create_limit_tpsl(client,coin,signal,quantity,stop_price,take_profit):
    if signal=='BUY':
        
        #SL
        client.futures_create_order(
        symbol=f'{coin}USDT',
        side='SELL',
        positionSide='LONG',
        type='STOP_MARKET',
        stopPrice=round(stop_price,2),
        closePosition=True,
        timeInForce='GTE_GTC',
        workingType='MARK_PRICE',
        priceProtect=True
        
        )
        
        #tp
        tp_order=client.futures_create_order(
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
        
        return tp_order['orderId']
    
    
            
    elif signal=='SELL':
  
        #Sl
        client.futures_create_order(
            symbol=f'{coin}USDT',
            side='BUY',
            positionSide='SHORT',
            type='STOP_MARKET',
            stopPrice=round(stop_price,2),
            closePosition=True,
            workingType='MARK_PRICE',
            timeInForce='GTE_GTC',
            priceProtect=True     
        )
        
        #tp
        tp_order=client.futures_create_order(
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
        
      
        
        
        return tp_order['orderId']



def create_order(client,coin,signal,quantity,entry_2,stop_price,take_profit):
    if signal=='BUY':
        #buy
        client.futures_create_order(symbol=f'{coin}USDT', side='BUY', type='MARKET', quantity=quantity,dualSidePosition=True,positionSide='LONG')
        
        
        #SL
        client.futures_create_order(
        symbol=f'{coin}USDT',
        side='SELL',
        positionSide='LONG',
        type='STOP_MARKET',
        stopPrice=round(stop_price,2),
        closePosition=True,
        timeInForce='GTE_GTC',
        workingType='MARK_PRICE',
        priceProtect=True
        
        )
        
        #2nd barrier
        barrier_order=client.futures_create_order(
        symbol=f'{coin}USDT',
        price=entry_2,
        side='BUY',
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

        #tp
        tp_order=client.futures_create_order(
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
        
        return tp_order['orderId'],barrier_order['orderId']
    
    
            
    elif signal=='SELL':
        #sell
        order=client.futures_create_order(symbol=f'{coin}USDT', side='SELL', type='MARKET', quantity=quantity,dualSidePosition=True,positionSide='SHORT')
        
        #Sl
        client.futures_create_order(
            symbol=f'{coin}USDT',
            side='BUY',
            positionSide='SHORT',
            type='STOP_MARKET',
            stopPrice=round(stop_price,2),
            closePosition=True,
            workingType='MARK_PRICE',
            timeInForce='GTE_GTC',
            priceProtect=True     
        )
        
        
        #2nd barrier
        barrier_order=client.futures_create_order(
        symbol=f'{coin}USDT',
        price=entry_2,
        side='SELL',
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
    
        #tp
        tp_order=client.futures_create_order(
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
        
      
        
        
        return tp_order['orderId'],barrier_order['orderId']
    
    
def candle_size(x):
    return abs(((x['close']-x['open'])/x['open'])*100)

def fetch_data(exchange,coin,timeframe,period,atr_trend):
        bars = exchange.fetch_ohlcv(f'{coin}/USDT', timeframe=timeframe, limit=350)
        df = pd.DataFrame(bars[:-1], columns=['OpenTime', 'open', 'high', 'low', 'close', 'volume']) #-1 as bars contain unclosed cnadle in its final row
        df['OpenTime'] = pd.to_datetime(df['OpenTime'], unit='ms')+ pd.DateOffset(hours=5, minutes=30)

        bars = exchange.fetch_ohlcv(f'{coin}/USDT', timeframe='1m', limit=2)
        df_1m = pd.DataFrame(bars[:-1], columns=['OpenTime', 'open', 'high', 'low', 'close', 'volume'])
        df_1m['OpenTime'] = pd.to_datetime(df_1m['OpenTime'], unit='ms')+ pd.DateOffset(hours=5, minutes=30)

        super_df=supertrend(df,period,atr_trend)
        
        trade_df=create_signal_df(super_df,df,coin,timeframe,atr_trend,period,100,100)
        trade_df['max']=((trade_df['local_max']-trade_df['entry'])/trade_df['entry'])*100
        trade_df['min']=((trade_df['local_min']-trade_df['entry'])/trade_df['entry'])*100

        super_df['ema_20_pos']=super_df[['ema_20','close']].apply(ema_pos,col_name='ema_20',axis=1)
        super_df['ema_33_pos']=super_df[['ema_33','close']].apply(ema_pos,col_name='ema_33',axis=1)
        super_df['ema_55_pos']=super_df[['ema_55','close']].apply(ema_pos,col_name='ema_55',axis=1)
        
        super_df['upper_perc'],super_df['lower_perc']=zip(*super_df[['upperband','lowerband','close']].apply(atr_perc,axis=1))

        return super_df,trade_df,df_1m


def handle_barrier(coin,exchange,client,df_1m,trade,entry_2,openorders,change_in_tp,quantity,tp_order_id,notifier):
    if trade =='SELL':
        if (df_1m.iloc[-1]['high'] >= entry_2) & (len(openorders) > 0) & (change_in_tp==0):
            quantity=quantity*2
            take_profit=entry_2-(entry_2*0.011) 
            exchange.cancel_order(tp_order_id, f'{coin}USDT')
            notifier(f'OLD TP order canceled : {tp_order_id}')
            msg=f'''singal :{trade},quantity : {quantity},takeprofit :{take_profit},entry_2:{entry_2}
        change_in_tp: {change_in_tp}, tp_order_id: {tp_order_id}
        '''
            print(msg)
            tp_order_id=change_tp(client,coin,trade,quantity,take_profit) 
            notifier(f'New TP placed with order id: {tp_order_id}')
            change_in_tp=1
        else:
            pass
    elif trade == 'BUY':
        if (df_1m.iloc[-1]['low'] <= entry_2) & (len(openorders) > 0) & (change_in_tp==0):
            quantity=quantity*2
            take_profit=entry_2+(entry_2*0.011)
            exchange.cancel_order(tp_order_id, f'{coin}USDT')
            notifier(f'OLD TP order canceled : {tp_order_id}')
            msg=f'''singal :{trade},quantity : {quantity},takeprofit :{take_profit},entry_2:{entry_2}
        change_in_tp: {change_in_tp}, tp_order_id: {tp_order_id}
        '''
            print(msg)
            tp_order_id=change_tp(client,coin,trade,quantity,take_profit) 
            notifier(f'New TP placed with order id: {tp_order_id}')
           
            change_in_tp=1
        else:
            pass
    else:
        pass

    
    return tp_order_id,change_in_tp


def features(super_df,trade_df):
            
            trade_df['max_bin']=[1 if x > 1.8 else 0 for x in trade_df['max']]
            trade_df['min_bin']=[1 if x < -1.5 else 0 for x in trade_df['min']]
            
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
            
            for i in range(1,5):
                trade_df[f'prev_max_{i}']=trade_df['max_bin'].shift(i)
            
            prev_max_1=trade_df['max_bin'].iloc[-1]
            prev_max_two=trade_df['max_bin'].iloc[-1]+trade_df['prev_max_1'].iloc[-1]
            prev_max_three=trade_df['max_bin'].iloc[-1]+trade_df['prev_max_1'].iloc[-1]+trade_df['prev_max_2'].iloc[-1]
            prev_max_four=trade_df['max_bin'].iloc[-1]+trade_df['prev_max_1'].iloc[-1]+trade_df['prev_max_2'].iloc[-1]+trade_df['prev_max_3'].iloc[-1]
            
            for i in range(1,5):
                trade_df[f'prev_min_{i}']=trade_df['min_bin'].shift(i)
                
            prev_min_1 =trade_df['min_bin'].iloc[-1]
            prev_min_two=trade_df['min_bin'].iloc[-1]+trade_df['prev_min_1'].iloc[-1]
            prev_min_three=trade_df['min_bin'].iloc[-1]+trade_df['prev_min_1'].iloc[-1]+trade_df['prev_min_2'].iloc[-1]
            prev_min_four=trade_df['min_bin'].iloc[-1]+trade_df['prev_min_1'].iloc[-1]+trade_df['prev_min_2'].iloc[-1]+trade_df['prev_min_3'].iloc[-1]
            
            
            return ([signal,ema_55_pos,ema_20_pos,ema_33_pos,size,upper_perc,lower_perc,rsi,prev_trend_1,prev_trend_2,
                    prev_local_max_bar,prev_local_min_bar,prev_max_per,prev_min_per,prev_max_1,prev_max_two,prev_max_three,prev_max_four,
                    prev_min_1,prev_min_two,prev_min_three,prev_min_four]),signal