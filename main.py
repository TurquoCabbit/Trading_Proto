from logging import PlaceHolder
from types import coroutine
from pybit import HTTP
from time import localtime
from time import strftime
from time import time
from datetime import datetime
import sys
import os
import json
import gc
import random
random.seed()

import Make_log
import Update_Symbol_List
import Loading_animation
from error_code import get_error_msg

##########################################################
Version = '3.04'
Date = '2021/11/13'

Start_time = (int)(time())

Symbol_List = []

delay = Loading_animation.delay_anima()

##############################################################################################################################
### init log
log = Make_log.Log('log')
log.log()
log.log('=============================START==============================')
log.log_and_show('Bybit USDT perpetual trading bot ver {} {}'.format(Version, Date))

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
        self.trailing = 0

class CFG:
    def __init__(self, version) -> None:
        self.version = version
        self.Test_net = True
        self.Max_operate_position = None
        self.operate_USDT = None
        self.Leverage = None
        self.side = None
        self.TP_percentage = None
        self.SL_percentage = None
        self.Trigger = None
        self.Trailing_Stop = None
        self.Group = None
        self.open_order_interval = None
        self.poll_order_interval = None
        self.Token_list = []
        self.Black_list = []
        
        self.cfg_init = {
                            'Version' : Version,
                            'Run_on_testnet' : True,
                            'Operate_position' : 5,
                            'Order_value_USDT' : 10,
                            'Leverage' : 20,
                            'Side' : 'Both',
                            'TP_percentage' : 100,
                            'SL_percentage' : 10,
                            'Trigger' : 'LastPrice',
                            'Trailing_Stop_percentag' : 0,
                            'Favorite_group' : 'all',
                            'open_interval' : 1,
                            'poll_interval' : 60,
                            'Black_list' : [],
                            'Group_0' : [
                                'BTC',  'ETH',  'DOT',  'SOL',
                                'BNB',  'FTT',  'UNI',  'AXS',
                                'LUNA', 'ATOM', 'AAVE', 'FTM',
                                'BIT',  'ADA',  'ICP'
                                ]
                        }

    
    def new_cfg(self):
        with open('cfg.json', 'w') as file:
            json.dump(self.cfg_init, file, indent = 4)

    def load_cfg(self):
        with open('cfg.json', 'r') as file:
            self.cfg = json.load(file)
        try:
            self.version = self.cfg['Version']
            if self.version != Version:
                return False

            self.Test_net = self.cfg['Run_on_testnet']
            self.Max_operate_position = self.cfg['Operate_position']
            self.operate_USDT = self.cfg['Order_value_USDT']
            self.Leverage = self.cfg['Leverage']
            self.side = self.cfg['Side']
            self.TP_percentage = self.cfg['TP_percentage']
            self.SL_percentage = self.cfg['SL_percentage']
            self.Trigger = self.cfg['Trigger']
            self.Trailing_Stop = self.cfg['Trailing_Stop_percentag']

            self.Group = self.cfg['Favorite_group']
            self.open_order_interval = self.cfg['open_interval']
            self.poll_order_interval = self.cfg['poll_interval']
            self.Black_list.clear()
            for i in self.cfg['Black_list']:
                self.Black_list.append('{}USDT'.format(i))

            self.Token_list.clear()
            if self.Group in self.cfg and self.Group != 'Black_list':
                for i in self.cfg[self.Group]:
                    self.Token_list.append('{}USDT'.format(i))
            else:
                self.Group = 'all'
            return True
        
        except KeyError:
            self.archive_cfg('cfg.json corrupted, archive as cfg_{}.json'.format(strftime('%Y%m%d-%H;%M;%S', localtime(os.path.getmtime('cfg.json')))))
    
    def update_version(self):
        self.version = Version
        self.cfg['Version'] = self.version
        with open('cfg.json', 'w') as file:
            json.dump(self.cfg, file, indent = 4)
    
    def upgrade_cfg(self):
        System_Msg('cfg.json upgraded, archive as cfg_{}.json'.format(strftime('%Y%m%d-%H;%M;%S', localtime(os.path.getmtime('cfg.json')))))
        if not os.path.isdir('archive'):
            os.mkdir('archive')
        os.rename('cfg.json', 'archive/cfg_{}.json'.format(strftime('%Y%m%d-%H;%M;%S', localtime(os.path.getmtime('cfg.json')))))

        for i in self.cfg_init:
            if not i in self.cfg:
                self.cfg[i] = self.cfg_init[i]

        self.update_version()

        log.log_and_show('Upgrade cfg.json')
        os.system('pause')
        os._exit(0)

    def archive_cfg(self, msg):
        System_Msg(msg)
        if not os.path.isdir('archive'):
            os.mkdir('archive')
        os.rename('cfg.json', 'archive/cfg_{}.json'.format(strftime('%Y%m%d-%H;%M;%S', localtime(os.path.getmtime('cfg.json')))))
        self.new_cfg()
        log.log_and_show('Generate new cfg.json')
        os.system('pause')
        os._exit(0)

