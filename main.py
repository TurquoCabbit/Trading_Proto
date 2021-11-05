import decimal
from hmac import digest_size
from tkinter.constants import E
from pybit import HTTP
from time import sleep
import os
import random
random.seed()
import math

import key

Token_List = ['BTCUSDT', 'ETHUSDT', 'DOTUSDT', 'SOLUSDT', 'BITUSDT', 'AVAXUSDT', 'FTTUSDT']  #from loaded cfg
operate_USDT = 1000
Leverage = 20
TP_percentage = 100
SL_percentage = 10
Max_operate_position = 5

class Symbol:
    def __init__(self, Symbol, tick_size, qty_step) -> None:
        self.Symbol = Symbol
        self.tick_size = (float)(tick_size)
        self.qty_step = (float)(qty_step)
        self.opened = False
        self.isolate = False
        self.leverage = Leverage
        self.tpsl_mode = 'Full'

Symbol_List = []

qty_step_list = []



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
    os.system('echo [0m')
    # os.system('echo [0m{}'.format('--------------------------------------------------------------------'))

def Print_and_pause(str):
    print(str)
    os.system('pause')

def rand_symbol():
    rand = random.randint(0, len(Symbol_List) - 1)
    if Symbol_List[rand].opened:
        return rand_symbol()
    else:
        return rand

def qty_trim(qty, step):
    digi = abs((int)(format(step, '1E').split('E')[1]))
    qty = (int)(qty * pow(10, digi))
    step = (int)(step * pow(10, digi))
    qty -= qty % step
    
    return qty / pow(10, digi)


def price_trim(price, tick, up = 0):
    digi = abs((int)(format(tick, '1E').split('E')[1]))
    price = (int)(price * pow(10, digi))
    tick = (int)(tick * pow(10, digi))
    
    if up:
        price -= price % tick - tick
    else:
        price -= price % tick
    
    return price / pow(10, digi)



### Connect client
try:
    client = HTTP(key.host, api_key=key.api, api_secret=key.api_secret)
except :
    Error_Msg('Connect Error')
    os.system('pause')
    os._exit(0)

### Check Sym list
try:
    Symbol_querry = client.query_symbol()
    if not Symbol_querry['ret_code']:
        for i in Token_List:
            exist = 0
            for j in Symbol_querry['result']:
                if i == j['name']:
                    exist = 1
                    Symbol_List.append(Symbol(i, j['price_filter']['tick_size'],\
                                                 j['lot_size_filter']['qty_step']))
                    break
            if not exist:
                raise Exception('\"{}\" not exist in Symbol list'.format(i))
            else:
                exist = 0
    else:
        raise Exception('Return code :{}'.format(Symbol_querry['ret_code']))

except Exception as Err:
    Error_Msg(Err)
    os.system('pause')
    os._exit(0)


while True:
    try:
        ### Querry current wallet balance
        wallet = client.get_wallet_balance(coin="USDT")
        if not wallet['ret_code']:
            wallet_available = wallet['result']['USDT']['available_balance']
            wallet_equity = wallet['result']['USDT']['equity']
            # print('wallet_available : {}'.format(wallet_available))
            # print('wallet_equity : {}'.format(wallet_equity))
        else:
            raise Exception('Querry Wallet Fail !!\tReturn code: {}\tReturn msg: {}'.format(wallet['ret_code'], wallet['ret_msg']))


        ### Querry current position
        current_position_qty = 0
        for i in Symbol_List:
            position = client.my_position(symbol = i.Symbol)
            if not position['ret_code']:
                i.isolate = position['result'][0]['is_isolated']
                i.leverge = (int)(position['result'][0]['leverage'])
                i.tpsl_mode = position['result'][0]['tp_sl_mode']
                if position['result'][0]['size'] > 0:
                    current_position_qty += 1
                    i.opened = True
            else:
                raise Exception('Querry Position Fail !!\tReturn code: {}\tReturn msg: {}'.format(position['ret_code'], position['ret_msg']))

        print('Opened order : {}'.format(current_position_qty))


        ### Randonly open position
        if current_position_qty < Max_operate_position:
            # Random pick
            open_ID = rand_symbol()
            open_sym = Symbol_List[open_ID].Symbol

            # Set Full Position TP/SL
            if Symbol_List[open_ID].tpsl_mode != 'Full':
                temp = client.full_partial_position_tp_sl_switch(symbol = open_sym, tp_sl_mode = 'Full')
                # print(temp)
                if temp['ret_code'] == 0:
                    raise Exception('Set Full Position TP/SL Error\tReturn code: {}\tReturn msg: {}'.format(temp['ret_code'], temp['ret_msg']))

            # Switch to isolated margin mode and set leverage
            if Symbol_List[open_ID].isolate != True:
                temp = client.cross_isolated_margin_switch(symbol = open_sym, is_isolated = True, buy_leverage = Leverage, sell_leverage = Leverage)
                # print(temp)
                if temp['ret_code']:
                    raise Exception('Set Margin mode Error\tReturn code: {}\tReturn msg: {}'.format(temp['ret_code'], temp['ret_msg']))

            #Modify leverage
            if Symbol_List[open_ID].leverge != Leverage:
                temp = client.set_leverage(symbol = open_sym, buy_leverage = Leverage, sell_leverage = Leverage)
                if temp['ret_code']:
                    raise Exception('Set Leverage Error\tReturn code: {}\tReturn msg: {}'.format(temp['ret_code'], temp['ret_msg']))

            # Querry price
            temp = client.latest_information_for_symbol(symbol = open_sym)
            if temp['ret_code']:
                raise Exception('Querry current price Error\tReturn code: {}\tReturn msg: {}'.format(temp['ret_code'], temp['ret_msg']))
            else:
                open_price = (float)(temp['result'][0]['last_price'])
                

            # Calculate TP/SL
            open_qty = qty_trim((operate_USDT * Leverage / open_price), Symbol_List[open_ID].qty_step)
            open_TP = price_trim((1 + (TP_percentage / Leverage / 100)) * open_price, Symbol_List[open_ID].tick_size)
            open_SL = price_trim((1 - (SL_percentage / Leverage / 100)) * open_price, Symbol_List[open_ID].tick_size, True)

            print('Open {} {} Order at {} with TP : {}, SL : {}'.format(open_qty, open_sym, open_price, open_TP, open_SL))
            

            # Open position
            open_posi = client.place_active_order(symbol = open_sym,\
                                                side = "Buy",\
                                                order_type = "Market",\
                                                qty = open_qty,\
                                                time_in_force = "GoodTillCancel",\
                                                reduce_only = False,\
                                                close_on_trigger = False,\
                                                take_profit = open_TP,\
                                                stop_loss = open_SL)

            if open_posi['ret_code'] != 0:
                raise Exception('{} Order Create Fail !!\tReturn code: {}\tReturn msg: {}'.format(open_sym, open_posi['ret_code'], open_posi['ret_msg']))
            elif open_posi['ret_msg'] != 'OK':
                print('{} Order Create Successfully !!\tReturn msg: {}'.format(open_sym,open_posi['ret_msg']))
            else:
                print('{} Order Create Successfully !!'.format(open_sym))
            
            sleep(10)
        else:
            sleep(1)


    except Exception as Err:
        Error_Msg(Err)
        os.system('pause')
        os._exit(0)