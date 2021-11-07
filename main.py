from pybit import HTTP
from time import localtime
from time import strftime
from datetime import datetime
import sys
import os
import json
import gc
import random
random.seed()

import Make_log
import key
import Update_Symbol_List
import Loading_animation

##########################################################
Version = '1.01'
Date = '2021/11/07'

Symbol_List = []

delay = Loading_animation.delay_anima()

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

class CFG:
    def __init__(self, version) -> None:
        self.version = version
        self.Test_net = True
        self.Max_operate_position = 5
        self.operate_USDT = 10
        self.Leverage = 20
        self.TP_percentage = 100
        self.SL_percentage = 10
        self.Group = 'all'
        self.open_order_interval = 1
        self.poll_order_interval = 60        
        self.Token_list = ['BTC', 'ETH']

    
    def make_cfg(self):
        self.cfg_init = {'Version' : Version,
                    'Run_on_testnet' : True,
                    'Operate_position' : 5,
                    'Order_value_USDT' : 10,
                    'Leverage' : 20,
                    'TP_percentage' : 100,
                    'SL_percentage' : 10,
                    'Favorite_group' : 'all',
                    'open_interval' : 1,
                    'poll_interval' : 60,
                    'Group_0' : [
                        'BTC',  'ETH',  'DOT',  'SOL',
                        'BNB',  'FTT',  'UNI',  'AXS',
                        'LUNA', 'ATOM', 'AAVE', 'FTM',
                        'BIT',  'ADA',  'ICP'
                        ]
                    }
        with open('cfg.json', 'w') as file:
            json.dump(self.cfg_init, file, indent = 4)
        del self.cfg_init
        gc.collect()

    def load_cfg(self):
        with open('cfg.json', 'r') as file:
            self.cfg = json.load(file)

        self.version = self.cfg['Version']
        self.Test_net = self.cfg['Run_on_testnet']
        self.Max_operate_position = self.cfg['Operate_position']
        self.operate_USDT = self.cfg['Order_value_USDT']
        self.Leverage = self.cfg['Leverage']
        self.TP_percentage = self.cfg['TP_percentage']
        self.SL_percentage = self.cfg['SL_percentage']
        self.Group = self.cfg['Favorite_group']
        self.open_order_interval = self.cfg['open_interval']
        self.poll_order_interval = self.cfg['poll_interval']
        self.Token_list.clear()
        if self.Group in self.cfg:
            for i in self.cfg[self.Group]:
                self.Token_list.append('{}USDT'.format(i))
        else:
            self.Group = 'all'
        
    def update_version(self):
        self.version = Version
        self.cfg['Version'] = self.version
        with open('cfg.json', 'w') as file:
            json.dump(self.cfg, file, indent = 4)



def Error_Msg(str, extreme = 0):
    log.log(str)
    time = datetime.now()
    if extreme:
        os.system('echo [41m{} : {}'.format(time.strftime('%H:%M:%S'), str))
        os.system('echo [0m{} :'.format(time.strftime('%H:%M:%S')))
    else:
        os.system('echo [31m{} : {}'.format(time.strftime('%H:%M:%S'), str))
        os.system('echo [0m{} :'.format(time.strftime('%H:%M:%S')))

def System_Msg(str):
    log.log(str)
    time = datetime.now()
    os.system('echo [33m{} : {}'.format(time.strftime('%H:%M:%S'), str))
    os.system('echo [0m{} :'.format(time.strftime('%H:%M:%S')))
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
log.log_and_show('Bybit USDT perpetual trading bot ver {} {}'.format(Version, Date))
log.log_and_show('========================START=========================')

##############################################################################################################################
### Load Cfg File
cfg = CFG(Version)

if not os.path.isfile('cfg.json'):
    System_Msg('cfg.json file missing. Generate a new one')
    cfg.make_cfg()
    os.system('pause')

cfg.load_cfg()
if (int)(cfg.version.split('.')[0]) != (int)(Version.split('.')[0]):
    # Main version different
    System_Msg('cfg.json main version defferent, archive as cfg_{}.json'.format(strftime('%Y%m%d-%H;%M;%S', localtime(os.path.getmtime('cfg.json')))))
    log.log_and_show('Generate new cfg.json')
    os.rename('cfg.json', 'cfg_{}.json'.format(strftime('%Y%m%d-%H;%M;%S', localtime(os.path.getmtime('cfg.json')))))
    cfg.make_cfg()
    os.system('pause')
    os._exit(0)

elif (int)(cfg.version.split('.')[1]) < (int)(Version.split('.')[1]):
    #Sub version different
    cfg.update_version()


if cfg.open_order_interval < 1:
    cfg.open_order_interval = 1
    
if cfg.poll_order_interval < 10:
    cfg.poll_order_interval = 10

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
    if len(sys.argv) == 3 and not cfg.Test_net:
        # main net api and serect were passed
        log.log_and_show('Operate on Main Net !!!')
        client = HTTP(key.host, api_key=sys.argv[1], api_secret=sys.argv[2])
    else:
        client = HTTP(key.test_host, api_key=key.test_api, api_secret=key.test_secret)
except :
    Error_Msg('Connect Error')
    os.system('pause')
    os._exit(0)

