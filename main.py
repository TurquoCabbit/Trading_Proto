from logging import log
from pybit import HTTP
from time import sleep
from datetime import datetime
import os
import json
import gc
import random
random.seed()

import Make_log
import key
import Update_Symbol_List

class Symbol:
    def __init__(self, Symbol, tick_size, qty_step) -> None:
        self.symbol = Symbol
        self.tick_size = (float)(tick_size)
        self.qty_step = (float)(qty_step)
        self.opened = False
        self.isolate = False
        self.leverage = 0
        self.tpsl_mode = 'Partial'

class Open:
    def __init__(self) -> None:
        self.ID = 0
        self.sym = ''
        self.price = 0
        self.side = ''
        self.qty = 0
        self.TP = 0
        self.SL = 0

Symbol_List = []

Token_List = []

Position_List = {'symbol' : [], 'Buy' : [], 'Sell' : []}

current_position_qty = 0

def Error_Msg(str, extreme = 0):
    log.log(str)
    if extreme:
        os.system('echo [41m{}'.format(str))
        os.system('echo [0m{}'.format('--------------------------------------------------------------------'))
    else:
        os.system('echo [31m{}'.format(str))
        os.system('echo [0m{}'.format('--------------------------------------------------------------------'))

def System_Msg(str):
    log.log(str)
    os.system('echo [33m{}'.format(str))
    os.system('echo [0m')
    # os.system('echo [0m{}'.format('--------------------------------------------------------------------'))

def Print_and_pause(str = ''):
    log.show(str)
    os.system('pause')

def rand_symbol():
    rand = random.randint(0, len(Symbol_List) - 1)
    if Symbol_List[rand].opened:
        return rand_symbol()
    else:
        return rand

        
def rand_side():
    if random.randint(0, 1):
        return "Buy"
    else:
        return "Sell"
        

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



##############################################################################################################################
### init log
log = Make_log.Log('log')
log.log_and_show('========================START=========================')

##############################################################################################################################
### Load Cfg File
if not os.path.isfile('cfg.json'):
    System_Msg('Cfg.json file missing')
    log.show('cfg.json example : ')
    log.show('{')
    log.show('\t\"Test_net\" : ,')
    log.show('\t\"Max_operate_position\" : ,')
    log.show('\t\"operate_USDT\" : ,')
    log.show('\t\"Leverage\" : ,')
    log.show('\t"TP_percentage\" : ,')
    log.show('\t\"SL_percentage\" : ,')
    log.show('\tTrade_all\" : ,')
    log.show('\t\"Token\" : [')
    log.show('\t\t\"BTC\",')
    log.show('\t\t\"ETH\",')
    log.show('\t\t.. ,')
    log.show('\t\t.. ,')
    log.show('\t]')
    log.show('}')
    
    os.system('pause')
    os._exit(0)

else:
    with open('cfg.json') as file:
        Cfg_data = json.load(file)

    Test = Cfg_data['Test_net']
    Max_operate_position = Cfg_data['Max_operate_position']
    operate_USDT = Cfg_data['operate_USDT']
    Leverage = Cfg_data['Leverage']
    TP_percentage = Cfg_data['TP_percentage']
    SL_percentage = Cfg_data['SL_percentage']
    Trade_all = Cfg_data['Trade_all']
    

    if not Trade_all:
        for i in Cfg_data['Token']:
            Token_List.append('{}USDT'.format(i))

##############################################################################################################################
### Load Symbol List
if not os.path.isfile('Symbol_list.json'):
    if Update_Symbol_List.Querry_USDT_Perpetual_Symbol():
        with open('Symbol_list.json', 'r') as file:
            Symbol_querry = json.load(file)
else:    
    with open('Symbol_list.json', 'r') as file:
        Symbol_querry = json.load(file)

    if Symbol_querry['version'] != Update_Symbol_List.Symbol_list_ver:
        if Update_Symbol_List.Querry_USDT_Perpetual_Symbol():
            with open('Symbol_list.json', 'r') as file:
                Symbol_querry = json.load(file)

##############################################################################################################################
### Connect client
try:
    if Test:
        log.log_and_show('Operate on Test Net !!!')
        client = HTTP(key.test_host, api_key=key.test_api, api_secret=key.test_secret)
    else:
        client = HTTP(key.host, api_key=key.api, api_secret=key.secret)
except :
    Error_Msg('Connect Error')
    os.system('pause')
    os._exit(0)

### Check Sym list
if Trade_all:
    for i in Symbol_querry['data']:
        Symbol_List.append(Symbol(i['name'], i['price_filter']['tick_size'], i['lot_size_filter']['qty_step']))
else:
    for i in Token_List:
        if i in Symbol_querry['name']:
            sym = Symbol_querry['data'][Symbol_querry['name'].index(i)]
            Symbol_List.append(Symbol(sym['name'], sym['price_filter']['tick_size'], sym['lot_size_filter']['qty_step']))
