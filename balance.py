from binance.client import Client
import config


client=Client(config.api_key,config.secret_key)

account_info = client.futures_account_info()

for balance in account_info['balances']:
    if balance['asset'] == 'USDT':
        usdt_free=balance['free']
        usdt_locked=balance['locked']
    if balance['asset'] == 'BUSD':
        busd_free=balance['free']
        busd_locked=balance['locked']


free=usdt_free+busd_free
locked=usdt_locked+busd_locked
total=free+locked

print(f'Total Balance : {total}')
print(f'Locked : {locked}')