### Check Sym list
if cfg.Group == 'all':
    for i in Symbol_querry['data']:
        Symbol_List.append(Symbol(i['name'], i['price_filter']['tick_size'], i['lot_size_filter']['qty_step']))
else:
    for i in cfg.Token_list:
        if i in Symbol_querry['name']:
            sym = Symbol_querry['data'][Symbol_querry['name'].index(i)]
            Symbol_List.append(Symbol(sym['name'], sym['price_filter']['tick_size'], sym['lot_size_filter']['qty_step']))

while True:
    try:
        ### Querry current wallet balance
        wallet = client.get_wallet_balance(coin="USDT")
        if not wallet['ret_code']:
            wallet_available = wallet['result']['USDT']['available_balance']
            wallet_equity = wallet['result']['USDT']['equity']
            log.show('')  
            log.log_and_show('Balance available:\t{:.2f}\tUSDT'.format(wallet_available))
            log.log_and_show('Balance equity:\t{:.2f}\tUSDT'.format(wallet_equity))
        else:
            raise Exception('Querry Wallet Fail !!\tReturn code: {}\tReturn msg: {}'.format(wallet['ret_code'], wallet['ret_msg']))


        ### Querry current position
        current_position_qty = 0
        Position_List = {'symbol' : [], 'Buy' : [], 'Sell' : []}
        opened_order = []

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
        
        for i in Symbol_List:
            if i.symbol in Position_List['symbol']:
                index = Position_List['symbol'].index(i.symbol)
                
                if Position_List['Buy'][index]['is_isolated'] and Position_List['Sell'][index]['is_isolated']:
                    i.isolate = True
                else:
                    i.isolate = False
                
                if Position_List['Buy'][index]['leverage'] == cfg.Leverage and Position_List['Sell'][index]['leverage'] == cfg.Leverage:
                    i.leverage = cfg.Leverage
                else:
                    i.leverage = 0

                if Position_List['Buy'][index]['tp_sl_mode'] == 'Full' and Position_List['Sell'][index]['tp_sl_mode'] == 'Full':
                    i.tpsl_mode = 'Full'
                else:
                    i.tpsl_mode = 'Partial'
                
                if Position_List['Buy'][index]['position_value'] + Position_List['Sell'][index]['position_value'] > 0:
                    current_position_qty += 1
                    if Position_List['Buy'][index]['position_value'] > 0:
                        opened_order.append('  {}\t{}'.format(Position_List['symbol'][index], 'Buy'))
                    elif Position_List['Sell'][index]['position_value'] > 0:
                        opened_order.append('  {}\t{}'.format(Position_List['symbol'][index], 'Sell'))
                    i.opened =True

        log.show('')       
        log.log_and_show('Opened Position: {}'.format(current_position_qty))
        for i in opened_order:
            log.log_and_show('\t{}'.format(i))

        del opened_order
        del position
        del Position_List


        ### Randonly open position
        if current_position_qty < cfg.Max_operate_position:
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
                temp = client.cross_isolated_margin_switch(symbol = open.sym, is_isolated = True, buy_leverage = cfg.Leverage, sell_leverage = cfg.Leverage)
                if temp['ret_code']:
                    raise Exception('Set Margin mode Error\tReturn code: {}\tReturn msg: {}'.format(temp['ret_code'], temp['ret_msg']))
                Symbol_List[open.ID].isolate = True
                Symbol_List[open.ID].leverage = cfg.Leverage

            # Modify leverage
            if Symbol_List[open.ID].leverage != cfg.Leverage:
                temp = client.set_leverage(symbol = open.sym, buy_leverage = cfg.Leverage, sell_leverage = cfg.Leverage)
                if temp['ret_code']:
                    raise Exception('Set Leverage Error\tReturn code: {}\tReturn msg: {}'.format(temp['ret_code'], temp['ret_msg']))
                Symbol_List[open.ID].leverage = cfg.Leverage

            # Querry price
            temp = client.latest_information_for_symbol(symbol = open.sym)
            if temp['ret_code']:
                raise Exception('Querry current price Error\tReturn code: {}\tReturn msg: {}'.format(temp['ret_code'], temp['ret_msg']))
            else:
                open.price = (float)(temp['result'][0]['last_price'])
                
            # Calculate TP/SL
            open.side = rand_side()
            open.qty = qty_trim((cfg.operate_USDT * cfg.Leverage / open.price), Symbol_List[open.ID].qty_step)
            if open.side == 'Buy':
                open.TP = price_trim((1 + (cfg.TP_percentage / cfg.Leverage / 100)) * open.price, Symbol_List[open.ID].tick_size)
                open.SL = price_trim((1 - (cfg.SL_percentage / cfg.Leverage / 100)) * open.price, Symbol_List[open.ID].tick_size, True)
            elif open.side == 'Sell':
                open.TP = price_trim((1 - (cfg.TP_percentage / cfg.Leverage / 100)) * open.price, Symbol_List[open.ID].tick_size)
                open.SL = price_trim((1 + (cfg.SL_percentage / cfg.Leverage / 100)) * open.price, Symbol_List[open.ID].tick_size, True)
            
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
            gc.collect()
            delay.delay(cfg.open_order_interval)
        else:
            delay.anima_bar(cfg.poll_order_interval)


    except Exception as Err:
        Error_Msg(Err)
        os.system('pause')
        os._exit(0)