def Error_Msg(str = ''):
    log.log(str)
    str = str.split('\n')

    for i in str:
        os.system('echo [31m{} : {}'.format(datetime.now().strftime('%H:%M:%S'), i))        
    os.system('echo [0m{} :'.format(datetime.now().strftime('%H:%M:%S')))

def System_Msg(str = ''):
    log.log(str)
    str = str.split('\n')

    for i in str:
        os.system('echo [33m{} : {}'.format(datetime.now().strftime('%H:%M:%S'), i))
    os.system('echo [0m{} :'.format(datetime.now().strftime('%H:%M:%S')))

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
### Load Cfg File
cfg = CFG(Version)

if not os.path.isfile('cfg.json'):
    System_Msg('cfg.json file missing. Generate a new one')
    cfg.new_cfg()
    os.system('pause')

if not cfg.load_cfg():
    if (int)(cfg.version.split('.')[0]) != (int)(Version.split('.')[0]):
        # Main version different
        cfg.upgrade_cfg()

    elif (int)(cfg.version.split('.')[1]) < (int)(Version.split('.')[1]):
        #Sub version different
        cfg.update_version()

### Check parameter
if cfg.open_order_interval < 1:
    cfg.open_order_interval = 1
    
if cfg.poll_order_interval < 10:
    cfg.poll_order_interval = 10

if cfg.side != 'Buy' and cfg.side != 'Sell':
    cfg.side = 'Both'

if cfg.Trigger != 'MarkPrice' and cfg.Trigger != 'LastPrice' and cfg.Trigger != 'IndexPrice':
    cfg.Trigger = 'LastPrice'

log.log_and_show('cfg.json loaded:')
log.log('\t\tVersion: {}\n\
         \tRun on test net: {}\n\
         \tOperate position: {}\n\
         \tOperate USDT: {}\n\
         \tLeverage: {}\n\
         \tOperate side: {}\n\
         \tTP: {}%\n\
         \tSL: {}%\n\
         \tTPSL trigger: {}\n\
         \tTrailing stop: {}%\n\
         \tOperate group: {}\n\
         \tOpen order interval: {}s\n\
         \tPolling interval: {}s'.format(\
         cfg.version, cfg.Test_net, cfg.Max_operate_position,\
         cfg.operate_USDT, cfg.Leverage, cfg.side, cfg.TP_percentage,\
         cfg.SL_percentage, cfg.Trigger, cfg.Trailing_Stop, cfg.Group,\
         cfg.open_order_interval, cfg.poll_order_interval))

##############################################################################################################################
### Load Symbol List
if not os.path.isfile('Symbol_list.json'):
    if Update_Symbol_List.Query_USDT_Perpetual_Symbol():
        with open('Symbol_list.json', 'r') as file:
            Symbol_query = json.load(file)
else:    
    with open('Symbol_list.json', 'r') as file:
        Symbol_query = json.load(file)

    if Symbol_query['version'] != Update_Symbol_List.Symbol_list_ver:
        if Update_Symbol_List.Query_USDT_Perpetual_Symbol():
            with open('Symbol_list.json', 'r') as file:
                Symbol_query = json.load(file)

##############################################################################################################################
### Create client
if len(sys.argv) == 3:
    if cfg.Test_net:
        # main net api and serect were passed
        log.log_and_show('Operate on Test Net !!!')
        client = HTTP('https://api-testnet.bybit.com', api_key=sys.argv[1], api_secret=sys.argv[2])
    else:
        # main net api and serect were passed
        log.log_and_show('Operate on Main Net !!!')
        client = HTTP('https://api.bybit.com', api_key=sys.argv[1], api_secret=sys.argv[2])
else:
    log.show('Execution cmd :')
    log.show('main.exe <api key> <api secret>')
    os.system('pause')
    os._exit(0)