sleep(1)
while True:
    try:
        ### Querry current wallet balance
        if False:
            wallet = client.get_wallet_balance(coin="USDT")
            if not wallet['ret_code']:
                wallet_available = wallet['result']['USDT']['available_balance']
                wallet_equity = wallet['result']['USDT']['equity']
                log.log_and_show('wallet_available : {}'.format(wallet_available))
                log.log_and_show('wallet_equity : {}'.format(wallet_equity))
            else:
                raise Exception('Querry Wallet Fail !!\tReturn code: {}\tReturn msg: {}'.format(wallet['ret_code'], wallet['ret_msg']))


        ### Querry current position
        position = client.my_position(endpoint = '/private/linear/position/list')
        if not position['ret_code']:
            for i in position['result']:
                if i['is_valid']:
                    if len(Position_List['symbol']) == 0 or Position_List['symbol'][-1] != i['data']['symbol']:
                        Position_List['symbol'].append(i['data']['symbol'])
                        Position_List['Buy'].append(i['data'])
                    else:
                        Position_List['Sell'].append(i['data'])
                else:
                    raise Exception('Querry Position data NOT valid')
        else:
            raise Exception('Querry Position Fail !!\tReturn code: {}\tReturn msg: {}'.format(position['ret_code'], position['ret_msg']))
        
        del position
        gc.collect()
        
        current_position_qty = 0
        for i in Symbol_List:
            if i.symbol in Position_List['symbol']:
                index = Position_List['symbol'].index(i.symbol)
                
                if Position_List['Buy'][index]['is_isolated'] and Position_List['Sell'][index]['is_isolated']:
                    i.isolate = True
                else:
                    i.isolate = False
                
                if Position_List['Buy'][index]['leverage'] == Leverage and Position_List['Sell'][index]['leverage'] == Leverage:
                    i.leverage = Leverage
                else:
                    i.leverage = 0

                if Position_List['Buy'][index]['tp_sl_mode'] == 'Full' and Position_List['Sell'][index]['tp_sl_mode'] == 'Full':
                    i.tpsl_mode = 'Full'
                else:
                    i.tpsl_mode = 'Partial'

                if Position_List['Buy'][index]['size'] + Position_List['Sell'][index]['size'] > 0:
                    current_position_qty += 1
                    i.opened =True

        log.log_and_show('Opened order : {}'.format(current_position_qty))

        ### Randonly open position
        if current_position_qty < Max_operate_position:
            open = Open()

            # Random pick
            open.ID = rand_symbol()
            open.sym = Symbol_List[open.ID].symbol

            # Set Full Position TP/SL
            if Symbol_List[open.ID].tpsl_mode != 'Full':
                temp = client.full_partial_position_tp_sl_switch(symbol = open.sym, tp_sl_mode = 'Full')
                if temp['ret_code'] == 0:
                    raise Exception('Set Full Position TP/SL Error\tReturn code: {}\tReturn msg: {}'.format(temp['ret_code'], temp['ret_msg']))
                Symbol_List[open.ID].tpsl_mode = 'Full'

            # Switch to isolated margin mode and set leverage
            if Symbol_List[open.ID].isolate != True:
                temp = client.cross_isolated_margin_switch(symbol = open.sym, is_isolated = True, buy_leverage = Leverage, sell_leverage = Leverage)
                if temp['ret_code']:
                    raise Exception('Set Margin mode Error\tReturn code: {}\tReturn msg: {}'.format(temp['ret_code'], temp['ret_msg']))
                Symbol_List[open.ID].isolate = True
                Symbol_List[open.ID].leverage = Leverage

            # Modify leverage
            if Symbol_List[open.ID].leverage != Leverage:
                temp = client.set_leverage(symbol = open.sym, buy_leverage = Leverage, sell_leverage = Leverage)
                if temp['ret_code']:
                    raise Exception('Set Leverage Error\tReturn code: {}\tReturn msg: {}'.format(temp['ret_code'], temp['ret_msg']))
                Symbol_List[open.ID].leverage = Leverage

            # Querry price
            temp = client.latest_information_for_symbol(symbol = open.sym)
            if temp['ret_code']:
                raise Exception('Querry current price Error\tReturn code: {}\tReturn msg: {}'.format(temp['ret_code'], temp['ret_msg']))
            else:
                open.price = (float)(temp['result'][0]['last_price'])
                
            # Calculate TP/SL
            open.side = rand_side()
            open.qty = qty_trim((operate_USDT * Leverage / open.price), Symbol_List[open.ID].qty_step)
            if open.side == 'Buy':
                open.TP = price_trim((1 + (TP_percentage / Leverage / 100)) * open.price, Symbol_List[open.ID].tick_size)
                open.SL = price_trim((1 - (SL_percentage / Leverage / 100)) * open.price, Symbol_List[open.ID].tick_size, True)
            elif open.side == 'Sell':
                open.TP = price_trim((1 - (TP_percentage / Leverage / 100)) * open.price, Symbol_List[open.ID].tick_size)
                open.SL = price_trim((1 + (SL_percentage / Leverage / 100)) * open.price, Symbol_List[open.ID].tick_size, True)
            
            log.log_and_show('Open {} {} {} order at {} with TP : {}, SL : {}'.format(open.qty, open.sym, open.side, open.price, open.TP, open.SL))
            

            # Open position
            open.posi = client.place_active_order(symbol = open.sym,\
                                                side = open.side,\
                                                order_type = "Market",\
                                                qty = open.qty,\
                                                time_in_force = "GoodTillCancel",\
                                                reduce_only = False,\
                                                close_on_trigger = False,\
                                                take_profit = open.TP,\
                                                stop_loss = open.SL)

            if open.posi['ret_code'] != 0:
                raise Exception('{} Order Create Fail !!\tReturn code: {}\tReturn msg: {}'.format(open.sym, open.posi['ret_code'], open.posi['ret_msg']))
            elif open.posi['ret_msg'] != 'OK':
                log.log_and_show('{} Order Create Successfully !!\tReturn msg: {}'.format(open.sym,open.posi['ret_msg']))
            else:
                log.log_and_show('{} Order Create Successfully !!'.format(open.sym))
            
            del open
            sleep(5)
        else:
            sleep(60)


    except Exception as Err:
        Error_Msg(Err)
        os.system('pause')
        os._exit(0)