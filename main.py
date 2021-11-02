from tkinter.constants import E
import bybit
from time import sleep
import os
import random

import key

Sym_list = ['BTCUSDT', 'ETHUSDT', 'DOTUSDT', 'SOLUSDT', 'BITUSDT']
Posi_list = []
wallet_available = 0
wallet_equity = 0

Max_operate_size = 1000     #USDT
Max_operate_position = 4

current_position_qty = 0

def Error_Msg(str, extreme = 0):
    if extreme:
        os.system('echo [41m{}'.format(str))
        os.system('echo [0m{}'.format('--------------------------------------------------------------------'))
    else:
        os.system('echo [31m{}'.format(str))
        os.system('echo [0m{}'.format('--------------------------------------------------------------------'))

def System_Msg(str):
    os.system('echo [33m{}'.format(str))
    os.system('echo [0m{}'.format('--------------------------------------------------------------------'))

def Print_and_pause(str):
    print(str)
    os.system('pause')

def rand_symbol():
    rand = random.random(0,len(Sym_list) - 1)
    if Posi_list[rand]['size'] > 0:
        return rand_symbol()
    else:
        return Sym_list[rand]

### Connect client
try:
    client = bybit.bybit(test=True, api_key=key.api, api_secret=key.api_secret)
except :
    Error_Msg('Connect Error')


### Check Sym list
try:
    Symbol = client.Symbol.Symbol_get().result()[0]
    if not Symbol['ret_code']:
        for i in Sym_list:
            exist = 0
            for j in Symbol['result']:
                if i == j['name']:
                    exist = 1
                    break
            if not exist:
                raise Exception('\"{}\" not exist in Symbol list'.format(i))
            else:
                exist = 0
    else:
        raise Exception('Return code :{}'.format(Symbol['ret_code']))

except Exception as Err:
    Error_Msg(Err)

# while True:
### Check Wallet status
wallet_available = client.Wallet.Wallet_getBalance(coin="USDT").result()[0]['result']['USDT']['available_balance']
wallet_equity = client.Wallet.Wallet_getBalance(coin="USDT").result()[0]['result']['USDT']['equity']

print('wallet_available : {}'.format(wallet_available))
print('wallet_equity : {}'.format(wallet_equity))

### Check account status
for i in Sym_list:
    current_position_qty = 0
    Posi_list.append(client.LinearPositions.LinearPositions_myPosition(symbol = i).result()[0]['result'][0])
    if Posi_list[-1]['size'] > 0:
        current_position_qty += 1

print(current_position_qty)

### Randonly open position
if current_position_qty < Max_operate_position:
    




os.system('pause')