### Check Sym list
if cfg.Group == 'all':
    for i in Symbol_query['data']:
        if not i['name'] in cfg.Black_list:
            Symbol_List.append(Symbol(i['name'], i['price_filter']['tick_size'], i['lot_size_filter']['qty_step']))
else:
    for i in cfg.Token_list:
        if i in Symbol_query['name'] and not i in cfg.Black_list:
            sym = Symbol_query['data'][Symbol_query['name'].index(i)]
            Symbol_List.append(Symbol(sym['name'], sym['price_filter']['tick_size'], sym['lot_size_filter']['qty_step']))


while True:
    log.log_and_show(log.get_run_time(Start_time))

    ### Check if eligible symbol qty exceed max operated qty
    if cfg.Max_operate_position > len(Symbol_List):
        System_Msg('Decrease Operate_position form {} to {}'.format(cfg.Max_operate_position, len(Symbol_List)))
        cfg.Max_operate_position = len(Symbol_List)

    
    try:
        ### Query current wallet balance
        try:
            wallet = client.get_wallet_balance(coin = "USDT")
            wallet_available = wallet['result']['USDT']['available_balance']
            wallet_equity = wallet['result']['USDT']['equity']
            log.show('')
            log.log_and_show('Balance available:\t{:.2f}\tUSDT'.format(wallet_available))
            log.log_and_show('Balance equity:\t{:.2f}\tUSDT'.format(wallet_equity))
        except Exception as err:
            err = str(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            Error_Msg('Get wallet balance Fail!!\n#{} : {}\n{}'.format(ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case '10003':   # invalid api_key 
                    os.system('pause')
                    os._exit(0)
                case _:
                    log.log('untrack_error_code')
                    pass


        ### Query current position
        current_position_qty = 0
        current_position_buy = 0
        current_position_sel = 0
        Position_List = {'symbol' : [], 'Buy' : [], 'Sell' : []}
        opened_order = []

        try:
            position = client.my_position(endpoint = '/private/linear/position/list')
        except Exception as err:
            err = str(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            Error_Msg('Query Position Fail!!\n#{} : {}\n{}'.format(ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case _:
                    log.log('untrack_error_code')
                    os.system('pause')
                    os._exit(0)
                    
        if not position['ret_code']:
            for i in position['result']:
                if i['is_valid']:
                    if len(Position_List['symbol']) == 0 or Position_List['symbol'][-1] != i['data']['symbol']:
                        Position_List['symbol'].append(i['data']['symbol'])
                        Position_List['Buy'].append(i['data'])
                    else:
                        Position_List['Sell'].append(i['data'])
                else:
                    Error_Msg('{} position data NOT valid'.format(i['data']['symbol']))
        
        ### Chek position status
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
                
                if Position_List['Buy'][index]['size'] + Position_List['Sell'][index]['size'] > 0:
                    current_position_qty += 1
                    if Position_List['Buy'][index]['position_value'] > 0:
                        current_position_buy += 1
                        opened_order.append('  {}\t{}'.format(Position_List['symbol'][index], 'Buy'))
                    elif Position_List['Sell'][index]['position_value'] > 0:
                        current_position_sel += 1
                        opened_order.append('  {}\t{}'.format(Position_List['symbol'][index], 'Sell'))
                    i.opened = True
                else:
                    i.opened = False
        
        log.show('')
        log.log_and_show('Opened Position: {}\tBuy: {} Sell: {}'.format(current_position_qty, current_position_buy, current_position_sel))
        for i in opened_order:
            log.show('\t{}'.format(i))
        
        log.show('')

        del opened_order
        del position
        del Position_List
        
        ### Randonly open position
        if current_position_qty < cfg.Max_operate_position:
            open = Open()

            # Random pick
            open.ID = rand_symbol()
            open.sym = Symbol_List[open.ID].symbol
            if cfg.side == 'Both':
                open.side = rand_side()
            else:
                open.side = cfg.side

            # Set Full Position TP/SL
            if Symbol_List[open.ID].tpsl_mode != 'Full':
                try:
                    temp = client.full_partial_position_tp_sl_switch(symbol = open.sym, tp_sl_mode = 'Full')
                    Symbol_List[open.ID].tpsl_mode = 'Full'
                except Exception as err:
                    err = str(err)
                    ret_code = err.split('(ErrCode: ')[1].split(')')[0]
                    ret_note = err.split('(ErrCode: ')[0]
                    Error_Msg('Set {} TPSL mode Fail!!\n#{} : {}\n{}'.format(open.sym, ret_code, get_error_msg(ret_code), ret_note))
                    match ret_code:
                        case _:
                            log.log('untrack_error_code')
                            Symbol_List.pop(open.ID)
                            System_Msg('Remove {} from Symbol List'. format(open.sym))
                            continue

            # Switch to isolated margin mode and set leverage
            if Symbol_List[open.ID].isolate != True:
                try:
                    temp = client.cross_isolated_margin_switch(symbol = open.sym, is_isolated = True,\
                                                               buy_leverage = cfg.Leverage, sell_leverage = cfg.Leverage)
                    Symbol_List[open.ID].isolate = True
                    Symbol_List[open.ID].leverage = cfg.Leverage
                except Exception as err:
                    err = str(err)
                    ret_code = err.split('(ErrCode: ')[1].split(')')[0]
                    ret_note = err.split('(ErrCode: ')[0]
                    Error_Msg('Set {} margin mode Fail!!\n#{} : {}\n{}'.format(open.sym, ret_code, get_error_msg(ret_code), ret_note))
                    match ret_code:
                        case _:
                            log.log('untrack_error_code')
                            Symbol_List.pop(open.ID)
                            System_Msg('Remove {} from Symbol List'. format(open.sym))
                            continue

            # Modify leverage
            if Symbol_List[open.ID].leverage != cfg.Leverage:
                try:
                    temp = client.set_leverage(symbol = open.sym, buy_leverage = cfg.Leverage, sell_leverage = cfg.Leverage)
                    Symbol_List[open.ID].leverage = cfg.Leverage
                except Exception as err:
                    err = str(err)
                    ret_code = err.split('(ErrCode: ')[1].split(')')[0]
                    ret_note = err.split('(ErrCode: ')[0]
                    Error_Msg('Set {} leverage Fail!!\n#{} : {}\n{}'.format(open.sym, ret_code, get_error_msg(ret_code), ret_note))
                    match ret_code:
                        case _:
                            log.log('untrack_error_code')
                            Symbol_List.pop(open.ID)
                            System_Msg('Remove {} from Symbol List'. format(open.sym))
                            continue

            # Query price
            try:
                temp = client.latest_information_for_symbol(symbol = open.sym)
                open.price = (float)(temp['result'][0]['last_price'])
            except Exception as err:
                err = str(err)
                ret_code = err.split('(ErrCode: ')[1].split(')')[0]
                ret_note = err.split('(ErrCode: ')[0]
                Error_Msg('Get {} price Fail!!\n#{} : {}\n{}'.format(open.sym, ret_code, get_error_msg(ret_code), ret_note))
                match ret_code:
                    case _:
                        log.log('untrack_error_code')
                        Symbol_List.pop(open.ID)
                        System_Msg('Remove {} from Symbol List'. format(open.sym))
                        continue

            # Calculate rough TP/SL and qty
            open.qty = qty_trim((cfg.operate_USDT * cfg.Leverage / open.price), Symbol_List[open.ID].qty_step)
            if open.side == 'Buy':
                open.TP = price_trim((1 + (cfg.TP_percentage / cfg.Leverage / 100)) * open.price, Symbol_List[open.ID].tick_size)
                open.SL = price_trim((1 - (cfg.SL_percentage / cfg.Leverage / 100)) * open.price, Symbol_List[open.ID].tick_size, True)
            elif open.side == 'Sell':
                open.TP = price_trim((1 - (cfg.TP_percentage / cfg.Leverage / 100)) * open.price, Symbol_List[open.ID].tick_size)
                open.SL = price_trim((1 + (cfg.SL_percentage / cfg.Leverage / 100)) * open.price, Symbol_List[open.ID].tick_size, True)
            
            log.log_and_show('Opening {} {} {} order at about {}'.format(open.qty, open.sym, open.side, open.price))

            # Open order
            try:
                open.posi = client.place_active_order(
                                                        symbol = open.sym,\
                                                        side = open.side,\
                                                        order_type = "Market",\
                                                        qty = open.qty,\
                                                        time_in_force = "GoodTillCancel",\
                                                        reduce_only = False,\
                                                        close_on_trigger = False,\
                                                        take_profit = open.TP,\
                                                        stop_loss = open.SL
                                                    )
                if open.posi['ret_msg'] != 'OK':
                    System_Msg('{} Order Create Successfully !!\nwith return msg: {}'.format(open.sym,open.posi['ret_msg']))
                else:
                    log.log_and_show('{} Order Create Successfully !!'.format(open.sym))
            except Exception as err:
                err = str(err)
                log.log(err)
                ret_code = err.split('(ErrCode: ')[1].split(')')[0]
                ret_note = err.split('(ErrCode: ')[0]
                Error_Msg('Open {} order Fail!!\n#{} : {}\n{}'.format(open.sym, ret_code, get_error_msg(ret_code), ret_note))
                match ret_code:
                    case '130023':
                        Symbol_List.pop(open.ID)
                        System_Msg('Remove {} from Symbol List'. format(open.sym))
                        continue
                    case _:
                        log.log('untrack_error_code')
                        Symbol_List.pop(open.ID)
                        System_Msg('Remove {} from Symbol List'. format(open.sym))
                        continue

            try:
                retry = 3
                while retry:
                    #Get entry price                    
                    temp = client.my_position(symbol = open.sym)
                    if open.side == 'Buy':
                        if temp['result'][0]['size'] > 0:
                                open.price = (float)(temp['result'][0]['entry_price'])
                                # Calculate new TP/SL
                                open.TP = price_trim((1 + (cfg.TP_percentage / cfg.Leverage / 100)) * open.price, Symbol_List[open.ID].tick_size)
                                open.SL = price_trim((1 - (cfg.SL_percentage / cfg.Leverage / 100)) * open.price, Symbol_List[open.ID].tick_size, True)
                                break
                    elif open.side == 'Sell':
                        if temp['result'][1]['size'] > 0:
                            open.price = (float)(temp['result'][1]['entry_price'])
                            # Calculate new TP/SL
                            open.TP = price_trim((1 - (cfg.TP_percentage / cfg.Leverage / 100)) * open.price, Symbol_List[open.ID].tick_size)
                            open.SL = price_trim((1 + (cfg.SL_percentage / cfg.Leverage / 100)) * open.price, Symbol_List[open.ID].tick_size, True)
                            break
                    delay.delay(0.2)
                    retry -= 1

                if not retry:
                    Error_Msg('Get {} position entry retry Fail!!'.format(open.sym))
                    continue
            except Exception as err:
                err = str(err)
                ret_code = err.split('(ErrCode: ')[1].split(')')[0]
                ret_note = err.split('(ErrCode: ')[0]
                Error_Msg('Get {} position entry price Fail!!\n#{} : {}\n{}'.format(open.sym, ret_code, get_error_msg(ret_code), ret_note))
                match ret_code:
                    case _:
                        log.log('untrack_error_code')
                        continue

            
            # Calculate Trailing price
            try:
                if cfg.Trailing_Stop != 0:
                    open.trailing = price_trim(open.price * (cfg.Trailing_Stop / cfg.Leverage / 100), Symbol_List[open.ID].tick_size)

                    # Set trailing stop
                    temp = client.set_trading_stop(symbol = open.sym, side = open.side, trailing_stop = open.trailing,\
                                                take_profit = open.TP, stop_loss = open.SL,\
                                                tp_trigger_by = cfg.Trigger, sl_trigger_by = cfg.Trigger)
                else:
                    # fine tune TPSL
                    temp = client.set_trading_stop(symbol = open.sym, side = open.side,\
                                                take_profit = open.TP, stop_loss = open.SL,\
                                                tp_trigger_by = cfg.Trigger, sl_trigger_by = cfg.Trigger)
            except Exception as err:
                err = str(err)
                ret_code = err.split('(ErrCode: ')[1].split(')')[0]
                ret_note = err.split('(ErrCode: ')[0]
                Error_Msg('Set {} trailing and fine tune TPSL Fail!!\n#{} : {}\n{}'.format(open.sym, ret_code, get_error_msg(ret_code), ret_note))
                match ret_code:
                    case _:
                        log.log('untrack_error_code')
                        continue
                        
            log.log_and_show('Entry pirce : {}'.format(open.price))
            if cfg.Trailing_Stop != 0:
                log.log_and_show('TP : {},  SL : {},  Trailing stop : {}'.format(open.TP, open.SL, open.trailing))
            else:
                log.log_and_show('TP : {},  SL : {}'.format(open.TP, open.SL))
            log.show('')

            del open
            gc.collect()
            delay.delay(cfg.open_order_interval)
        else:
            delay.anima_runtime(cfg.poll_order_interval, Start_time)


    except Exception as Err:
        log.log(Err)
        os.system('pause')
        os._exit(0)