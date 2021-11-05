from pybit import HTTP
from time import sleep
import os
import json
import random
random.seed()

import key

class Symbol:
    def __init__(self, Symbol, tick_size, qty_step) -> None:
        self.Symbol = Symbol
        self.tick_size = (float)(tick_size)
        self.qty_step = (float)(qty_step)
        self.opened = False
        self.isolate = False
        self.leverage = Leverage
        self.tpsl_mode = 'Full'

class Open:
    def __init__(self) -> None:
        self.ID = 0
        self.sym = ''
        self.price = 0
        self.qty = 0
        self.TP = 0
        self.SL = 0

Symbol_List = []

qty_step_list = []

Token_List = []


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

##############################################################################################################################
Cfg_missing = True
file_list = os.listdir()
for i in file_list:
    if i.endswith('.json'):
        file = open(i)
        Cfg_missing = False
        break

if Cfg_missing:
    System_Msg('Cfg.json file missing')
    print('cfg.json example : ')
    print('{\n\t\"Test_net\" : ,\n\t\"Max_operate_position\" : ,\n\t\"operate_USDT\" : ,\n\t\"Leverage\" : ,')
    print('\t"TP_percentage\" : ,\n\t\"SL_percentage\" : ,\n\Trade_all\" : ,\n\t\"Token\" : [')
    print('\t    "BTC\",\n\t    \"ETH\",\n\t    .. ,\n\t    .. ,\n\t]\n}')
    
    os.system('pause')
    os._exit(0)

else:
    Cfg_data = json.load(file)
    file.close()

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
### Connect client
try:
    if Test:
        client = HTTP(key.host_test, api_key=key.api, api_secret=key.api_secret)
    else:
        client = HTTP(key.host, api_key=key.api, api_secret=key.api_secret)
except :
    Error_Msg('Connect Error')
    os.system('pause')
    os._exit(0)

### Check Sym list
try:
    Symbol_querry = client.query_symbol()
    if not Symbol_querry['ret_code']:
        if not Trade_all:
            for i in Token_List:
                exist = 0
                for j in Symbol_querry['result']:
                    if i == j['name']:
                        exist = 1
                        Symbol_List.append(Symbol(i, j['price_filter']['tick_size'], j['lot_size_filter']['qty_step']))
                        break
                if not exist:
                    raise Exception('\"{}\" not exist in Symbol list'.format(i))
                else:
                    exist = 0
        else:
            for i in Symbol_querry['result']:
                if i['name'].endswith('USDT'):
                    # print('\t\t\"{}\",'.format(i['name'].split('USDT')[0]))
                    Symbol_List.append(Symbol(i['name'], i['price_filter']['tick_size'], i['lot_size_filter']['qty_step']))
        
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
            sleep(0.25)

        print('Opened order : {}'.format(current_position_qty))


        ### Randonly open position
        if current_position_qty < Max_operate_position:
            open = Open()

            # Random pick
            open.ID = rand_symbol()
            open.sym = Symbol_List[open.ID].Symbol

            # Set Full Position TP/SL
            if Symbol_List[open.ID].tpsl_mode != 'Full':
                temp = client.full_partial_position_tp_sl_switch(symbol = open.sym, tp_sl_mode = 'Full')
                # print(temp)
                if temp['ret_code'] == 0:
                    raise Exception('Set Full Position TP/SL Error\tReturn code: {}\tReturn msg: {}'.format(temp['ret_code'], temp['ret_msg']))
                Symbol_List[open.ID].tpsl_mode = 'Full'

            # Switch to isolated margin mode and set leverage
            if Symbol_List[open.ID].isolate != True:
                temp = client.cross_isolated_margin_switch(symbol = open.sym, is_isolated = True, buy_leverage = Leverage, sell_leverage = Leverage)
                # print(temp)
                if temp['ret_code']:
                    raise Exception('Set Margin mode Error\tReturn code: {}\tReturn msg: {}'.format(temp['ret_code'], temp['ret_msg']))
                Symbol_List[open.ID].isolate = True
                Symbol_List[open.ID].leverge = Leverage

            # Modify leverage
            if Symbol_List[open.ID].leverge != Leverage:
                temp = client.set_leverage(symbol = open.sym, buy_leverage = Leverage, sell_leverage = Leverage)
                if temp['ret_code']:
                    raise Exception('Set Leverage Error\tReturn code: {}\tReturn msg: {}'.format(temp['ret_code'], temp['ret_msg']))
                Symbol_List[open.ID].leverge = Leverage

            # Querry price
            temp = client.latest_information_for_symbol(symbol = open.sym)
            if temp['ret_code']:
                raise Exception('Querry current price Error\tReturn code: {}\tReturn msg: {}'.format(temp['ret_code'], temp['ret_msg']))
            else:
                open.price = (float)(temp['result'][0]['last_price'])
                

            # Calculate TP/SL
            open.qty = qty_trim((operate_USDT * Leverage / open.price), Symbol_List[open.ID].qty_step)
            open.TP = price_trim((1 + (TP_percentage / Leverage / 100)) * open.price, Symbol_List[open.ID].tick_size)
            open.SL = price_trim((1 - (SL_percentage / Leverage / 100)) * open.price, Symbol_List[open.ID].tick_size, True)

            print('Open {} {} Order at {} with TP : {}, SL : {}'.format(open.qty, open.sym, open.price, open.TP, open.SL))
            

            # Open position
            open.posi = client.place_active_order(symbol = open.sym,\
                                                side = "Buy",\
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
                print('{} Order Create Successfully !!\tReturn msg: {}'.format(open.sym,open.posi['ret_msg']))
            else:
                print('{} Order Create Successfully !!'.format(open.sym))
            
            del open
            sleep(30)
        else:
            sleep(60)


    except Exception as Err:
        Error_Msg(Err)
        os.system('pause')
        os._exit(0)